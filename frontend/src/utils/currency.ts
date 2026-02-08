/**
 * Currency Utilities - Simple and Dynamic
 * Uses browser's Intl API for proper currency formatting
 */

/**
 * Format amount with proper currency symbol and formatting
 * Uses Intl.NumberFormat for correct localization
 */
export const formatCurrency = (
    amount: number,
    currencyCode: string = 'USD',
    options: Intl.NumberFormatOptions = {}
): string => {
    try {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currencyCode.toUpperCase(),
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
            ...options,
        }).format(amount);
    } catch (error) {
        // Fallback if currency code is invalid
        console.warn(`Invalid currency code: ${currencyCode}, using USD`);
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
            ...options,
        }).format(amount);
    }
};

/**
 * Format currency in compact notation (K, M, B)
 */
export const formatCurrencyCompact = (
    amount: number,
    currencyCode: string = 'USD'
): string => {
    const absAmount = Math.abs(amount);
    const sign = amount < 0 ? '-' : '';

    if (absAmount >= 1_000_000_000) {
        return `${sign}${formatCurrency(absAmount / 1_000_000_000, currencyCode, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}B`;
    } else if (absAmount >= 1_000_000) {
        return `${sign}${formatCurrency(absAmount / 1_000_000, currencyCode, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}M`;
    } else if (absAmount >= 1_000) {
        return `${sign}${formatCurrency(absAmount / 1_000, currencyCode, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}K`;
    }

    return formatCurrency(amount, currencyCode);
};

/**
 * Get currency symbol from currency code
 * Uses Intl to extract just the symbol
 */
export const getCurrencySymbol = (currencyCode: string = 'USD'): string => {
    try {
        const formatted = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currencyCode.toUpperCase(),
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(0);

        // Extract symbol by removing digits and spaces
        return formatted.replace(/[\d\s,]/g, '');
    } catch (error) {
        // Fallback symbol map for common currencies
        const symbols: Record<string, string> = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
            'INR': '₹', 'NGN': '₦', 'CAD': 'C$', 'AUD': 'A$', 'ZAR': 'R',
            'BRL': 'R$', 'CHF': 'Fr', 'KRW': '₩', 'MXN': '$',
        };

        return symbols[currencyCode.toUpperCase()] || currencyCode;
    }
};
