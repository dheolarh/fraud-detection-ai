"""
Repository implementations for data access.
Implements Repository pattern for clean data layer abstraction.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta

from core.base import BaseRepository
from core.exceptions import DatabaseError
from storage.models import User, Transaction, AuthLog, Case, PaySimData
from passlib.hash import bcrypt
from loguru import logger


class UserRepository(BaseRepository):
    """User data access repository."""
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            return self.db.query(User).filter(User.user_id == user_id).first()
        except Exception as e:
            logger.error(f"UserRepository.get_by_id failed: {e}")
            raise DatabaseError(f"Failed to fetch user: {e}")
    
    def get_by_username(self, username: str) -> Optional[User]:
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"UserRepository.get_by_username failed: {e}")
            raise DatabaseError(f"Failed to fetch user: {e}")
    
    def get_all(self) -> List[User]:
        try:
            return self.db.query(User).all()
        except Exception as e:
            logger.error(f"UserRepository.get_all failed: {e}")
            raise DatabaseError(f"Failed to fetch users: {e}")
    
    def create(self, user_id: str, username: str, password: str, balance: float = 0.00) -> User:
        try:
            user = User(
                user_id=user_id,
                username=username,
                password_hash=bcrypt.hash(password),
                account_balance=balance
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created user: {user_id}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"UserRepository.create failed: {e}")
            raise DatabaseError(f"Failed to create user: {e}")
    
    def update(self, user: User) -> User:
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"UserRepository.update failed: {e}")
            raise DatabaseError(f"Failed to update user: {e}")
    
    def delete(self, user_id: str) -> bool:
        try:
            user = self.get_by_id(user_id)
            if user:
                self.db.delete(user)
                self.db.commit()
                logger.info(f"Deleted user: {user_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"UserRepository.delete failed: {e}")
            raise DatabaseError(f"Failed to delete user: {e}")
    
    def freeze_account(self, user_id: str) -> bool:
        try:
            user = self.get_by_id(user_id)
            if user:
                user.is_frozen = True
                self.db.commit()
                logger.warning(f"Froze account: {user_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"UserRepository.freeze_account failed: {e}")
            raise DatabaseError(f"Failed to freeze account: {e}")


class TransactionRepository(BaseRepository):
    """Transaction data access repository."""
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        try:
            return self.db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        except Exception as e:
            logger.error(f"TransactionRepository.get_by_id failed: {e}")
            raise DatabaseError(f"Failed to fetch transaction: {e}")
    
    def get_all(self) -> List[Transaction]:
        try:
            return self.db.query(Transaction).all()
        except Exception as e:
            logger.error(f"TransactionRepository.get_all failed: {e}")
            raise DatabaseError(f"Failed to fetch transactions: {e}")
    
    def create(self, sender_id: str, receiver_id: str, amount: float, 
               category: str, location: str, narration: str = None, currency: str = 'USD') -> Transaction:
        try:
            transaction = Transaction(
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                currency=currency,
                category=category,
                location=location,
                narration=narration
            )
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            logger.info(f"Created transaction: {transaction.transaction_id}")
            return transaction
        except Exception as e:
            self.db.rollback()
            logger.error(f"TransactionRepository.create failed: {e}")
            raise DatabaseError(f"Failed to create transaction: {e}")
    
    def update(self, transaction: Transaction) -> Transaction:
        try:
            self.db.commit()
            self.db.refresh(transaction)
            return transaction
        except Exception as e:
            self.db.rollback()
            logger.error(f"TransactionRepository.update failed: {e}")
            raise DatabaseError(f"Failed to update transaction: {e}")
    
    def delete(self, transaction_id: int) -> bool:
        try:
            transaction = self.get_by_id(transaction_id)
            if transaction:
                self.db.delete(transaction)
                self.db.commit()
                logger.info(f"Deleted transaction: {transaction_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"TransactionRepository.delete failed: {e}")
            raise DatabaseError(f"Failed to delete transaction: {e}")
    
    def get_user_transactions(self, user_id: str, limit: int = 20) -> List[Transaction]:
        """Get recent transactions for user"""
        try:
            return self.db.query(Transaction).filter(
                (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
            ).order_by(desc(Transaction.timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"TransactionRepository.get_user_transactions failed: {e}")
            raise DatabaseError(f"Failed to fetch user transactions: {e}")
    
    def get_flagged_transactions(self, user_id: str = None) -> List[Transaction]:
        """Get flagged transactions, optionally filtered by user"""
        try:
            query = self.db.query(Transaction).filter(Transaction.is_flagged == True)
            if user_id:
                query = query.filter(
                    (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
                )
            return query.all()
        except Exception as e:
            logger.error(f"TransactionRepository.get_flagged_transactions failed: {e}")
            raise DatabaseError(f"Failed to fetch flagged transactions: {e}")


class PaySimRepository(BaseRepository):
    """PaySim dataset repository."""
    
    def get_by_id(self, id: int) -> Optional[PaySimData]:
        try:
            return self.db.query(PaySimData).filter(PaySimData.id == id).first()
        except Exception as e:
            logger.error(f"PaySimRepository.get_by_id failed: {e}")
            raise DatabaseError(f"Failed to fetch PaySim data: {e}")
    
    def get_all(self) -> List[PaySimData]:
        try:
            return self.db.query(PaySimData).all()
        except Exception as e:
            logger.error(f"PaySimRepository.get_all failed: {e}")
            raise DatabaseError(f"Failed to fetch PaySim data: {e}")
    
    def create(self, data: PaySimData) -> PaySimData:
        try:
            self.db.add(data)
            self.db.commit()
            self.db.refresh(data)
            return data
        except Exception as e:
            self.db.rollback()
            logger.error(f"PaySimRepository.create failed: {e}")
            raise DatabaseError(f"Failed to create PaySim record: {e}")
    
    def bulk_create(self, records: List[dict]) -> int:
        """Bulk insert PaySim records for performance"""
        try:
            objects = [PaySimData(**record) for record in records]
            self.db.bulk_save_objects(objects)
            self.db.commit()
            logger.info(f"Bulk inserted {len(records)} PaySim records")
            return len(records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"PaySimRepository.bulk_create failed: {e}")
            raise DatabaseError(f"Failed to bulk insert PaySim data: {e}")
    
    def update(self, data: PaySimData) -> PaySimData:
        try:
            self.db.commit()
            self.db.refresh(data)
            return data
        except Exception as e:
            self.db.rollback()
            logger.error(f"PaySimRepository.update failed: {e}")
            raise DatabaseError(f"Failed to update PaySim data: {e}")
    
    def delete(self, id: int) -> bool:
        try:
            data = self.get_by_id(id)
            if data:
                self.db.delete(data)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"PaySimRepository.delete failed: {e}")
            raise DatabaseError(f"Failed to delete PaySim data: {e}")
    
    def count_fraud(self) -> dict:
        """Get fraud statistics from PaySim data"""
        try:
            total = self.db.query(PaySimData).count()
            fraud = self.db.query(PaySimData).filter(PaySimData.isFraud == 1).count()
            return {
                'total': total,
                'fraud': fraud,
                'legitimate': total - fraud,
                'fraud_rate': (fraud / total * 100) if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"PaySimRepository.count_fraud failed: {e}")
            raise DatabaseError(f"Failed to count fraud records: {e}")
