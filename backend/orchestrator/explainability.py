"""
Explainability System
Generates human-readable explanations for fraud detection decisions.
"""

from typing import List, Dict, Optional


def generate_explanation(
    triggered_buckets: List[str],
    triggered_logics: List[str],
    bucket_scores: Dict[str, float],
    ml_explanation: Optional[str] = None,
    ml_triggered: bool = False
) -> str:
    """
    Generate human-readable explanation for flagged transaction.
    
    Args:
        triggered_buckets: List of risk buckets that exceeded threshold
        triggered_logics: List of specific logics that flagged
        bucket_scores: Scores for each bucket
        ml_explanation: Optional ML-generated explanation
        ml_triggered: Whether ML flagged the transaction
        
    Returns:
        str: Human-readable explanation
    """
    
    if not triggered_buckets and not ml_triggered:
        return "Transaction approved - no risk factors detected"
    
    explanations = []
    
    # Rule-based explanations
    if "ACCOUNT_COMPROMISE" in triggered_buckets:
        score = bucket_scores["ACCOUNT_COMPROMISE"]
        if score >= 0.7:
            explanations.append(
                "account compromise indicators (failed logins, device changes, or impossible travel)"
            )
        else:
            explanations.append("elevated account risk")
    
    if "AMOUNT_ANOMALY" in triggered_buckets:
        score = bucket_scores["AMOUNT_ANOMALY"]
        if score >= 0.7:
            explanations.append("abnormal transaction amount (significantly above user baseline)")
        else:
            explanations.append("elevated transaction volume")
   
    if "AML_STRUCTURING" in triggered_buckets:
        explanations.append(
            "structuring pattern detected (multiple small transactions)"
        )
    
    if "AUTOMATION_ABUSE" in triggered_buckets:
        explanations.append(
            "rapid transaction velocity (too many transactions in short time window)"
        )
    
    if "GEO_ANOMALY" in triggered_buckets:
        explanations.append(
            "geographic anomaly (cross-border transaction or unusual location)"
        )
    
    # Build rule-based explanation
    if explanations:
        rule_explanation = f"Transaction flagged due to {' combined with '.join(explanations)}."
    else:
        rule_explanation = ""
    
    # Add ML explanation if available
    if ml_triggered and ml_explanation:
        if rule_explanation:
            return f"{rule_explanation} | ML: {ml_explanation}"
        else:
            return f"ML: {ml_explanation}"
    
    # If no specific rule explanation or ML explanation, check if anything was triggered
    if triggered_buckets or triggered_logics:
        # Something was triggered but no specific explanation - provide generic message
        return "Multiple risk factors detected - transaction flagged for review"
    
    return rule_explanation if rule_explanation else "Transaction approved - no risk factors detected"


def get_triggered_logic_details(triggered_logics: List[str]) -> Dict[str, str]:
    """
    Get detailed descriptions for each triggered logic.
    
    Args:
        triggered_logics: List of logic class names that triggered
        
    Returns:
        Dict mapping logic names to human-readable descriptions
    """
    logic_descriptions = {
        "LoginIntegrityLogic": "Suspicious login activity detected",
        "VolumeAnalysisLogic": "Transaction volume exceeds normal patterns",
        "StructuringLogic": "Potential money laundering structuring",
        "TransactionSpikeLogic": "Unusual spike in transaction frequency",
        "VolumeThresholdLogic": "Transaction amount exceeds threshold",
        "CrossBorderLogic": "Cross-border transaction to high-risk country",
        "VelocityLogic": "Too many transactions in short time period",
        "BehavioralBiometricsLogic": "Unusual user behavior patterns",
        "HistoricalBaselineLogic": "Deviates from historical spending patterns",
        "LocationDetectionLogic": "Unusual location or impossible travel",
        "ML_AnomalyDetection": "Machine learning detected anomalous pattern"
    }
    
    return {
        logic: logic_descriptions.get(logic, "Unknown risk factor")
        for logic in triggered_logics
    }

