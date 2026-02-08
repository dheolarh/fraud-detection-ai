"""
Banking API Routes - Currency Agnostic
Updated to support ANY currency conversions
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from pydantic import BaseModel

from services.location import location_service
from services.exchange_rate import exchange_service
from services.account import account_service

router = APIRouter(prefix="/api/banking", tags=["banking"])


# Request/Response Models
class ConvertCurrencyRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str  # NOW REQUIRED - no default!


class VerifyAccountRequest(BaseModel):
    account_number: str
    country: str
    bank_name: str = None


# Location Endpoints
@router.get("/locations/search")
async def search_locations(query: str, limit: int = 10):
    """
    Search for locations with autocomplete
    
    Query params:
        query: Search term (city or country)
        limit: Max results (default 10)
    """
    try:
        results = location_service.search(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locations/currency")
async def get_location_currency(location: str):
    """
    Get currency information for a location
    
    Query params:
        location: Location string like "Lagos, Nigeria"
    """
    try:
        currency_info = location_service.get_currency_for_location(location)
        if not currency_info:
            raise HTTPException(status_code=404, detail="Location not found")
        return currency_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Exchange Rate Endpoints
@router.get("/exchange-rates")
async def get_exchange_rates(base_currency: str = Query('USD', description="Base currency for rates")):
    """
    Get all exchange rates FROM a base currency.
    
    Query params:
        base_currency: Base currency (default: USD)
    
    Returns rates as: 1 BASE_CURRENCY = X OTHER_CURRENCY
    Example: base=USD returns {'EUR': 0.93, 'GBP': 0.79, ...}
    """
    try:
        rates = exchange_service.get_rates(base_currency)
        return {
            "rates": rates,
            "base_currency": base_currency.upper(),
            "timestamp": "live"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-rates/{from_currency}/{to_currency}")
async def get_exchange_rate(
    from_currency: str,
    to_currency: str = 'USD'
):
    """
    Get specific exchange rate between two currencies.
    
    Path params:
        from_currency: Source currency code
        to_currency: Target currency code (default: USD)
    """
    try:
        rate = exchange_service.get_rate(from_currency, to_currency)
        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "rate": rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert")
async def convert_currency(request: ConvertCurrencyRequest):
    """
    Convert amount between ANY two currencies.
    
    Request body:
        {
            "amount": 100,
            "from_currency": "USD",
            "to_currency": "EUR"  // NOW REQUIRED!
        }
    """
    try:
        result = exchange_service.convert(
            request.amount,
            request.from_currency,
            request.to_currency
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Account Endpoints
@router.get("/accounts/internationalBank/{country}")
async def get_internationalBank_account(country: str):
    """
    Get International Bank account for a specific country
    
    Path params:
        country: Country name (Nigeria, USA, UK, etc.)
    """
    try:
        account = account_service.get_internationalBank_account(country)
        if not account:
            raise HTTPException(
                status_code=404,
                detail=f"No International Bank account found for {country}"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/internationalBank")
async def get_all_internationalBank_accounts():
    """Get all International Bank accounts"""
    try:
        accounts = account_service.get_all_internationalBank_accounts()
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/hoover")
async def get_hoover_account():
    """Get Hoover Bank account details"""
    try:
        account = account_service.get_hoover_account()
        return account
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/verify")
async def verify_account(request: VerifyAccountRequest):
    """
    Verify account exists before transfer
    
    Request body:
        {
            "account_number": "SKY-NG-001234",
            "country": "Nigeria",
            "bank_name": "International Bank"  # Optional
        }
    """
    try:
        account = account_service.verify_account(
            request.account_number,
            request.country,
            request.bank_name
        )
        
        if not account:
            raise HTTPException(
                status_code=404,
                detail="Account not found or country mismatch"
            )
        
        return {
            "verified": True,
            "account": account
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
