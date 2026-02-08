"""
Base class for all fraud detection logic modules.
Provides common interface and utilities for risk analysis.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session


class BaseFraudLogic(ABC):
    """
    Abstract base class for fraud detection logic modules.
    All logic modules must inherit from this class and implement the analyze method.
    """
    
    def __init__(self):
        self.logic_name = self.__class__.__name__
        self.risk_bucket = self._get_risk_bucket()
    
    @abstractmethod
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze a transaction and return a risk score.
        
        Args:
            transaction: Dictionary containing transaction data
            db_session: Database session for queries
            
        Returns:
            float: Risk score between 0.0 (no risk) and 1.0 (maximum risk)
        """
        pass
    
    def _get_risk_bucket(self) -> str:
        """
        Determine which risk bucket this logic belongs to.
        Returns bucket name or None if not yet configured.
        """
        from config.fraud_config import RISK_BUCKETS
        
        for bucket, logics in RISK_BUCKETS.items():
            if self.logic_name in logics:
                return bucket
        
        return "UNKNOWN"
    
    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to 0.0-1.0 range.
        
        Args:
            value: The value to normalize
            min_val: Minimum possible value
            max_val: Maximum possible value
            
        Returns:
            float: Normalized score between 0.0 and 1.0
        """
        if max_val == min_val:
            return 0.0
        
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
