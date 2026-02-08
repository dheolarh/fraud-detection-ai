"""
Logic 6: Cross-Border Matrix
Detects fraud based on transaction country patterns and high-risk jurisdictions.
"""

from typing import Dict, Any
from decimal import Decimal
from loguru import logger
from sqlalchemy.orm import Session

from logic_modules.base_logic import BaseFraudLogic
from utils.currency_converter import CurrencyConverter
from utils.dynamic_thresholds import DynamicThresholdCalculator


class CrossBorderLogic(BaseFraudLogic):
    """
    Cross-border transaction fraud detection.
    
    Detects:
    - Transactions from/to high-risk countries
    - Unusual country pairs
    - Sudden geographic changes
    - High-value international transfers (DYNAMIC threshold per user)
    
    Risk Bucket: GEO_ANOMALY
    
    NOTE: No hardcoded thresholds! Adapts to each user's spending pattern.
    """
    
    # High-risk countries (simplified list for demo)
    HIGH_RISK_COUNTRIES = {
        'North Korea', 'Iran', 'Syria', 'Afghanistan', 
        'Yemen', 'Somalia', 'Sudan', 'Venezuela'
    }
    
    # Medium-risk countries
    MEDIUM_RISK_COUNTRIES = {
        'Russia', 'China', 'Pakistan', 'Iraq',
        'Libya', 'Lebanon', 'Belarus'
    }
    
    # High-risk country pairs (sender -> receiver)
    HIGH_RISK_PAIRS = {
        ('Nigeria', 'Russia'),
        ('China', 'North Korea'),
        ('Pakistan', 'Afghanistan'),
        ('Russia', 'Iran')
    }
    

    
    def __init__(self):
        super().__init__()
        self.name = "CrossBorderLogic"
    
    async def analyze(self, transaction: Dict[str, Any], db_session: Session) -> float:
        """
        Analyze cross-border transaction risk.
        
        Args:
            transaction: Transaction data with amount, currency, location
            db_session: Database session
            
        Returns:
            float: Risk score (0.0-1.0)
        """
        try:
            amount = Decimal(str(transaction.get('amount', 0)))
            currency = transaction.get('currency')  # Required field
            sender_id = transaction.get('sender_id')
            
            if not currency:
                return 0.0  # Cannot analyze without currency
            
            # Convert to USD for threshold comparison
            amount_usd = CurrencyConverter.to_usd(amount, currency)
            
            # Get user's PERSONALIZED international transfer threshold
            user_threshold = await DynamicThresholdCalculator.get_threshold(
                sender_id, 'high_value_international', db_session
            )
            
            score = 0.0
            
            # Extract location from transaction
            # Location field contains the transaction destination
            location = transaction.get('location', 'Unknown')
            
            # Extract country from location string (e.g., "Moscow, Russia" -> "Russia")
            receiver_country = location.split(',')[-1].strip() if ',' in location else location
            sender_country = "UK"  # Default sender country (can be enhanced)
            
            # Check if cross-border (international transaction)
            is_cross_border = receiver_country not in ['UK', 'United Kingdom', 'Unknown']
            
            if is_cross_border:
                # Higher risk for large international transfers
                if amount_usd >= user_threshold:
                    score = 0.6  # High-value international transfer
                elif amount_usd >= user_threshold / 2:
                    score = 0.3  # Moderate international transfer
                else:
                    score = 0.1  # Small international transfer
            
            # Check 1: High-risk country involvement
            if receiver_country in self.HIGH_RISK_COUNTRIES:
                score = max(score, 0.9)
                logger.warning(f"High-risk country detected: {receiver_country}")
            
            # Check 2: Medium-risk country (Russia, China, etc.)
            elif receiver_country in self.MEDIUM_RISK_COUNTRIES:
                score = max(score, 0.7)  # Increased from 0.6
                logger.warning(f"Medium-risk country detected: {receiver_country}")
            
            # Check 3: High-risk country pairs
            country_pair = (sender_country, receiver_country)
            if country_pair in self.HIGH_RISK_PAIRS:
                score = max(score, 0.85)
                logger.warning(f"High-risk country pair: {country_pair}")
            
            # Check 4: Impossible travel detection
            try:
                from sqlalchemy import text
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
                        'sender_id': transaction.get('sender_id'),
                        'current_time': transaction.get('timestamp')
                    }
                ).fetchone()
                
                if result:
                    last_location = result[0]
                    last_time = result[1]
                    current_time = transaction.get('timestamp')
                    
                    # If locations are very different and time gap is small
                    if last_location != location and current_time and last_time:
                        if isinstance(current_time, str):
                            from datetime import datetime
                            current_time = datetime.fromisoformat(current_time)
                        
                        time_diff_hours = (current_time - last_time).total_seconds() / 3600
                        
                        # Different continents in < 12 hours (impossible travel)
                        if time_diff_hours < 12 and self._different_continents(last_location, location):
                            score = max(score, 1.0)
                            logger.error(f"Impossible travel: {last_location} -> {location} in {time_diff_hours:.1f}h")
            except Exception as db_error:
                logger.debug(f"Could not check impossible travel: {db_error}")
            
            # Generate explanation
            if score >= 0.4:
                if receiver_country in self.HIGH_RISK_COUNTRIES:
                    transaction['_crossborder_explanation'] = f"Transaction to {receiver_country} (critical-risk country)"
                elif receiver_country in self.MEDIUM_RISK_COUNTRIES:
                    transaction['_crossborder_explanation'] = f"Transaction to {receiver_country} (high-risk country)"
                elif is_cross_border and amount_usd >= user_threshold:
                    transaction['_crossborder_explanation'] = f"Large international transfer to {receiver_country}"
            
            return score
            
        except Exception as e:
            logger.error(f"Cross-border analysis error: {e}")
            return 0.0
    
    def _different_continents(self, location1: str, location2: str) -> bool:
        """
        Check if two locations are on different continents using geopy.
        """
        try:
            from geopy.geocoders import Nominatim
            
            # Initialize geocoder
            geolocator = Nominatim(user_agent="fraud_detection_system")
            
            # Geocode locations
            loc1 = geolocator.geocode(location1, addressdetails=True)
            loc2 = geolocator.geocode(location2, addressdetails=True)
            
            if not loc1 or not loc2:
                logger.warning(f"Could not geocode locations: {location1}, {location2}")
                return False  # Can't determine, assume same continent
            
            # Extract country codes
            country1 = loc1.raw.get('address', {}).get('country_code', '').upper()
            country2 = loc2.raw.get('address', {}).get('country_code', '').upper()
            
            # Map country codes to continents (simplified)
            continent_map = {
                # Africa
                'NG': 'Africa', 'GH': 'Africa', 'KE': 'Africa', 'ZA': 'Africa', 'EG': 'Africa',
                # Asia
                'CN': 'Asia', 'IN': 'Asia', 'PK': 'Asia', 'AF': 'Asia', 'RU': 'Asia', 'JP': 'Asia', 'SG': 'Asia', 'AE': 'Asia',
                # Europe
                'GB': 'Europe', 'DE': 'Europe', 'FR': 'Europe', 'IT': 'Europe', 'ES': 'Europe',
                # Americas
                'US': 'Americas', 'CA': 'Americas', 'BR': 'Americas', 'MX': 'Americas', 'VE': 'Americas',
            }
            
            continent1 = continent_map.get(country1, 'Unknown')
            continent2 = continent_map.get(country2, 'Unknown')
            
            # Different continents if they don't match
            result = continent1 != continent2 and continent1 != 'Unknown' and continent2 != 'Unknown'
            
            logger.debug(f"Continent check: {location1} ({continent1}) vs {location2} ({continent2}) = {result}")
            return result
            
        except Exception as e:
            logger.error(f"Continent check error: {e}")
            return False  # Default to same continent on error
