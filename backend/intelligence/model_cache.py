"""
Model Cache System
Loads and caches trained ML models for fraud detection
"""

import os
import json
from datetime import datetime, timedelta
import joblib
from loguru import logger

class ModelCache:
    """Cache and load trained ML models"""
    
    def __init__(self, model_dir=None):
        if model_dir is None:
            # Use absolute path relative to this file's location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_dir = os.path.join(current_dir, "models")
        self.model_dir = model_dir
        self.cache = {}
        self.metadata = {}
    
    def check_model_exists(self, user_id):
        """Check if models exist for user"""
        metadata_file = f"{self.model_dir}/user_{user_id}_metadata.json"
        return os.path.exists(metadata_file)
    
    def is_model_valid(self, user_id, max_age_days=30):
        """Check if model is still valid (not too old)"""
        if not self.check_model_exists(user_id):
            return False
        
        metadata_file = f"{self.model_dir}/user_{user_id}_metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        trained_at = datetime.fromisoformat(metadata['trained_at'])
        age = (datetime.utcnow() - trained_at).days
        
        return age <= max_age_days
    
    def load_models(self, user_id):
        """Load all models for a user"""
        logger.info(f"Loading ML models for user {user_id}")
        
        # Check if already cached
        if user_id in self.cache:
            logger.info(f"Using cached models for {user_id}")
            return self.cache[user_id]
        
        # Check if models exist
        if not self.check_model_exists(user_id):
            logger.warning(f"No models found for {user_id}")
            return None
        
        # Load metadata
        metadata_file = f"{self.model_dir}/user_{user_id}_metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Load models
        models = {
            'metadata': metadata,
            'isolation_forest': joblib.load(f"{self.model_dir}/user_{user_id}_isolation_forest.joblib"),
            'login_svm': joblib.load(f"{self.model_dir}/user_{user_id}_login_svm.joblib"),
            'transaction_scaler': joblib.load(f"{self.model_dir}/user_{user_id}_transaction_scaler.joblib"),
            'login_scaler': joblib.load(f"{self.model_dir}/user_{user_id}_login_scaler.joblib")
        }
        
        # Cache models
        self.cache[user_id] = models
        self.metadata[user_id] = metadata
        
        logger.info(f"Loaded models trained at {metadata['trained_at']}")
        return models
    
    def get_model_info(self, user_id):
        """Get model metadata"""
        if user_id in self.metadata:
            return self.metadata[user_id]
        
        if not self.check_model_exists(user_id):
            return None
        
        metadata_file = f"{self.model_dir}/user_{user_id}_metadata.json"
        with open(metadata_file, 'r') as f:
            return json.load(f)


# Global cache instance
_model_cache = ModelCache()

def get_model_cache():
    """Get global model cache instance"""
    return _model_cache
