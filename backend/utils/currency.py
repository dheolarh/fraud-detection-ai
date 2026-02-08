"""
Currency Utilities - Server Side Only
Uses pycountry to map locations/countries to currencies
"""

from typing import Tuple
from babel.numbers import format_currency as babel_format
import re


# Location → Currency mapping using proper country data
LOCATION_TO_CURRENCY = {
    'nigeria': 'NGN',
    'lagos': 'NGN',
    'united states': 'USD',
    'usa': 'USD',
    'new york': 'USD',
    'los angeles': 'USD',
    'california': 'USD',
    'uk': 'GBP',
    'united kingdom': 'GBP',
    'london': 'GBP',
    'japan': 'JPY',
    'tokyo': 'JPY',
    'france': 'EUR',
    'paris': 'EUR',
    'germany': 'EUR',
    'berlin': 'EUR',
    'italy': 'EUR',
    'spain': 'EUR',
    'dubai': 'AED',
    'uae': 'AED',
    'singapore': 'SGD',
    'australia': 'AUD',
    'sydney': 'AUD',
    'canada': 'CAD',
    'toronto': 'CAD',
    'india': 'INR',
    'mumbai': 'INR',
    'china': 'CNY',
    'shanghai': 'CNY',
    'south korea': 'KRW',
    'seoul': 'KRW',
}


def get_currency_from_location(location: str) -> str:
    """
    Determine currency code from location string
    Uses location→currency mapping based on geography
    """
    if not location:
        return 'USD'  
    
    location_lower = location.lower().strip()
    
    # Direct match
    for key, currency in LOCATION_TO_CURRENCY.items():
        if key in location_lower:
            return currency
    
    # Default to USD for unrecognized locations
    return 'USD'


def format_money(amount: float, location: str = None) -> Tuple[str, str]:
    """
    Format amount with proper currency symbol and formatted string
    
    Returns:
        Tuple of (formatted_amount, currency_code)
    """
    currency_code = get_currency_from_location(location) if location else 'USD'  # USD fallback
    
    symbols = {
        'NGN': '₦',
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
        'JPY': '¥',
        'INR': '₹',
        'AED': 'د.إ',
        'SGD': 'S$',
        'AUD': 'A$',
        'CAD': 'C$',
        'CNY': '¥',
        'KRW': '₩',
        'ZAR': 'R',
        'CHF': 'CHF',
        'SEK': 'kr',
        'NOK': 'kr',
        'DKK': 'kr',
        'THB': '฿'
    }
    
    symbol = symbols.get(currency_code, currency_code + ' ')
    formatted = f"{symbol}{amount:,.2f}"  # Symbol only, no currency code
    return (formatted, currency_code)
