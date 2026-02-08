"""
ML Anomaly Detector
Uses trained ML models to detect anomalous transactions and logins
"""

import numpy as np
from datetime import datetime
from loguru import logger
from intelligence.model_cache import get_model_cache

class MLAnomalyDetector:
    """Detect anomalies using trained ML models"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.model_cache = get_model_cache()
        self.models = None
        self.metadata = None
    
    def load_models(self):
        """Load models from cache"""
        self.models = self.model_cache.load_models(self.user_id)
        if self.models:
            self.metadata = self.models['metadata']
            return True
        return False
    
    def prepare_transaction_features(self, transaction):
        """
        Extract features from a transaction for ML prediction.
        
        Must match the features used during training.
        """
        if not self.models:
            return None
        
        # Parse timestamp
        if isinstance(transaction.get('timestamp'), str):
            timestamp = datetime.fromisoformat(transaction['timestamp'])
        else:
            timestamp = transaction.get('timestamp', datetime.utcnow())
        
        # Get encoding maps from metadata
        category_map = self.metadata.get('category_map', {})
        location_map = self.metadata.get('location_map', {})
        
        # Extract features (same order as training)
        features = [
            float(transaction.get('amount', 0)),
            timestamp.hour,
            timestamp.weekday(),
            category_map.get(transaction.get('category', ''), 0),
            location_map.get(transaction.get('location', ''), 0),
            1 if transaction.get('transaction_flow') == 'incoming' else 0
        ]
        
        return np.array([features])
    
    def prepare_login_features(self, auth_log):
        """
        Extract features from a login for ML prediction.
        
        Must match the features used during training.
        """
        if not self.models:
            return None
        
        # Parse timestamp
        if isinstance(auth_log.get('timestamp'), str):
            timestamp = datetime.fromisoformat(auth_log['timestamp'])
        else:
            timestamp = auth_log.get('timestamp', datetime.utcnow())
        
        # Get encoding maps from metadata
        user_agent_map = self.metadata.get('login_user_agent_map', {})
        location_map = self.metadata.get('login_location_map', {})
        
        # Extract features (same order as training)
        features = [
            timestamp.hour,
            timestamp.weekday(),
            user_agent_map.get(auth_log.get('user_agent', ''), -1),  # -1 for unknown
            location_map.get(auth_log.get('location', ''), 0)
        ]
        
        return np.array([features])
    
    def detect_transaction_anomaly(self, transaction):
        """
        Detect if a transaction is anomalous.
        
        Returns:
            dict: {
                'is_anomaly': bool,
                'anomaly_score': float (0-1, higher = more anomalous),
                'confidence': float (0-1),
                'explanation': str
            }
        """
        if not self.models:
            logger.warning(f"No models loaded for {self.user_id}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'explanation': 'ML models not available'
            }
        
        try:
            # Prepare features
            X = self.prepare_transaction_features(transaction)
            if X is None:
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.0,
                    'explanation': 'Could not extract features'
                }
            
            # Scale features
            scaler = self.models['transaction_scaler']
            X_scaled = scaler.transform(X)
            
            # Predict using Isolation Forest
            model = self.models['isolation_forest']
            prediction = model.predict(X_scaled)[0]  # -1 = anomaly, 1 = normal
            anomaly_score_raw = model.score_samples(X_scaled)[0]  # Lower = more anomalous
            
            # Convert to 0-1 scale (higher = more anomalous)
            # Isolation Forest scores are typically between -0.5 and 0.5
            anomaly_score = max(0, min(1, (-anomaly_score_raw + 0.5)))
            
            is_anomaly = prediction == -1
            confidence = abs(anomaly_score - 0.5) * 2  # 0-1 scale
            
            # Generate explanation
            if is_anomaly:
                reasons = []
                amount = transaction.get('amount', 0)
                category = transaction.get('category', 'Unknown')
                
                if anomaly_score > 0.7:
                    reasons.append(f"Highly unusual transaction pattern")
                if amount > 500:
                    reasons.append(f"Large amount (£{amount:.2f})")
                reasons.append(f"Category: {category}")
                
                explanation = "; ".join(reasons)
            else:
                explanation = "Transaction matches normal user behavior"
            
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': round(anomaly_score, 3) if is_anomaly else 0.0,
                'confidence': round(confidence, 3),
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"Error detecting transaction anomaly: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'explanation': f'ML detection error: {str(e)}'
            }
    
    def detect_login_anomaly(self, auth_log):
        """
        Detect if a login is anomalous.
        
        Returns:
            dict: {
                'is_anomaly': bool,
                'anomaly_score': float (0-1),
                'confidence': float (0-1),
                'explanation': str
            }
        """
        if not self.models or 'login_svm' not in self.models:
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'explanation': 'Login ML model not available'
            }
        
        try:
            # Prepare features
            X = self.prepare_login_features(auth_log)
            if X is None:
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.0,
                    'explanation': 'Could not extract login features'
                }
            
            # Check for unknown user agent
            user_agent_map = self.metadata.get('login_user_agent_map', {})
            user_agent = auth_log.get('user_agent', '')
            is_unknown_agent = user_agent not in user_agent_map
            
            # Scale features
            scaler = self.models['login_scaler']
            X_scaled = scaler.transform(X)
            
            # Predict using One-Class SVM
            model = self.models['login_svm']
            prediction = model.predict(X_scaled)[0]  # -1 = anomaly, 1 = normal
            decision_score = model.decision_function(X_scaled)[0]
            
            # Convert to 0-1 scale
            anomaly_score = max(0, min(1, (-decision_score + 1) / 2))
            
            # Unknown user agent is highly suspicious
            if is_unknown_agent:
                anomaly_score = max(anomaly_score, 0.8)
            
            is_anomaly = prediction == -1 or is_unknown_agent
            confidence = abs(anomaly_score - 0.5) * 2
            
            # Generate explanation
            if is_anomaly:
                reasons = []
                if is_unknown_agent:
                    reasons.append("Unknown device/user agent")
                if anomaly_score > 0.7:
                    reasons.append("Unusual login pattern")
                
                location = auth_log.get('location', 'Unknown')
                reasons.append(f"Location: {location}")
                
                explanation = "; ".join(reasons)
            else:
                explanation = "Login matches normal user behavior"
            
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': round(anomaly_score, 3),
                'confidence': round(confidence, 3),
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"Error detecting login anomaly: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'explanation': f'ML detection error: {str(e)}'
            }
