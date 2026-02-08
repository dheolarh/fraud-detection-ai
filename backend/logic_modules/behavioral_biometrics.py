"""
Logic 8: Behavioral Biometrics
Session-based fraud detection through behavioral patterns.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text

from logic_modules.base_logic import BaseFraudLogic
from clients.banking_client import get_banking_client


class BehavioralBiometricsLogic(BaseFraudLogic):
    """
    Detects fraud through behavioral anomalies.
    
    Analyzes:
    - Session duration patterns
    - Device fingerprint consistency (future)
    - Typing speed anomalies (future)
    - Mouse movement patterns (future)
    
    Risk Bucket: ACCOUNT_COMPROMISE
    
    NOTE: This logic queries the Banking Backend API for auth history.
    It does NOT access the database directly.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "BehavioralBiometricsLogic"
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze behavioral patterns for fraud indicators.
        
        Args:
            transaction: Transaction data
            db_session: Database session (used for transaction queries only)
            
        Returns:
            float: Risk score 0.0-1.0
        """
        try:
            sender_id = transaction.get('sender_id')
            current_user_agent = transaction.get('user_agent', 'UNKNOWN')
            current_time = transaction.get('timestamp', datetime.now())
            
            risk_score = 0.0
            
            # Check 1: Session duration anomalies
            session_score = await self._check_session_duration(sender_id, current_time, db_session, transaction)
            risk_score = max(risk_score, session_score)
            
            # Check 2: Device fingerprint verification (using user agent)
            device_score = await self._check_device_consistency(sender_id, current_user_agent, transaction)
            risk_score = max(risk_score, device_score)
            
            # Check 3: Unusual transaction timing
            timing_score = await self._check_timing_patterns(sender_id, current_time, db_session, transaction)
            risk_score = max(risk_score, timing_score)
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Behavioral biometrics error: {e}")
            return 0.0
    
    async def _check_session_duration(
        self, sender_id: str, current_time: datetime, db_session: Session
    ) -> float:
        """Check if session duration is suspicious."""
        try:
            # Get last transaction time
            result = db_session.execute(
                text('''
                    SELECT timestamp
                    FROM transactions
                    WHERE sender_id = :sender_id
                    ORDER BY timestamp DESC
                    LIMIT 1
                '''),
                {'sender_id': sender_id}
            ).fetchone()
            
            if result:
                last_txn_time = result[0]
                if current_time and last_txn_time:
                    time_diff_seconds = (current_time - last_txn_time).total_seconds()
                    
                    # Extremely fast transactions (< 1 second) - bot behavior
                    if time_diff_seconds < 1:
                        return 0.9
                    # Very fast (< 5 seconds) - suspicious
                    elif time_diff_seconds < 5:
                        return 0.7
                    # Unusually long session gap (> 24 hours) with sudden activity
                    elif time_diff_seconds > 86400:  # 24 hours
                        # Check if there's a pattern of long gaps
                        return 0.3
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Session duration check error: {e}")
            return 0.0
    
    async def _check_device_consistency(
        self, sender_id: str, current_user_agent: str
    ) -> float:
        """
        Check device fingerprint consistency using user agent.
        Queries Banking Backend API for auth history.
        """
        try:
            # Get banking client
            banking_client = get_banking_client()
            
            # Query auth history from banking backend (last 30 days)
            auth_data = await banking_client.get_auth_history(
                user_id=sender_id,
                hours=720,  # 30 days
                limit=1000
            )
            
            logs = auth_data.get('logs', [])
            
            if logs:
                # Get successful logins only
                successful_logins = [log for log in logs if log.get('login_success', False)]
                
                # Get unique user agents (device fingerprints)
                known_user_agents = set(
                    log.get('user_agent')
                    for log in successful_logins
                    if log.get('user_agent') and log.get('user_agent') != 'Unknown'
                )
                
                # Unknown user agent being used
                if current_user_agent not in known_user_agents and current_user_agent != 'UNKNOWN':
                    # New device/browser = moderate risk
                    return 0.5
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Device consistency error: {e}")
            return 0.0
    
    async def _check_timing_patterns(
        self, sender_id: str, current_time: datetime, db_session: Session
    ) -> float:
        """Check if transaction time matches user's normal patterns."""
        try:
            if not current_time:
                return 0.0
            
            hour_of_day = current_time.hour
            
            # Get user's historical transaction hours
            result = db_session.execute(
                text('''
                    SELECT EXTRACT(HOUR FROM timestamp) as hour, COUNT(*) as count
                    FROM transactions
                    WHERE sender_id = :sender_id
                    GROUP BY hour
                    ORDER BY count DESC
                    LIMIT 5
                '''),
                {'sender_id': sender_id}
            ).fetchall()
            
            if result and len(result) >= 3:
                common_hours = [int(row[0]) for row in result]
                
                # Transaction at unusual hour (3-6 AM) not in user's pattern
                if hour_of_day in [3, 4, 5] and hour_of_day not in common_hours:
                    return 0.6
                # Transaction at very unusual hour for this user
                elif hour_of_day not in common_hours:
                    return 0.3
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Timing pattern error: {e}")
            return 0.0
