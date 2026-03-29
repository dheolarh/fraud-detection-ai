"""
Fraud Detection API Routes
Endpoints for fraud alerts, stats, and detection results
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from storage.database import get_db
from storage.models import FraudDecision, Transaction
from sqlalchemy import desc, or_
from utils.currency import format_money

router = APIRouter(prefix="/api/fraud", tags=["fraud"])


@router.get("/alerts/{user_id}")
async def get_fraud_alerts(user_id: str, db: Session = Depends(get_db)):
    """
    Get fraud alerts for a specific user
    Returns transactions with fraud decisions (MONITORED/FLAGGED)
    """
    try:
        from clients.banking_client import get_banking_client
        
        # Get banking client
        banking_client = get_banking_client()
        
        # Get all transactions from banking backend
        result = await banking_client.get_transactions(user_id=user_id, limit=10000)
        all_transactions = result.get('transactions', [])
        
        # Get all fraud decisions from fraud DB
        try:
            fraud_decisions = db.query(FraudDecision).filter(
                FraudDecision.verdict.in_(['MONITORED', 'FLAGGED'])
            ).order_by(desc(FraudDecision.timestamp)).limit(50).all()
        except Exception as db_error:
            # If database query fails, return empty list
            print(f"Database query failed: {db_error}")
            return []
        
        # Create a map of transaction_id -> fraud decision
        fraud_map = {fd.transaction_id: fd for fd in fraud_decisions}
        
        # Filter transactions that have fraud decisions and belong to user
        alerts = []
        
        # Get bank location for currency (only need to call once)
        try:
            bank_location = await banking_client.get("/api/bank/location")
            currency_code = bank_location.get('currency', 'GBP')
        except:
            currency_code = 'GBP'
        
        for t in all_transactions:
            tx_id = t.get('transaction_id')
            if tx_id in fraud_map:
                fraud_decision = fraud_map[tx_id]
                
                # Use format_money to get proper currency symbol
                formatted_amt, _ = format_money(float(t.get('amount', 0)), t.get('location'))
                
                alerts.append({
                    "transaction_id": tx_id,
                    "amount": float(t.get('amount', 0)),
                    "formatted_amount": formatted_amt,
                    "currency_code": currency_code,
                    "timestamp": t.get('timestamp'),
                    "location": t.get('location'),
                    "verdict": fraud_decision.verdict,
                    "risk_score": float(fraud_decision.final_risk_score) if fraud_decision.final_risk_score else 0.5,
                    "final_risk_score": float(fraud_decision.final_risk_score) if fraud_decision.final_risk_score else 0.5,
                    "explanation_text": fraud_decision.explanation_text or "Transaction flagged for review",
                    "triggered_logics": fraud_decision.triggered_logics or [],
                    "category": t.get('category'),
                    "narration": t.get('narration')
                })
        
        return alerts
        
    except Exception as e:
        print(f"ERROR in get_fraud_alerts: {str(e)}")
        # Return empty array instead of failing
        return []


@router.get("/stats/{user_id}")
async def get_fraud_stats(user_id: str, db: Session = Depends(get_db)):
    """
    Get fraud detection statistics for a user
    """
    try:
        # Get user's transactions
        total_txns = db.query(Transaction).filter(
            Transaction.sender_id == user_id
        ).count()
        
        # Get flagged count
        flagged_count = db.query(Transaction).filter(
            Transaction.sender_id == user_id,
            Transaction.is_flagged == True
        ).count()
        
        return {
            "total_transactions": total_txns,
            "blocked_count": 0,  # Not tracking this yet
            "held_count": flagged_count,
            "approved_count": total_txns - flagged_count,
            "fraud_rate": flagged_count / total_txns if total_txns > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suspicion-level/{user_id}")
async def get_suspicion_level(user_id: str, db: Session = Depends(get_db)):
    """
    Get suspicion level for a user (0-5 scale).
    
    Calculation based on:
    - Number of fraud decisions (MONITORED/FLAGGED) for user's transactions in last 30 days
    - Number of suspicious logins in last 30 days
    - Average risk score of flagged transactions and logins
    - Uses fraud_config thresholds for risk assessment
    - Applies exponential time decay (10% per day) - older anomalies contribute less
    
    Returns:
        Suspicion level: 0 (no suspicion) to 5 (high suspicion)
    """
    try:
        from datetime import timedelta, datetime
        from sqlalchemy import func
        from clients.banking_client import get_banking_client
        import httpx
        import math
        
        # Get fraud decisions from last 30 days FOR THIS USER
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        now = datetime.utcnow()
        
        # Get user's transactions from banking backend
        banking_client = get_banking_client()
        result = await banking_client.get_transactions(
            user_id=user_id,
            start_date=thirty_days_ago,
            limit=1000
        )
        user_transactions = result.get('transactions', [])
        user_transaction_ids = {t.get('transaction_id') for t in user_transactions}
        
        # Filter fraud decisions to only user's transactions
        fraud_decisions = db.query(FraudDecision).filter(
            FraudDecision.verdict.in_(['MONITORED', 'FLAGGED']),
            FraudDecision.timestamp >= thirty_days_ago,
            FraudDecision.transaction_id.in_(user_transaction_ids)
        ).all() if user_transaction_ids else []
        
        # Get suspicious logins using the endpoint (uses fraud_config thresholds)
        async with httpx.AsyncClient() as client:
            login_response = await client.get(
                f"http://localhost:8000/api/suspicious-logins/{user_id}?hours={24*30}",
                timeout=10.0
            )
            suspicious_logins = login_response.json() if login_response.status_code == 200 else []
        
        # Calculate combined metrics
        transaction_flagged_count = len(fraud_decisions)
        login_flagged_count = len(suspicious_logins)
        total_flagged_count = transaction_flagged_count + login_flagged_count
        
        if total_flagged_count == 0:
            return {
                "suspicion_level": 0, 
                "description": "No suspicious activity",
                "flagged_count": 0,
                "average_risk_score": 0
            }
        
        # Calculate average risk score with TIME DECAY
        # Exponential decay: e^(-0.1 × days_old)
        # Recent anomalies have full weight, older ones contribute less
        
        weighted_risk_sum = 0.0
        total_weight = 0.0
        
        # Process transaction fraud decisions
        for fd in fraud_decisions:
            if fd.final_risk_score:
                base_risk = float(fd.final_risk_score) * 100  # Convert 0-1 to 0-100
                
                # Calculate time decay
                days_old = (now - fd.timestamp).days
                time_weight = math.exp(-0.1 * days_old)  # 10% decay per day
                
                # Apply time decay to risk score
                weighted_risk = base_risk * time_weight
                weighted_risk_sum += weighted_risk
                total_weight += time_weight
        
        # Process login anomalies
        for login in suspicious_logins:
            base_risk = float(login.get('risk_score', 0))  # Already 0-100
            
            # Parse timestamp
            timestamp_str = login.get('timestamp', '')
            try:
                # Format: "December 28, 2025 at 13:24 UTC"
                timestamp = datetime.strptime(
                    timestamp_str.replace(' UTC', ''), 
                    "%B %d, %Y at %H:%M"
                )
                
                # Calculate time decay
                days_old = (now - timestamp).days
                time_weight = math.exp(-0.1 * days_old)  # 10% decay per day
                
                # Apply time decay to risk score
                weighted_risk = base_risk * time_weight
                weighted_risk_sum += weighted_risk
                total_weight += time_weight
            except Exception:
                # If timestamp parsing fails, use full weight
                weighted_risk_sum += base_risk
                total_weight += 1.0
        
        # Calculate weighted average risk score
        avg_risk_score = weighted_risk_sum / total_weight if total_weight > 0 else 0
        
        # Calculate suspicion level (0-5) based on flagged count and risk score
        # Base score from flagged count
        if total_flagged_count >= 10:
            count_score = 3.0
        elif total_flagged_count >= 5:
            count_score = 2.0
        elif total_flagged_count >= 3:
            count_score = 1.5
        elif total_flagged_count >= 1:
            count_score = 1.0
        else:
            count_score = 0.0
        
        # Risk score contribution (0-2 points)
        # avg_risk_score is 0-100, so divide by 100 to get 0-1, then multiply by 2.5
        risk_score_contribution = min((avg_risk_score / 100) * 2.5, 2.0)
        
        # Final suspicion level (capped at 5)
        suspicion_level = min(round(count_score + risk_score_contribution), 5)
        
        # Description
        if suspicion_level == 0:
            description = "No suspicious activity"
        elif suspicion_level <= 2:
            description = "Low suspicion - monitor activity"
        elif suspicion_level <= 3:
            description = "Moderate suspicion - increased monitoring"
        else:
            description = "High suspicion - requires investigation"
        
        return {
            "suspicion_level": suspicion_level,
            "description": description,
            "flagged_count": total_flagged_count,
            "average_risk_score": round(avg_risk_score / 100, 2)  # Convert to 0-1 scale
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating suspicion level: {str(e)}")


@router.get("/trend/{user_id}")
async def get_user_risk_trend(user_id: str, db: Session = Depends(get_db)):
    """
    Get user risk trend for 7-day and 30-day windows.

    Returns:
    - average risk score for last 7 and 30 days
    - flagged counts for last 7 and 30 days
    """
    try:
        from clients.banking_client import get_banking_client

        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        banking_client = get_banking_client()
        result = await banking_client.get_transactions(
            user_id=user_id,
            start_date=thirty_days_ago,
            limit=10000,
        )

        transactions = result.get("transactions", [])
        user_transaction_ids = [
            t.get("transaction_id")
            for t in transactions
            if t.get("transaction_id") is not None
        ]

        if not user_transaction_ids:
            return {
                "user_id": user_id,
                "avg_risk_score_7d": 0.0,
                "avg_risk_score_30d": 0.0,
                "flagged_count_7d": 0,
                "flagged_count_30d": 0,
                "sample_size_7d": 0,
                "sample_size_30d": 0,
                "trend": "stable",
            }

        decisions = db.query(FraudDecision).filter(
            FraudDecision.transaction_id.in_(user_transaction_ids),
            FraudDecision.timestamp >= thirty_days_ago,
        ).all()

        def _window_stats(cutoff: datetime) -> dict:
            window = [d for d in decisions if d.timestamp and d.timestamp >= cutoff]
            scored = [float(d.final_risk_score) for d in window if d.final_risk_score is not None]
            flagged = [d for d in window if d.verdict in ["MONITORED", "FLAGGED"]]

            avg_risk = round(sum(scored) / len(scored), 4) if scored else 0.0
            return {
                "avg_risk": avg_risk,
                "flagged_count": len(flagged),
                "sample_size": len(window),
            }

        stats_7d = _window_stats(seven_days_ago)
        stats_30d = _window_stats(thirty_days_ago)

        if stats_7d["avg_risk"] > stats_30d["avg_risk"] + 0.03:
            trend = "up"
        elif stats_7d["avg_risk"] < stats_30d["avg_risk"] - 0.03:
            trend = "down"
        else:
            trend = "stable"

        return {
            "user_id": user_id,
            "avg_risk_score_7d": stats_7d["avg_risk"],
            "avg_risk_score_30d": stats_30d["avg_risk"],
            "flagged_count_7d": stats_7d["flagged_count"],
            "flagged_count_30d": stats_30d["flagged_count"],
            "sample_size_7d": stats_7d["sample_size"],
            "sample_size_30d": stats_30d["sample_size"],
            "trend": trend,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating risk trend: {str(e)}")

