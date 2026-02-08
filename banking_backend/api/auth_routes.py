"""
Banking Backend Authentication Routes
Handles user login, logout, and authentication history for fraud detection.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional
import logging

from database import get_db
from models.database import User, AuthLog
from schemas import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and log the attempt with detailed information.
    
    Args:
        request: Login credentials (username, password, device_id)
        req: FastAPI request object (for IP address and user agent)
        db: Database session
    
    Returns:
        LoginResponse with user info and token
    """
    import random
    
    # Extract client information
    client_ip = req.client.host if req.client else "127.0.0.1"
    user_agent = req.headers.get("user-agent", "")
    
    # Detect device type from user agent
    device_type = detect_device_type(user_agent)
    
    # Use location from request if provided, otherwise detect from IP
    location = request.location if hasattr(request, 'location') and request.location else get_location_from_ip(client_ip)
    
    # Generate random 10-digit log ID
    log_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    
    try:
        # Find user
        user = db.query(User).filter(User.username == request.username).first()
        
        # Log failed attempt if user not found
        if not user:
            auth_log = AuthLog(
                log_id=log_id,
                user_id="unknown",
                device_type=device_type,
                ip_address=client_ip,
                location=location,
                user_agent=user_agent,
                login_success=False,
                timestamp=datetime.utcnow()
            )
            db.add(auth_log)
            db.commit()
            
            logger.warning(f"Login attempt for non-existent user: {request.username} from {location}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password - Check against user's password_hash
        # In production, use bcrypt.checkpw(request.password, user.password_hash)
        # For now, plain text comparison (password_hash contains plain text for testing)
        user_password = user.password_hash if hasattr(user, 'password_hash') else None
        
        if not user_password:
            # No password set - reject login
            logger.error(f"User {user.username} has no password set!")
            raise HTTPException(status_code=500, detail="Account configuration error")
        
        # Compare passwords
        password_valid = request.password == user_password
        
        if not password_valid:
            # Generate new log ID for failed attempt
            log_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            
            # Log failed attempt
            auth_log = AuthLog(
                log_id=log_id,
                user_id=user.user_id,
                device_type=device_type,
                ip_address=client_ip,
                location=location,
                user_agent=user_agent,
                login_success=False,
                timestamp=datetime.utcnow()
            )
            db.add(auth_log)
            db.commit()
            
            logger.warning(f"Failed login attempt for user: {user.username} from {location}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate new log ID for successful attempt
        log_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        
        # Log successful attempt
        auth_log = AuthLog(
            log_id=log_id,
            user_id=user.user_id,
            device_type=device_type,
            ip_address=client_ip,
            location=location,
            user_agent=user_agent,
            login_success=True,
            timestamp=datetime.utcnow()
        )
        db.add(auth_log)
        db.commit()
        
        logger.info(f"Successful login: {user.username} from {location} ({device_type})")
        
        # Generate token
        token = f"token_{user.user_id}_{datetime.utcnow().timestamp()}"
        
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


def detect_device_type(user_agent: str) -> str:
    """Detect device type from user agent string"""
    user_agent_lower = user_agent.lower()
    
    if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone', 'ipod']):
        return "Mobile"
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        return "Tablet"
    else:
        return "Desktop"


def get_location_from_ip(ip_address: str) -> str:
    """
    Get location from IP address.
    In production, use a GeoIP service like MaxMind or ipapi.
    For now, return a default location.
    """
    if ip_address in ["127.0.0.1", "localhost", "unknown"]:
        return "Local Development"
    
    # In production, use:
    # import requests
    # response = requests.get(f"https://ipapi.co/{ip_address}/json/")
    # data = response.json()
    # return f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
    
    return "London, United Kingdom"  # Default for testing



@router.get("/api/auth/history/{user_id}")
async def get_auth_history(
    user_id: str,
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get authentication history for a user.
    This endpoint is called by Fraud AI to analyze login patterns.
    
    Args:
        user_id: User account ID
        hours: Lookback period in hours (default: 24)
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        {
            "user_id": str,
            "logs": [
                {
                    "log_id": str (10-digit random ID),
                    "device_type": str,
                    "ip_address": str,
                    "location": str,
                    "user_agent": str,
                    "login_success": bool,
                    "date_time": str (UTC format)
                }
            ],
            "total": int
        }
    """
    try:
        lookback_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query auth logs
        auth_logs = db.query(AuthLog).filter(
            AuthLog.user_id == user_id,
            AuthLog.timestamp >= lookback_time
        ).order_by(AuthLog.timestamp.desc()).limit(limit).all()
        
        # Get total count
        total_count = db.query(AuthLog).filter(
            AuthLog.user_id == user_id,
            AuthLog.timestamp >= lookback_time
        ).count()
        
        return {
            "user_id": user_id,
            "logs": [
                {
                    "log_id": log.log_id,
                    "device_type": log.device_type or "Unknown",
                    "ip_address": log.ip_address,
                    "location": log.location or "Unknown",
                    "user_agent": log.user_agent or "Unknown",
                    "login_success": log.login_success,
                    "date_time": log.timestamp.strftime("%B %d, %Y at %H:%M UTC")
                }
                for log in auth_logs
            ],
            "total": total_count
        }
    
    except Exception as e:
        logger.error(f"Failed to get auth history for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve auth history")



@router.get("/api/auth/stats/{user_id}")
async def get_auth_stats(
    user_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get authentication statistics for fraud analysis.
    
    Args:
        user_id: User account ID
        days: Lookback period in days
        db: Database session
    
    Returns:
        {
            "failed_attempts": int,
            "successful_logins": int,
            "unique_devices": int,
            "unique_ips": int,
            "last_login": str (ISO format),
            "last_failed_attempt": str (ISO format)
        }
    """
    try:
        lookback_time = datetime.utcnow() - timedelta(days=days)
        
        # Count failed attempts
        failed_count = db.query(AuthLog).filter(
            AuthLog.user_id == user_id,
            AuthLog.login_success == False,
            AuthLog.timestamp >= lookback_time
        ).count()
        
        # Count successful logins
        success_count = db.query(AuthLog).filter(
            AuthLog.user_id == user_id,
            AuthLog.login_success == True,
            AuthLog.timestamp >= lookback_time
        ).count()
        
        # Count unique devices (successful logins only)
        unique_devices_query = text("""
            SELECT COUNT(DISTINCT device_id) as device_count
            FROM auth_logs
            WHERE user_id = :user_id
            AND login_success = true
            AND timestamp >= :lookback_time
            AND device_id IS NOT NULL
        """)
        
        unique_devices_result = db.execute(
            unique_devices_query,
            {"user_id": user_id, "lookback_time": lookback_time}
        ).fetchone()
        unique_devices = unique_devices_result[0] if unique_devices_result else 0
        
        # Count unique IPs
        unique_ips_query = text("""
            SELECT COUNT(DISTINCT ip_address) as ip_count
            FROM auth_logs
            WHERE user_id = :user_id
            AND timestamp >= :lookback_time
            AND ip_address IS NOT NULL
        """)
        
        unique_ips_result = db.execute(
            unique_ips_query,
            {"user_id": user_id, "lookback_time": lookback_time}
        ).fetchone()
        unique_ips = unique_ips_result[0] if unique_ips_result else 0
        
        # Get last successful login
        last_login = db.query(AuthLog).filter(
            AuthLog.user_id == user_id,
            AuthLog.login_success == True
        ).order_by(AuthLog.timestamp.desc()).first()
        
        # Get last failed attempt
        last_failed = db.query(AuthLog).filter(
            AuthLog.user_id == user_id,
            AuthLog.login_success == False
        ).order_by(AuthLog.timestamp.desc()).first()
        
        return {
            "failed_attempts": failed_count,
            "successful_logins": success_count,
            "unique_devices": unique_devices,
            "unique_ips": unique_ips,
            "last_login": last_login.timestamp.isoformat() if last_login else None,
            "last_failed_attempt": last_failed.timestamp.isoformat() if last_failed else None
        }
    
    except Exception as e:
        logger.error(f"Failed to get auth stats for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve auth stats")
