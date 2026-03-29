# Version 2 Release Notes

This document summarizes what was added and updated in the second-version rollout.

## 1. Smart Fraud Analysis

### New endpoint
- `POST /api/fraud/analyze-smart`

### What changed
- Introduced a smart ML analysis layer that combines:
  - baseline ML anomaly score
  - adaptive user-specific thresholding
  - confidence-aware adjustment from feature completeness and model confidence
- Added smart blending with baseline orchestrator score for a more stable final risk decision.

### Why it helps
- Reduces over-reliance on static thresholds
- Improves handling for users with changing behavior patterns
- Produces more explainable ML-driven outcomes

## 2. Beneficiary Trust Score

### What changed
- Added beneficiary trust scoring based on recipient relationship history:
  - number of historical interactions (`beneficiary_history_count`)
  - age of relationship (`beneficiary_age_days`, `beneficiary_first_seen`)
  - amount consistency (`beneficiary_avg_amount` vs current amount)
- Smart analyzer now applies a **small, bounded risk reduction** when beneficiary trust is high and transaction amount is not an extreme outlier.

### Why it helps
- Reduces false positives for frequent, legitimate beneficiaries
- Keeps conservative behavior for new or unusual recipient patterns

## 3. User Risk Trend API

### New endpoint
- `GET /api/fraud/trend/{user_id}`

### Response highlights
- `avg_risk_score_7d`
- `avg_risk_score_30d`
- `flagged_count_7d`
- `flagged_count_30d`
- `trend` (`up`, `down`, `stable`)

### Why it helps
- Enables analyst visibility into direction of user risk over time
- Supports proactive monitoring, not only point-in-time alerts

## 4. Banking Payload Enrichment

### What changed
- Added a context builder in banking backend to enrich fraud analysis payloads.
- Enriched payload now includes:
  - request/device signals (IP, user-agent, device ID)
  - account profile metrics (account age, rolling transaction behavior)
  - beneficiary relationship history metrics

### Why it helps
- Better feature quality for ML scoring
- More context-aware and explainable decisions

## 5. Frontend Dashboard Updates

### What changed
- Added a Risk Trend card to the dashboard that shows:
  - 7-day average risk
  - 30-day average risk
  - flagged counts
  - directional trend with delta indicator
- Added frontend API integration for risk trend endpoint.

### Why it helps
- Gives operations teams a compact, actionable risk trajectory view

## 6. Deployment/Config Updates

### What changed
- Added `deployment.md` with deployment and startup guidance.
- Corrected DB alignment and documented authoritative mapping:
  - Fraud service DB: `fraudai_db`
  - Banking service DB: `hooverbank`

### Why it helps
- Prevents schema/runtime mismatch issues
- Simplifies setup across environments

## 7. Notes

- Endpoint paths do not include version tags.
- Versioned implementation code is organized under version-specific folders for controlled rollout.
