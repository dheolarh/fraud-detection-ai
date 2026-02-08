"""
Logic 9: Historical Baseline
Long-term pattern learning and seasonal adjustment.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text

from logic_modules.base_logic import BaseFraudLogic
from utils.currency_converter import CurrencyConverter


class HistoricalBaselineLogic(BaseFraudLogic):
    """
    Detects anomalies by comparing against historical spending patterns.
    
    Risk Indicators:
    - Amount >5x user's daily average
    - New category with large amount
    - Unusual day/time patterns
    
    NOTE: All amounts normalized to USD for consistent comparison
    
    Risk Bucket: AMOUNT_ANOMALY
    """
    
    def __init__(self):
        super().__init__()
        self.name = "HistoricalBaselineLogic"
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze transaction against long-term historical patterns.
        
        Args:
            transaction: Transaction data
            db_session: Database session
            
        Returns:
            float: Risk score 0.0-1.0
        """
        try:
            sender_id = transaction.get('sender_id')
            amount = float(transaction.get('amount', 0))
            currency = transaction.get('currency', 'USD')  # USD fallback
            category = transaction.get('category', 'UNKNOWN')
            current_time = transaction.get('timestamp', datetime.now())
            
            # Convert to USD for all historical comparisons
            amount_usd = float(CurrencyConverter.to_usd(Decimal(str(amount)), currency))
            
            risk_score = 0.0
            
            # Check 1: Day-of-week pattern (using USD amount)
            dow_score = await self._check_day_of_week(sender_id, current_time, amount_usd, db_session)
            risk_score = max(risk_score, dow_score)
            
            # Check 2: Category preference deviation (using USD amount)
            cat_score = await self._check_category_pattern(sender_id, category, amount_usd, db_session)
            risk_score = max(risk_score, cat_score)
            
            # Check 3: Monthly spending pattern (using USD amount)
            monthly_score = await self._check_monthly_pattern(sender_id, amount_usd, current_time, db_session)
            risk_score = max(risk_score, monthly_score)
            
            # Collect explanations
            explanations = []
            if hasattr(self, '_last_dow_explanation'):
                explanations.append(self._last_dow_explanation)
            if hasattr(self, '_last_cat_explanation'):
                explanations.append(self._last_cat_explanation)
            if hasattr(self, '_last_monthly_explanation'):
                explanations.append(self._last_monthly_explanation)
            
            # Store combined explanation
            if explanations:
                transaction['_baseline_explanation'] = "; ".join(explanations)
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Historical baseline error: {e}")
            return 0.0
    
    async def _check_day_of_week(
        self, sender_id: str, current_time: datetime, amount: float, db_session: Session
    ) -> float:
        """Check if day-of-week matches historical pattern."""
        try:
            if not current_time:
                return 0.0
            
            current_dow = current_time.weekday()  # 0=Monday, 6=Sunday
            
            # Get historical day-of-week spending
            result = db_session.execute(
                text('''
                    SELECT 
                        EXTRACT(DOW FROM timestamp) as dow,
                        AVG(amount) as avg_amount,
                        COUNT(*) as count
                    FROM transactions
                    WHERE sender_id = :sender_id
                    GROUP BY dow
                    ORDER BY count DESC
                '''),
                {'sender_id': sender_id}
            ).fetchall()
            
            if result and len(result) >= 3:
                # Find current day's average
                current_day_avg = None
                for row in result:
                    if int(row[0]) == current_dow:
                        current_day_avg = float(row[1])
                        break
                
                if current_day_avg:
                    # Compare to day's average
                    if amount > current_day_avg * 5:
                        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        self._last_dow_explanation = f"Amount is {amount/current_day_avg:.1f}× user's typical {day_names[current_dow]} spending"
                        return 0.6
                    elif amount > current_day_avg * 3:
                        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        self._last_dow_explanation = f"Amount is {amount/current_day_avg:.1f}× user's typical {day_names[current_dow]} spending"
                        return 0.4
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Day-of-week check error: {e}")
            return 0.0
    
    async def _check_category_pattern(
        self, sender_id: str, category: str, amount: float, db_session: Session
    ) -> float:
        """Check if category usage matches historical pattern."""
        try:
            # Get historical category distribution
            result = db_session.execute(
                text('''
                    SELECT 
                        category,
                        AVG(amount) as avg_amount,
                        COUNT(*) as count
                    FROM transactions
                    WHERE sender_id = :sender_id
                    GROUP BY category
                    ORDER BY count DESC
                '''),
                {'sender_id': sender_id}
            ).fetchall()
            
            if result:
                categories = {row[0]: {'avg': float(row[1]), 'count': row[2]} for row in result}
                
                # Rarely used category with large amount
                if category in categories:
                    cat_data = categories[category]
                    if cat_data['count'] < 3 and amount > cat_data['avg'] * 3:
                        return 0.5
                else:
                    # Completely new category with large amount (>$100 USD)
                    if amount > 100:  # $100 USD threshold
                        return 0.6
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Category pattern error: {e}")
            return 0.0
    
    async def _check_monthly_pattern(
        self, sender_id: str, amount: float, current_time: datetime, db_session: Session
    ) -> float:
        """Check monthly spending patterns."""
        try:
            if not current_time:
                return 0.0
            
            # Get current month's spending
            month_start = current_time.replace(day=1, hour=0, minute=0, second=0)
            
            result = db_session.execute(
                text('''
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM transactions
                    WHERE sender_id = :sender_id
                    AND timestamp >= :month_start
                    AND timestamp < :current_time
                '''),
                {
                    'sender_id': sender_id,
                    'month_start': month_start,
                    'current_time': current_time
                }
            ).fetchone()
            
            if result:
                month_total = float(result[0])
                
                # Get historical monthly average
                avg_result = db_session.execute(
                    text('''
                        SELECT AVG(monthly_total) as avg_monthly
                        FROM (
                            SELECT 
                                DATE_TRUNC('month', timestamp) as month,
                                SUM(amount) as monthly_total
                            FROM transactions
                            WHERE sender_id = :sender_id
                            GROUP BY month
                        ) as monthly_totals
                    '''),
                    {'sender_id': sender_id}
                ).fetchone()
                
                if avg_result and avg_result[0]:
                    avg_monthly = float(avg_result[0])
                    
                    # This transaction would push month over 3x normal
                    if (month_total + amount) > avg_monthly * 3:
                        return 0.5
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Monthly pattern error: {e}")
            return 0.0
