"""
Pydantic schemas for API request/response validation.
Type-safe data models with automatic validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class LoginRequest(BaseModel):
    """Login credentials"""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Login response with user info and token"""
    user_id: str
    username: str
    account_balance: float
    is_frozen: bool
    token: str
    message: str = "Login successful"


class TransactionRequest(BaseModel):
    """Transaction submission request"""
    sender_id: str = Field(..., min_length=3, max_length=50)
    sender_name: Optional[str] = Field(None, max_length=255, description="Sender's full name")
    receiver_id: str = Field(..., min_length=3, max_length=50)
    receiver_name: Optional[str] = Field(None, max_length=255, description="Receiver's full name")
    amount: float = Field(..., gt=0, description="Amount must be positive")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code - REQUIRED")
    category: str = Field(..., description="Transaction category")
    location: str = Field(..., min_length=2)
    narration: Optional[str] = Field(None, max_length=500)
    transaction_flow: Optional[str] = Field(None, description="'incoming' or 'outgoing'")
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['shopping', 'bills', 'airtime', 'family', 'other', 
                           'Shopping', 'Bills', 'Transfer', 'Salary', 'Entertainment', 
                           'Food', 'Travel', 'Healthcare', 'Other']
        if v not in valid_categories:
            raise ValueError(f'Invalid category. Must be one of: {", ".join(valid_categories)}')
        return v.lower()


class TransactionResponse(BaseModel):
    """Transaction processing result"""
    transaction_id: int
    status: str
    risk_score: float
    flagged_logics: List[str]
    message: str
    trace_id: str


class TransactionDetail(BaseModel):
    """Transaction details for feed"""
    transaction_id: int
    sender_id: str
    sender_name: Optional[str] = None
    receiver_id: str
    receiver_name: Optional[str] = None
    transaction_flow: Optional[str] = None
    amount: float
    formatted_amount: Optional[str] = None  
    currency_code: Optional[str] = None      
    category: str
    location: str
    narration: Optional[str]
    timestamp: str
    risk_score: Optional[float]
    is_flagged: bool
    flagged_logics: Optional[List[str]]
    status: str


class AccountBalanceResponse(BaseModel):
    """Account balance and status"""
    user_id: str
    account_balance: float
    is_frozen: bool
    total_in: float = 0.0
    total_out: float = 0.0
    transaction_count: int = 0
    currency: str = 'USD'  # ISO 4217 currency code


class FreezeAccountRequest(BaseModel):
    """Account freeze request"""
    user_id: str
    reason: str = Field(..., min_length=10, max_length=500)


class StatusResponse(BaseModel):
    """Generic status response"""
    status: str
    message: str


class AnalyticsResponse(BaseModel):
    """Dashboard analytics data"""
    total_sent: float
    total_received: float
    activity_score: float
    country_distribution: dict
    transaction_count: int


class CaseResponse(BaseModel):
    """Fraud case details"""
    case_id: int
    transaction_id: int
    description: str
    status: str
    created_at: str
