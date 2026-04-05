import sys
import os
import asyncio
from datetime import datetime
from loguru import logger

# Add project root to path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage.database import SessionLocal
from storage.models import Transaction, FraudDecision
from orchestrator.risk_orchestrator import RiskOrchestrator
from config.fraud_config import FRAUD_MODEL_VERSION, THRESHOLD_PROFILE

from sqlalchemy import desc

async def analyze_user_history(user_id: str, days: int = 30, limit: int = 50, skip_ml: bool = False):
    """
    Analyze transactions for a user within a specific time window.
    """
    from utils.currency_converter import CurrencyConverter
    # Force fallback rates for speed
    CurrencyConverter.use_live_rates = False
    
    logger.info(f"Starting optimized historical analysis for user: {user_id}")
    logger.info(f"Window: {days} days, Limit: {limit}, Skip ML: {skip_ml}")
    
    db = SessionLocal()
    orchestrator = RiskOrchestrator()
    
    try:
        # 1. Calculate cutoff date
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # 2. Fetch transactions for this user within the window, most recent first
        transactions = db.query(Transaction).filter(
            Transaction.sender_id == user_id,
            Transaction.timestamp >= cutoff
        ).order_by(desc(Transaction.timestamp)).limit(limit).all()
        
        logger.info(f"Found {len(transactions)} transactions in the target window.")
        
        # 3. Get existing decision IDs to avoid duplicates
        existing_decision_ids = {
            d.transaction_id for d in db.query(FraudDecision.transaction_id).all()
        }
        
        count = 0
        for tx in transactions:
            if tx.transaction_id in existing_decision_ids:
                continue
                
            # Convert model to dict for orchestrator
            tx_data = {
                "id": tx.transaction_id,
                "sender_id": tx.sender_id,
                "receiver_id": tx.receiver_id,
                "amount": float(tx.amount),
                "currency": tx.currency or "GBP",
                "category": tx.category,
                "location": tx.location,
                "narration": tx.narration,
                "timestamp": tx.timestamp.isoformat() if tx.timestamp else datetime.utcnow().isoformat(),
                "context": {}
            }
            
            # Analyze (with optional skip_ml)
            risk_score, triggered_logics, verdict, explanation = await orchestrator.analyze_transaction(
                tx_data, db, skip_ml=skip_ml
            )
            
            # Save decision
            decision = FraudDecision(
                transaction_id=tx.transaction_id,
                model_version=f"{FRAUD_MODEL_VERSION}-RULEONLY" if skip_ml else FRAUD_MODEL_VERSION,
                threshold_profile=THRESHOLD_PROFILE,
                final_risk_score=risk_score,
                verdict=verdict,
                triggered_buckets=[],
                triggered_logics=triggered_logics,
                explanation_text=explanation,
                bucket_scores="{}",
                timestamp=tx.timestamp or datetime.utcnow()
            )
            db.add(decision)
            count += 1
            
            if count % 10 == 0:
                db.commit()
                logger.info(f"Analyzed {count}/{len(transactions)} transactions...")
        
        db.commit()
        logger.success(f"Optimized analysis complete. Generated {count} decisions.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during historical analysis: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze historical transactions for a user")
    parser.add_argument("--user_id", type=str, default="HOV-2426-1226", help="User ID to analyze")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back")
    parser.add_argument("--limit", type=int, default=50, help="Max number of transactions to analyze")
    parser.add_argument("--skip-ml", action="store_true", help="Skip ML analysis for speed")
    args = parser.parse_args()
    
    asyncio.run(analyze_user_history(args.user_id, args.days, args.limit, args.skip_ml))
