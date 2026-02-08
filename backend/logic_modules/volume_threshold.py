"""
Logic 5: Volume Threshold Monitor
Enforces hard transaction limits based on user type and account status.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from logic_modules.base_logic import BaseFraudLogic


class VolumeThresholdLogic(BaseFraudLogic):
    """
    Monitors transactions against behavioral threshold limits.
    
    Risk Indicators:
    - Transaction exceeds 100x user's average (single txn)
    - Daily volume exceeds 500x user's average daily
    - Account balance drain exceeds 80%
    """
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Check transaction against behavioral threshold limits.
        
        Args:
            transaction: Transaction data
            db_session: Database session
            
        Returns:
            float: Risk score (0.0 = within limits, 1.0 = exceeded)
        """
        try:
            sender_id = transaction.get('sender_id')
            current_amount = Decimal(str(transaction.get('amount', 0)))
            
            if not sender_id or current_amount <= 0:
                return 0.0
            
            single_txn_score = await self._check_single_transaction_limit(
                sender_id, current_amount, db_session, transaction
            )
            
            daily_volume_score = await self._check_daily_volume_limit(
                sender_id, current_amount, db_session, transaction
            )
            
            balance_drain_score = await self._check_balance_drain(
                sender_id, current_amount, db_session, transaction
            )
            
            # Collect explanations
            explanations = []
            if hasattr(self, '_last_single_explanation'):
                explanations.append(self._last_single_explanation)
            if hasattr(self, '_last_daily_explanation'):
                explanations.append(self._last_daily_explanation)
            if hasattr(self, '_last_drain_explanation'):
                explanations.append(self._last_drain_explanation)
            
            # Store combined explanation
            if explanations:
                transaction['_volume_threshold_explanation'] = "; ".join(explanations)
            
            final_score = max(
                single_txn_score,
                daily_volume_score,
                balance_drain_score
            )
            
            return min(final_score, 1.0)
            
        except Exception as e:
            return 0.0
    
    async def _check_single_transaction_limit(
        self, user_id: str, amount: Decimal, db_session: Session, transaction: Dict[str, Any] = None
    ) -> float:
        """
        Check if single transaction exceeds user's behavioral baseline.
        
        Args:
            user_id: User identifier
            amount: Transaction amount  
            db_session: Database session
            transaction: Transaction data for explanation storage
            
        Returns:
            float: Risk score
        """
        try:
            # Get user's 30-day average
            query = text("""
                SELECT AVG(amount) as avg_amount
                FROM transactions
                WHERE sender_id = :user_id
                AND timestamp >= NOW() - INTERVAL '30 days'
            """)
            
            result = db_session.execute(query, {"user_id": user_id}).fetchone()
            
            if result and result[0]:
                user_avg = Decimal(str(result[0]))
                
                if user_avg > 0:
                    multiplier = float(amount / user_avg)
                    
                    # Generate explanation
                    if multiplier >= 10:
                        self._last_single_explanation = f"Transaction amount is {multiplier:.0f}× user's 30-day average of ${float(user_avg):,.2f}"
                    
                    # Behavioral thresholds (relative to user's normal)
                    if multiplier >= 100:  # 100x their average
                        return 1.0
                    elif multiplier >= 50:  # 50x their average
                        return 0.8
                    elif multiplier >= 30:  # 30x their average
                        return 0.6
                    elif multiplier >= 10:  # 10x their average
                        return 0.3
            
            return 0.0
                
        except Exception as e:
            return 0.0
    
    
    async def _check_daily_volume_limit(
        self, user_id: str, current_amount: Decimal, db_session: Session, transaction: Dict[str, Any] = None
    ) -> float:
        """
        Check if daily volume exceeds user's behavioral baseline.
        
        Args:
            user_id: User identifier
            current_amount: Current transaction amount
            db_session: Database session
            transaction: Transaction data for explanation storage
            
        Returns:
            float: Risk score
        """
        try:
            from datetime import datetime, timedelta
            
            # Get today's volume so far
            lookback_time = datetime.utcnow() - timedelta(hours=24)
            
            query = text("""
                SELECT COALESCE(SUM(amount), 0) as daily_volume
                FROM transactions
                WHERE sender_id = :user_id
                AND timestamp > :lookback_time
            """)
            
            result = db_session.execute(
                query,
                {"user_id": user_id, "lookback_time": lookback_time}
            ).fetchone()
            
            daily_volume = Decimal(str(result[0])) if result and result[0] else Decimal('0')
            total_with_current = daily_volume + current_amount
            
            # Get user's average daily volume
            avg_query = text("""
                SELECT AVG(daily_sum) as avg_daily
                FROM (
                    SELECT DATE(timestamp) as day, SUM(amount) as daily_sum
                    FROM transactions
                    WHERE sender_id = :user_id
                    AND timestamp >= NOW() - INTERVAL '30 days'
                    GROUP BY day
                ) as daily_totals
            """)
            
            avg_result = db_session.execute(avg_query, {"user_id": user_id}).fetchone()
            
            if avg_result and avg_result[0]:
                user_avg_daily = Decimal(str(avg_result[0]))
                
                if user_avg_daily > 0:
                    multiplier = float(total_with_current / user_avg_daily)
                    
                    # Generate explanation
                    if multiplier >= 20:
                        self._last_daily_explanation = f"Daily volume would be {multiplier:.0f}× user's normal daily spending of ${float(user_avg_daily):,.2f}"
                    
                    # Behavioral thresholds for daily volume
                    if multiplier >= 500:  # 500x their average daily
                        return 1.0
                    elif multiplier >= 100:  # 100x their average daily
                        return 0.8
                    elif multiplier >= 50:  # 50x their average daily
                        return 0.6
                    elif multiplier >= 20:  # 20x their average daily
                        return 0.3
            
            return 0.0
                
        except Exception as e:
            return 0.0
    
    async def _check_balance_drain(
        self, user_id: str, current_amount: Decimal, db_session: Session, transaction: Dict[str, Any] = None
    ) -> float:
        """
        Check if transaction drains significant portion of balance.
        
        Args:
            user_id: User identifier
            current_amount: Transaction amount
            db_session: Database session
            transaction: Transaction data for explanation storage
            
        Returns:
            float: Risk score
        """
        try:
            query = text("""
                SELECT account_balance
                FROM users
                WHERE user_id = :user_id
            """)
            
            result = db_session.execute(query, {"user_id": user_id}).fetchone()
            
            if not result or not result[0]:
                return 0.0
            
            balance = Decimal(str(result[0]))
            
            if balance <= 0:
                return 0.0
            
            drain_ratio = float(current_amount / balance)
            
            # Generate explanation
            if drain_ratio >= 0.4:
                percentage = drain_ratio * 100
                self._last_drain_explanation = f"Transaction would drain {percentage:.0f}% of account balance (${float(current_amount):,.2f} of ${float(balance):,.2f})"
            
            if drain_ratio >= 0.95:
                return 1.0
            elif drain_ratio >= 0.8:
                return 0.8
            elif drain_ratio >= 0.6:
                return 0.5
            elif drain_ratio >= 0.4:
                return 0.3
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
