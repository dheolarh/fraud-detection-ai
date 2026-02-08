"""
Train ML Models on User Data
Fetches data from banking backend and trains fraud detection models
"""

import sys
sys.path.append('/home/adejuwonlo/Desktop/Fraud AI/backend')

import asyncio
from clients.banking_client import get_banking_client
from intelligence.pattern_analyzer import PatternAnalyzer
from intelligence.ml_trainer import MLTrainer

async def train_models(user_id):
    """Train ML models for a user"""
    print("="*70)
    print(f"ML Training Pipeline for {user_id}")
    print("="*70)
    
    # Get banking client
    banking_client = get_banking_client()
    
    # Step 1: Fetch transactions
    print("\n1. Fetching transactions...")
    tx_result = await banking_client.get_transactions(
        user_id=user_id,
        limit=5000
    )
    transactions = tx_result.get('transactions', [])
    print(f"   Fetched {len(transactions)} transactions")
    
    # Step 2: Fetch auth logs from database directly
    print("\n2. Fetching auth logs from database...")
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        database="hooverbank",
        user="fraudai_user",
        password="password123"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT log_id, device_type, ip_address, location, user_agent, 
               login_success, timestamp
        FROM auth_logs
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT 5000
    """, (user_id,))
    
    auth_logs = []
    for row in cursor.fetchall():
        auth_logs.append({
            'log_id': row[0],
            'device_type': row[1],
            'ip_address': row[2],
            'location': row[3],
            'user_agent': row[4],
            'login_success': row[5],
            'timestamp': row[6].isoformat()
        })
    cursor.close()
    conn.close()
    print(f"   Fetched {len(auth_logs)} auth logs")
    
    # Step 3: Analyze patterns
    print("\n3. Analyzing patterns...")
    analyzer = PatternAnalyzer(user_id)
    analyzer.analyze_transactions(transactions)
    analyzer.analyze_logins(auth_logs)
    analyzer.save_patterns(f"backend/intelligence/models/user_{user_id}_patterns.json")
    
    # Step 4: Train ML models
    print("\n4. Training ML models...")
    trainer = MLTrainer(user_id)
    trainer.train_transaction_anomaly_detector(transactions)
    trainer.train_login_anomaly_detector(auth_logs)
    trainer.save_models()
    
    print("\n" + "="*70)
    print("✅ ML Training Complete!")
    print("="*70)
    print(f"\nModels saved to: backend/intelligence/models/")
    print(f"  - Isolation Forest (transaction anomalies)")
    print(f"  - One-Class SVM (login anomalies)")
    print(f"  - User patterns (JSON)")
    
    return True

def train_all_models():
    """
    Train all ML models (wrapper for scheduler).
    Returns True if successful, False otherwise.
    """
    try:
        user_id = "HOV-2426-1226"  # Default user for training
        asyncio.run(train_models(user_id))
        return True
    except Exception as e:
        print(f"Error training models: {e}")
        return False

if __name__ == "__main__":
    train_all_models()
