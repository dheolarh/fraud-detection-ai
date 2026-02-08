"""
Location Service
Provides location autocomplete with currency information
"""

from typing import List, Dict, Optional

class LocationService:
    """Service for managing locations and their currencies"""
    
    # Comprehensive location database
    LOCATIONS = [
        # Nigeria
        {"city": "Lagos", "country": "Nigeria", "currency": "NGN", "symbol": "₦"},
        {"city": "Abuja", "country": "Nigeria", "currency": "NGN", "symbol": "₦"},
        {"city": "Kano", "country": "Nigeria", "currency": "NGN", "symbol": "₦"},
        {"city": "Port Harcourt", "country": "Nigeria", "currency": "NGN", "symbol": "₦"},
        {"city": "Ibadan", "country": "Nigeria", "currency": "NGN", "symbol": "₦"},
        
        # USA
        {"city": "New York", "country": "USA", "currency": "USD", "symbol": "$"},
        {"city": "Los Angeles", "country": "USA", "currency": "USD", "symbol": "$"},
        {"city": "Chicago", "country": "USA", "currency": "USD", "symbol": "$"},
        {"city": "Houston", "country": "USA", "currency": "USD", "symbol": "$"},
        {"city": "Miami", "country": "USA", "currency": "USD", "symbol": "$"},
        
        # UK
        {"city": "London", "country": "UK", "currency": "GBP", "symbol": "£"},
        {"city": "Manchester", "country": "UK", "currency": "GBP", "symbol": "£"},
        {"city": "Birmingham", "country": "UK", "currency": "GBP", "symbol": "£"},
        
        # UAE
        {"city": "Dubai", "country": "UAE", "currency": "AED", "symbol": "د.إ"},
        {"city": "Abu Dhabi", "country": "UAE", "currency": "AED", "symbol": "د.إ"},
        
        # South Africa
        {"city": "Johannesburg", "country": "South Africa", "currency": "ZAR", "symbol": "R"},
        {"city": "Cape Town", "country": "South Africa", "currency": "ZAR", "symbol": "R"},
        
        # Ghana
        {"city": "Accra", "country": "Ghana", "currency": "GHS", "symbol": "GH₵"},
        {"city": "Kumasi", "country": "Ghana", "currency": "GHS", "symbol": "GH₵"},
        
        # Kenya  
        {"city": "Nairobi", "country": "Kenya", "currency": "KES", "symbol": "KSh"},
        {"city": "Mombasa", "country": "Kenya", "currency": "KES", "symbol": "KSh"},
        
        # Saudi Arabia
        {"city": "Riyadh", "country": "Saudi Arabia", "currency": "SAR", "symbol": "﷼"},
        {"city": "Jeddah", "country": "Saudi Arabia", "currency": "SAR", "symbol": "﷼"},
        
        # Europe
        {"city": "Paris", "country": "France", "currency": "EUR", "symbol": "€"},
        {"city": "Berlin", "country": "Germany", "currency": "EUR", "symbol": "€"},
        {"city": "Rome", "country": "Italy", "currency": "EUR", "symbol": "€"},
        {"city": "Madrid", "country": "Spain", "currency": "EUR", "symbol": "€"},
        {"city": "Amsterdam", "country": "The Netherlands", "currency": "EUR", "symbol": "€"},
        {"city": "Rotterdam", "country": "The Netherlands", "currency": "EUR", "symbol": "€"},
        {"city": "The Hague", "country": "The Netherlands", "currency": "EUR", "symbol": "€"},
    ]
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search locations by city or country name
        
        Args:
            query: Search string
            limit: Maximum results to return
            
        Returns:
            List of matching locations
        """
        if not query or len(query) < 2:
            return []
        
        query_lower = query.lower()
        results = []
        
        for location in self.LOCATIONS:
            if (query_lower in location['city'].lower() or 
                query_lower in location['country'].lower()):
                results.append({
                    'city': location['city'],
                    'country': location['country'],
                    'full_location': f"{location['city']}, {location['country']}",
                    'currency': location['currency'],
                    'currency_symbol': location['symbol']
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_currency_for_location(self, location: str) -> Optional[Dict]:
        """
        Get currency info for a location string
        
        Args:
            location: Location string like "Lagos, Nigeria"
            
        Returns:
            Currency info or None
        """
        for loc in self.LOCATIONS:
            if location.startswith(loc['city']) or loc['country'] in location:
                return {
                    'currency': loc['currency'],
                    'symbol': loc['symbol']
                }
        
        return None
    
    def extract_country(self, location: str) -> str:
        """
        Extract country from location string
        
        Args:
            location: "City, Country" format
            
        Returns:
            Country name
        """
        if ',' in location:
            return location.split(',')[-1].strip()
        return location.strip()


# Singleton instance
location_service = LocationService()
