"""
Transaction routes.
Handles transaction submission, retrieval, and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
from decimal import Decimal
import uuid

from storage.database import get_db
from storage.repositories import UserRepository, TransactionRepository
from storage.models import Transaction
from data_retriever.schemas import (
    TransactionRequest, TransactionResponse, TransactionDetail
)
from core.exceptions import InsufficientBalanceError, AccountFrozenError
from config.constants import STATUS_SAFE, STATUS_FLAGGED, STATUS_FLAGGED
from utils.currency import format_money
from clients.banking_client import get_banking_client  # NEW: Banking API client

router = APIRouter()


@router.post("/send", response_model=TransactionResponse)
async def send_money(request: TransactionRequest, db: Session = Depends(get_db)):
    """
    Process money transfer transaction with fraud detection.
    
    Supports both:
    - Internal transfers (both sender and receiver in our system)
    - External incoming (sender from external bank like International, receiver in our system)
    
    Args:
        request: Transaction details
        db: Database session
    
    Returns:
        TransactionResponse with fraud analysis results
    """
    try:
        user_repo = UserRepository(db)
        txn_repo = TransactionRepository(db)
        
        # Get receiver - must always exist
        receiver = user_repo.get_by_id(request.receiver_id)
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")
        
        # Get sender - may or may not exist (external senders like International Bank are OK)
        sender = user_repo.get_by_id(request.sender_id)
        
        # If sender exists in our system, validate and deduct balance
        if sender:
            if sender.is_frozen:
                raise AccountFrozenError(f"Account {request.sender_id} is frozen")
            
            if sender.account_balance < request.amount:
                raise InsufficientBalanceError("Insufficient balance")
            
            # Deduct from internal sender
            sender.account_balance -= Decimal(str(request.amount))
        
        # Always add to receiver (whether from internal or external sender)
        receiver.account_balance += Decimal(str(request.amount))
        
        # Create transaction record (stores sender_id even if sender doesn't exist in our DB)
        transaction = txn_repo.create(
            sender_id=request.sender_id,  # Can be external ID like "INT-US-123456"
            sender_name=request.sender_name,  # NEW: Sender's full name
            receiver_id=request.receiver_id,
            receiver_name=request.receiver_name,  # NEW: Receiver's full name
            amount=request.amount,
            currency=request.currency,  # Store currency
            category=request.category,
            location=request.location,
            narration=request.narration,
            transaction_flow=request.transaction_flow  # NEW: 'incoming' or 'outgoing'
        )
        
        
        # Run fraud detection
        from orchestrator.risk_orchestrator import RiskOrchestrator
        orchestrator = RiskOrchestrator()
        
        # Prepare transaction data for fraud analysis
        transaction_data = {
            'id': transaction.transaction_id,
            'sender_id': request.sender_id,
            'receiver_id': request.receiver_id,
            'amount': request.amount,
            'currency': request.currency,  # NEW: Pass currency to fraud detection
            'category': request.category,
            'location': request.location,
            'timestamp': transaction.timestamp  # Should be datetime object from DB
        }
        
        # Debug logging
        logger.info(f"Fraud check for TX {transaction.transaction_id}: timestamp type={type(transaction.timestamp)}, value={transaction.timestamp}")
        
        risk_score, flagged_logics, verdict, explanation = await orchestrator.analyze_transaction(
            transaction_data, db
        )
        
        # Handle fraud verdict and set transaction status
        if verdict == "FLAGGED":
            # Reverse the balance changes for blocked transactions
            if sender:  # Only if internal sender
                sender.account_balance += Decimal(str(request.amount))  # Give money back
            receiver.account_balance -= Decimal(str(request.amount))  # Remove from receiver
            
            status = "blocked"
            is_flagged = True
            logger.error(f"Transaction {transaction.transaction_id} FLAGGED: {explanation}")
        elif verdict == "MONITORED":
            status = "held"
            is_flagged = True
            logger.warning(f"Transaction {transaction.transaction_id} held for review: {explanation}")
        elif verdict == "APPROVED":
            status = STATUS_SAFE
            is_flagged = False
        else:
            status = STATUS_SAFE
            is_flagged = False
        
        # Update transaction with fraud detection results
        transaction.risk_score = risk_score if risk_score is not None else 0.0
        transaction.is_flagged = is_flagged
        transaction.flagged_logics = flagged_logics if flagged_logics else []  # Empty array instead of None
        transaction.status = status
        
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Transaction {transaction.transaction_id}: {request.sender_id} -> {request.receiver_id}, ${request.amount}, verdict={verdict}")
        
        return TransactionResponse(
            transaction_id=transaction.transaction_id,
            status="success",
            risk_score=risk_score,
            flagged_logics=flagged_logics,
            message="Transaction completed successfully",
            trace_id=str(transaction.trace_id)
        )
    
    except (InsufficientBalanceError, AccountFrozenError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction error: {e}")
        logger.exception("Full exception traceback:")
        raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")


@router.get("/recent/{user_id}", response_model=List[TransactionDetail])
async def get_recent_transactions(
    user_id: str, 
    limit: int = 20,
    page: int = 1,
    direction: str = None,  # 'incoming', 'outgoing', or None for all
    min_amount: float = None,
    max_amount: float = None,
    country: str = None,  # Filter by country
    db: Session = Depends(get_db)
):
    """
    Get recent transactions for a user from banking backend.
    
    NOW QUERIES BANKING BACKEND API - does not store transactions locally.
    
    Args:
        user_id: User ID
        limit: Number of transactions per page (default: 20)
        page: Page number (default: 1)
        direction: Filter by 'incoming' or 'outgoing'
        min_amount: Minimum transaction amount
        max_amount: Maximum transaction amount
        country: Filter by country name
        db: Database session (unused, kept for compatibility)
    
    Returns:
        List of recent transactions from banking backend
    """
    try:
        
        # Get banking client
        banking_client = get_banking_client()
        
        # Check if any filters are applied
        has_filters = bool(direction or min_amount is not None or max_amount is not None or country)
        
        if has_filters:
            # When filters are applied, fetch ALL transactions then filter client-side
            result = await banking_client.get_transactions(
                user_id=user_id,
                limit=5000,  # Fetch all transactions
                offset=0     # Start from beginning
            )
        else:
            # No filters - use normal pagination
            offset = (page - 1) * limit
            backend_limit = min(limit, 5000)
            
            result = await banking_client.get_transactions(
                user_id=user_id,
                limit=backend_limit,
                offset=offset
            )
        
        # Extract transactions from response
        all_transactions = result.get('transactions', [])
        # Client-side filtering (only if filters are applied)
        if has_filters:
            filtered = all_transactions
            
            # Filter by direction
            if direction:
                filtered = [t for t in filtered if t.get('transaction_flow') == direction]
            
            # Filter by amount range
            if min_amount is not None:
                filtered = [t for t in filtered if t.get('amount', 0) >= min_amount]
            if max_amount is not None:
                filtered = [t for t in filtered if t.get('amount', 0) <= max_amount]
            
            # Filter by country
            if country:
                filtered = [t for t in filtered if country.lower() in t.get('location', '').lower()]
            
            # Apply pagination after filtering
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated = filtered[start_idx:end_idx]
        else:
            # No filters - use transactions as-is from banking backend (already paginated)
            paginated = all_transactions
        
        # Convert to TransactionDetail format
        transactions_detail = []
        for t in paginated:
            # Get bank location for currency formatting
            bank_location = await banking_client.get_bank_location(user_id)
            currency_code = bank_location.get('currency', 'GBP')
            
            # Format amount (simple formatting for now)
            formatted_amt = f"{currency_code} {t.get('amount', 0):.2f}"
            
            transactions_detail.append(TransactionDetail(
                transaction_id=t.get('transaction_id'),
                sender_id=t.get('sender_id'),
                sender_name=t.get('sender_name'),
                receiver_id=t.get('receiver_id'),
                receiver_name=t.get('receiver_name'),
                transaction_flow=t.get('transaction_flow'),
                amount=float(t.get('amount', 0)),
                formatted_amount=formatted_amt,
                currency_code=currency_code,
                category=t.get('category'),
                location=t.get('location'),
                narration=t.get('narration'),
                timestamp=t.get('timestamp'),
                risk_score=None,  # Fraud detection data not stored with transaction
                is_flagged=False,
                flagged_logics=[],
                status=t.get('status', 'completed')
            ))
        
        logger.info(f"Fetched {len(transactions_detail)} transactions from banking backend for user {user_id}")
        return transactions_detail
    
    except Exception as e:
        logger.error(f"Failed to fetch transactions from banking backend: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")


@router.get("/flagged/{user_id}", response_model=List[TransactionDetail])
async def get_flagged_transactions(user_id: str, db: Session = Depends(get_db)):
    """
    Get flagged (suspicious) transactions for a user from fraud decisions.
    
    NOW QUERIES BANKING BACKEND for transaction details + fraud_decisions for flags.
    
    Args:
        user_id: User ID
        db: Database session (for fraud_decisions table)
    
    Returns:
        List of flagged transactions with fraud metadata
    """
    try:
        from storage.models import FraudDecision
        
        # Get banking client
        banking_client = get_banking_client()
        
        # Get all transactions from banking backend
        result = await banking_client.get_transactions(user_id=user_id, limit=10000)
        all_transactions = result.get('transactions', [])
        
        # Get all fraud decisions from fraud DB
        fraud_decisions = db.query(FraudDecision).filter(
            FraudDecision.verdict.in_(['MONITORED', 'FLAGGED'])
        ).all()
        
        # Create a map of transaction_id -> fraud decision
        fraud_map = {fd.transaction_id: fd for fd in fraud_decisions}
        
        # Filter transactions that have fraud decisions and belong to user
        flagged_transactions = []
        for t in all_transactions:
            tx_id = t.get('transaction_id')
            if tx_id in fraud_map:
                fraud_decision = fraud_map[tx_id]
                
                # Get bank location for currency
                bank_location = await banking_client.get_bank_location(user_id)
                currency_code = bank_location.get('currency', 'GBP')
                formatted_amt = f"{currency_code} {t.get('amount', 0):.2f}"
                
                flagged_transactions.append(TransactionDetail(
                    transaction_id=tx_id,
                    sender_id=t.get('sender_id'),
                    sender_name=t.get('sender_name'),
                    receiver_id=t.get('receiver_id'),
                    receiver_name=t.get('receiver_name'),
                    transaction_flow=t.get('transaction_flow'),
                    amount=float(t.get('amount', 0)),
                    formatted_amount=formatted_amt,
                    currency_code=currency_code,
                    category=t.get('category'),
                    location=t.get('location'),
                    narration=t.get('narration'),
                    timestamp=t.get('timestamp'),
                    risk_score=float(fraud_decision.final_risk_score) if fraud_decision.final_risk_score else None,
                    is_flagged=True,
                    flagged_logics=fraud_decision.triggered_logics or [],
                    status=fraud_decision.verdict.lower()
                ))
        
        logger.info(f"Found {len(flagged_transactions)} flagged transactions for user {user_id}")
        return flagged_transactions
    
    except Exception as e:
        logger.error(f"Failed to fetch flagged transactions: {e}")
        logger.exception("Full exception traceback:")
        raise HTTPException(status_code=500, detail="Failed to fetch flagged transactions")

@router.get("/geo-analytics/{user_id}")
async def get_geo_analytics(user_id: str, limit: int = 10):
    """
    Get transaction analytics aggregated by country/location from banking backend.
    
    NOW QUERIES BANKING BACKEND API - does not use local database.
    
    Args:
        user_id: User ID
        limit: Number of top countries to return (default: 10)
    
    Returns:
        List of countries with incoming and outgoing transaction totals
    """
    from collections import defaultdict
    
    # Get banking client
    banking_client = get_banking_client()
    
    # Get all user transactions from banking backend (increased limit)
    result = await banking_client.get_transactions(user_id=user_id, limit=10000)
    transactions = result.get('transactions', [])
    
    # Aggregate by country
    country_data = defaultdict(lambda: {'incoming': 0.0, 'outgoing': 0.0})
    
    for t in transactions:
        # Extract country from location (part after comma)
        location = t.get('location', '')
        if ',' in location:
            country = location.split(',')[-1].strip()
        else:
            country = location.strip()
        
        # Determine if incoming or outgoing
        if t.get('receiver_id') == user_id:
            country_data[country]['incoming'] += float(t.get('amount', 0))
        else:
            country_data[country]['outgoing'] += float(t.get('amount', 0))
    
    # Convert to list and sort by total volume
    result_list = []
    for country, amounts in country_data.items():
        total = amounts['incoming'] + amounts['outgoing']
        result_list.append({
            'country': country,
            'incoming': amounts['incoming'],
            'outgoing': amounts['outgoing'],
            'total': total
        })
    
    # Sort by total volume descending and limit
    result_list.sort(key=lambda x: x['total'], reverse=True)
    result_list = result_list[:limit]
    
    # Remove the 'total' field before returning
    for item in result_list:
        del item['total']
    
    return result_list



@router.get("/countries/{user_id}")
async def get_user_countries(user_id: str):
    """
    Get unique list of countries from user's transactions from banking backend.
    
    NOW QUERIES BANKING BACKEND API - does not use local database.
    
    Args:
        user_id: User ID
    
    Returns:
        List of unique country names sorted alphabetically
    """
    try:
        # Get banking client
        banking_client = get_banking_client()
        
        # Get all user transactions from banking backend
        result = await banking_client.get_transactions(user_id=user_id, limit=10000)
        transactions = result.get('transactions', [])
        
        # Extract unique countries from locations
        countries = set()
        for t in transactions:
            location = t.get('location', '')
            if ',' in location:
                country = location.split(',')[-1].strip()
            else:
                country = location.strip()
            if country:  # Only add non-empty countries
                countries.add(country)
        
        # Return sorted list
        return sorted(list(countries))
    
    except Exception as e:
        logger.error(f"Failed to fetch countries from banking backend: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch countries")
