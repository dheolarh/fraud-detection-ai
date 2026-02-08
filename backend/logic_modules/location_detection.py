"""
Logic 10: Location Detection
GPS-based fraud detection and impossible travel scenarios.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text

from logic_modules.base_logic import BaseFraudLogic


class LocationDetectionLogic(BaseFraudLogic):
    """
    GPS-based fraud detection.
    
    Detects:
    - Impossible travel (too fast between locations)
    - Unusual locations for user
    - High-risk geographic areas
    - Velocity-based location anomalies
    """
    
    def __init__(self):
        super().__init__()
        self.name = "LocationDetectionLogic"
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze location-based fraud indicators.
        
        Args:
            transaction: Transaction data with location
            db_session: Database session
            
        Returns:
            float: Risk score 0.0-1.0
        """
        try:
            sender_id = transaction.get('sender_id')
            location = transaction.get('location', 'Unknown')
            current_time = transaction.get('timestamp', datetime.now())
            
            risk_score = 0.0
            
            # Check 1: Impossible travel
            travel_score = await self._check_impossible_travel(
                sender_id, location, current_time, db_session, transaction
            )
            risk_score = max(risk_score, travel_score)
            
            # Check 2: Unusual location for user
            unusual_score = await self._check_unusual_location(sender_id, location, db_session, transaction)
            risk_score = max(risk_score, unusual_score)
            
            # Check 3: Rapid location changes
            velocity_score = await self._check_location_velocity(sender_id, current_time, db_session)
            risk_score = max(risk_score, velocity_score)
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Location detection error: {e}")
            return 0.0
    
    async def _check_impossible_travel(
        self, sender_id: str, current_location: str, current_time: datetime, db_session: Session, transaction: Dict[str, Any] = None
    ) -> float:
        """Detect impossible travel scenarios."""
        try:
            # Get last transaction location and time
            result = db_session.execute(
                text('''
                    SELECT location, timestamp
                    FROM transactions
                    WHERE sender_id = :sender_id
                    AND timestamp < :current_time
                    ORDER BY timestamp DESC
                    LIMIT 1
                '''),
                {
                    'sender_id': sender_id,
                    'current_time': current_time
                }
            ).fetchone()
            
            if result and current_time:
                last_location = result[0]
                last_time = result[1]
                
                if last_location != current_location:
                    # Calculate distance and time
                    distance_km = self._calculate_distance(last_location, current_location)
                    time_diff_hours = (current_time - last_time).total_seconds() / 3600
                    
                    if time_diff_hours > 0 and distance_km > 0:
                        # Calculate required speed (km/h)
                        required_speed = distance_km / time_diff_hours
                        
                        # Generate explanation
                        if required_speed > 300 and transaction:
                            transaction['_location_explanation'] = f"Impossible travel: {last_location} to {current_location} in {time_diff_hours:.1f} hours ({required_speed:.0f} km/h required)"
                        
                        # Impossible by commercial flight (>900 km/h)
                        if required_speed > 900:
                            logger.error(
                                f"Impossible travel: {last_location} -> {current_location} "
                                f"({distance_km:.0f}km in {time_diff_hours:.1f}h = {required_speed:.0f}km/h)"
                            )
                            return 1.0
                        # Very suspicious (>600 km/h, faster than most flights)
                        elif required_speed > 600:
                            return 0.9
                        # Suspicious (>300 km/h, very fast)
                        elif required_speed > 300:
                            return 0.7
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Impossible travel check error: {e}")
            return 0.0
    
    async def _check_unusual_location(
        self, sender_id: str, location: str, db_session: Session, transaction: Dict[str, Any] = None
    ) -> float:
        """Check if location is unusual for this user."""
        try:
            # Get user's common locations
            result = db_session.execute(
                text('''
                    SELECT location, COUNT(*) as count
                    FROM transactions
                    WHERE sender_id = :sender_id
                    GROUP BY location
                    ORDER BY count DESC
                    LIMIT 5
                '''),
                {'sender_id': sender_id}
            ).fetchall()
            
            if result:
                common_locations = [row[0] for row in result]
                
                # Completely new location
                if location not in common_locations:
                    if transaction and not transaction.get('_location_explanation'):  # Don't override impossible travel
                        transaction['_location_explanation'] = f"Transaction from {location} (user has never transacted from this location)"
                    return 0.4
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Unusual location error: {e}")
            return 0.0
    
    async def _check_location_velocity(
        self, sender_id: str, current_time: datetime, db_session: Session
    ) -> float:
        """Check for rapid location changes (account sharing indicator)."""
        try:
            # Get locations in last 24 hours
            window_start = current_time - timedelta(hours=24)
            
            result = db_session.execute(
                text('''
                    SELECT DISTINCT location
                    FROM transactions
                    WHERE sender_id = :sender_id
                    AND timestamp >= :window_start
                    AND timestamp < :current_time
                '''),
                {
                    'sender_id': sender_id,
                    'window_start': window_start,
                    'current_time': current_time
                }
            ).fetchall()
            
            if result:
                unique_locations = len(result)
                
                # 5+ different locations in 24h (account sharing?)
                if unique_locations >= 5:
                    return 0.7
                # 3-4 different locations
                elif unique_locations >= 3:
                    return 0.4
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Location velocity error: {e}")
            return 0.0
    
    def _calculate_distance(self, location1: str, location2: str) -> float:
        """
        Calculate distance between two locations using geopy.
        Returns distance in kilometers.
        """
        try:
            from geopy.geocoders import Nominatim
            from geopy.distance import geodesic
            
            # Initialize geocoder
            geolocator = Nominatim(user_agent="fraud_detection_system")
            
            # Geocode locations
            loc1 = geolocator.geocode(location1)
            loc2 = geolocator.geocode(location2)
            
            if not loc1 or not loc2:
                logger.warning(f"Could not geocode locations: {location1}, {location2}")
                return 500  # Default moderate distance for unknown locations
            
            # Calculate distance using geodesic (more accurate than haversine)
            coords1 = (loc1.latitude, loc1.longitude)
            coords2 = (loc2.latitude, loc2.longitude)
            
            distance = geodesic(coords1, coords2).kilometers
            
            logger.debug(f"Distance {location1} -> {location2}: {distance:.2f} km")
            return distance
            
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return 500  # Default fallback distance
