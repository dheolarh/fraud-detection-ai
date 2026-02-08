"""
Fraud Detection Configuration
Fraud detection parameters, risk buckets, and threshold profiles.
"""

FRAUD_MODEL_VERSION = "1.0.0"
THRESHOLD_PROFILE = "CONSERVATIVE"

RISK_BUCKETS = {
    "ACCOUNT_COMPROMISE": [
        "LoginIntegrityLogic",
        "BehavioralBiometricsLogic"
    ],
    "AMOUNT_ANOMALY": [
        "VolumeAnalysisLogic",
        "VolumeThresholdLogic"
    ],
    "AML_STRUCTURING": [
        "StructuringLogic"
    ],
    "AUTOMATION_ABUSE": [
        "TransactionSpikeLogic",
        "VelocityLogic"
    ],
    "GEO_ANOMALY": [
        "CrossBorderLogic",
        "LocationDetectionLogic"
    ]
}

# Stricter weights - prioritize amount and geo anomalies
BUCKET_WEIGHTS = {
    "ACCOUNT_COMPROMISE": 0.20,
    "AMOUNT_ANOMALY": 0.30,      # Increased from 0.20
    "AML_STRUCTURING": 0.15,
    "AUTOMATION_ABUSE": 0.10,
    "GEO_ANOMALY": 0.25          # Increased from 0.20
}

# Stricter thresholds - lower values mean more transactions flagged
THRESHOLD_PROFILES = {
    "CONSERVATIVE": {"block": 0.30, "hold": 0.18},  # Lowered from 0.40/0.25
    "MODERATE": {"block": 0.40, "hold": 0.25},      # Lowered from 0.50/0.30
    "AGGRESSIVE": {"block": 0.50, "hold": 0.35},    # Lowered from 0.65/0.40
    "CUSTOM": {"block": 0.35, "hold": 0.20}
}

HARD_STOP_THRESHOLDS = {
    "GEO_ANOMALY": 0.9,
    "ACCOUNT_COMPROMISE": 0.9
}

LOGIC_WEIGHTS = {
    "LoginIntegrityLogic": 0.15,
    "VolumeAnalysisLogic": 0.12,
    "StructuringLogic": 0.18,
    "TransactionSpikeLogic": 0.10,
    "VolumeThresholdLogic": 0.08,
    "CrossBorderLogic": 0.12,
    "VelocityLogic": 0.08,
    "BehavioralBiometricsLogic": 0.07,
    "HistoricalBaselineLogic": 0.06,
    "LocationDetectionLogic": 0.04
}
