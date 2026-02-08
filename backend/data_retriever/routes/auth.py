"""
Authentication routes.
Handles user login and session management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from storage.database import get_db
from storage.repositories import UserRepository
from data_retriever.schemas import LoginRequest, LoginResponse, StatusResponse
from utils.security import PasswordHasher, JWTHandler
from core.exceptions import AuthenticationError

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    Args:
        request: Login credentials (username, password)
        db: Database session
    
    Returns:
        LoginResponse with user info and JWT token
    """
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_username(request.username)
        
        if not user:
            logger.warning(f"Login attempt for non-existent user: {request.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not PasswordHasher.verify_password(request.password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {request.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token_data = {
            "sub": user.user_id,
            "username": user.username
        }
        token = JWTHandler.create_access_token(token_data)
        
        logger.info(f"Successful login: {user.username}")
        
        return LoginResponse(
            user_id=user.user_id,
            username=user.username,
            account_balance=float(user.account_balance),
            is_frozen=user.is_frozen,
            token=token
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/status", response_model=StatusResponse)
async def auth_status(token: str):
    """
    Verify authentication token status.
    
    Args:
        token: JWT token to verify
    
    Returns:
        StatusResponse with token validity
    """
    try:
        payload = JWTHandler.decode_token(token)
        return StatusResponse(
            status="valid",
            message=f"Token valid for user: {payload.get('username')}"
        )
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")
