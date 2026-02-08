"""
Application constants.
Single source of truth for constant values used throughout the application.
"""

# Fraud Detection Thresholds
RISK_THRESHOLD_SAFE = 0.35  # Below this = Safe
RISK_THRESHOLD_CRITICAL = 0.70  # Above this = Blocked

# Transaction Categories
VALID_CATEGORIES = [
    'shopping',
    'bills',
    'airtime',
    'family',
    'other'
]

# Transaction Status
STATUS_SAFE = "safe"
STATUS_FLAGGED = "flagged"
STATUS_FLAGGED = "blocked"
STATUS_SUCCESS = "success"

# Account Status
ACCOUNT_ACTIVE = "active"
ACCOUNT_FROZEN = "frozen"

# Case Status
CASE_ONGOING = "ongoing"
CASE_RESOLVED = "resolved"
CASE_CLOSED = "closed"

# Logic Weights (for risk scoring)
LOGIC_WEIGHTS = {
    'LoginIntegrityLogic': 0.15,
    'VolumeAnalysisLogic': 0.12,
    'StructuringLogic': 0.18,
    'TransactionSpikeLogic': 0.10,
    'VolumeThresholdLogic': 0.08,
    'CrossBorderLogic': 0.14,
    'VelocityLogic': 0.09,
    'BehavioralBiometricsLogic': 0.07,
    'HistoricalBaselineLogic': 0.11,
    'LocationDetectionLogic': 0.16,
}

# ML Model
ML_WEIGHT = 0.15
ML_CONTAMINATION = 0.1  # Assumed fraud rate for Isolation Forest

# Time Windows (in hours)
WINDOW_24_HOURS = 24
WINDOW_7_DAYS = 168  # 7 * 24
WINDOW_30_DAYS = 720  # 30 * 24

# Velocity Thresholds
IMPOSSIBLE_TRAVEL_SPEED_KMH = 900  # km/h (faster than commercial aircraft)
SUSPICIOUS_TRAVEL_SPEED_KMH = 500  # km/h

# Volume Thresholds
VOLUME_SPIKE_RATIO = 4.0  # 400% of average
CARD_TESTING_COUNT = 10  # Number of transactions in short time

# Database Limits
MAX_RECENT_TRANSACTIONS = 20
MAX_TRANSACTION_HISTORY = 1000
