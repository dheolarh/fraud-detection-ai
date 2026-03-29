# Smart ML Analysis Update

This folder contains the second-version implementation focused on making ML analysis smarter.

## What is new

- Adaptive thresholding per user (instead of one static ML cutoff)
- Confidence-aware scoring using model health and feature completeness
- Structured ML output with reasons, confidence, and metadata

Main module:

- smart_ml_analysis.py

## Quick usage

```python
from smart_ml_analysis import SmartMLAnalyzer, get_recent_user_scores

analyzer = SmartMLAnalyzer()
recent_scores = get_recent_user_scores(db_session, user_id)

result = analyzer.analyze_transaction(
    transaction=transaction_data,
    user_id=user_id,
    recent_scores=recent_scores,
    model_confidence=0.92,
    feature_completeness=0.88,
)

print(result.to_dict())
```

## Suggested integration point

Integrate this in the existing orchestration flow after baseline logic scores are computed and before final verdict mapping.

You can blend scores like this:

- final_score = (rule_score * 0.55) + (smart_ml.adjusted_ml_score * 0.45)

Then map final_score to APPROVED / MONITORED / FLAGGED using your threshold profile.

## Why this improves intelligence

- Users with naturally high-variance behavior no longer trigger static-threshold false positives as often.
- Low-quality data now increases uncertainty-aware caution instead of silently underestimating risk.
- Analysts get clearer reasons and confidence context for each ML-driven decision.
