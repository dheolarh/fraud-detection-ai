"""
Logic 7: Velocity Logic
Transaction velocity tracking with user-specific thresholds.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text

from logic_modules.base_logic import BaseFraudLogic


class VelocityLogic(BaseFraudLogic):
    """
    Multi-window transaction velocity detection with adaptive thresholds.
    
    Compares current velocity to user's historical average:
    - 1 hour window
    - 24 hour window
    - 7 day window
    
    Uses user-specific thresholds to avoid false positives for high-volume users.
    
    Risk Bucket: AUTOMATION_ABUSE
    """
    
    def __init__(self):
        super().__init__()
        self.name = "VelocityLogic"
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze transaction velocity against user's historical patterns.
        
        Args:
            transaction: Transaction data
            db_session: Database session
            
        Returns:
            float: Risk score 0.0-1.0
        """
        try:
            sender_id = transaction.get('sender_id')
            current_time = transaction.get('timestamp', datetime.now())
            
            if not sender_id:
                return 0.0
            
            risk_scores = []
            explanations = []
            
            # Check 1 hour velocity
            score_1h, exp_1h = await self._check_window_adaptive(
                sender_id, current_time, hours=1, db_session=db_session
            )
            risk_scores.append(score_1h)
            if exp_1h:
                explanations.append(exp_1h)
            
            # Check 24 hour velocity
            score_24h, exp_24h = await self._check_window_adaptive(
                sender_id, current_time, hours=24, db_session=db_session
            )
            risk_scores.append(score_24h)
            if exp_24h:
                explanations.append(exp_24h)
            
            # Check 7 day velocity
            score_7d, exp_7d = await self._check_window_adaptive(
                sender_id, current_time, days=7, db_session=db_session
            )
            risk_scores.append(score_7d)
            if exp_7d:
                explanations.append(exp_7d)
            
            # Return maximum score across all windows
            final_score = max(risk_scores) if risk_scores else 0.0
            
            # Store explanation for later use (will be picked up by orchestrator)
            if explanations and final_score > 0:
                # Store the explanation with highest score
                max_idx = risk_scores.index(final_score)
                if max_idx < len(explanations):
                    transaction['_velocity_explanation'] = explanations[max_idx]
            
            if final_score >= 0.7:
                logger.warning(f"High velocity detected for {sender_id}: score={final_score:.2f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Velocity analysis error: {e}")
            return 0.0
    
    async def _check_window_adaptive(
        self, sender_id: str, current_time: datetime,
        hours: int = None, days: int = None, db_session: Session = None
    ) -> tuple[float, str]:
        """
        Check transaction velocity using user-specific thresholds.
        
        Compares current velocity to user's historical average.
        Returns (risk_score, explanation)
        """
        try:
            # Calculate window
            if days:
                window_start = current_time - timedelta(days=days)
                window_hours = days * 24
                window_name = f"{days} day{'s' if days > 1 else ''}"
            else:
                window_start = current_time - timedelta(hours=hours)
                window_hours = hours
                window_name = f"{hours} hour{'s' if hours > 1 else ''}"
            
            # Count transactions in current window (BOTH incoming and outgoing)
            result = db_session.execute(
                text('''
                    SELECT COUNT(*) as txn_count
                    FROM transactions
                    WHERE (sender_id = :sender_id OR receiver_id = :sender_id)
                    AND timestamp >= :window_start
                    AND timestamp < :current_time
                '''),
                {
                    'sender_id': sender_id,
                    'window_start': window_start,
                    'current_time': current_time
                }
            ).fetchone()
            
            current_count = result[0] if result else 0
            
            # Get user's historical average for this window size (both directions)
            avg_result = db_session.execute(
                text('''
                    SELECT AVG(window_count) as avg_count
                    FROM (
                        SELECT 
                            DATE_TRUNC('hour', timestamp) as hour_bucket,
                            COUNT(*) as window_count
                        FROM transactions
                        WHERE (sender_id = :sender_id OR receiver_id = :sender_id)
                        AND timestamp < :current_time - INTERVAL '7 days'
                        AND timestamp >= :current_time - INTERVAL '90 days'
                        GROUP BY hour_bucket
                    ) as hourly_counts
                '''),
                {
                    'sender_id': sender_id,
                    'current_time': current_time
                }
            ).fetchone()
            
            user_avg = float(avg_result[0]) if avg_result and avg_result[0] else 2.0
            
            # Scale average to window size
            user_avg_for_window = user_avg * window_hours
            
            # Calculate ratio
            if user_avg_for_window <= 0:
                user_avg_for_window = 2.0  # Default minimum
            
            ratio = current_count / user_avg_for_window
            
            # Generate explanation
            explanation = ""
            if ratio >= 1.5:
                explanation = f"{current_count} transactions in {window_name} ({ratio:.1f}× user's normal rate of {user_avg_for_window:.0f})"
            
            # Score based on ratio (user-specific!)
            if ratio >= 5.0:  # 5× user's normal velocity
                return 1.0, explanation
            elif ratio >= 3.0:  # 3× user's normal
                return 0.8, explanation
            elif ratio >= 2.0:  # 2× user's normal
                return 0.5, explanation
            elif ratio >= 1.5:  # 1.5× user's normal
                return 0.3, explanation
            else:
                return 0.0, ""
        
        except Exception as e:
            logger.error(f"Adaptive window check error: {e}")
            return 0.0, ""


