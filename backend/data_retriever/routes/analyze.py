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
from config.fraud_config import FRAUD_MODEL_VERSION, THRESHOLD_PROFILE, THRESHOLD_PROFILES

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
    context: Optional[Dict[str, Any]] = None


class TransactionAnalysisResponse(BaseModel):
    """Response model for transaction analysis"""
    transaction_id: int
    verdict: str  # APPROVED, MONITORED, FLAGGED
    risk_score: float  # 0.0 - 1.0
    explanation: str
    triggered_logics: list


def _score_to_verdict(score: float) -> str:
    """Map risk score to verdict using configured threshold profile."""
    thresholds = THRESHOLD_PROFILES[THRESHOLD_PROFILE]
    if score >= thresholds["block"]:
        return "FLAGGED"
    if score >= thresholds["hold"]:
        return "MONITORED"
    return "APPROVED"


def _estimate_feature_completeness(context: Dict[str, Any]) -> float:
    """Estimate feature completeness from smart context payload."""
    if not context:
        return 0.75

    tracked_fields = [
        "ip_address",
        "user_agent",
        "device_id",
        "session_age_seconds",
        "is_new_device",
        "account_age_days",
        "avg_transaction_amount",
        "daily_txn_count_24h",
        "amount_ratio_to_user_avg",
        "beneficiary_age_days",
    ]

    present = 0
    for field in tracked_fields:
        value = context.get(field)
        if value is not None and value != "":
            present += 1

    return round(present / len(tracked_fields), 4)


def _save_fraud_decision(
    transaction_id: int,
    risk_score: float,
    verdict: str,
    triggered_logics: list,
    explanation: str,
) -> None:
    """Save fraud decision for monitored/flagged transactions."""
    from loguru import logger
    from storage.database import SessionLocal
    from storage.models import FraudDecision

    if verdict not in ["MONITORED", "FLAGGED"]:
        logger.info(f"Transaction {transaction_id} approved - not saving to fraud_decisions")
        return

    save_db = SessionLocal()
    try:
        fraud_decision = FraudDecision(
            transaction_id=transaction_id,
            model_version=FRAUD_MODEL_VERSION,
            threshold_profile=THRESHOLD_PROFILE,
            final_risk_score=risk_score,
            verdict=verdict,
            triggered_buckets=[],
            triggered_logics=triggered_logics,
            explanation_text=explanation,
            bucket_scores="{}",
            timestamp=datetime.utcnow(),
        )
        save_db.add(fraud_decision)
        save_db.commit()
        logger.info(f"FraudDecision saved for transaction {transaction_id}: {verdict}")
    except Exception as save_error:
        save_db.rollback()
        logger.error(f"Failed to save FraudDecision for transaction {transaction_id}: {save_error}")
    finally:
        save_db.close()


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
            "timestamp": request.timestamp or datetime.utcnow().isoformat(),
            "context": request.context or {}
        }
        
        # Run fraud detection through RiskOrchestrator
        orchestrator = RiskOrchestrator()
        risk_score, triggered_logics, verdict, explanation = await orchestrator.analyze_transaction(
            transaction_data, 
            db
        )
        
        _save_fraud_decision(
            transaction_id=request.transaction_id,
            risk_score=risk_score,
            verdict=verdict,
            triggered_logics=triggered_logics,
            explanation=explanation,
        )
        
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


@router.post("/analyze-smart", response_model=TransactionAnalysisResponse)
async def analyze_transaction_smart(
    request: TransactionAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze transaction with baseline orchestration + smart adaptive ML layer.

    Endpoint intentionally avoids version tags in URL.
    """
    try:
        from loguru import logger
        from v2.smart_ml_analysis import SmartMLAnalyzer, get_recent_user_scores

        logger.info(f"Smart analysis started for transaction {request.transaction_id}")

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
            "timestamp": request.timestamp or datetime.utcnow().isoformat(),
            "context": request.context or {},
        }

        # Baseline orchestrator score (rules + existing ML blend)
        orchestrator = RiskOrchestrator()
        base_score, base_logics, _base_verdict, base_explanation = await orchestrator.analyze_transaction(
            transaction_data,
            db,
        )

        user_id = request.sender_id or request.receiver_id
        context = request.context or {}

        analyzer = SmartMLAnalyzer()
        recent_scores = get_recent_user_scores(db, user_id=user_id, limit=120)
        model_confidence = float(context.get("model_confidence", 1.0))
        feature_completeness = float(
            context.get("feature_completeness", _estimate_feature_completeness(context))
        )

        smart_result = analyzer.analyze_transaction(
            transaction=transaction_data,
            user_id=user_id,
            recent_scores=recent_scores,
            model_confidence=model_confidence,
            feature_completeness=feature_completeness,
        )

        # Blend keeps existing orchestration while upgrading ML adaptivity.
        risk_score = round(min(1.0, (base_score * 0.55) + (smart_result.adjusted_ml_score * 0.45)), 4)
        verdict = _score_to_verdict(risk_score)

        triggered_logics = list(base_logics)
        if smart_result.verdict in ["MONITORED", "FLAGGED"]:
            triggered_logics.append("SmartMLAnalysis")
        triggered_logics = list(dict.fromkeys(triggered_logics))

        smart_reason_text = "; ".join(smart_result.reasons)
        explanation = (
            f"{base_explanation} | Smart ML: {smart_reason_text} "
            f"(confidence={smart_result.confidence:.2f}, "
            f"threshold={smart_result.adaptive_threshold:.2f}, "
            f"adjusted_score={smart_result.adjusted_ml_score:.2f})"
        )

        _save_fraud_decision(
            transaction_id=request.transaction_id,
            risk_score=risk_score,
            verdict=verdict,
            triggered_logics=triggered_logics,
            explanation=explanation,
        )

        logger.info(
            f"Smart analysis complete for transaction {request.transaction_id}: "
            f"base={base_score:.3f}, smart={smart_result.adjusted_ml_score:.3f}, "
            f"final={risk_score:.3f}, verdict={verdict}"
        )

        return TransactionAnalysisResponse(
            transaction_id=request.transaction_id,
            verdict=verdict,
            risk_score=risk_score,
            explanation=explanation,
            triggered_logics=triggered_logics,
        )

    except Exception as e:
        from loguru import logger

        logger.error(f"Smart fraud analysis failed for transaction {request.transaction_id}: {str(e)}")
        db.rollback()
        return TransactionAnalysisResponse(
            transaction_id=request.transaction_id,
            verdict="APPROVED",
            risk_score=0.0,
            explanation=f"Smart fraud analysis failed: {str(e)}",
            triggered_logics=[],
        )
