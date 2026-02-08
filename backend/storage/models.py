"""
SQLAlchemy ORM models for all database tables.
Defines the schema and relationships for the Fraud AI database.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, ARRAY, Numeric, DECIMAL, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from storage.database import Base


class User(Base):
    """
    User account model.
    Represents both International Bank and Hoover Bank users.
    """
    __tablename__ = 'users'
    
    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    account_balance = Column(DECIMAL(15, 2), default=0.00, nullable=False)
    is_frozen = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    auth_logs = relationship("AuthLog", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, balance={self.account_balance})>"


class Transaction(Base):
    """Transaction records with fraud detection metadata"""
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Transaction participants
    sender_id = Column(String(50), nullable=False)  # No FK - allows external senders like International Bank
    sender_name = Column(String(255))  # NEW: Sender's full name
    receiver_id = Column(String(50), ForeignKey('users.user_id'), nullable=False)
    receiver_name = Column(String(255))  # NEW: Receiver's full name
    
    # Transaction details
    transaction_flow = Column(String(20))  # NEW: 'incoming' or 'outgoing'
    amount = Column(Numeric(15, 2), nullable=False)
    category = Column(String(50))
    location = Column(String(100))  # Transaction destination/origin
    narration = Column(Text)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    currency = Column(String(3), nullable=False, default='USD')  # ISO 4217 currency code, USD fallback
    
    # Fraud detection metadata
    risk_score = Column(Numeric(5, 4), default=0.0)
    is_flagged = Column(Boolean, nullable=False, default=False)
    flagged_logics = Column(ARRAY(String))
    status = Column(String(20), default='completed')  # Added status field
    trace_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True)
    
    # Only receiver has relationship - sender may be external
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_transactions")
    
    __table_args__ = (
        Index('idx_transactions_sender', 'sender_id'),
        Index('idx_transactions_receiver', 'receiver_id'),
        Index('idx_transactions_timestamp', 'timestamp'),
        Index('idx_transactions_flagged', 'is_flagged'),
    )

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, {self.sender_id}->{self.receiver_id}, amount={self.amount})>"


class AuthLog(Base):
    """
    Authentication log model.
    Tracks all login attempts for fraud detection (Logic 1: Login Integrity).
    """
    __tablename__ = 'auth_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.user_id'), nullable=False, index=True)
    device_id = Column(String(100))
    ip_address = Column(INET)
    login_success = Column(Boolean, nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="auth_logs")
    
    def __repr__(self):
        status = "SUCCESS" if self.login_success else "FAILED"
        return f"<AuthLog(user_id={self.user_id}, status={status}, timestamp={self.timestamp})>"


class Case(Base):
    """
    Fraud case model.
    Stores ongoing and resolved fraud investigation cases.
    Supports multiple affected transactions (both regular transactions and login anomalies).
    """
    __tablename__ = 'cases'
    
    case_id = Column(String(50), primary_key=True)  # Changed to string for custom IDs
    title = Column(String(200), nullable=False)  # Added title field
    description = Column(Text)
    priority = Column(String(20), default='medium', nullable=False)  # low, medium, high, critical
    status = Column(String(20), default='open', nullable=False, index=True)  # open, resolved
    affected_transactions = Column(Text)  # JSON array of {id, type} objects
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    resolved_at = Column(TIMESTAMP)
    
    def __repr__(self):
        return f"<Case(case_id={self.case_id}, status={self.status}, title={self.title})>"


class PaySimData(Base):
    """
    PaySim synthetic dataset model.
    Stores pre-labeled fraud data for ML model training.
    """
    __tablename__ = 'paysim_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    step = Column(Integer)  # Time step (1 hour increments)
    type = Column(String(20))  # Transaction type (CASH_OUT, PAYMENT, etc.)
    amount = Column(DECIMAL(15, 2))
    nameOrig = Column(String(50))  # Reciever ID
    oldbalanceOrg = Column(DECIMAL(15, 2))  # Sender balance before
    newbalanceOrig = Column(DECIMAL(15, 2))  # Sender balance after
    nameDest = Column(String(50))  # Receiver ID
    oldbalanceDest = Column(DECIMAL(15, 2))  # Receiver balance before
    newbalanceDest = Column(DECIMAL(15, 2))  # Receiver balance after
    isFraud = Column(Integer, nullable=False, index=True)  # 1 = fraud, 0 = legitimate
    isFlaggedFraud = Column(Integer)  # Simple rule-based flag
    
    def __repr__(self):
        fraud_status = "FRAUD" if self.isFraud else "LEGIT"
        return f"<PaySimData(id={self.id}, type={self.type}, amount={self.amount}, status={fraud_status})>"


class FraudDecision(Base):
    """
    Fraud decision model.
    Stores all fraud detection decisions with explainability and governance tracking.
    Required for compliance.
    """
    __tablename__ = 'fraud_decisions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey('transactions.transaction_id'), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    threshold_profile = Column(String(50), nullable=False)
    final_risk_score = Column(DECIMAL(5, 4))
    verdict = Column(String(20))
    triggered_buckets = Column(ARRAY(Text))
    triggered_logics = Column(ARRAY(Text))
    explanation_text = Column(Text)
    bucket_scores = Column(Text)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    transaction = relationship("Transaction", backref="fraud_decision")
    
    def __repr__(self):
        return f"<FraudDecision(id={self.id}, transaction_id={self.transaction_id}, verdict={self.verdict})>"


class HooverTransaction(Base):
    """
    Hoover Bank transaction model.
    Separate tracking for receiver-side fraud detection.
    """
    __tablename__ = 'hoover_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey('transactions.transaction_id'), nullable=False)
    receiver_id = Column(String(50), nullable=False, index=True)
    amount = Column(DECIMAL(15, 2), nullable=False)
    fraud_checked = Column(Boolean, default=True, nullable=False)
    risk_score = Column(DECIMAL(5, 4))
    received_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    transaction = relationship("Transaction", backref="hoover_transaction")
    
    __table_args__ = (
        Index('idx_hoover_receiver', 'receiver_id'),
        Index('idx_hoover_timestamp', 'received_at'),
    )
    
    def __repr__(self):
        return f"<HooverTransaction(id={self.id}, receiver_id={self.receiver_id}, amount={self.amount})>"
