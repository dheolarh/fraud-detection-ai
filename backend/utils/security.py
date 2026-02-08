"""
Security utilities for production-grade authentication and authorization.
Implements JWT tokens, password hashing, and security best practices.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from config.settings import settings
from core.exceptions import AuthenticationError
from loguru import logger

# Password hashing configuration (bcrypt with 12 rounds minimum)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__min_rounds=12,
    bcrypt__max_rounds=14
)

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class PasswordHasher:
    """Secure password hashing using bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt (min 12 rounds)"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise AuthenticationError("Failed to hash password")
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """Check if password needs rehashing (security upgrade)"""
        return pwd_context.needs_update(hashed_password)


class JWTHandler:
    """JWT token creation and validation"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
            to_encode.update({"exp": expire, "type": "access"})
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
            
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise AuthenticationError("Failed to create access token")
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token (longer expiration)"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            to_encode.update({"exp": expire, "type": "refresh"})
            
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Refresh token creation failed: {e}")
            raise AuthenticationError("Failed to create refresh token")
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid or expired token")
        except Exception as e:
            logger.error(f"Token decode failed: {e}")
            raise AuthenticationError("Token validation failed")
    
    @staticmethod
    def verify_token_type(token: str, expected_type: str) -> dict:
        """Verify token is of expected type (access/refresh)"""
        payload = JWTHandler.decode_token(token)
        
        if payload.get("type") != expected_type:
            raise AuthenticationError(f"Invalid token type. Expected: {expected_type}")
        
        return payload


class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate password meets security requirements:
        - Minimum 8 characters
        - Contains uppercase and lowercase
        - Contains numbers
        - Contains special characters
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain uppercase letters")
        
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain lowercase letters")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain numbers")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise ValueError("Password must contain special characters")
        
        return True
    
    @staticmethod
    def sanitize_input(value: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not value:
            return value
        
        # Remove potential XSS characters
        dangerous_chars = ["<", ">", "&", '"', "'", "/"]
        sanitized = value
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized.strip()
