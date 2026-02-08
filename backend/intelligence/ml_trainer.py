"""
ML Trainer
Trains machine learning models for fraud detection

Models:
1. Isolation Forest - Transaction anomaly detection
2. One-Class SVM - Alternative anomaly detection  
3. Login Pattern Classifier - Unusual login detection
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

class MLTrainer:
    """Train ML models for fraud detection"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.models = {}
        self.scalers = {}
        self.model_dir = "backend/intelligence/models"
        
        # Create models directory if it doesn't exist
        os.makedirs(self.model_dir, exist_ok=True)
    
    def prepare_transaction_features(self, transactions):
        """
        Extract features from transactions for ML training.
        
        Features:
        - amount (normalized)
        - hour of day (0-23)
        - day of week (0-6)
        - category (encoded)
        - location (encoded)
        - transaction_flow (0=outgoing, 1=incoming)
        """
        print(f"Preparing features from {len(transactions)} transactions...")
        
        features = []
        
        # Create encoding maps
        categories = list(set(tx['category'] for tx in transactions))
        category_map = {cat: i for i, cat in enumerate(categories)}
        
        locations = list(set(tx['location'] for tx in transactions))
        location_map = {loc: i for i, loc in enumerate(locations)}
        
        for tx in transactions:
            timestamp = datetime.fromisoformat(tx['timestamp'])
            
            feature_vector = [
                float(tx['amount']),
                timestamp.hour,
                timestamp.weekday(),
                category_map.get(tx['category'], 0),
                location_map.get(tx['location'], 0),
                1 if tx['transaction_flow'] == 'incoming' else 0
            ]
            features.append(feature_vector)
        
        return np.array(features), category_map, location_map
    
    def train_transaction_anomaly_detector(self, transactions):
        """Train Isolation Forest for transaction anomaly detection"""
        print("\nTraining Isolation Forest...")
        
        # Prepare features
        X, category_map, location_map = self.prepare_transaction_features(transactions)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train Isolation Forest
        # contamination=0.05 means we expect ~5% of transactions to be anomalies
        model = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100
        )
        model.fit(X_scaled)
        
        # Save model and scaler
        self.models['isolation_forest'] = model
        self.scalers['transaction_scaler'] = scaler
        self.models['category_map'] = category_map
        self.models['location_map'] = location_map
        
        print(f"  ✅ Trained on {len(X)} transactions")
        print(f"  Categories: {len(category_map)}")
        print(f"  Locations: {len(location_map)}")
    
    def train_login_anomaly_detector(self, auth_logs):
        """Train One-Class SVM for login anomaly detection"""
        print("\nTraining One-Class SVM for login patterns...")
        
        successful_logins = [log for log in auth_logs if log.get('login_success', True)]
        
        if len(successful_logins) < 10:
            print("  ⚠️  Not enough login data, skipping")
            return
        
        # Prepare features
        features = []
        
        # Use user_agent instead of device_type for better granularity
        user_agents = list(set(log['user_agent'] for log in successful_logins))
        user_agent_map = {ua: i for i, ua in enumerate(user_agents)}
        
        locations = list(set(log['location'] for log in successful_logins))
        location_map = {loc: i for i, loc in enumerate(locations)}
        
        for log in successful_logins:
            timestamp = datetime.fromisoformat(log['timestamp'])
            
            feature_vector = [
                timestamp.hour,
                timestamp.weekday(),
                user_agent_map.get(log['user_agent'], 0),  # Changed from device_type
                location_map.get(log['location'], 0)
            ]
            features.append(feature_vector)
        
        X = np.array(features)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train One-Class SVM
        model = OneClassSVM(kernel='rbf', gamma='auto', nu=0.05)
        model.fit(X_scaled)
        
        # Save model and scaler
        self.models['login_svm'] = model
        self.scalers['login_scaler'] = scaler
        self.models['login_user_agent_map'] = user_agent_map  # Changed from device_map
        self.models['login_location_map'] = location_map
        
        print(f"Trained on {len(X)} logins")
        print(f"User agents: {len(user_agent_map)}")  # Changed from devices
        print(f"Locations: {len(location_map)}")
    
    def save_models(self):
        """Save all trained models"""
        print("\nSaving models...")
        
        # Save each model
        for model_name, model in self.models.items():
            if model_name.endswith('_map'):
                # Save maps as JSON
                continue
            
            filename = f"{self.model_dir}/user_{self.user_id}_{model_name}.joblib"
            joblib.dump(model, filename)
            print(f"  ✅ Saved {model_name}")
        
        # Save scalers
        for scaler_name, scaler in self.scalers.items():
            filename = f"{self.model_dir}/user_{self.user_id}_{scaler_name}.joblib"
            joblib.dump(scaler, filename)
            print(f"  ✅ Saved {scaler_name}")
        
        # Save metadata
        metadata = {
            "user_id": self.user_id,
            "trained_at": datetime.utcnow().isoformat(),
            "models": list(self.models.keys()),
            "category_map": self.models.get('category_map', {}),
            "location_map": self.models.get('location_map', {}),
            "login_user_agent_map": self.models.get('login_user_agent_map', {}),  # Changed
            "login_location_map": self.models.get('login_location_map', {})
        }
        
        import json
        metadata_file = f"{self.model_dir}/user_{self.user_id}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"  ✅ Saved metadata")


if __name__ == "__main__":
    print("ML Trainer - Test Mode")
    print("="*70)
    
    trainer = MLTrainer("HOV-2426-1226")
    print("\n✅ ML trainer ready")
    print("Use this to train models on user transaction and login data")
