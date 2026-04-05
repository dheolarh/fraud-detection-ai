"""
Rate limiting middleware for API protection.
Prevents abuse and DDoS attacks.
"""

from fastapi import Request, HTTPException
from typing import Dict
import time
from collections import defaultdict
from loguru import logger

class RateLimiter:
    """
    In-memory rate limiter (use Redis in production for distributed systems)
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit
        
        Args:
            identifier: Client identifier (IP address or user ID)
        
        Returns:
            bool: True if allowed, False if rate limited
        """
        try:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > minute_ago
            ]
            
            # Check limit
            if len(self.requests[identifier]) >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for: {identifier}")
                return False
            
            # Add current request
            self.requests[identifier].append(now)
            return True
        
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Fail open in case of errors


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=1000)  # Increased from 60 to 1000 for development


LOCALHOST_IPS = {"127.0.0.1", "::1", "localhost"}

async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    Localhost and CORS preflight requests are always allowed.
    """
    client_ip = request.client.host

    # Skip rate limiting for local development frontend and CORS preflight
    if client_ip in LOCALHOST_IPS or request.method == "OPTIONS":
        return await call_next(request)

    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

    response = await call_next(request)
    return response
