"""
Banking Backend Database Models
PostgreSQL schema for HooverBank
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Bank user account"""
    __tablename__ = 'users'
    
    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    account_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    is_frozen = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, balance={self.account_balance})>"


class Transaction(Base):
    """Bank transaction records"""
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Participants
    sender_id = Column(String(50), nullable=False, index=True)
    sender_name = Column(String(255))
    receiver_id = Column(String(50), nullable=False, index=True)
    receiver_name = Column(String(255))
    
    # Transaction details
    transaction_flow = Column(String(20))  # 'incoming' or 'outgoing'
    amount = Column(Numeric(15, 2), nullable=False)  # Original amount
    currency = Column(String(3), nullable=False, default='GBP')  # Original currency
    amount_in_bank_currency = Column(Numeric(15, 2), nullable=True)  # Converted amount (stored once)
    category = Column(String(50))
    location = Column(String(100))
    narration = Column(Text)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    status = Column(String(20), default='completed')
    
    __table_args__ = (
        Index('idx_sender', 'sender_id'),
        Index('idx_receiver', 'receiver_id'),
        Index('idx_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, {self.sender_id}→{self.receiver_id}, {self.amount})>"


class AuthLog(Base):
    """
    Authentication log model.
    Tracks all login attempts for fraud detection with detailed information.
    """
    __tablename__ = 'auth_logs'
    
    log_id = Column(String(10), primary_key=True)  # Random 10-digit ID
    user_id = Column(String(50), nullable=False, index=True)
    device_type = Column(String(50))  # e.g., "Mobile", "Desktop", "Tablet"
    ip_address = Column(String(45))  # IPv4 or IPv6
    location = Column(String(200))  # e.g., "London, United Kingdom"
    user_agent = Column(String(500))  # Browser/device user agent string
    login_success = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_auth_user_timestamp', 'user_id', 'timestamp'),
    )
    
    def __repr__(self):
        status = "SUCCESS" if self.login_success else "FAILED"
        return f"<AuthLog(log_id={self.log_id}, user_id={self.user_id}, status={status}, location={self.location})>"
