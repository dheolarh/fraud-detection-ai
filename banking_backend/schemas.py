"""
Pydantic schemas for banking backend API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction"""
    sender_id: str = Field(..., description="Sender's account ID")
    sender_name: str = Field(..., description="Sender's full name")
    receiver_id: str = Field(..., description="Receiver's account ID")
    receiver_name: str = Field(..., description="Receiver's full name")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    category: str = Field(..., description="Transaction category")
    location: str = Field(..., description="Transaction location")
    narration: Optional[str] = Field(None, description="Transaction description")
    transaction_flow: Optional[str] = Field(None, description="'incoming' or 'outgoing'")


class TransactionResponse(BaseModel):
    """Schema for transaction creation response"""
    transaction_id: int
    sender_id: str
    receiver_id: str
    amount: float
    currency: str
    status: str
    timestamp: str
    message: str


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    device_id: Optional[str] = Field(None, description="Device identifier")
    location: Optional[str] = Field(None, description="User's current location")


class LoginResponse(BaseModel):
    """Schema for login response"""
    user_id: str
    username: str
    account_balance: float
    is_frozen: bool
    token: str
