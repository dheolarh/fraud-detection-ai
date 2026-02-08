"""
Exchange Rate Service - Currency Agnostic
Fetches live exchange rates and converts between ANY currencies
NO HARDCODED CURRENCIES!
"""

import requests
from typing import Dict, Optional
from datetime import datetime, timedelta


class ExchangeRateService:
    """
    Currency-agnostic exchange rate service.
    Works with ANY base currency, not just NGN!
    """
    
    def __init__(self, default_base: str = 'USD'):
        """
        Initialize exchange rate service.
        
        Args:
            default_base: Default base currency (USD recommended for global system)
        """
        self.default_base = default_base
        self.cache: Dict[str, Dict] = {}  # Cache per base currency
        self.cache_duration = timedelta(hours=1)
        self.cache_expiry: Dict[str, datetime] = {}
    
    def get_rates(self, base_currency: str = None) -> Dict[str, float]:
        """
        Get exchange rates FROM a base currency to all other currencies.
        
        Args:
            base_currency: Base currency (e.g., 'USD', 'EUR', 'NGN')
                          If None, uses default_base
        
        Returns:
            Dict of currency codes to exchange rates
            Example: {'EUR': 0.93, 'GBP': 0.79, ...}
        """
        base = (base_currency or self.default_base).upper()
        
        # Check cache
        if base in self.cache and base in self.cache_expiry:
            if datetime.now() < self.cache_expiry[base]:
                return self.cache[base]
        
        # Fetch fresh rates
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{base}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            
            # Update cache
            self.cache[base] = rates
            self.cache_expiry[base] = datetime.now() + self.cache_duration
            
            return rates
            
        except requests.RequestException as e:
            print(f"Failed to fetch exchange rates for {base}: {e}")
            
            # Return fallback rates if available
            if base in self.cache:
                return self.cache[base]
            
            # Last resort fallback
            return self._get_fallback_rates(base)
    
    def _get_fallback_rates(self, base: str) -> Dict[str, float]:
        """
        Fallback exchange rates when API is unavailable.
        Uses approximate rates (updated periodically).
        """
        # Common fallback rates (as of Dec 2024)
        if base == 'USD':
            return {
                'USD': 1.0,
                'EUR': 0.93,
                'GBP': 0.79,
                'JPY': 150.0,
                'NGN': 1500.0,
                'GHS': 12.0,
                'ZAR': 18.5,
                'CAD': 1.35,
                'AUD': 1.52,
                'CHF': 0.88,
                'CNY': 7.24,
                'INR': 83.0,
            }
        elif base == 'NGN':
            return {
                'NGN': 1.0,
                'USD': 1/1500.0,
                'EUR': 1/1600.0,
                'GBP': 1/1900.0,
                'JPY': 0.10,
            }
        else:
            # Return USD-based rates if we don't have specific fallback
            return {'USD': 1.0}
    
    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = None
    ) -> Dict:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code (defaults to default_base)
        
        Returns:
            Dict with converted_amount, from_currency, to_currency, rate
        """
        to_curr = (to_currency or self.default_base).upper()
        from_curr = from_currency.upper()
        
        # Same currency = no conversion needed
        if from_curr == to_curr:
            return {
                'amount': amount,
                'converted_amount': amount,
                'from_currency': from_curr,
                'to_currency': to_curr,
                'rate': 1.0
            }
        
        # Get rates FROM source currency
        rates = self.get_rates(from_curr)
        
        # Get rate to target currency
        rate = rates.get(to_curr, 1.0)
        converted = amount * rate
        
        return {
            'amount': amount,
            'converted_amount': round(converted, 2),
            'from_currency': from_curr,
            'to_currency': to_curr,
            'rate': round(rate, 6)
        }
    
    def get_rate(self, from_currency: str, to_currency: str = None) -> float:
        """
        Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency (defaults to default_base)
        
        Returns:
            Exchange rate as float
        """
        to_curr = (to_currency or self.default_base).upper()
        from_curr = from_currency.upper()
        
        if from_curr == to_curr:
            return 1.0
        
        rates = self.get_rates(from_curr)
        return rates.get(to_curr, 1.0)
    
    def clear_cache(self, base_currency: str = None):
        """Clear cache for specific or all currencies."""
        if base_currency:
            if base_currency in self.cache:
                del self.cache[base_currency]
            if base_currency in self.cache_expiry:
                del self.cache_expiry[base_currency]
        else:
            self.cache.clear()
            self.cache_expiry.clear()


# Singleton instance with USD as default (global standard)
exchange_service = ExchangeRateService(default_base='USD')
