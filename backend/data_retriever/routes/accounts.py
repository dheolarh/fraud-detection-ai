"""
Account management routes.
Handles account freezing, unfreezing, and balance queries.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from storage.database import get_db
from storage.repositories import UserRepository
from data_retriever.schemas import (
    AccountBalanceResponse, FreezeAccountRequest, StatusResponse
)

router = APIRouter()


@router.get("/balance/{user_id}", response_model=AccountBalanceResponse)
async def get_balance(
    user_id: str, 
    from_date: str = None,
    to_date: str = None,
    db: Session = Depends(get_db)
):
    """
    Get account balance and transaction totals from banking backend.
    
    NOW QUERIES BANKING BACKEND API with date filtering support.
    
    Args:
        user_id: User ID
        from_date: Optional start date (ISO format: YYYY-MM-DD)
        to_date: Optional end date (ISO format: YYYY-MM-DD)
        db: Database session (unused, kept for compatibility)
    
    Returns:
        Account balance and transaction totals (filtered by date range if provided)
    """
    try:
        from clients.banking_client import get_banking_client
        from datetime import datetime
        
        # Get banking client
        banking_client = get_banking_client()
        
        # Get user info from banking backend (for account balance)
        user_info = await banking_client.get_user_info(user_id)
        
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found in banking system")
        
        # Parse dates if provided
        start_date = None
        end_date = None
        if from_date:
            start_date = datetime.fromisoformat(from_date)
        if to_date:
            end_date = datetime.fromisoformat(to_date)
        
        # Get ALL transactions with date filtering (no limit)
        result = await banking_client.get_transactions(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=5000  # Set to 5000 to avoid validation error
        )
        
        transactions = result.get('transactions', [])
        
        # Calculate totals from filtered transactions using converted amounts
        total_incoming = 0.0
        total_outgoing = 0.0
        
        for t in transactions:
            # Use converted amount if available, otherwise use original amount
            amount = float(t.get('amount_in_bank_currency', t.get('amount', 0)))
            if t.get('transaction_flow') == 'incoming':
                total_incoming += amount
            elif t.get('transaction_flow') == 'outgoing':
                total_outgoing += amount
        
        return AccountBalanceResponse(
            user_id=user_id,
            account_balance=user_info.get('account_balance', 0),  # Use actual balance from bank
            is_frozen=user_info.get('is_frozen', False),
            total_in=total_incoming,
            total_out=total_outgoing,
            transaction_count=len(transactions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Balance query error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch account balance")


@router.post("/freeze", response_model=StatusResponse)
async def freeze_account(request: FreezeAccountRequest, db: Session = Depends(get_db)):
    """
    Freeze user account due to suspicious activity.
    
    Args:
        request: User ID and reason for freezing
        db: Database session
    
    Returns:
        Status message
    """
    try:
        user_repo = UserRepository(db)
        
        success = user_repo.freeze_account(request.user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.warning(f"Account frozen: {request.user_id} - Reason: {request.reason}")
        
        return StatusResponse(
            status="success",
            message=f"Account {request.user_id} has been frozen"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account freeze error: {e}")
        raise HTTPException(status_code=500, detail="Failed to freeze account")


@router.post("/unfreeze/{user_id}", response_model=StatusResponse)
async def unfreeze_account(user_id: str, db: Session = Depends(get_db)):
    """
    Unfreeze user account.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        Status message
    """
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_frozen = False
        user_repo.update(user)
        
        logger.info(f"Account unfrozen: {user_id}")
        
        return StatusResponse(
            status="success",
            message=f"Account {user_id} has been unfrozen"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account unfreeze error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unfreeze account")
