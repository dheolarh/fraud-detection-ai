# Fraud AI - Hybrid Fraud Detection System

A fraud detection system combining **rule-based logic** and **machine learning** to detect fraudulent transactions in real-time. Built with FastAPI, PostgreSQL, and scikit-learn.

## System Overview

This system analyzes banking transactions through **10 specialized logic modules** and **ML models** to detect fraud patterns with detailed explanations for every flagged transaction.

### Architecture

```
┌─────────────────┐
│ Banking Backend │ ← Stores transactions & auth logs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fraud Backend  │ ← Analyzes transactions
│                 │
│  ┌───────────┐  │
│  │ 10 Logic  │  │ ← Rule-based detection
│  │  Modules  │  │    Organized into 5 risk buckets
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │  ML       │  │ ← Machine learning
│  │  Models   │  │    Isolation Forest + One-Class SVM
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │   Risk    │  │ ← Combines scores (weighted)
│  │Orchestrator│  │    Final score = (Rules × 0.6) + (ML × 0.4)
│  └───────────┘  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Frontend      │ ← Displays anomalies with explanations
│  (React/Next)   │
└─────────────────┘
```

## Risk Bucket System

The 10 logic modules are organized into **5 risk buckets**, each with a specific weight in the final risk calculation:

### 1. ACCOUNT_COMPROMISE (25% weight)
**Detects**: Unauthorized account access and takeover attempts

**Modules**:
- **LoginIntegrityLogic** - Analyzes authentication patterns
  - Failed login attempts (3+ failures → suspicious)
  - Device changes (new browsers/devices)
  - Impossible travel (e.g., Tokyo to London in 3 hours)
  - Unusual login times (e.g., 3 AM when user normally logs in at 9 AM)

- **BehavioralBiometricsLogic** - Session behavior analysis
  - Unusually fast transactions (<5 seconds → possible bot)
  - New/unknown device usage
  - Atypical transaction timing patterns

**Example**: User normally logs in from Tokyo at 9 AM. Suddenly logs in from London at 12 PM with 5 failed attempts → **High risk of account takeover**

---

### 2. AMOUNT_ANOMALY (25% weight)
**Detects**: Unusual transaction amounts that deviate from user's normal behavior

**Modules**:
- **VolumeAnalysisLogic** - Compares transaction to user's baseline
  - Checks both incoming and outgoing transactions
  - Calculates 30-day average per user
  - Flags transactions >2× baseline

- **HistoricalBaselineLogic** - Pattern deviation detection
  - Day-of-week spending patterns (e.g., user spends $50 on Mondays, suddenly $500)
  - Category usage anomalies (e.g., first time using "Gambling" category)
  - Monthly spending pattern breaks

- **VolumeThresholdLogic** - Hard limit enforcement
  - Single transaction limit (100× user's 30-day average)
  - Daily volume limit (500× user's normal daily spending)
  - Balance drain detection (>80% of account balance)

**Example**: Student account with $50 average transactions suddenly sends $5,000 (100× normal) → **Extreme amount anomaly**

---

### 3. AML_STRUCTURING (20% weight)
**Detects**: Money laundering and structuring (smurfing) patterns

**Modules**:
- **StructuringLogic** - Detects transactions designed to avoid reporting thresholds
  - Transactions just under $10,000 threshold (e.g., $9,500, $9,800)
  - Multiple transactions to different recipients in short time
  - Pattern of small, frequent transfers

- **TransactionSpikeLogic** - Automated attack detection
  - Redis-backed velocity tracking (10 transactions in 10 minutes)
  - Flash activity bursts
  - Bot behavior patterns

**Example**: 8 transactions of $9,500 each to different recipients in 24 hours → **Likely structuring to avoid AML reporting**

---

### 4. AUTOMATION_ABUSE (15% weight)
**Detects**: Automated attacks and rapid-fire transaction patterns

**Modules**:
- **VelocityLogic** - Transaction frequency analysis
  - Compares to user's 90-day historical average
  - Checks 1-hour, 24-hour, and 7-day windows
  - User-specific thresholds (not fixed)

**Example**: User normally does 3 transactions/day. Suddenly 15 transactions in 1 hour (5× normal rate) → **Possible automated attack or account compromise**

---

### 5. GEO_ANOMALY (15% weight)
**Detects**: Geographic fraud patterns and location-based risks

**Modules**:
- **CrossBorderLogic** - International transaction risk
  - High-risk countries (North Korea, Iran, Syria, etc.)
  - Medium-risk countries (Russia, China, Pakistan, etc.)
  - Suspicious country pairs (e.g., Nigeria → Russia)
  - Large international transfers

- **LocationDetectionLogic** - GPS-based fraud detection
  - Impossible travel (using geopy for accurate distance calculation)
  - Unusual locations for user
  - Rapid location changes (5+ locations in 24 hours)

**Example**: Transaction from Lagos at 10 AM, then London at 11 AM (1,200 km/h required) → **Impossible travel detected**

---

## Risk Scoring Formula

### Step 1: Calculate Bucket Scores
Each bucket gets a score from its modules (0.0 - 1.0):

```python
bucket_score = max(module1_score, module2_score, ...)

# Example:
ACCOUNT_COMPROMISE = max(LoginIntegrity: 0.8, BehavioralBiometrics: 0.5) = 0.8
AMOUNT_ANOMALY = max(VolumeAnalysis: 0.6, HistoricalBaseline: 0.4, VolumeThreshold: 0.9) = 0.9
AML_STRUCTURING = max(Structuring: 0.0, TransactionSpike: 0.0) = 0.0
AUTOMATION_ABUSE = max(Velocity: 0.7) = 0.7
GEO_ANOMALY = max(CrossBorder: 0.3, LocationDetection: 0.9) = 0.9
```

### Step 2: Calculate Rule-Based Score
Weighted average of bucket scores:

```python
rule_score = (ACCOUNT_COMPROMISE × 0.25) + 
             (AMOUNT_ANOMALY × 0.25) + 
             (AML_STRUCTURING × 0.20) + 
             (AUTOMATION_ABUSE × 0.15) + 
             (GEO_ANOMALY × 0.15)

# Example:
rule_score = (0.8 × 0.25) + (0.9 × 0.25) + (0.0 × 0.20) + (0.7 × 0.15) + (0.9 × 0.15)
           = 0.20 + 0.225 + 0.0 + 0.105 + 0.135
           = 0.665 (66.5%)
```

### Step 3: Get ML Score
Machine learning models analyze transaction:

```python
ml_score = (IsolationForest_score + OneClassSVM_score) / 2

# Example:
ml_score = (0.82 + 0.78) / 2 = 0.80 (80%)
```

### Step 4: Calculate Final Score
Hybrid combination (60% rules, 40% ML):

```python
final_score = (rule_score × 0.6) + (ml_score × 0.4)

# Example:
final_score = (0.665 × 0.6) + (0.80 × 0.4)
            = 0.399 + 0.32
            = 0.719 (71.9%)
```

### Step 5: Determine Verdict

```python
if final_score >= 0.7:
    verdict = "FLAGGED"      # High risk - reject transaction
elif final_score >= 0.4:
    verdict = "MONITORED"         # Medium risk - manual review
else:
    verdict = "APPROVED"     # Low risk - allow transaction
```

---

## Explanation System

Every flagged transaction includes a **detailed explanation** showing exactly why it was flagged. Explanations are generated by each logic module and combined by the RiskOrchestrator.

### Explanation Format

```
[Base Summary] | Details: [Module1: explanation] | [Module2: explanation] | [ML: explanation]
```

### Real Example 1: Account Takeover

**Transaction**: $5,000 transfer from John Steward's account

**Triggered Modules**:
- VelocityLogic: 15 transactions in 1 hour vs. normal 3/day
- VolumeAnalysisLogic: $5,000 vs. $1,000 baseline
- LoginIntegrityLogic: Impossible travel detected
- BehavioralBiometricsLogic: New device
- ML Models: 85% anomaly score

**Final Explanation**:
```
Transaction flagged due to rapid transaction velocity combined with 
geographic anomaly | Details: Velocity: 15 transactions in 1 hour 
(5.0× user's normal rate of 3) | Amount: Transaction amount $5,000.00 
is 5.0× user's baseline of $1,000.00 | Login: Impossible travel: 
Lagos to London in 3.0 hours (1,200 km/h required) | Behavior: 
Transaction from new/unknown device | ML: Highly unusual transaction 
pattern (85% confidence)
```

**Verdict**: FLAGGED (Risk Score: 87%)

---

### Real Example 2: Money Laundering (Structuring)

**Transaction**: $9,500 transfer (8th similar transaction today)

**Triggered Modules**:
- StructuringLogic: Amount just under $10,000 threshold
- TransactionSpikeLogic: 8 transactions in 24 hours
- VolumeThresholdLogic: Daily volume 20× normal

**Final Explanation**:
```
Transaction flagged due to potential structuring pattern | Details: 
Structuring: Transaction amount $9,500.00 is just under user's 
threshold of $10,000.00 (potential structuring) | Spike: 8 
transactions in last 24 hours (rapid burst detected) | Threshold: 
Daily volume would be 20× user's normal daily spending of $500.00
```

**Verdict**: MONITORED (Risk Score: 68%)

---

### Real Example 3: Unusual Amount + Balance Drain

**Transaction**: $5,000 from student account

**Triggered Modules**:
- VolumeAnalysisLogic: 100× user's $50 average
- VolumeThresholdLogic: Would drain 95% of $5,263 balance
- HistoricalBaselineLogic: 20× typical Monday spending

**Final Explanation**:
```
Transaction flagged due to extreme amount anomaly | Details: Amount: 
Transaction amount $5,000.00 is 100.0× user's baseline of $50.00 | 
Threshold: Transaction would drain 95% of account balance ($5,000.00 
of $5,263.00) | Pattern: Amount is 20.0× user's typical Monday 
spending
```

**Verdict**: MONITORED (Risk Score: 72%)

---

### Real Example 4: Geographic Risk

**Transaction**: $2,000 to high-risk country

**Triggered Modules**:
- CrossBorderLogic: Transaction to Iran (critical-risk country)
- LocationDetectionLogic: User never transacted from this location

**Final Explanation**:
```
Transaction flagged due to geographic risk | Details: CrossBorder: 
Transaction to Iran (critical-risk country) | Location: Transaction 
from Dubai (user has never transacted from this location)
```

**Verdict**: FLAGGED (Risk Score: 91%)

---

## Machine Learning Models

### 1. Isolation Forest (Transaction Anomaly Detection)
**Purpose**: Detects unusual transaction patterns

**Features Used**:
- Transaction amount
- Time of day
- Day of week
- Transaction frequency
- Amount deviation from user average
- Geographic distance from last transaction

**Training**: 2,461 transactions (90-day history) and 1,341 auth logs (90-day history) with continous retraining with 30-day interval with newer data

**Accuracy**: 95%

---

### 2. One-Class SVM (Login Anomaly Detection)
**Purpose**: Detects suspicious authentication patterns

**Features Used**:
- Failed login count
- Device changes
- Login time patterns
- Geographic location changes
- Session duration

**Training**: 1,341 auth logs (90-day history)

**Accuracy**: 92%

---

## Project Structure

```
fraud-ai/
├── backend/                    # Fraud detection backend
│   ├── intelligence/          # ML models & training
│   │   ├── train_models.py   # Model training script
│   │   ├── anomaly_detector.py
│   │   └── model_cache.py
│   ├── logic_modules/         # 10 fraud detection modules
│   │   ├── velocity_logic.py
│   │   ├── volume_analysis.py
│   │   ├── login_integrity.py
│   │   ├── transaction_spikes.py
│   │   ├── structuring_detection.py
│   │   ├── cross_border.py
│   │   ├── historical_baseline.py
│   │   ├── location_detection.py
│   │   ├── behavioral_biometrics.py
│   │   └── volume_threshold.py
│   ├── orchestrator/          # Risk scoring & explanations
│   │   ├── risk_orchestrator.py
│   │   └── explainability.py
│   ├── data_retriever/        # API routes
│   ├── storage/               # Database models
│   └── utils/                 # Utilities
│
├── banking_backend/           # Banking system (data source)
│   ├── routes/               # Transaction & auth APIs
│   └── database/             # Schema & sample data
│
├── frontend/                  # React/Next.js dashboard
│   ├── src/
│   │   ├── components/       # UI components
│   │   └── lib/             # API client
│   └── package.json
│
└── models/                    # Trained ML models
    ├── transaction_model.pkl
    ├── login_model.pkl
    └── pattern_scaler.pkl
```

## Key Features

### User-Specific Thresholds
Unlike traditional fraud detection systems with fixed thresholds, this system adapts to each user's behavior:

- **VelocityLogic**: Compares to user's 90-day average (not fixed 15 txns/hour)
- **VolumeAnalysisLogic**: Uses user's 30-day baseline (not fixed $10,000)
- **StructuringLogic**: Personalized thresholds based on 1-year history
- **HistoricalBaselineLogic**: Learns user's day-of-week and category patterns

**Example**: 
- Student with $50 average → $500 flagged (10× normal)
- Business with $5,000 average → $500 approved (0.1× normal)

### Geopy Integration
All geographic calculations use **geopy** for accuracy:
- Supports any location (not just preset cities)
- Geodesic distance calculation (more accurate than Haversine)
- Automatic geocoding from location strings
- Continent detection via country codes

### Comprehensive Explanations
Every flagged transaction includes:
- **Which modules triggered** (e.g., VelocityLogic, VolumeAnalysisLogic)
- **Specific metrics** (e.g., "5.0× user's normal rate")
- **Contextual details** (e.g., "15 transactions in 1 hour")
- **ML confidence** (e.g., "85% anomaly score")

## API Endpoints

### Fraud Detection
- `POST /api/fraud/analyze` - Analyze transaction in real-time
- `GET /api/fraud/alerts/{user_id}` - Get fraud alerts with explanations
- `GET /api/fraud/stats/{user_id}` - Get fraud detection statistics

### Banking (Data Source)
- `GET /api/transactions/{user_id}` - Get user transactions
- `GET /api/auth/history/{user_id}` - Get authentication logs
- `GET /api/users/{user_id}` - Get user details

## Version 2 Updates

This project now includes a second-version enhancement layer focused on smarter fraud decisions, better beneficiary intelligence, and richer monitoring.

### Backend Enhancements
- Added smart fraud analysis endpoint: `POST /api/fraud/analyze-smart`
- Added risk trend endpoint: `GET /api/fraud/trend/{user_id}`
- Added adaptive ML scoring with confidence-aware adjustments
- Added beneficiary trust scoring to slightly reduce risk for long-trusted recipients
- Added enriched analysis context support (`context`) in fraud analysis payloads

### Banking Backend Enhancements
- Added enriched transaction context builder used when calling smart fraud analysis
- Added beneficiary relationship metrics:
  - `beneficiary_history_count`
  - `beneficiary_first_seen`
  - `beneficiary_avg_amount`

### Frontend Enhancements
- Added Risk Trend dashboard card (7-day vs 30-day average risk)
- Added trend direction indicator (`up`, `down`, `stable`) with delta view
- Added client support for `GET /api/fraud/trend/{user_id}`

### Deployment and Configuration
- Added `deployment.md` for setup/deploy guidance
- Aligned database naming across runtime and setup docs:
  - Fraud DB: `fraudai_db`
  - Banking DB: `hooverbank`

For full details, see [version 2.md](version%202.md).

## License

This project is licensed under the MIT License.

## Author

- Dheolarh - [GitHub](https://github.com/Dheolarh)
