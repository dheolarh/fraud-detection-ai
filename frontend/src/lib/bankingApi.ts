/**
 * Banking API Client
 * Connects to banking backend (port 8001)
 */

const BANKING_API_URL = import.meta.env.VITE_BANKING_API_URL || 'http://localhost:8001';

interface LocationResult {
    city: string;
    country: string;
    full_location: string;
    currency: string;
    currency_symbol: string;
}

interface ConversionResult {
    original_amount: number;
    original_currency: string;
    converted_amount: number;
    exchange_rate: number;
    timestamp: string;
}

interface AccountDetails {
    account_number: string;
    account_name: string;
    bank_name: string;
    country: string;
    currency: string;
}

class BankingApiService {
    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    }

    // Location Services
    async searchLocations(query: string, limit: number = 10): Promise<LocationResult[]> {
        const response = await fetch(
            `${BANKING_API_URL}/api/banking/locations/search?query=${encodeURIComponent(query)}&limit=${limit}`
        );
        const data = await this.handleResponse<{ results: LocationResult[] }>(response);
        return data.results;
    }

    async getLocationCurrency(location: string): Promise<{ currency: string; symbol: string }> {
        const response = await fetch(
            `${BANKING_API_URL}/api/banking/locations/currency?location=${encodeURIComponent(location)}`
        );
        return this.handleResponse<{ currency: string; symbol: string }>(response);
    }

    // Exchange Rate Services
    async getExchangeRates(): Promise<Record<string, number>> {
        const response = await fetch(`${BANKING_API_URL}/api/banking/exchange-rates`);
        const data = await this.handleResponse<{ rates: Record<string, number> }>(response);
        return data.rates;
    }

    async getExchangeRate(currency: string): Promise<number> {
        const response = await fetch(
            `${BANKING_API_URL}/api/banking/exchange-rates/${currency}`
        );
        const data = await this.handleResponse<{ rate: number }>(response);
        return data.rate;
    }

    /**
     * Convert amount between any two currencies
     * @param amount Amount to convert
     * @param fromCurrency Source currency code
     * @param toCurrency Target currency code (REQUIRED)
     */
    async convertCurrency(amount: number, fromCurrency: string, toCurrency: string): Promise<ConversionResult> {
        const response = await fetch(`${BANKING_API_URL}/api/banking/convert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount,
                from_currency: fromCurrency,
                to_currency: toCurrency  // Now required!
            })
        });
        return this.handleResponse<ConversionResult>(response);
    }

    // Account Services
    async getInternationalAccount(country: string): Promise<AccountDetails> {
        const response = await fetch(
            `${BANKING_API_URL}/api/banking/accounts/internationalBank/${encodeURIComponent(country)}`
        );
        return this.handleResponse<AccountDetails>(response);
    }

    async getAllInternationalAccounts(): Promise<AccountDetails[]> {
        const response = await fetch(`${BANKING_API_URL}/api/banking/accounts/internationalBank`);
        const data = await this.handleResponse<{ accounts: AccountDetails[] }>(response);
        return data.accounts;
    }

    async getHooverAccount(): Promise<AccountDetails> {
        const response = await fetch(`${BANKING_API_URL}/api/banking/accounts/hoover`);
        return this.handleResponse<AccountDetails>(response);
    }

    async verifyAccount(accountNumber: string, country: string, bankName?: string): Promise<{
        verified: boolean;
        account: AccountDetails;
    }> {
        const response = await fetch(`${BANKING_API_URL}/api/banking/accounts/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                account_number: accountNumber,
                country,
                bank_name: bankName
            })
        });

        const result = await this.handleResponse<{ verified: boolean; account: AccountDetails }>(response);

        // Strict validation: account number AND country must match
        if (!result.verified || result.account.country !== country) {
            throw new Error('Account number and country do not match');
        }

        return result;
    }
}

export const bankingApi = new BankingApiService();
export default bankingApi;
