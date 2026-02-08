"""
Base classes for Fraud AI components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseLogic(ABC):
    """    
    Each logic module must implement the analyze method and return
    a risk score between 0.0 (safe) and 1.0 (high risk).
    """
    
    def __init__(self, weight: float = 0.1):
        """
        Initialize logic module.
        
        Args:
            weight: Importance weight for final scoring (0.0 - 1.0)
        """
        self.weight = weight
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def analyze(self, transaction: Dict[str, Any], db_session) -> float:
        """
        Analyze transaction and return risk score.
        
        Args:
            transaction: Dict with sender_id, receiver_id, amount, location, etc.
            db_session: Database session for queries
        
        Returns:
            float: Risk score between 0.0 (safe) and 1.0 (high risk)
        """
        pass
    
    def get_weighted_score(self, raw_score: float) -> float:
        """
        Apply weight to raw score.
        
        Args:
            raw_score: Un weighted score from analyze()
        
        Returns:
            float: Weighted score
        """
        return raw_score * self.weight


class BaseService(ABC):
    """
    Abstract base class for service layer components.
    """
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the service operation."""
        pass


class BaseRepository(ABC):
    """
    Abstract base class for repository pattern implementation.
    Provides data access abstraction.
    """
    
    def __init__(self, db_session):
        """
        Initialize repository with database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    @abstractmethod
    def get_by_id(self, id: Any):
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def get_all(self):
        """Get all entities."""
        pass
    
    @abstractmethod
    def create(self, entity):
        """Create new entity."""
        pass
    
    @abstractmethod
    def update(self, entity):
        """Update existing entity."""
        pass
    
    @abstractmethod
    def delete(self, id: Any):
        """Delete entity by ID."""
        pass
