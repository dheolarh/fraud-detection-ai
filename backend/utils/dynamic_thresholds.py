"""
Dynamic Threshold Calculator
Calculates personalized fraud detection thresholds based on user's transaction history.

Key Principle:
- If user typically transacts in hundreds (₦100-900) → threshold ~₦100,000
- If user typically transacts in thousands (₦1K-9K) → threshold ~₦1,000,000
- If user typically transacts in tens of thousands → threshold ~₦10,000,000

All amounts normalized to USD for consistency.
"""

from decimal import Decimal
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger
import math

from utils.currency_converter import CurrencyConverter


class DynamicThresholdCalculator:
    """
    Calculates adaptive fraud thresholds based on user's spending patterns.
    Thresholds are personalized - no more hardcoded $10K!
    """
    
    # Default thresholds (used only for brand new users with no history)
    DEFAULT_STRUCTURING_THRESHOLD_USD = Decimal('10000')  # $10K
    DEFAULT_LARGE_TRANSACTION_USD = Decimal('5000')  # $5K
    
    # Multipliers for threshold calculation
    STRUCTURING_MULTIPLIER = 100  # If avg is $100, threshold is $10,000
    LARGE_TRANSACTION_MULTIPLIER = 50  # If avg is $100, large is $5,000
    
    @classmethod
    async def get_user_thresholds(cls, user_id: str, db_session: Session) -> Dict[str, Decimal]:
        """
        Calculate personalized thresholds for a user based on their history.
        
        Returns dict with:
        - structuring_threshold: Amount just below which is suspicious (e.g., $9,500 repeatedly)
        - large_transaction: Amount above which is considered unusually large
        - high_value_international: Threshold for cross-border transfers
        
        Args:
            user_id: User identifier
            db_session: Database session
            
        Returns:
            Dict of threshold names to USD amounts
        """
        try:
            # Get user's historical transaction statistics
            query = text("""
                SELECT 
                    COUNT(*) as total_count,
                    AVG(amount) as avg_amount,
                    STDDEV(amount) as std_amount,
                    MAX(amount) as max_amount,
                    MIN(amount) as min_amount,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY amount) as median,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount) as p75,
                    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY amount) as p90,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY amount) as p95
                FROM transactions
                WHERE sender_id = :user_id
                AND amount > 0
                AND timestamp >= NOW() - INTERVAL '90 days'
            """)
            
            result = db_session.execute(query, {"user_id": user_id}).fetchone()
            
            if not result or not result[0] or result[0] < 5:
                # Not enough history, use defaults
                logger.info(f"User {user_id} has insufficient history, using default thresholds")
                return cls._get_default_thresholds()
            
            count = result[0]
            avg_amount = Decimal(str(result[1])) if result[1] else Decimal('0')
            std_amount = Decimal(str(result[2])) if result[2] else Decimal('0')
            max_amount = Decimal(str(result[3])) if result[3] else Decimal('0')
            median = Decimal(str(result[5])) if result[5] else Decimal('0')
            p75 = Decimal(str(result[6])) if result[6] else Decimal('0')
            p90 = Decimal(str(result[7])) if result[7] else Decimal('0')
            p95 = Decimal(str(result[8])) if result[8] else Decimal('0')
            
            # Convert historical amounts to USD for threshold calculation
            # Note: This assumes historical transactions have currency field
            # For mixed currencies, we need to normalize each
            avg_amount_usd = await cls._normalize_historical_avg(user_id, db_session)
            
            # Calculate thresholds based on user's typical transaction range
            thresholds = cls._calculate_adaptive_thresholds(
                avg_amount_usd, median, p75, p90, p95, max_amount
            )
            
            logger.info(f"User {user_id} adaptive thresholds: {thresholds}")
            return thresholds
            
        except Exception as e:
            logger.error(f"Error calculating thresholds for {user_id}: {e}")
            return cls._get_default_thresholds()
    
    @classmethod
    async def _normalize_historical_avg(cls, user_id: str, db_session: Session) -> Decimal:
        """
        Calculate average transaction amount in USD by normalizing each transaction.
        """
        try:
            # Get all transactions with currency
            query = text("""
                SELECT amount, COALESCE(currency, 'USD') as currency
                FROM transactions
                WHERE sender_id = :user_id
                AND amount > 0
                AND timestamp >= NOW() - INTERVAL '365 days'
                LIMIT 1000
            """)
            
            results = db_session.execute(query, {"user_id": user_id}).fetchall()
            
            if not results:
                return Decimal('100')  # Default $100
            
            # Convert each to USD and calculate average
            usd_amounts = []
            for row in results:
                amount = Decimal(str(row[0]))
                currency = row[1]
                amount_usd = CurrencyConverter.to_usd(amount, currency)
                usd_amounts.append(amount_usd)
            
            avg_usd = sum(usd_amounts) / len(usd_amounts)
            return avg_usd
            
        except Exception as e:
            logger.error(f"Error normalizing historical avg: {e}")
            return Decimal('100')
    
    @classmethod
    def _calculate_adaptive_thresholds(
        cls,
        avg_amount: Decimal,
        median: Decimal,
        p75: Decimal,
        p90: Decimal,
        p95: Decimal,
        max_amount: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate thresholds based on user's spending pattern.
        
        Logic:
        - If user typically does $100-$900 transactions → threshold ~$10K-$100K
        - If user typically does $1K-$9K transactions → threshold ~$100K-$1M
        - If user typically does $10K+ transactions → threshold ~$1M+
        """
        # Determine the "order of magnitude" of user's typical transactions
        # This tells us if they're a "hundreds", "thousands", or "tens of thousands" user
        typical_amount = max(avg_amount, median)
        
        if typical_amount <= 0:
            return cls._get_default_thresholds()
        
        # Calculate order of magnitude (e.g., 500 → 2, 5000 → 3, 50000 → 4)
        magnitude = int(math.log10(float(typical_amount)))
        
        # Structuring threshold: 2-3 orders of magnitude above typical
        # If typical is $100 (magnitude 2), threshold is $10K-$100K (magnitude 4-5)
        # If typical is $1K (magnitude 3), threshold is $100K-$1M (magnitude 5-6)
        structuring_threshold = Decimal(10 ** (magnitude + 2))
        
        # Large transaction: 1-2 orders of magnitude above typical
        # This catches unusually large (but not necessarily illegal) transactions
        large_transaction = p90 * Decimal('3')  # 3x the 90th percentile
        if large_transaction < structuring_threshold / 2:
            large_transaction = structuring_threshold / 2
        
        # High-value international: same as structuring threshold
        # International transfers warrant extra scrutiny
        high_value_international = structuring_threshold
        
        # Cross-border suspicious: even lower threshold for international
        cross_border_suspicious = structuring_threshold / 2
        
        return {
            'structuring_threshold': structuring_threshold,
            'large_transaction': large_transaction,
            'high_value_international': high_value_international,
            'cross_border_suspicious': cross_border_suspicious,
            'typical_amount': typical_amount,
            'max_seen': max_amount
        }
    
    @classmethod
    def _get_default_thresholds(cls) -> Dict[str, Decimal]:
        """Default thresholds for users with no history."""
        return {
            'structuring_threshold': cls.DEFAULT_STRUCTURING_THRESHOLD_USD,
            'large_transaction': cls.DEFAULT_LARGE_TRANSACTION_USD,
           'high_value_international': cls.DEFAULT_STRUCTURING_THRESHOLD_USD,
            'cross_border_suspicious': cls.DEFAULT_LARGE_TRANSACTION_USD,
            'typical_amount': Decimal('100'),
            'max_seen': Decimal('0')
        }
    
    @classmethod
    async def get_threshold(
        cls,
        user_id: str,
        threshold_type: str,
        db_session: Session
    ) -> Decimal:
        """
        Get a specific threshold for a user.
        
        Args:
            user_id: User identifier
            threshold_type: Type of threshold ('structuring_threshold', 'large_transaction', etc.)
            db_session: Database session
            
        Returns:
            Threshold amount in USD
        """
        thresholds = await cls.get_user_thresholds(user_id, db_session)
        return thresholds.get(threshold_type, cls.DEFAULT_STRUCTURING_THRESHOLD_USD)
