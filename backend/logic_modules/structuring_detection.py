"""
Logic 3: Structuring Detection (Smurfing)
Detects money laundering patterns through multiple small transactions.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from decimal import Decimal

from logic_modules.base_logic import BaseFraudLogic
from utils.currency_converter import CurrencyConverter
from utils.dynamic_thresholds import DynamicThresholdCalculator


class StructuringLogic(BaseFraudLogic):
    """
    Detects structuring (smurfing) patterns in transaction history.
    
    Risk Indicators:
    - Multiple transactions just below PERSONALIZED threshold
    - Transactions to many unique recipients in short time
    - Pattern of small, frequent transfers
    
    NOTE: Thresholds are DYNAMIC - personalized per user based on 1-year history!
    """
    
    JUST_UNDER_BUFFER = Decimal('500')  # $500 buffer below user's threshold
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze for structuring/smurfing patterns.
        
        Args:
            transaction: Transaction data
            db_session: Database session
            
        Returns:
            float: Risk score (0.0 = no pattern, 1.0 = clear structuring)
        """
        try:
            sender_id = transaction.get('sender_id')
            current_amount = Decimal(str(transaction.get('amount', 0)))
            currency = transaction.get('currency', 'USD')  # USD fallback
            
            if not sender_id:
                return 0.0
            
            # Convert to USD for threshold comparison
            amount_usd = CurrencyConverter.to_usd(current_amount, currency)
            
            # Get user's PERSONALIZED structuring threshold (based on 1-year history)
            user_threshold = await DynamicThresholdCalculator.get_threshold(
                sender_id, 'structuring_threshold', db_session
            )
            
            just_under_score = self._check_just_under_threshold(amount_usd, user_threshold)
            
            frequency_score = await self._check_transaction_frequency(
                sender_id, db_session
            )
            
            recipient_diversity_score = await self._check_recipient_diversity(
                sender_id, db_session
            )
            
            final_score = max(
                just_under_score * 0.4 + frequency_score * 0.3 + recipient_diversity_score * 0.3,
                just_under_score,
                frequency_score
            )
            
            # Generate explanation
            if final_score >= 0.5:
                if just_under_score > 0:
                    transaction['_structuring_explanation'] = f"Transaction amount ${float(amount_usd):,.2f} is just under user's threshold of ${float(user_threshold):,.2f} (potential structuring)"
                elif frequency_score > 0:
                    transaction['_structuring_explanation'] = "Multiple transactions in short time period (potential structuring pattern)"
            
            return min(final_score, 1.0)
            
        except Exception as e:
            return 0.0
    
    def _check_just_under_threshold(self, amount_usd: Decimal, user_threshold: Decimal) -> float:
        """
        Check if transaction is just under user's PERSONALIZED threshold.
        
        Args:
            amount_usd: Transaction amount in USD
            user_threshold: User's personalized structuring threshold (calculated from history)
            
        Returns:
            float: Risk score
        """
        buffer = self.JUST_UNDER_BUFFER  # $500 buffer
        
        if user_threshold - buffer <= amount_usd < user_threshold:
            return 0.9  # Very suspicious - just under their threshold!
        elif user_threshold - (buffer * 2) <= amount_usd < user_threshold - buffer:
            return 0.7  # Moderately suspicious
        else:
            return 0.0
    
    async def _check_transaction_frequency(
        self, user_id: str, db_session: Session
    ) -> float:
        """
        Check for high frequency of transactions in short time window.
        
        Args:
            user_id: User identifier
            db_session: Database session
            
        Returns:
            float: Risk score based on frequency
        """
        try:
            lookback_hours = 24
            lookback_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
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
    
    async def _check_recipient_diversity(
        self, user_id: str, db_session: Session
    ) -> float:
        """
        Check for transactions to many unique recipients.
        
        Args:
            user_id: User identifier
            db_session: Database session
            
        Returns:
            float: Risk score based on recipient diversity
        """
        try:
            lookback_hours = 48
            lookback_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            query = text("""
                SELECT COUNT(DISTINCT receiver_id) as unique_receivers
                FROM transactions
                WHERE sender_id = :user_id
                AND timestamp > :lookback_time
            """)
            
            result = db_session.execute(
                query,
                {"user_id": user_id, "lookback_time": lookback_time}
            ).fetchone()
            
            unique_count = result[0] if result else 0
            
            if unique_count >= 8:
                return 0.9
            elif unique_count >= 6:
                return 0.7
            elif unique_count >= 4:
                return 0.5
            elif unique_count >= 3:
                return 0.3
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
