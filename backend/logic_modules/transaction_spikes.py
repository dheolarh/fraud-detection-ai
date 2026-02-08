"""
Logic 4: Transaction Spike Detection
Detects rapid bursts of transactions characteristic of automated attacks.
Uses Redis for high-speed velocity tracking.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import redis

from logic_modules.base_logic import BaseFraudLogic


class TransactionSpikeLogic(BaseFraudLogic):
    """
    Detects transaction spikes using Redis-backed counters.
    
    Risk Indicators:
    - Multiple transactions within seconds (bot behavior)
    - Flash activity bursts
    - Rapid-fire transaction patterns
    """
    
    def __init__(self):
        super().__init__()
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_available = True
        except Exception:
            self.redis_client = None
            self.redis_available = False
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze transaction velocity for spike patterns.
        
        Args:
            transaction: Transaction data
            db_session: Database session
            
        Returns:
            float: Risk score (0.0 = normal, 1.0 = clear bot activity)
        """
        try:
            sender_id = transaction.get('sender_id')
            
            if not sender_id:
                return 0.0
            
            if self.redis_available:
                redis_score = await self._check_redis_velocity(sender_id)
            else:
                redis_score = 0.0
            
            db_score = await self._check_database_velocity(sender_id, db_session, transaction)
            
            final_score = max(redis_score, db_score)
            
            return min(final_score, 1.0)
            
        except Exception as e:
            return 0.0
    
    async def _check_redis_velocity(self, user_id: str) -> float:
        """
        Check transaction velocity using Redis counters.
        
        Args:
            user_id: User identifier
            
        Returns:
            float: Risk score based on velocity
        """
        try:
            if not self.redis_client:
                return 0.0
            
            key_10s = f"txn_count:{user_id}:10s"
            key_60s = f"txn_count:{user_id}:60s"
            
            self.redis_client.incr(key_10s)
            self.redis_client.expire(key_10s, 10)
            
            self.redis_client.incr(key_60s)
            self.redis_client.expire(key_60s, 60)
            
            count_10s = int(self.redis_client.get(key_10s) or 0)
            count_60s = int(self.redis_client.get(key_60s) or 0)
            
            if count_10s >= 5:
                return 1.0
            elif count_10s >= 3:
                return 0.8
            elif count_60s >= 15:
                return 0.9
            elif count_60s >= 10:
                return 0.7
            elif count_60s >= 6:
                return 0.5
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
    
    async def _check_database_velocity(
        self, user_id: str, db_session: Session, transaction: Dict[str, Any] = None
    ) -> float:
        """
        Fallback: Check velocity using database timestamps.
        
        Args:
            user_id: User identifier
            db_session: Database session
            transaction: Transaction data for explanation storage
            
        Returns:
            float: Risk score
        """
        try:
            lookback_minutes = 10
            lookback_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            
            query = text("""
                SELECT COUNT(*) as transaction_count
                FROM transactions
                WHERE sender_id = :user_id
                AND timestamp > :lookback_time
            """)
            
            result = db_session.execute(
                query,
                {"user_id": user_id, "lookback_time": lookback_time}
            ).fetchone()
            
            count = result[0] if result else 0
            
            # Generate explanation
            if count >= 3 and transaction:
                transaction['_spike_explanation'] = f"{count} transactions in last {lookback_minutes} minutes (rapid burst detected)"
            
            if count >= 10:
                return 0.9
            elif count >= 7:
                return 0.7
            elif count >= 5:
                return 0.5
            elif count >= 3:
                return 0.3
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
