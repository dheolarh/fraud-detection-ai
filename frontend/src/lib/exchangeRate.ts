/**
 * Exchange Rate Service
 * Fetches live exchange rates from API
 */

const EXCHANGE_API_BASE = 'https://api.exchangerate-api.com/v4/latest';

interface ExchangeRates {
    [currency: string]: number;
}

let cachedRates: ExchangeRates | null = null;
let lastFetchTime = 0;
const CACHE_DURATION = 3600000; // 1 hour in milliseconds

/**
 * Fetch exchange rates from API with caching
 * @param baseCurrency Base currency (default: GBP)
 * @returns Exchange rates object
 */
export async function getExchangeRates(baseCurrency: string = 'GBP'): Promise<ExchangeRates> {
    const now = Date.now();

    // Return cached rates if still valid
    if (cachedRates && (now - lastFetchTime) < CACHE_DURATION) {
        return cachedRates;
    }

    try {
        const response = await fetch(`${EXCHANGE_API_BASE}/${baseCurrency}`);

        if (!response.ok) {
            throw new Error(`Exchange rate API error: ${response.status}`);
        }

        const data = await response.json();

        // Convert rates to "from foreign currency to base currency"
        // API gives us "1 GBP = X USD", we need "1 USD = Y GBP"
        const rates: ExchangeRates = {};
        for (const [currency, rate] of Object.entries(data.rates as ExchangeRates)) {
            rates[currency] = 1 / rate; // Invert the rate
        }

        cachedRates = rates;
        lastFetchTime = now;

        console.log(`✅ Fetched exchange rates for ${Object.keys(rates).length} currencies`);
        return rates;

    } catch (error) {
        console.error('Failed to fetch exchange rates:', error);

        // Fallback to hardcoded rates if API fails
        return getFallbackRates();
    }
}

/**
 * Convert amount from one currency to another
 * @param amount Amount to convert
 * @param fromCurrency Source currency
 * @param toCurrency Target currency (default: GBP)
 * @returns Converted amount
 */
export async function convertCurrency(
    amount: number,
    fromCurrency: string,
    toCurrency: string = 'GBP'
): Promise<number> {
    if (fromCurrency === toCurrency) {
        return amount;
    }

    const rates = await getExchangeRates(toCurrency);
    const rate = rates[fromCurrency];

    if (!rate) {
        throw new Error(`Exchange rate not available for ${fromCurrency} → ${toCurrency}`);
    }

    return amount * rate;
}

/**
 * Fallback rates if API is unavailable
 */
function getFallbackRates(): ExchangeRates {
    return {
        // African currencies
        'NGN': 0.00052,
        'GHS': 0.053,
        'KES': 0.0062,
        'ZAR': 0.044,
        'EGP': 0.016,
        'TZS': 0.00032,
        'UGX': 0.00021,

        // Major currencies
        'USD': 0.79,
        'EUR': 0.86,
        'JPY': 0.0054,
        'CAD': 0.58,
        'AUD': 0.51,
        'CNY': 0.11,
        'INR': 0.0095,
        'BRL': 0.16,
        'MXN': 0.049,
        'GBP': 1.0,
    };
}
