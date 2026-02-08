"""
Banking Backend API Client for Fraud Detection Service

This client queries the Banking Backend (port 8001) to fetch:
- User account information
- Transaction history
- Bank location/currency
- Account balances

The fraud backend uses this data for analysis but does NOT store it.
"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BankingClient:
    """Client to interact with Banking Backend APIs"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user account information from banking backend
        
        Returns:
            {
                "user_id": str,
                "username": str,
                "account_balance": float,
                "is_frozen": bool,
                "created_at": str
            }
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    async def get_bank_location(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Get bank's physical location and currency
        
        Returns:
            {
                "country": "United Kingdom",
                "currency": "GBP",
                "city": "London"
            }
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/bank/location")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get bank location: {e}")
            return {"country": "United Kingdom", "currency": "GBP", "city": "London"}
    
    async def get_transactions(
        self, 
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history from banking backend
        
        Args:
            user_id: User account ID
            start_date: Filter transactions from this date
            end_date: Filter transactions until this date
            limit: Maximum number of transactions to return
            offset: Pagination offset
        
        Returns:
            List of transactions with structure:
            [{
                "transaction_id": int,
                "sender_id": str,
                "sender_name": str,
                "receiver_id": str,
                "receiver_name": str,
                "transaction_flow": str,  # 'incoming' or 'outgoing'
                "amount": float,
                "currency": str,
                "category": str,
                "location": str,
                "narration": str,
                "timestamp": str,
                "status": str
            }]
        """
        try:
            params = {
                "user_id": user_id,
                "offset": offset
            }
            
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()
            if limit:
                params["limit"] = limit
            
            response = await self.client.get(
                f"{self.base_url}/api/transactions",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get transactions for {user_id}: {e}")
            # Return empty dict structure to match expected format
            return {"transactions": [], "total": 0, "limit": limit or 100, "offset": offset}
    
    async def get_transaction_stats(
        self,
        user_id: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        Get transaction statistics for behavioral analysis
        
        Returns:
            {
                "total_incoming": float,
                "total_outgoing": float,
                "avg_transaction_amount": float,
                "transaction_count": int,
                "most_common_categories": List[str],
                "avg_monthly_income": float,
                "avg_monthly_spending": float
            }
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            response = await self.client.get(
                f"{self.base_url}/api/transactions/stats",
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get transaction stats for {user_id}: {e}")
            return {}
    
    async def analyze_transaction(
        self,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit a new transaction to banking backend for storage
        Banking backend will then call fraud backend for analysis
        
        Args:
            transaction_data: Transaction details
        
        Returns:
            {
                "transaction_id": int,
                "status": str,
                "message": str
            }
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/transactions/send",
                json=transaction_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to submit transaction: {e}")
            raise
    
    async def get_auth_history(
        self,
        user_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get authentication history from banking backend.
        Used by fraud detection to analyze login patterns.
        
        Args:
            user_id: User account ID
            hours: Lookback period in hours
            limit: Maximum number of records
        
        Returns:
            {
                "user_id": str,
                "logs": [
                    {
                        "log_id": int,
                        "device_id": str,
                        "ip_address": str,
                        "login_success": bool,
                        "timestamp": str
                    }
                ],
                "total": int
            }
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/auth/history/{user_id}",
                params={"hours": hours, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get auth history for {user_id}: {e}")
            return {"user_id": user_id, "logs": [], "total": 0}
    
    async def get_auth_stats(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get authentication statistics from banking backend.
        
        Args:
            user_id: User account ID
            days: Lookback period in days
        
        Returns:
            {
                "failed_attempts": int,
                "successful_logins": int,
                "unique_devices": int,
                "unique_ips": int,
                "last_login": str,
                "last_failed_attempt": str
            }
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/auth/stats/{user_id}",
                params={"days": days}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get auth stats for {user_id}: {e}")
            return {
                "failed_attempts": 0,
                "successful_logins": 0,
                "unique_devices": 0,
                "unique_ips": 0,
                "last_login": None,
                "last_failed_attempt": None
            }



# Global client instance
_banking_client: Optional[BankingClient] = None

def get_banking_client() -> BankingClient:
    """Get or create global banking client instance"""
    global _banking_client
    if _banking_client is None:
        _banking_client = BankingClient()
    return _banking_client

async def close_banking_client():
    """Close global banking client"""
    global _banking_client
    if _banking_client:
        await _banking_client.close()
        _banking_client = None
