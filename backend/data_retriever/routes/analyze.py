"""
Fraud Analysis API Routes
Endpoint to trigger fraud detection analysis on transactions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from storage.database import get_db
from orchestrator.risk_orchestrator import RiskOrchestrator

router = APIRouter(prefix="/api/fraud", tags=["fraud-analysis"])


class TransactionAnalysisRequest(BaseModel):
    """Request model for transaction analysis"""
    transaction_id: int
    sender_id: str
    sender_name: Optional[str] = None
    receiver_id: str
    receiver_name: Optional[str] = None
    amount: float
    currency: str
    category: Optional[str] = None
    location: Optional[str] = None
    narration: Optional[str] = None
    timestamp: Optional[str] = None


class TransactionAnalysisResponse(BaseModel):
    """Response model for transaction analysis"""
    transaction_id: int
    verdict: str  # APPROVED, MONITORED, FLAGGED
    risk_score: float  # 0.0 - 1.0
    explanation: str
    triggered_logics: list


@router.post("/analyze", response_model=TransactionAnalysisResponse)
async def analyze_transaction(
    request: TransactionAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a transaction for fraud using RiskOrchestrator.
    
    This endpoint is called by the banking backend after a transaction is created.
    It runs the transaction through all 10 fraud detection logic modules and
    saves the fraud decision to the database.
    
    Args:
        request: Transaction data to analyze
        db: Database session
        
    Returns:
        Analysis result with verdict, risk score, and explanation
    """
    try:
        from loguru import logger
        
        logger.info(f"Analyzing transaction {request.transaction_id}: ${request.amount} {request.currency}")
        
        # Convert request to transaction dictionary format expected by RiskOrchestrator
        transaction_data = {
            "id": request.transaction_id,
            "sender_id": request.sender_id,
            "sender_name": request.sender_name,
            "receiver_id": request.receiver_id,
            "receiver_name": request.receiver_name,
            "amount": request.amount,
            "currency": request.currency,
            "category": request.category,
            "location": request.location,
            "narration": request.narration,
            "timestamp": request.timestamp or datetime.utcnow().isoformat()
        }
        
        # Run fraud detection through RiskOrchestrator
        orchestrator = RiskOrchestrator()
        risk_score, triggered_logics, verdict, explanation = await orchestrator.analyze_transaction(
            transaction_data, 
            db
        )
        
        # Save FraudDecision ONLY for flagged transactions (MONITORED/FLAGGED)
        # APPROVED transactions should NOT be saved to fraud_decisions
        if verdict in ['MONITORED', 'FLAGGED']:
            try:
                from storage.database import SessionLocal
                from storage.models import FraudDecision
                from config.fraud_config import FRAUD_MODEL_VERSION, THRESHOLD_PROFILE
                
                # Create a fresh database session
                save_db = SessionLocal()
                try:
                    # Save FraudDecision for flagged transactions only
                    fraud_decision = FraudDecision(
                        transaction_id=request.transaction_id,
                        model_version=FRAUD_MODEL_VERSION,
                        threshold_profile=THRESHOLD_PROFILE,
                        final_risk_score=risk_score,
                        verdict=verdict,
                        triggered_buckets=[],  # Will be populated by orchestrator if needed
                        triggered_logics=triggered_logics,
                        explanation_text=explanation,
                        bucket_scores="{}",  # Will be populated by orchestrator if needed
                        timestamp=datetime.utcnow()
                    )
                    save_db.add(fraud_decision)
                    save_db.commit()
                    logger.info(f"FraudDecision saved for transaction {request.transaction_id}: {verdict}")
                except Exception as save_error:
                    save_db.rollback()
                    logger.error(f"Failed to save FraudDecision: {save_error}")
                finally:
                    save_db.close()
            except Exception as e:
                logger.error(f"Error creating save session: {e}")
        else:
            logger.info(f"Transaction {request.transaction_id} approved - not saving to fraud_decisions")
        
        logger.info(
            f"Transaction {request.transaction_id} analysis complete: "
            f"Verdict={verdict}, Risk={risk_score:.2f}, Logics={triggered_logics}"
        )
        
        return TransactionAnalysisResponse(
            transaction_id=request.transaction_id,
            verdict=verdict,
            risk_score=risk_score,
            explanation=explanation,
            triggered_logics=triggered_logics
        )
        
    except Exception as e:
        # Log error but don't fail - return APPROVED to allow transaction to proceed
        from loguru import logger
        logger.error(f"Fraud analysis failed for transaction {request.transaction_id}: {str(e)}")
        
        # Rollback any partial database changes
        db.rollback()
        
        # Return APPROVED verdict so transaction isn't blocked due to analysis failure
        return TransactionAnalysisResponse(
            transaction_id=request.transaction_id,
            verdict="APPROVED",
            risk_score=0.0,
            explanation=f"Fraud analysis failed: {str(e)}",
            triggered_logics=[]
        )
