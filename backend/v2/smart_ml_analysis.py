"""
Smart ML Analysis
Adaptive, confidence-aware ML scoring for fraud detection.

This module is intentionally isolated in the version-2 folder so it can be
adopted incrementally without breaking the existing pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from statistics import mean, median
from typing import Any, Dict, List, Optional, Sequence

from loguru import logger


@dataclass
class SmartMLResult:
    """Normalized output of smart ML analysis."""

    raw_ml_score: float
    adjusted_ml_score: float
    adaptive_threshold: float
    confidence: float
    verdict: str
    reasons: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptiveThresholdPolicy:
    """
    Robust threshold policy based on user-specific score history.

    Uses median + MAD-like dispersion to avoid being skewed by outliers.
    """

    def __init__(
        self,
        default_threshold: float = 0.62,
        min_history: int = 20,
        threshold_floor: float = 0.50,
        threshold_ceiling: float = 0.90,
    ) -> None:
        self.default_threshold = default_threshold
        self.min_history = min_history
        self.threshold_floor = threshold_floor
        self.threshold_ceiling = threshold_ceiling

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def compute(self, recent_scores: Sequence[float]) -> float:
        """Compute adaptive threshold from recent per-user ML scores."""
        cleaned = [float(s) for s in recent_scores if s is not None]

        if len(cleaned) < self.min_history:
            return self.default_threshold

        center = median(cleaned)
        deviations = [abs(s - center) for s in cleaned]
        mad = median(deviations) if deviations else 0.0

        # Dynamic threshold: center + spread buffer.
        dynamic = center + (2.2 * mad)

        # Keep threshold within practical risk-action boundaries.
        return self._clamp(dynamic, self.threshold_floor, self.threshold_ceiling)


class SmartMLAnalyzer:
    """
    Smarter ML scoring layer.

    Improvements over baseline ML scoring:
    - Per-user adaptive thresholding
    - Feature-completeness and model-confidence adjustment
    - Confidence-aware verdicting
    - Rich structured reasons for explainability
    """

    def __init__(self, threshold_policy: Optional[AdaptiveThresholdPolicy] = None) -> None:
        self.threshold_policy = threshold_policy or AdaptiveThresholdPolicy()

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, value))

    def _get_base_ml_score(self, user_id: str, transaction: Dict[str, Any]) -> float:
        """
        Use the existing detector as the baseline anomaly score.

        Returns score in range [0, 1]. If models are unavailable, returns 0.0.
        """
        try:
            from intelligence.anomaly_detector import MLAnomalyDetector

            detector = MLAnomalyDetector(user_id)
            if not detector.load_models():
                return 0.0

            result = detector.detect_transaction_anomaly(transaction)
            return self._clamp(float(result.get("anomaly_score", 0.0)))
        except Exception as exc:
            logger.warning(f"Smart ML baseline detector failed: {exc}")
            return 0.0

    def _adjust_score(
        self,
        raw_score: float,
        model_confidence: float,
        feature_completeness: float,
    ) -> float:
        """
        Adjust score reliability based on model and feature quality.

        If confidence/completeness drop, risk is slightly amplified to keep
        the system conservative under uncertainty.
        """
        mc = self._clamp(model_confidence)
        fc = self._clamp(feature_completeness)
        reliability = (0.6 * mc) + (0.4 * fc)

        # Reliability in [0, 1], uncertainty grows as reliability drops.
        uncertainty_boost = (1.0 - reliability) * 0.18
        adjusted = raw_score + uncertainty_boost
        return self._clamp(adjusted)

    def _compute_confidence(
        self,
        adjusted_score: float,
        threshold: float,
        model_confidence: float,
        feature_completeness: float,
    ) -> float:
        distance = abs(adjusted_score - threshold)
        reliability = self._clamp((0.6 * model_confidence) + (0.4 * feature_completeness))
        confidence = (distance * 1.8) + (reliability * 0.35)
        return self._clamp(confidence)

    def _apply_beneficiary_trust_adjustment(
        self,
        transaction: Dict[str, Any],
        adjusted_score: float,
    ) -> tuple[float, float, float, str]:
        """
        Apply a slight risk reduction for long-trusted beneficiaries.

        Returns:
            adjusted_score_after, trust_score, adjustment_applied, reason
        """
        context = transaction.get("context") or {}

        history_count = int(context.get("beneficiary_history_count") or 0)
        beneficiary_age_days = float(context.get("beneficiary_age_days") or 0.0)
        beneficiary_avg_amount = float(context.get("beneficiary_avg_amount") or 0.0)
        amount = float(transaction.get("amount") or 0.0)

        if history_count <= 0:
            return adjusted_score, 0.0, 0.0, "No beneficiary history"

        # Trust components (0-1 each)
        count_score = min(history_count / 25.0, 1.0)
        age_score = min(beneficiary_age_days / 180.0, 1.0)

        if beneficiary_avg_amount > 0:
            ratio = amount / beneficiary_avg_amount
            consistency_score = max(0.0, 1.0 - min(abs(ratio - 1.0) / 2.0, 1.0))
        else:
            consistency_score = 0.6

        trust_score = self._clamp((count_score * 0.45) + (age_score * 0.35) + (consistency_score * 0.20))

        # Only reduce slightly when trust is meaningful and amount is not an extreme outlier.
        if trust_score >= 0.65 and (beneficiary_avg_amount <= 0 or amount <= (beneficiary_avg_amount * 3.0)):
            adjustment = min(0.08, trust_score * 0.08)
            new_score = self._clamp(adjusted_score - adjustment)
            reason = (
                f"Beneficiary trusted (history={history_count}, age_days={int(beneficiary_age_days)}, "
                f"trust_score={trust_score:.2f}); reduced risk by {adjustment:.3f}"
            )
            return new_score, trust_score, adjustment, reason

        return adjusted_score, trust_score, 0.0, (
            f"Beneficiary trust observed (score={trust_score:.2f}) but no reduction applied"
        )

    def _verdict(self, adjusted_score: float, threshold: float, confidence: float) -> str:
        if adjusted_score >= threshold + 0.18 and confidence >= 0.55:
            return "FLAGGED"
        if adjusted_score >= threshold - 0.05:
            return "MONITORED"
        return "APPROVED"

    def analyze_transaction(
        self,
        transaction: Dict[str, Any],
        user_id: str,
        recent_scores: Optional[Sequence[float]] = None,
        model_confidence: float = 1.0,
        feature_completeness: float = 1.0,
    ) -> SmartMLResult:
        """
        Run smart ML analysis for one transaction.

        Args:
            transaction: Transaction payload
            user_id: User identifier for model loading and personalization
            recent_scores: Historical per-user ML scores (newest preferred)
            model_confidence: Runtime model health in [0, 1]
            feature_completeness: Feature availability ratio in [0, 1]
        """
        history = list(recent_scores or [])
        threshold = self.threshold_policy.compute(history)
        raw = self._get_base_ml_score(user_id, transaction)
        adjusted = self._adjust_score(raw, model_confidence, feature_completeness)
        adjusted, trust_score, trust_adjustment, trust_reason = self._apply_beneficiary_trust_adjustment(
            transaction=transaction,
            adjusted_score=adjusted,
        )
        confidence = self._compute_confidence(adjusted, threshold, model_confidence, feature_completeness)
        verdict = self._verdict(adjusted, threshold, confidence)

        reasons: List[str] = []
        if history:
            reasons.append(f"Adaptive threshold from {len(history)} historical scores")
        else:
            reasons.append("Default threshold applied (insufficient history)")

        if adjusted >= threshold:
            reasons.append(f"Adjusted ML score {adjusted:.3f} exceeds threshold {threshold:.3f}")
        else:
            reasons.append(f"Adjusted ML score {adjusted:.3f} below threshold {threshold:.3f}")

        if feature_completeness < 0.85:
            reasons.append("Feature completeness is low; uncertainty boost applied")
        if model_confidence < 0.85:
            reasons.append("Model confidence is reduced; conservative scoring applied")
        if trust_reason:
            reasons.append(trust_reason)

        metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "history_mean": round(mean(history), 4) if history else None,
            "history_median": round(median(history), 4) if history else None,
            "model_confidence": round(self._clamp(model_confidence), 4),
            "feature_completeness": round(self._clamp(feature_completeness), 4),
            "beneficiary_trust_score": round(trust_score, 4),
            "beneficiary_risk_reduction": round(trust_adjustment, 4),
        }

        return SmartMLResult(
            raw_ml_score=round(raw, 4),
            adjusted_ml_score=round(adjusted, 4),
            adaptive_threshold=round(threshold, 4),
            confidence=round(confidence, 4),
            verdict=verdict,
            reasons=reasons,
            metadata=metadata,
        )


def get_recent_user_scores(db_session: Any, user_id: str, limit: int = 120) -> List[float]:
    """
    Optional helper to fetch historical scores from fraud_decisions.

    This is deliberately defensive because deployments may differ in schema
    and data types. Returns an empty list on any failure.
    """
    try:
        from storage.models import FraudDecision

        rows = (
            db_session.query(FraudDecision.final_risk_score)
            .filter(FraudDecision.final_risk_score.isnot(None))
            .order_by(FraudDecision.timestamp.desc())
            .limit(limit)
            .all()
        )

        scores = [float(r[0]) for r in rows if r and r[0] is not None]
        return scores
    except Exception as exc:
        logger.warning(f"Could not fetch recent user scores for {user_id}: {exc}")
        return []
