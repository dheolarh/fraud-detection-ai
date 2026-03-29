"""
Transaction Context Builder
Builds richer context payloads for smarter fraud ML analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def build_context_payload(
    transaction: Dict[str, Any],
    request_meta: Optional[Dict[str, Any]] = None,
    account_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create enriched fraud payload with optional behavioral/context features.

    Args:
        transaction: Core transaction fields
        request_meta: Optional client/session metadata (ip, user_agent, device_id)
        account_profile: Optional profile stats (avg_txn, account_age_days, etc.)
    """
    request_meta = request_meta or {}
    account_profile = account_profile or {}

    amount = _safe_float(transaction.get("amount"))
    avg_amount = _safe_float(account_profile.get("avg_transaction_amount"), default=0.0)

    if avg_amount > 0:
        amount_ratio = amount / avg_amount
    else:
        amount_ratio = 1.0

    payload = {
        "transaction_id": transaction.get("transaction_id"),
        "sender_id": transaction.get("sender_id"),
        "sender_name": transaction.get("sender_name"),
        "receiver_id": transaction.get("receiver_id"),
        "receiver_name": transaction.get("receiver_name"),
        "amount": amount,
        "currency": transaction.get("currency", "GBP"),
        "category": transaction.get("category"),
        "location": transaction.get("location"),
        "narration": transaction.get("narration"),
        "timestamp": transaction.get("timestamp") or datetime.utcnow().isoformat(),
        "context": {
            "ip_address": request_meta.get("ip_address"),
            "user_agent": request_meta.get("user_agent"),
            "device_id": request_meta.get("device_id"),
            "session_age_seconds": request_meta.get("session_age_seconds"),
            "is_new_device": request_meta.get("is_new_device"),
            "account_age_days": account_profile.get("account_age_days"),
            "avg_transaction_amount": avg_amount,
            "daily_txn_count_24h": account_profile.get("daily_txn_count_24h"),
            "amount_ratio_to_user_avg": round(amount_ratio, 4),
            "beneficiary_age_days": account_profile.get("beneficiary_age_days"),
            "beneficiary_history_count": account_profile.get("beneficiary_history_count"),
            "beneficiary_first_seen": account_profile.get("beneficiary_first_seen"),
            "beneficiary_avg_amount": account_profile.get("beneficiary_avg_amount"),
        },
    }

    return payload
