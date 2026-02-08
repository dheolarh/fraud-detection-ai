"""
Logic 2: Volume Analysis
Detects abnormal transaction volumes by comparing against user baseline.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from decimal import Decimal

from logic_modules.base_logic import BaseFraudLogic
from utils.currency_converter import CurrencyConverter


class VolumeAnalysisLogic(BaseFraudLogic):
    """
    Analyzes transaction volume patterns to detect anomalies.
    
    Risk Indicators:
    - Transaction amount spike (>4x baseline) - BOTH incoming and outgoing
    - Sudden burst of high-value transactions
    - Deviation from historical spending patterns
    
    NOTE: All amounts normalized to USD for comparison
    """
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze transaction volume against user baseline.
        
        Args:
            transaction: Transaction data with 'amount' and 'currency'
            db_session: Database session
            
        Returns:
            float: Risk score (0.0 = normal, 1.0 = extreme spike)
        """
        try:
            sender_id = transaction.get('sender_id')
            current_amount = Decimal(str(transaction.get('amount', 0)))
            currency = transaction.get('currency')  # Must be provided!
            
            if not sender_id or not currency:
                return 0.0
            
            if not sender_id or current_amount <= 0:
                return 0.0
            
            # Convert to USD for standardized comparison
            current_amount_usd = CurrencyConverter.to_usd(current_amount, currency)
            
            baseline = await self._calculate_baseline(sender_id, db_session)
            
            if baseline == 0:
                return 0.0
            
            volume_ratio = float(current_amount_usd / baseline)
            
            # Generate explanation if amount is unusual
            if volume_ratio >= 1.5:
                # Format amounts nicely
                amount_str = f"${float(current_amount_usd):,.2f}" if currency == 'USD' else f"{currency} {float(current_amount):,.2f}"
                baseline_str = f"${float(baseline):,.2f}"
                
                explanation = f"Transaction amount {amount_str} is {volume_ratio:.1f}× user's maximum of {baseline_str}"
                transaction['_volume_explanation'] = explanation
            
            # Risk scoring based on volume ratio (user-specific)
            # High risk at 25× user's max transaction
            if volume_ratio >= 25.0:
                return 1.0  # Extreme: 25× or more
            elif volume_ratio >= 15.0:
                return 0.9  # Very high: 15-25×
            elif volume_ratio >= 10.0:
                return 0.8  # High: 10-15×
            elif volume_ratio >= 5.0:
                return 0.6  # Moderate-high: 5-10×
            elif volume_ratio >= 3.0:
                return 0.4  # Moderate: 3-5×
            elif volume_ratio >= 2.0:
                return 0.2  # Low: 2-3×
            else:
                return 0.0  # Normal: < 2×
                
        except Exception as e:
            return 0.0

    
    async def _calculate_baseline(self, user_id: str, db_session: Session) -> Decimal:
        """
        Calculate user's MAXIMUM transaction amount (in USD) over last 90 days.
        This represents the upper bound of their normal spending.
        
        Fraud suspicion triggers at 25× this amount (e.g., if max is $2800, then $70k is suspicious).
        
        Args:
            user_id: User identifier
            db_session: Database session
            
        Returns:
            Decimal: Maximum transaction amount in USD
        """
        try:
            lookback_days = 90  # Increased from 30 to get better max
            lookback_time = datetime.utcnow() - timedelta(days=lookback_days)
            
            # Get ALL transactions (both incoming and outgoing) with currency
            query = text("""
                SELECT amount, currency
                FROM transactions
                WHERE (sender_id = :user_id OR receiver_id = :user_id)
                AND timestamp > :lookback_time
                AND amount > 0
                ORDER BY amount DESC
                LIMIT 100
            """)
            
            results = db_session.execute(
                query,
                {"user_id": user_id, "lookback_time": lookback_time}
            ).fetchall()
            
            if not results:
                return Decimal('100')  # Default baseline: $100 USD
            
            # Convert all amounts to USD and find maximum
            usd_amounts = []
            for row in results:
                amount = Decimal(str(row[0]))
                currency = row[1] or 'USD'  # USD fallback
                amount_usd = CurrencyConverter.to_usd(amount, currency)
                usd_amounts.append(amount_usd)
            
            # Use maximum transaction as baseline
            max_amount_usd = max(usd_amounts)
            
            return max_amount_usd if max_amount_usd > 0 else Decimal('100')
            
        except Exception as e:
            return Decimal('100')  # Default: $100 USD
