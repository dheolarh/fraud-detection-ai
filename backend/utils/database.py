"""
Utility functions for database operations.
Reusable helper functions to avoid code duplication.
"""

from sqlalchemy.orm import Session
from storage.models import Transaction, User
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger


def get_user_transactions_in_window(
    db: Session,
    user_id: str,
    hours: Optional[int] = None,
    days: Optional[int] = None
) -> List[Transaction]:
    """
    Get user transactions within a time window.
    Reusable across multiple logic modules.
    
    Args:
        db: Database session
        user_id: User ID to query
        hours: Time window in hours (mutually exclusive with days)
        days: Time window in days (mutually exclusive with hours)
    
    Returns:
        List of Transaction objects
    """
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
    elif days:
        cutoff = datetime.utcnow() - timedelta(days=days)
    else:
        raise ValueError("Must specify either hours or days")
    
    transactions = db.query(Transaction).filter(
        Transaction.sender_id == user_id,
        Transaction.timestamp >= cutoff
    ).all()
    
    logger.debug(f"Found {len(transactions)} transactions for {user_id} in last {hours or days} {'hours' if hours else 'days'}")
    return transactions


def count_transactions_in_window(
    db: Session,
    user_id: str,
    hours: Optional[int] = None,
    days: Optional[int] = None
) -> int:
    """
    Count user transactions within a time window.
    
    Args:
        db: Database session
        user_id: User ID to query
        hours: Time window in hours
        days: Time window in days
    
    Returns:
        Transaction count
    """
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
    elif days:
        cutoff = datetime.utcnow() - timedelta(days=days)
    else:
        raise ValueError("Must specify either hours or days")
    
    count = db.query(Transaction).filter(
        Transaction.sender_id == user_id,
        Transaction.timestamp >= cutoff
    ).count()
    
    return count


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        User object or None
    """
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username.
    
    Args:
        db: Database session
        username: Username
    
    Returns:
        User object or None
    """
    return db.query(User).filter(User.username == username).first()


def freeze_user_account(db: Session, user_id: str) -> bool:
    """
    Freeze a user account.
    
    Args:
        db: Database session
        user_id: User ID to freeze
    
    Returns:
        bool: True if successful
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.is_frozen = True
        db.commit()
        logger.warning(f"Account frozen: {user_id}")
        return True
    return False


def unfreeze_user_account(db: Session, user_id: str) -> bool:
    """
    Unfreeze a user account.
    
    Args:
        db: Database session
        user_id: User ID to unfreeze
    
    Returns:
        bool: True if successful
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.is_frozen = False
        db.commit()
        logger.info(f"Account unfrozen: {user_id}")
        return True
    return False
