"""
Bank Configuration
Defines the bank's location and currency settings using real APIs
"""

import pycountry
from forex_python.converter import CurrencyRates
from decimal import Decimal

# Bank Location Settings
# Change these values to relocate the bank
BANK_COUNTRY = "United Kingdom"  # Full country name
BANK_CITY = "London"

# Get currency from country using pycountry
def get_currency_for_country(country_name: str) -> str:
    """
    Get ISO currency code for a country using pycountry library
    
    Args:
        country_name: Full country name (e.g., "United Kingdom", "United States")
    
    Returns:
        ISO 4217 currency code (e.g., "GBP", "USD")
    """
    try:
        # Try to find country by name
        country = pycountry.countries.search_fuzzy(country_name)[0]
        
        # Fallback: Common country-currency mappings
        common_mappings = {
            "GB": "GBP",  # United Kingdom
            "US": "USD",  # United States
            "CA": "CAD",  # Canada
            "AU": "AUD",  # Australia
            "JP": "JPY",  # Japan
            "CN": "CNY",  # China
            "IN": "INR",  # India
            "BR": "BRL",  # Brazil
            "MX": "MXN",  # Mexico
            "ZA": "ZAR",  # South Africa
            "NG": "NGN",  # Nigeria
            "KE": "KES",  # Kenya
            "EG": "EGP",  # Egypt
            "FR": "EUR",  # France
            "DE": "EUR",  # Germany
            "IT": "EUR",  # Italy
            "ES": "EUR",  # Spain
        }
        
        # Get from common mappings using alpha_2 code
        return common_mappings.get(country.alpha_2, "USD")
        
    except Exception as e:
        print(f"Warning: Could not determine currency for {country_name}, defaulting to USD. Error: {e}")
        return "USD"


# Auto-detect currency from country
BANK_CURRENCY = get_currency_for_country(BANK_COUNTRY)

# Initialize currency converter (uses real-time exchange rates)
currency_converter = CurrencyRates()


def get_bank_info():
    """Get bank location and currency information"""
    return {
        "country": BANK_COUNTRY,
        "city": BANK_CITY,
        "currency": BANK_CURRENCY
    }


def convert_to_bank_currency(amount: float, from_currency: str) -> float:
    """
    Convert amount from foreign currency to bank's currency using real-time exchange rates
    
    Uses forex-python library which fetches live rates from European Central Bank.
    Falls back to hardcoded rates for currencies not supported by ECB.
    
    Args:
        amount: Amount in foreign currency
        from_currency: ISO currency code (USD, EUR, GBP, etc.)
    
    Returns:
        Converted amount in bank's currency
    """
    if from_currency == BANK_CURRENCY:
        return amount
    
    # Fallback rates for currencies not supported by forex-python
    # These are approximate rates (update periodically)
    fallback_rates_to_gbp = {
        "NGN": 0.00052,  # 1 NGN = 0.00052 GBP (Nigerian Naira)
        "KES": 0.0062,   # 1 KES = 0.0062 GBP (Kenyan Shilling)
        "ZAR": 0.044,    # 1 ZAR = 0.044 GBP (South African Rand)
        "EGP": 0.016,    # 1 EGP = 0.016 GBP (Egyptian Pound)
        "GHS": 0.053,    # 1 GHS = 0.053 GBP (Ghanaian Cedi)
        "TZS": 0.00032,  # 1 TZS = 0.00032 GBP (Tanzanian Shilling)
        "UGX": 0.00021,  # 1 UGX = 0.00021 GBP (Ugandan Shilling)
    }
    
    fallback_rates_to_usd = {
        "NGN": 0.00065,  # 1 NGN = 0.00065 USD
        "KES": 0.0078,   # 1 KES = 0.0078 USD
        "ZAR": 0.055,    # 1 ZAR = 0.055 USD
        "EGP": 0.020,    # 1 EGP = 0.020 USD
        "GHS": 0.067,    # 1 GHS = 0.067 USD
        "TZS": 0.00040,  # 1 TZS = 0.00040 USD
        "UGX": 0.00027,  # 1 UGX = 0.00027 USD
    }
    
    try:
        # Try to get real-time exchange rate from forex-python
        rate = currency_converter.get_rate(from_currency, BANK_CURRENCY)
        converted = amount * rate
        print(f"Live rate: 1 {from_currency} = {rate:.6f} {BANK_CURRENCY}")
        print(f"Converting {amount:,.2f} {from_currency} → {converted:,.2f} {BANK_CURRENCY}")
        return converted
    except Exception as e:
        # Fallback to hardcoded rates
        print(f"⚠️ Live rate unavailable for {from_currency} → {BANK_CURRENCY}")
        print(f"⚠️ Error: {str(e)}")
        
        # Get fallback rate based on bank currency
        if BANK_CURRENCY == "GBP":
            rate = fallback_rates_to_gbp.get(from_currency)
        elif BANK_CURRENCY == "USD":
            rate = fallback_rates_to_usd.get(from_currency)
        else:
            rate = None
        
        if rate:
            converted = amount * rate
            print(f"Using fallback rate: 1 {from_currency} = {rate:.6f} {BANK_CURRENCY}")
            print(f"Converting {amount:,.2f} {from_currency} → {converted:,.2f} {BANK_CURRENCY}")
            return converted
        else:
            print(f"❌ No rate available for {from_currency} → {BANK_CURRENCY}, using 1:1 (NO CONVERSION)")
            return amount

# Trigger reload
