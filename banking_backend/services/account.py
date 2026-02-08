"""
Account Service
Manages bank accounts for International and Hoover banks
"""

from typing import Dict, Optional, List

class AccountService:
    """Service for managing bank accounts"""
    
    # International Bank accounts (external bank)
    SKYNE_ACCOUNTS = {
        "Nigeria": {
            "account_number": "SKY-NG-001234",
            "account_name": "Adewale Johnson",
            "bank_name": "International Bank",
            "country": "Nigeria",
            "currency": "NGN"
        },
        "USA": {
            "account_number": "SKY-US-567890",
            "account_name": "John Smith",
            "bank_name": "International Bank",
            "country": "USA",
            "currency": "USD"
        },
        "UK": {
            "account_number": "SKY-UK-111222",
            "account_name": "James Williams",
            "bank_name": "International Bank",
            "country": "UK",
            "currency": "GBP"
        },
        "UAE": {
            "account_number": "SKY-AE-333444",
            "account_name": "Ahmed Al-Mansoori",
            "bank_name": "International Bank",
            "country": "UAE",
            "currency": "AED"
        },
        "South Africa": {
            "account_number": "SKY-ZA-555666",
            "account_name": "Thabo Mbeki",
            "bank_name": "International Bank",
            "country": "South Africa",
            "currency": "ZAR"
        },
    }
    
    # Hoover Bank account (Nigerian bank - fraud detection enabled)
    HOOVER_ACCOUNT = {
        "account_number": "HOV-NG-001",
        "account_name": "USER001",
        "bank_name": "Hoover Bank",
        "country": "Nigeria",
        "currency": "NGN"
    }
    
    def get_internationalBank_account(self, country: str) -> Optional[Dict]:
        """
        Get International Bank account for a specific country
        
        Args:
            country: Country name
            
        Returns:
            Account details or None
        """
        return self.SKYNE_ACCOUNTS.get(country)
    
    def get_hoover_account(self) -> Dict:
        """Get Hoover Bank account details"""
        return self.HOOVER_ACCOUNT
    
    def verify_account(self, account_number: str, country: str, bank_name: str = None) -> Optional[Dict]:
        """
        Verify account exists
        
        Args:
            account_number: Account number to verify
            country: Country where account is registered
            bank_name: Optional bank name
            
        Returns:
            Account details if found, None otherwise
        """
        # Check International accounts
        for country_key, account in self.SKYNE_ACCOUNTS.items():
            if account['account_number'] == account_number and account['country'] == country:
                return account
        
        # Check Hoover account
        if self.HOOVER_ACCOUNT['account_number'] == account_number:
            return self.HOOVER_ACCOUNT
        
        return None
    
    def get_all_internationalBank_accounts(self) -> List[Dict]:
        """Get all International Bank accounts"""
        return list(self.SKYNE_ACCOUNTS.values())


# Singleton instance
account_service = AccountService()
