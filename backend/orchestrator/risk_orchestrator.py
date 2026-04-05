"""
Risk Orchestrator
Coordinates all fraud detection logics with bucketed aggregation.
"""

import asyncio
from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from datetime import datetime

from config.fraud_config import (
    RISK_BUCKETS, BUCKET_WEIGHTS, FRAUD_MODEL_VERSION,
    THRESHOLD_PROFILE, THRESHOLD_PROFILES, HARD_STOP_THRESHOLDS
)
from orchestrator.explainability import generate_explanation
from storage.models import FraudDecision

from logic_modules.login_integrity import LoginIntegrityLogic
from logic_modules.volume_analysis import VolumeAnalysisLogic
from logic_modules.structuring_detection import StructuringLogic
from logic_modules.transaction_spikes import TransactionSpikeLogic
from logic_modules.volume_threshold import VolumeThresholdLogic
from logic_modules.cross_border import CrossBorderLogic
from logic_modules.velocity_logic import VelocityLogic
from logic_modules.behavioral_biometrics import BehavioralBiometricsLogic
from logic_modules.historical_baseline import HistoricalBaselineLogic
from logic_modules.location_detection import LocationDetectionLogic


class RiskOrchestrator:
    """
    Fraud detection orchestrator.
    
    Features:
    - Bucketed aggregation (prevents rule stacking)
    - Hard-stop rules for critical threats
    - Explainability for every decision
    - Model versioning and governance tracking
    """
    
    def __init__(self):
        self.logics = [
            LoginIntegrityLogic(),
            VolumeAnalysisLogic(),
            StructuringLogic(),
            TransactionSpikeLogic(),
            VolumeThresholdLogic(),
            CrossBorderLogic(),
            VelocityLogic(),
            BehavioralBiometricsLogic(),
            HistoricalBaselineLogic(),
            LocationDetectionLogic()
        ]
    
    async def analyze_transaction(
        self, transaction: Dict[str, Any], db_session: Session, skip_ml: bool = False
    ) -> Tuple[float, List[str], str, str]:
        """
        Analyze transaction through all fraud detection logics + ML.
        
        Args:
            transaction: Transaction data dictionary
            db_session: Database session
            
        Returns:
            Tuple containing:
            - final_risk_score (float)
            - triggered_logics (list of str)
            - verdict (str: APPROVED/MONITORED/FLAGGED)
            - explanation (str)
        """
        from loguru import logger
        logger.info(f"Analyzing transaction {transaction.get('id')}")
        
        # Run rule-based detection
        tasks = [
            logic.analyze(transaction, db_session) 
            for logic in self.logics
        ]
        scores = await asyncio.gather(*tasks)
        
        logic_scores = {
            logic.__class__.__name__: score
            for logic, score in zip(self.logics, scores)
        }
        
        logger.info(f"Logic scores: {logic_scores}")
        
        # Calculate rule-based scores
        bucket_scores = self._calculate_bucket_scores(logic_scores)
        rule_based_score = self._calculate_final_score(bucket_scores)
        
        # Run ML-based detection
        ml_score = 0.0
        ml_explanation = ""
        ml_triggered = False
        
        if not skip_ml:
            try:
                from intelligence.anomaly_detector import MLAnomalyDetector
                
                user_id = transaction.get('sender_id') or transaction.get('receiver_id')
                if user_id:
                    detector = MLAnomalyDetector(user_id)
                    if detector.load_models():
                        ml_result = detector.detect_transaction_anomaly(transaction)
                        ml_score = ml_result['anomaly_score']
                        ml_triggered = ml_result['is_anomaly']
                        ml_explanation = ml_result['explanation']
                        logger.info(f"ML detection: score={ml_score}, triggered={ml_triggered}")
            except Exception as e:
                logger.warning(f"ML detection failed: {e}")
        
        # Combine scores: 60% rule-based, 40% ML
        if skip_ml:
            final_score = rule_based_score
        else:
            final_score = (rule_based_score * 0.6) + (ml_score * 0.4)
        
        # Check hard stops (using bucket scores)
        verdict, reason = self._check_hard_stops(bucket_scores, final_score)
        
        # Collect triggered logics
        triggered_buckets = [
            bucket for bucket, score in bucket_scores.items() if score > 0.5
        ]
        triggered_logics = [
            logic for logic, score in logic_scores.items() if score > 0.5
        ]
        
        # Add ML to triggered logics if it flagged
        if ml_triggered:
            triggered_logics.append("ML_AnomalyDetection")
        
        # Collect detailed explanations from logic modules
        module_explanations = []
        if transaction.get('_velocity_explanation'):
            module_explanations.append(f"Velocity: {transaction['_velocity_explanation']}")
        if transaction.get('_volume_explanation'):
            module_explanations.append(f"Amount: {transaction['_volume_explanation']}")
        if transaction.get('_login_explanation'):
            module_explanations.append(f"Login: {transaction['_login_explanation']}")
        if transaction.get('_spike_explanation'):
            module_explanations.append(f"Spike: {transaction['_spike_explanation']}")
        if transaction.get('_structuring_explanation'):
            module_explanations.append(f"Structuring: {transaction['_structuring_explanation']}")
        if transaction.get('_crossborder_explanation'):
            module_explanations.append(f"CrossBorder: {transaction['_crossborder_explanation']}")
        if transaction.get('_baseline_explanation'):
            module_explanations.append(f"Pattern: {transaction['_baseline_explanation']}")
        if transaction.get('_location_explanation'):
            module_explanations.append(f"Location: {transaction['_location_explanation']}")
        if transaction.get('_behavior_explanation'):
            module_explanations.append(f"Behavior: {transaction['_behavior_explanation']}")
        if transaction.get('_volume_threshold_explanation'):
            module_explanations.append(f"Threshold: {transaction['_volume_threshold_explanation']}")
        
        # Generate base explanation
        explanation = generate_explanation(
            triggered_buckets, 
            triggered_logics, 
            bucket_scores,
            ml_explanation=ml_explanation if ml_triggered else None,
            ml_triggered=ml_triggered
        )
        
        # Append detailed module explanations if available
        if module_explanations:
            detailed_exp = " | ".join(module_explanations)
            explanation = f"{explanation} | Details: {detailed_exp}"
        
        # Append detailed module explanations if available
        if module_explanations:
            detailed_exp = " | ".join(module_explanations)
            explanation = f"{explanation} | Details: {detailed_exp}"
        
        # NOTE: FraudDecision is now saved in the analyze endpoint with proper error handling
        # This prevents database transaction errors in logic modules from blocking the save
        # 
        # if transaction.get('id') and transaction.get('id') < 9000:
        #     fraud_decision = FraudDecision(...)
        #     db_session.add(fraud_decision)
        
        logger.info(f"Transaction {transaction.get('id')}: Rule={rule_based_score:.2f}, ML={ml_score:.2f}, Final={final_score:.2f}, Verdict={verdict}")
        return final_score, triggered_logics, verdict, explanation
    
    def _calculate_bucket_scores(self, logic_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate bucket scores using MAX aggregation.
        
        Args:
            logic_scores: Scores from individual logics
            
        Returns:
            Dictionary of bucket names to scores
        """
        bucket_scores = {}
        for bucket, logic_names in RISK_BUCKETS.items():
            bucket_scores[bucket] = max(
                logic_scores.get(logic, 0.0) for logic in logic_names
            )
        return bucket_scores
    
    def _calculate_final_score(self, bucket_scores: Dict[str, float]) -> float:
        """
        Calculate final risk score using weighted bucket scores.
        
        Args:
            bucket_scores: Scores for each bucket
            
        Returns:
            Final risk score (0.0-1.0)
        """
        score = sum(
            bucket_scores[bucket] * BUCKET_WEIGHTS[bucket]
            for bucket in BUCKET_WEIGHTS
        )
        return min(score, 1.0)
    
    def _check_hard_stops(
        self, bucket_scores: Dict[str, float], final_score: float
    ) -> Tuple[str, str]:
        """
        Check hard-stop rules that override normal scoring.
        
        Args:
            bucket_scores: Bucket risk scores
            final_score: Final calculated score
            
        Returns:
            Tuple of (verdict, reason)
        """
        # Hard-stop for impossible travel
        if bucket_scores["GEO_ANOMALY"] >= HARD_STOP_THRESHOLDS["GEO_ANOMALY"]:
            return "FLAGGED", "Impossible travel detected"
        
        # Hard-stop for account takeover
        if bucket_scores["ACCOUNT_COMPROMISE"] >= HARD_STOP_THRESHOLDS["ACCOUNT_COMPROMISE"]:
            return "FLAGGED", "Account takeover suspected"
        
        # NOTE: No hard-stop for AMOUNT_ANOMALY - use dynamic baseline comparison
        # Volume Analysis logic already detects anomalies relative to user behavior
        
        thresholds = THRESHOLD_PROFILES[THRESHOLD_PROFILE]
        
        if final_score >= thresholds["block"]:
            return "FLAGGED", "High composite fraud risk"
        elif final_score >= thresholds["hold"]:
            return "MONITORED", "Transaction requires review"
        else:
            return "APPROVED", "Transaction within normal behavior"
