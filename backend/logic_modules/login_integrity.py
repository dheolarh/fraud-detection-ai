"""
Logic 1: Login Integrity Checker
Detects account compromise indicators through authentication patterns.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from logic_modules.base_logic import BaseFraudLogic
from clients.banking_client import get_banking_client


class LoginIntegrityLogic(BaseFraudLogic):
    """
    Analyzes authentication logs to detect suspicious login patterns.
    
    Risk Indicators:
    - Multiple failed login attempts
    - Device ID changes
    - Failed attempts followed by immediate success
    - Impossible travel (login from distant locations too quickly)
    - Unusual login times (odd hours)
    
    NOTE: This logic queries the Banking Backend API for auth history.
    It does NOT access the database directly.
    """
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze login integrity for account compromise indicators.
        
        Args:
            transaction: Transaction data including sender_id
            db_session: Database session (not used - kept for interface compatibility)
            
        Returns:
            float: Risk score (0.0 = clean, 1.0 = high risk)
        """
        try:
            sender_id = transaction.get('sender_id')
            if not sender_id:
                return 0.0
            
            # Get banking client
            banking_client = get_banking_client()
            
            # Query auth history from banking backend (last 24 hours)
            auth_data = await banking_client.get_auth_history(
                user_id=sender_id,
                hours=24,
                limit=100
            )
            
            # Collect explanations
            explanations = []
            
            # Analyze failed attempts
            failed_attempts_score = self._analyze_failed_attempts(auth_data)
            if failed_attempts_score > 0 and hasattr(self, '_last_failed_explanation'):
                explanations.append(self._last_failed_explanation)
            
            # Analyze device changes (last 7 days)
            auth_data_7days = await banking_client.get_auth_history(
                user_id=sender_id,
                hours=168,  # 7 days
                limit=100
            )
            device_change_score = self._analyze_device_changes(auth_data_7days)
            if device_change_score > 0 and hasattr(self, '_last_device_explanation'):
                explanations.append(self._last_device_explanation)
            
            # NEW: Analyze impossible travel (last 48 hours)
            auth_data_48h = await banking_client.get_auth_history(
                user_id=sender_id,
                hours=48,
                limit=100
            )
            travel_score = self._analyze_impossible_travel(auth_data_48h)
            if travel_score > 0 and hasattr(self, '_last_travel_explanation'):
                explanations.append(self._last_travel_explanation)
            
            # NEW: Analyze unusual login times (last 24 hours)
            time_score = self._analyze_login_times(auth_data)
            if time_score > 0 and hasattr(self, '_last_time_explanation'):
                explanations.append(self._last_time_explanation)
            
            # Return maximum score (worst case)
            final_score = max(
                failed_attempts_score, 
                device_change_score,
                travel_score,
                time_score
            )
            
            # Store explanation
            if explanations and final_score > 0:
                transaction['_login_explanation'] = "; ".join(explanations)
            
            return min(final_score, 1.0)
            
        except Exception as e:
            # Log error but don't fail the transaction
            return 0.0

    
    def _analyze_failed_attempts(self, auth_data: Dict[str, Any]) -> float:
        """
        Analyze failed login attempts from auth history.
        
        Args:
            auth_data: Response from banking backend's /api/auth/history
            
        Returns:
            float: Risk score based on failed attempts
        """
        try:
            logs = auth_data.get('logs', [])
            
            # Count failed attempts
            failed_count = sum(1 for log in logs if not log.get('login_success', True))
            
            # Generate explanation
            if failed_count >= 1:
                self._last_failed_explanation = f"{failed_count} failed login attempt{'s' if failed_count > 1 else ''} in last 24 hours"
            
            if failed_count >= 5:
                return 0.9  # Critical - likely brute force attack
            elif failed_count >= 3:
                return 0.7  # High risk - multiple failed attempts
            elif failed_count >= 1:
                return 0.3  # Moderate risk - one failed attempt
            else:
                return 0.0  # Clean - no failed attempts
                
        except Exception as e:
            return 0.0
    
    def _analyze_device_changes(self, auth_data: Dict[str, Any]) -> float:
        """
        Analyze device type changes from auth history.
        
        Args:
            auth_data: Response from banking backend's /api/auth/history
            
        Returns:
            float: Risk score based on device changes
        """
        try:
            logs = auth_data.get('logs', [])
            
            # Get unique user agents from successful logins only (more accurate than device_type)
            successful_logins = [log for log in logs if log.get('login_success', False)]
            unique_user_agents = set(
                log.get('user_agent') 
                for log in successful_logins 
                if log.get('user_agent') and log.get('user_agent') != 'Unknown'
            )
            
            device_count = len(unique_user_agents)
            
            # Generate explanation
            if device_count >= 2:
                self._last_device_explanation = f"{device_count} different devices used in last 7 days"
            
            if device_count >= 4:
                return 0.8  # Suspicious - too many different browsers/devices
            elif device_count == 3:
                return 0.5  # Moderate risk
            elif device_count == 2:
                return 0.2  # Low risk - maybe phone + laptop
            else:
                return 0.0  # Normal - single device
                
        except Exception as e:
            return 0.0

    def _analyze_impossible_travel(self, auth_data: Dict[str, Any]) -> float:
        """
        Detect impossible travel - logins from distant locations too quickly.
        
        Args:
            auth_data: Response from banking backend's /api/auth/history
            
        Returns:
            float: Risk score based on impossible travel
        """
        try:
            logs = auth_data.get('logs', [])
            
            # Only check successful logins
            successful_logins = [log for log in logs if log.get('login_success', False)]
            
            if len(successful_logins) < 2:
                return 0.0
            
            # Check consecutive logins for impossible travel
            for i in range(len(successful_logins) - 1):
                current = successful_logins[i]
                previous = successful_logins[i + 1]  # Logs are in reverse chronological order
                
                current_location = current.get('location', 'Unknown')
                previous_location = previous.get('location', 'Unknown')
                
                # Skip if locations are unknown or same
                if current_location == 'Unknown' or previous_location == 'Unknown':
                    continue
                if current_location == previous_location:
                    continue
                
                # Parse timestamps (format: "December 27, 2025 at 15:25 UTC")
                current_time = self._parse_datetime(current.get('date_time', ''))
                previous_time = self._parse_datetime(previous.get('date_time', ''))
                
                if not current_time or not previous_time:
                    continue
                
                # Calculate time difference in hours
                time_diff = abs((current_time - previous_time).total_seconds() / 3600)
                
                # Calculate actual distance between locations
                distance_km = self._calculate_distance(current_location, previous_location)
                
                if distance_km > 0:
                    # Calculate required speed (km/h)
                    # Assume max realistic travel speed: 900 km/h (commercial flight)
                    required_speed = distance_km / time_diff if time_diff > 0 else float('inf')
                    
                    # Generate explanation for impossible travel
                    if required_speed > 300:
                        self._last_travel_explanation = f"Impossible travel: {previous_location} to {current_location} in {time_diff:.1f} hours ({required_speed:.0f} km/h required)"
                    
                    if required_speed > 900:
                        # Impossible - would need to travel faster than a plane!
                        return 0.95
                    elif required_speed > 600:
                        # Very suspicious - would need immediate flight
                        return 0.8
                    elif required_speed > 300:
                        # Suspicious - very fast travel
                        return 0.6
                
                # Fallback: Check if locations are on different continents
                elif self._different_continents(current_location, previous_location):
                    # Impossible to travel between continents in < 6 hours
                    if time_diff < 6:
                        self._last_travel_explanation = f"Impossible travel: {previous_location} to {current_location} in {time_diff:.1f} hours (different continents)"
                        return 0.95  # Critical - impossible travel detected!
                    elif time_diff < 12:
                        return 0.7  # High risk - very fast travel
            
            return 0.0
            
        except Exception as e:
            return 0.0

    def _calculate_distance(self, location1: str, location2: str) -> float:
        """
        Calculate distance between two locations using geopy library.
        
        Args:
            location1: First location (e.g., "Lagos, Nigeria")
            location2: Second location (e.g., "London, United Kingdom")
            
        Returns:
            float: Distance in kilometers
        """
        try:
            from geopy.geocoders import Nominatim
            from geopy.distance import geodesic
            
            # Initialize geocoder
            geolocator = Nominatim(user_agent="fraud_detection_system")
            
            # Get coordinates for both locations
            loc1 = geolocator.geocode(location1, timeout=5)
            loc2 = geolocator.geocode(location2, timeout=5)
            
            if not loc1 or not loc2:
                # If geocoding fails, return 0 (will use continent fallback)
                return 0.0
            
            # Extract coordinates
            coord1 = (loc1.latitude, loc1.longitude)
            coord2 = (loc2.latitude, loc2.longitude)
            
            # Calculate distance using geodesic (more accurate than Haversine)
            distance = geodesic(coord1, coord2).kilometers
            
            return distance
            
        except Exception as e:
            # If library fails, return 0 (will use continent fallback)
            return 0.0

    def _analyze_login_times(self, auth_data: Dict[str, Any]) -> float:
        """
        Detect unusual login times (odd hours).
        
        Args:
            auth_data: Response from banking backend's /api/auth/history
            
        Returns:
            float: Risk score based on login timing
        """
        try:
            logs = auth_data.get('logs', [])
            
            # Only check successful logins
            successful_logins = [log for log in logs if log.get('login_success', False)]
            
            if not successful_logins:
                return 0.0
            
            # Extract hours from login times
            login_hours = []
            for log in successful_logins:
                date_time_str = log.get('date_time', '')
                parsed_time = self._parse_datetime(date_time_str)
                if parsed_time:
                    login_hours.append(parsed_time.hour)
            
            if not login_hours:
                return 0.0
            
            # Check most recent login
            latest_hour = login_hours[0] if login_hours else None
            
            if latest_hour is not None:
                # Odd hours: 12 AM - 5 AM (midnight to early morning)
                if 0 <= latest_hour < 6:
                    # Check if this is unusual for the user
                    other_hours = login_hours[1:] if len(login_hours) > 1 else []
                    odd_hour_count = sum(1 for h in other_hours if 0 <= h < 6)
                    
                    # If user rarely logs in at odd hours, this is suspicious
                    if len(other_hours) > 0 and odd_hour_count / len(other_hours) < 0.2:
                        self._last_time_explanation = f"Login at unusual hour ({latest_hour}:00 - user rarely logs in between midnight and 5 AM)"
                        return 0.5  # Moderate risk - unusual login time
            
            return 0.0
            
        except Exception as e:
            return 0.0

    def _parse_datetime(self, date_time_str: str) -> datetime:
        """
        Parse date_time string from auth logs.
        Format: "December 27, 2025 at 15:25 UTC"
        """
        try:
            # Remove " UTC" suffix
            date_time_str = date_time_str.replace(' UTC', '')
            # Parse the datetime
            return datetime.strptime(date_time_str, "%B %d, %Y at %H:%M")
        except Exception:
            return None

    def _different_continents(self, location1: str, location2: str) -> bool:
        """Check if two locations are on different continents."""
        continents = {
            'Africa': ['Nigeria', 'Ghana', 'Kenya', 'South Africa', 'Egypt'],
            'Europe': ['United Kingdom', 'Germany', 'France', 'Spain', 'Italy'],
            'Asia': ['China', 'India', 'Japan', 'Singapore', 'UAE'],
            'North America': ['USA', 'Canada', 'Mexico'],
            'South America': ['Brazil', 'Argentina', 'Colombia'],
            'Oceania': ['Australia', 'New Zealand']
        }
        
        loc1_continent = None
        loc2_continent = None
        
        for continent, countries in continents.items():
            if any(country in location1 for country in countries):
                loc1_continent = continent
            if any(country in location2 for country in countries):
                loc2_continent = continent
        
        # If we can determine both continents and they're different
        if loc1_continent and loc2_continent:
            return loc1_continent != loc2_continent
        
        # If locations are clearly different and we can't determine continents
        # assume they might be on different continents
        return location1 != location2
