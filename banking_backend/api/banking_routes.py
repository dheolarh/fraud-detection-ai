"""
Banking API Routes
REST APIs for fraud backend to query transaction data
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from database import get_db
from models.database import User, Transaction
from schemas import TransactionCreate, TransactionResponse
from v2.transaction_context_builder import build_context_payload

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["banking"])


def _build_account_profile(
    db: Session,
    subject_user: Optional[User],
    sender_id: str,
    receiver_id: str,
) -> Dict[str, Any]:
    """Build lightweight account profile features for smarter fraud analysis payload."""
    if not subject_user:
        return {}

    now = datetime.utcnow()
    created_at = subject_user.created_at or now
    account_age_days = max(0, (now - created_at).days)

    user_txn_query = db.query(Transaction).filter(
        (Transaction.sender_id == subject_user.user_id) | (Transaction.receiver_id == subject_user.user_id)
    )

    avg_amount = user_txn_query.with_entities(func.avg(Transaction.amount)).scalar()
    daily_count = user_txn_query.filter(Transaction.timestamp >= now - timedelta(hours=24)).count()

    beneficiary_pair_query = db.query(Transaction).filter(
        (
            (Transaction.sender_id == sender_id)
            & (Transaction.receiver_id == receiver_id)
        )
        |
        (
            (Transaction.sender_id == receiver_id)
            & (Transaction.receiver_id == sender_id)
        )
    )

    beneficiary_history_count = beneficiary_pair_query.count()
    beneficiary_avg_amount = beneficiary_pair_query.with_entities(func.avg(Transaction.amount)).scalar()

    first_beneficiary_txn = (
        db.query(Transaction)
        .filter(
            (
                (Transaction.sender_id == sender_id)
                & (Transaction.receiver_id == receiver_id)
            )
            |
            (
                (Transaction.sender_id == receiver_id)
                & (Transaction.receiver_id == sender_id)
            )
        )
        .order_by(Transaction.timestamp.asc())
        .first()
    )

    beneficiary_age_days = None
    if first_beneficiary_txn and first_beneficiary_txn.timestamp:
        beneficiary_age_days = max(0, (now - first_beneficiary_txn.timestamp).days)

    beneficiary_first_seen = None
    if first_beneficiary_txn and first_beneficiary_txn.timestamp:
        beneficiary_first_seen = first_beneficiary_txn.timestamp.isoformat()

    return {
        "account_age_days": account_age_days,
        "avg_transaction_amount": float(avg_amount) if avg_amount is not None else 0.0,
        "daily_txn_count_24h": daily_count,
        "beneficiary_age_days": beneficiary_age_days,
        "beneficiary_history_count": beneficiary_history_count,
        "beneficiary_first_seen": beneficiary_first_seen,
        "beneficiary_avg_amount": float(beneficiary_avg_amount) if beneficiary_avg_amount is not None else 0.0,
    }


@router.get("/transactions")
async def get_transactions(
    user_id: str = Query(..., description="User ID to filter transactions"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=10000, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    transaction_flow: Optional[str] = Query(None, description="'incoming' or 'outgoing'"),
    db: Session = Depends(get_db)
):
    """
    Get transactions for a user with optional filters
    
    Used by fraud backend to analyze transaction history
    """
    try:
        # Build query
        query = db.query(Transaction).filter(
            (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
        )
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Transaction.timestamp <= datetime.fromisoformat(end_date))
        if transaction_flow:
            query = query.filter(Transaction.transaction_flow == transaction_flow)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and order
        transactions = query.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Format response
        from config import BANK_CURRENCY
        
        return {
            "transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "sender_id": t.sender_id,
                    "sender_name": t.sender_name,
                    "receiver_id": t.receiver_id,
                    "receiver_name": t.receiver_name,
                    "transaction_flow": t.transaction_flow,
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "amount_in_bank_currency": float(t.amount_in_bank_currency) if t.amount_in_bank_currency else float(t.amount),  # Read from DB
                    "bank_currency": BANK_CURRENCY,
                    "category": t.category,
                    "location": t.location,
                    "narration": t.narration,
                    "timestamp": t.timestamp.isoformat(),
                    "status": t.status
                }
                for t in transactions
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}\n\nTRACEBACK:\n{tb}")


@router.get("/users/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get user account information
    
    Returns basic account details including current balance
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "account_balance": float(user.account_balance),
            "is_frozen": user.is_frozen,
            "created_at": user.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.get("/bank/location")
async def get_bank_location():
    """
    Get bank's physical location and currency
    
    Dynamically determined from config.py
    """
    from config import get_bank_info
    return get_bank_info()


@router.get("/transactions/stats")
async def get_transaction_stats(
    user_id: str = Query(..., description="User ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get transaction statistics for behavioral analysis
    
    Used by fraud backend to understand user's normal spending patterns
    """
    try:
        # Build base query
        query = db.query(Transaction).filter(
            (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(Transaction.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Transaction.timestamp <= datetime.fromisoformat(end_date))
        
        transactions = query.all()
        
        if not transactions:
            return {
                "total_incoming": 0,
                "total_outgoing": 0,
                "avg_transaction_amount": 0,
                "transaction_count": 0,
                "most_common_categories": [],
                "avg_monthly_income": 0,
                "avg_monthly_spending": 0
            }
        
        # Calculate statistics
        incoming_txns = [t for t in transactions if t.transaction_flow == 'incoming']
        outgoing_txns = [t for t in transactions if t.transaction_flow == 'outgoing']
        
        total_incoming = sum(float(t.amount_in_bank_currency) for t in incoming_txns)
        total_outgoing = sum(float(t.amount_in_bank_currency) for t in outgoing_txns)
        
        # Category frequency
        category_counts = {}
        for t in transactions:
            if t.category:
                category_counts[t.category] = category_counts.get(t.category, 0) + 1
        
        most_common = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_categories = [cat for cat, _ in most_common]
        
        # Monthly averages (approximate based on date range)
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            months = max(1, (end_dt - start_dt).days / 30)
        else:
            # Assume all data
            months = 36  # 3 years
        
        return {
            "total_incoming": round(total_incoming, 2),
            "total_outgoing": round(total_outgoing, 2),
            "avg_transaction_amount": round(sum(float(t.amount) for t in transactions) / len(transactions), 2),
            "transaction_count": len(transactions),
            "most_common_categories": most_common_categories,
            "avg_monthly_income": round(total_incoming / months, 2),
            "avg_monthly_spending": round(total_outgoing / months, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction and update account balances.
    
    This endpoint handles all transaction creation for the banking system.
    Fraud detection happens asynchronously after the transaction completes.
    
    Steps:
    1. Validate receiver exists (must be in our system)
    2. Check sender balance if internal sender
    3. Update balances atomically
    4. Create transaction record with status='completed'
    5. Commit to database
    6. Return transaction details
    
    Args:
        transaction: Transaction details
        db: Database session
        
    Returns:
        TransactionResponse with transaction details
    """
    try:
        from config import BANK_CURRENCY, convert_to_bank_currency
        
        # Get sender and receiver
        sender = db.query(User).filter(User.user_id == transaction.sender_id).first()
        receiver = db.query(User).filter(User.user_id == transaction.receiver_id).first()
        
        # At least one party must exist in our system
        if not sender and not receiver:
            raise HTTPException(
                status_code=404,
                detail="At least one party (sender or receiver) must have an account in our system"
            )
        
        # Determine transaction type
        is_incoming = receiver is not None and sender is None  # External → Internal
        is_outgoing = sender is not None and receiver is None  # Internal → External
        is_internal = sender is not None and receiver is not None  # Internal → Internal
        
        print(f"Transaction type: {'Incoming' if is_incoming else 'Outgoing' if is_outgoing else 'Internal'}")
        print(f"Amount: {transaction.amount} {transaction.currency}")
        
        # If sender exists (internal or internal-to-internal), validate and deduct
        if sender:
            # Check if account is frozen
            if sender.is_frozen:
                raise HTTPException(
                    status_code=403,
                    detail=f"Sender account {transaction.sender_id} is frozen"
                )
            
            # Check sufficient balance (sender's balance is always in bank currency)
            if sender.account_balance < Decimal(str(transaction.amount)):
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Available: {sender.account_balance} {BANK_CURRENCY}, Required: {transaction.amount} {transaction.currency}"
                )
            
            # Deduct from sender (amount is already in bank currency for outgoing)
            sender.account_balance -= Decimal(str(transaction.amount))
            print(f"✅ Deducted {transaction.amount} {BANK_CURRENCY} from {transaction.sender_id}")
        
        # If receiver exists (internal or external-to-internal), add to balance
        if receiver:
            amount_to_add = Decimal(str(transaction.amount))
            
            # For INCOMING transactions, convert to bank's currency
            if is_incoming and transaction.currency != BANK_CURRENCY:
                converted_amount = convert_to_bank_currency(float(transaction.amount), transaction.currency)
                amount_to_add = Decimal(str(converted_amount))
                print(f"Converting {transaction.amount} {transaction.currency} → {amount_to_add} {BANK_CURRENCY}")
            
            # Add to receiver's balance (always in bank currency)
            receiver.account_balance += amount_to_add
            print(f"✅ Added {amount_to_add} {BANK_CURRENCY} to {transaction.receiver_id}")

        
        # Calculate converted amount once (for storage)
        if is_incoming and transaction.currency != BANK_CURRENCY:
            converted_amount = convert_to_bank_currency(float(transaction.amount), transaction.currency)
        else:
            converted_amount = float(transaction.amount)  # No conversion needed
        
        # Create transaction record with converted amount
        new_transaction = Transaction(
            sender_id=transaction.sender_id,
            sender_name=transaction.sender_name,
            receiver_id=transaction.receiver_id,
            receiver_name=transaction.receiver_name,
            amount=Decimal(str(transaction.amount)),
            currency=transaction.currency,
            amount_in_bank_currency=Decimal(str(converted_amount)),  # Store converted amount
            category=transaction.category,
            location=transaction.location,
            narration=transaction.narration,
            transaction_flow=transaction.transaction_flow,
            status='completed',  # Always completed - fraud detection happens later
            timestamp=datetime.utcnow()
        )
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        import sys
        print(
            f"Transaction created: ID={new_transaction.transaction_id}, "
            f"{transaction.sender_id} → {transaction.receiver_id}, "
            f"Amount={transaction.amount} {transaction.currency}",
            file=sys.stderr, flush=True
        )
        
        # Trigger fraud detection asynchronously
        try:
            import httpx
            print(f"Calling fraud detection for TX-{new_transaction.transaction_id}", file=sys.stderr, flush=True)

            profile_subject = sender if sender else receiver
            account_profile = _build_account_profile(
                db=db,
                subject_user=profile_subject,
                sender_id=new_transaction.sender_id,
                receiver_id=new_transaction.receiver_id,
            )

            request_meta = {
                "ip_address": req.client.host if req.client else None,
                "user_agent": req.headers.get("user-agent"),
                "device_id": req.headers.get("x-device-id"),
                "session_age_seconds": None,
                "is_new_device": None,
            }

            enriched_payload = build_context_payload(
                transaction={
                    "transaction_id": new_transaction.transaction_id,
                    "sender_id": new_transaction.sender_id,
                    "sender_name": new_transaction.sender_name,
                    "receiver_id": new_transaction.receiver_id,
                    "receiver_name": new_transaction.receiver_name,
                    "amount": float(new_transaction.amount),
                    "currency": new_transaction.currency,
                    "category": new_transaction.category,
                    "location": new_transaction.location,
                    "narration": new_transaction.narration,
                    "timestamp": new_transaction.timestamp.isoformat(),
                },
                request_meta=request_meta,
                account_profile=account_profile,
            )

            async with httpx.AsyncClient(timeout=5.0) as client:
                fraud_response = await client.post(
                    "http://localhost:8000/api/fraud/analyze-smart",
                    json=enriched_payload,
                )
                
                if fraud_response.status_code == 200:
                    fraud_result = fraud_response.json()
                    print(f"✅ Fraud analysis complete: Verdict={fraud_result.get('verdict')}, Risk={fraud_result.get('risk_score')}", file=sys.stderr, flush=True)
                else:
                    print(f"⚠️  Fraud analysis returned status {fraud_response.status_code}", file=sys.stderr, flush=True)
                    
        except Exception as fraud_error:
            # Don't fail transaction if fraud detection fails
            import traceback
            error_type = type(fraud_error).__name__
            error_msg = str(fraud_error)
            error_trace = traceback.format_exc()
            print(f"⚠️  Fraud detection failed (transaction still completed):", file=sys.stderr, flush=True)
            print(f"   Error Type: {error_type}", file=sys.stderr, flush=True)
            print(f"   Error Message: {error_msg}", file=sys.stderr, flush=True)
            print(f"   Traceback: {error_trace}", file=sys.stderr, flush=True)
        
        return TransactionResponse(
            transaction_id=new_transaction.transaction_id,
            sender_id=new_transaction.sender_id,
            receiver_id=new_transaction.receiver_id,
            amount=float(new_transaction.amount),
            currency=new_transaction.currency,
            status=new_transaction.status,
            timestamp=new_transaction.timestamp.isoformat(),
            message="Transaction completed successfully"
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR: Transaction creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")
