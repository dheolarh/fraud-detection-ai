"""
Custom exceptions for Fraud AI application.
All custom exceptions should extend FraudAIException.
"""


class FraudAIException(Exception):
    """Base exception for Fraud AI application."""
    pass


class DatabaseError(FraudAIException):
    """Raised when database operations fail."""
    pass


class ValidationError(FraudAIException):
    """Raised when input validation fails."""
    pass


class AuthenticationError(FraudAIException):
    """Raised when authentication fails."""
    pass


class InsufficientBalanceError(FraudAIException):
    """Raised when sender has insufficient balance."""
    pass


class AccountFrozenError(FraudAIException):
    """Raised when account is frozen due to suspicious activity."""
    pass


class TransactionBlockedError(FraudAIException):
    """Raised when transaction is blocked by fraud detection."""
    pass


class ModelNotFoundError(FraudAIException):
    """Raised when ML model file is not found."""
    pass


class ConfigurationError(FraudAIException):
    """Raised when configuration is invalid or missing."""
    pass
