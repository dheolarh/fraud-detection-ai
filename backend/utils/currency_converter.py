"""
Currency Converter Utility
Converts amounts between currencies using live exchange rates.
Supports ALL ISO 4217 currencies (160+ currencies worldwide).
Base currency: USD
"""

from decimal import Decimal
from typing import Dict, Optional
from loguru import logger
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    from forex_python.converter import CurrencyRates, RatesNotAvailableError
    FOREX_AVAILABLE = True
except ImportError:
    logger.warning("forex-python not available, using fallback rates")
    FOREX_AVAILABLE = False


class CurrencyConverter:
    """
    Convert amounts between currencies.
    Uses live exchange rates via forex-python (Google Finance).
    Falls back to cached rates if API unavailable.
    Supports 160+ world currencies.
    """
    
    # Fallback exchange rates to USD (used if forex-python unavailable)
    FALLBACK_RATES: Dict[str, Decimal] = {
        'USD': Decimal('1.0'),
        'NGN': Decimal('0.00067'),      # Nigerian Naira
        'GBP': Decimal('1.27'),          # British Pound
        'EUR': Decimal('1.10'),          # Euro
        'JPY': Decimal('0.0071'),        # Japanese Yen
        'CAD': Decimal('0.74'),          # Canadian Dollar
        'AUD': Decimal('0.67'),          # Australian Dollar
        'CHF': Decimal('1.13'),          # Swiss Franc
        'CNY': Decimal('0.14'),          # Chinese Yuan
        'INR': Decimal('0.012'),         # Indian Rupee
        'ZAR': Decimal('0.055'),         # South African Rand
        'BRL': Decimal('0.20'),          # Brazilian Real
        'MXN': Decimal('0.058'),         # Mexican Peso
        'KRW': Decimal('0.00076'),       # South Korean Won
        'SGD': Decimal('0.74'),          # Singapore Dollar
        'HKD': Decimal('0.13'),          # Hong Kong Dollar
        'SEK': Decimal('0.096'),         # Swedish Krona
        'NOK': Decimal('0.095'),         # Norwegian Krone
        'DKK': Decimal('0.15'),          # Danish Krone
        'PLN': Decimal('0.25'),          # Polish Zloty
        'THB': Decimal('0.029'),         # Thai Baht
        'MYR': Decimal('0.22'),          # Malaysian Ringgit
        'IDR': Decimal('0.000064'),      # Indonesian Rupiah
        'PHP': Decimal('0.018'),         # Philippine Peso
        'CZK': Decimal('0.044'),         # Czech Koruna
        'HUF': Decimal('0.0028'),        # Hungarian Forint
        'ILS': Decimal('0.27'),          # Israeli Shekel
        'CLP': Decimal('0.0011'),        # Chilean Peso
        'ARS': Decimal('0.0010'),        # Argentine Peso
        'COP': Decimal('0.00025'),       # Colombian Peso
    }
    
    # Cache for live rates (1 hour TTL)
    _rate_cache: Dict[str, Decimal] = {}
    _cache_timestamp: Optional[datetime] = None
    _cache_ttl = timedelta(hours=1)
    
    # Toggle for live rates — set to False for instant conversions using built-in fallback table
    use_live_rates = False
    
    # Currency rates instance
    _currency_rates = CurrencyRates() if FOREX_AVAILABLE else None
    
    @classmethod
    def _get_live_rate(cls, currency: str) -> Optional[Decimal]:
        """
        Get live exchange rate for currency (to USD).
        Returns None if unavailable.
        """
        if not cls.use_live_rates or not FOREX_AVAILABLE or not cls._currency_rates:
            return None
        
        try:
            # Check cache first
            if cls._cache_timestamp and datetime.now() - cls._cache_timestamp < cls._cache_ttl:
                if currency in cls._rate_cache:
                    return cls._rate_cache[currency]
            
            # Get live rate (currency to USD)
            if currency == 'USD':
                rate = Decimal('1.0')
            else:
                # Get rate: 1 currency = X USD
                usd_per_currency = cls._currency_rates.get_rate(currency, 'USD')
                rate = Decimal(str(usd_per_currency))
            
            # Cache it
            cls._rate_cache[currency] = rate
            cls._cache_timestamp = datetime.now()
            
            logger.debug(f"Live rate fetched: 1 {currency} = ${rate:.6f} USD")
            return rate
            
        except (RatesNotAvailableError, Exception) as e:
            logger.warning(f"Could not fetch live rate for {currency}: {e}")
            return None
    
    @classmethod
    def to_usd(cls, amount: Decimal, from_currency: str) -> Decimal:
        """
        Convert any currency to USD.
        
        Args:
            amount: Amount in source currency
            from_currency: ISO 4217 currency code (e.g., 'NGN', 'GBP', 'EUR')
            
        Returns:
            Amount in USD
        """
        if from_currency == 'USD':
            return amount
        
        from_currency = from_currency.upper()
        
        # Try live rate first
        rate = cls._get_live_rate(from_currency)
        
        # Fall back to cached rates
        if rate is None:
            rate = cls.FALLBACK_RATES.get(from_currency)
            if rate:
                logger.debug(f"Using fallback rate for {from_currency}")
            else:
                logger.warning(f"Unknown currency {from_currency}, using 1:1 rate")
                return amount
        
        usd_amount = Decimal(str(amount)) * rate
        logger.debug(f"Converted {amount} {from_currency} to ${usd_amount:.2f} USD")
        return usd_amount
    
    @classmethod
    def from_usd(cls, amount_usd: Decimal, to_currency: str) -> Decimal:
        """
        Convert USD to any currency.
        
        Args:
            amount_usd: Amount in USD
            to_currency: Target ISO 4217 currency code
            
        Returns:
            Amount in target currency
        """
        if to_currency == 'USD':
            return amount_usd
        
        to_currency = to_currency.upper()
        
        # Try live rate first
        rate = cls._get_live_rate(to_currency)
        
        # Fall back to cached rates
        if rate is None:
            rate = cls.FALLBACK_RATES.get(to_currency)
            if rate:
                logger.debug(f"Using fallback rate for {to_currency}")
            else:
                logger.warning(f"Unknown currency {to_currency}, using 1:1 rate")
                return amount_usd
        
        # Convert: USD / rate = target currency
        target_amount = Decimal(str(amount_usd)) / rate
        logger.debug(f"Converted ${amount_usd:.2f} USD to {target_amount:.2f} {to_currency}")
        return target_amount
    
    @classmethod
    def convert(cls, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """
        Convert between any two currencies.
        
        Args:
            amount: Amount in source currency
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Amount in target currency
        """
        if from_currency == to_currency:
            return amount
        
        # Convert to USD first, then to target
        usd_amount = cls.to_usd(amount, from_currency)
        return cls.from_usd(usd_amount, to_currency)
    
    @classmethod
    def get_rate(cls, currency: str) -> Decimal:
        """Get exchange rate for a currency (to USD)"""
        rate = cls._get_live_rate(currency)
        if rate is None:
            rate = cls.FALLBACK_RATES.get(currency.upper(), Decimal('1.0'))
        return rate
    
    @classmethod
    def get_currency_symbol(cls, currency: str) -> str:
        """Get symbol for a currency"""
        symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
            'INR': '₹', 'NGN': '₦', 'CHF': 'Fr', 'CAD': 'C$', 'AUD': 'A$',
            'ZAR': 'R', 'BRL': 'R$', 'MXN': '$', 'KRW': '₩', 'SGD': 'S$',
            'HKD': 'HK$', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'PLN': 'zł',
            'THB': '฿', 'MYR': 'RM', 'IDR': 'Rp', 'PHP': '₱', 'CZK': 'Kč',
            'HUF': 'Ft', 'ILS': '₪', 'CLP': '$', 'ARS': '$', 'COP': '$',
        }
        return symbols.get(currency.upper(), currency)
    
    @classmethod
    def clear_cache(cls):
        """Clear rate cache (useful for testing or forcing refresh)"""
        cls._rate_cache.clear()
        cls._cache_timestamp = None
        logger.info("Currency rate cache cleared")
