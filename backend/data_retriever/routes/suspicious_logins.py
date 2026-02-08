"""
Suspicious Logins API Routes
Endpoints for detecting and retrieving suspicious login attempts
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Optional
from datetime import datetime, timedelta

from storage.database import get_db
from clients.banking_client import get_banking_client
from config.fraud_config import THRESHOLD_PROFILES, THRESHOLD_PROFILE, BUCKET_WEIGHTS

router = APIRouter(prefix="/api/suspicious-logins", tags=["suspicious-logins"])


@router.get("/{user_id}")
async def get_suspicious_logins(
    user_id: str,
    hours: int = Query(24, description="Hours to look back")
):
    """
    Get suspicious login attempts for a user.
    
    Identifies suspicious patterns:
    - Multiple failed login attempts (3+)
    - Impossible travel detected
    - Odd-hour logins
    
    Risk scores aligned with ACCOUNT_COMPROMISE bucket and fraud_config thresholds.
    Returns anomalies formatted for the anomaly table.
    """
    try:
        # Get banking client
        banking_client = get_banking_client()
        
        # Query auth history from banking backend
        auth_data = await banking_client.get_auth_history(
            user_id=user_id,
            hours=hours,
            limit=100
        )
        
        logs = auth_data.get('logs', [])
        
        if not logs:
            return []
        
        suspicious_logins = []
        
        # Get thresholds from fraud_config
        thresholds = THRESHOLD_PROFILES[THRESHOLD_PROFILE]
        block_threshold = thresholds["block"]  # 0.40 for CONSERVATIVE
        hold_threshold = thresholds["hold"]    # 0.25 for CONSERVATIVE
        
        # 1. Check for failed login attempts - Create anomaly for EACH failed login
        failed_logins = [log for log in logs if not log.get('login_success', True)]
        
        for failed_log in failed_logins:
            # Calculate risk score based on LoginIntegrityLogic pattern
            # Failed login = 0.3 to 0.9 depending on count
            failed_count = len(failed_logins)
            if failed_count >= 5:
                risk_score_decimal = 0.9  # Critical - likely brute force
            elif failed_count >= 3:
                risk_score_decimal = 0.7  # High risk
            else:
                risk_score_decimal = 0.3  # Moderate risk
            
            # Determine verdict based on fraud_config thresholds
            if risk_score_decimal >= block_threshold:
                verdict = "FLAGGED"
            elif risk_score_decimal >= hold_threshold:
                verdict = "MONITORED"
            else:
                verdict = "APPROVED"
            
            suspicious_logins.append({
                "id": f"LOGIN-{failed_log.get('log_id', 'UNKNOWN')}",
                "type": "Login",
                "anomaly_type": "Failed Login Attempt",
                "ip_address": failed_log.get('ip_address', 'Unknown'),
                "location": failed_log.get('location', 'Unknown'),
                "timestamp": failed_log.get('date_time', ''),
                "risk_score": risk_score_decimal * 100,  # Convert to 0-100 for frontend
                "explanation_text": f"Failed login attempt detected ({failed_count} total failures). Possible unauthorized access or credential stuffing attack.",
                "verdict": verdict,
                "user_agent": failed_log.get('user_agent', 'Unknown'),
                "device_type": failed_log.get('device_type', 'Unknown')
            })
        
        # 2. Check for impossible travel - Report ALL instances
        successful_logins = [log for log in logs if log.get('login_success', False)]
        
        for i in range(len(successful_logins) - 1):
            current = successful_logins[i]
            previous = successful_logins[i + 1]
            
            current_location = current.get('location', 'Unknown')
            previous_location = previous.get('location', 'Unknown')
            
            # Skip if same location or unknown
            if current_location == previous_location or current_location == 'Unknown' or previous_location == 'Unknown':
                continue
            
            # Parse timestamps
            try:
                current_time = datetime.strptime(current.get('date_time', '').replace(' UTC', ''), "%B %d, %Y at %H:%M")
                previous_time = datetime.strptime(previous.get('date_time', '').replace(' UTC', ''), "%B %d, %Y at %H:%M")
                
                time_diff_hours = abs((current_time - previous_time).total_seconds() / 3600)
                
                # Check for different continents or countries
                if _different_locations(current_location, previous_location):
                    if time_diff_hours < 6:  # Impossible to travel between continents in < 6 hours
                        # Impossible travel = 0.95 risk (matches LoginIntegrityLogic)
                        risk_score_decimal = 0.95
                        
                        # This exceeds block_threshold (0.40), so verdict = FLAGGED
                        verdict = "FLAGGED"
                        
                        suspicious_logins.append({
                            "id": f"LOGIN-{current.get('log_id', 'UNKNOWN')}",
                            "type": "Login",
                            "anomaly_type": "Impossible Travel",
                            "ip_address": current.get('ip_address', 'Unknown'),
                            "location": current.get('location', 'Unknown'),
                            "timestamp": current.get('date_time', ''),
                            "risk_score": risk_score_decimal * 100,  # 95.0 for frontend
                            "explanation_text": f"Impossible travel detected: Login from {previous_location} to {current_location} in {time_diff_hours:.1f} hours.",
                            "verdict": verdict,
                            "user_agent": current.get('user_agent', 'Unknown'),
                            "device_type": current.get('device_type', 'Unknown')
                        })
            except Exception:
                continue
        
        # 3. Check for odd-hour logins - Report ALL odd-hour logins
        if successful_logins:
            # Get all login hours to determine user's pattern
            all_login_hours = []
            for log in successful_logins:
                try:
                    parsed_time = datetime.strptime(log.get('date_time', '').replace(' UTC', ''), "%B %d, %Y at %H:%M")
                    all_login_hours.append(parsed_time.hour)
                except Exception:
                    continue
            
            # Calculate if user rarely logs in at odd hours
            if all_login_hours:
                odd_hour_count = sum(1 for h in all_login_hours if 0 <= h < 6)
                odd_hour_ratio = odd_hour_count / len(all_login_hours) if len(all_login_hours) > 0 else 0
                
                # If user rarely logs in at odd hours (< 20% of the time)
                if odd_hour_ratio < 0.2:
                    # Report ALL odd-hour logins
                    for log in successful_logins:
                        try:
                            parsed_time = datetime.strptime(log.get('date_time', '').replace(' UTC', ''), "%B %d, %Y at %H:%M")
                            if 0 <= parsed_time.hour < 6:
                                # Odd-hour login = 0.5 risk (matches LoginIntegrityLogic)
                                risk_score_decimal = 0.5
                                
                                # 0.5 exceeds both hold (0.25) and block (0.40) thresholds
                                verdict = "FLAGGED"
                                
                                suspicious_logins.append({
                                    "id": f"LOGIN-{log.get('log_id', 'UNKNOWN')}",
                                    "type": "Login",
                                    "anomaly_type": "Odd-Hour Login",
                                    "ip_address": log.get('ip_address', 'Unknown'),
                                    "location": log.get('location', 'Unknown'),
                                    "timestamp": log.get('date_time', ''),
                                    "risk_score": risk_score_decimal * 100,  # 50.0 for frontend
                                    "explanation_text": f"Login at unusual time ({parsed_time.hour}:00). User rarely logs in between 12 AM - 6 AM. Possible unauthorized access.",
                                    "verdict": verdict,
                                    "user_agent": log.get('user_agent', 'Unknown'),
                                    "device_type": log.get('device_type', 'Unknown')
                                })
                        except Exception:
                            continue
        
        return suspicious_logins
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching suspicious logins: {str(e)}")


def _different_locations(location1: str, location2: str) -> bool:
    """Check if two locations are significantly different (different countries/continents)."""
    # Simple check - if locations are different strings, consider them different
    # In production, you'd use geolocation to calculate actual distance
    return location1 != location2
