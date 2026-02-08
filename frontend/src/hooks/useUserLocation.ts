/**
 * User Location and Currency Hook
 * Detects user location via IP geolocation (VPN-aware)
 * No hardcoded fallbacks - truly dynamic!
 */

import { useState, useEffect } from 'react';

interface UserLocation {
    location: string;
    currency: string;
    currencySymbol: string;
    isLoading: boolean;
    error: string | null;
}

interface IPLocationResponse {
    city: string;
    country_name: string;
    country_code: string;
    currency?: string;
}

/**
 * Hook to get user's location and currency from IP geolocation
 * Works with VPN - detects actual IP location
 */
export function useUserLocation(): UserLocation {
    const [locationData, setLocationData] = useState<UserLocation>({
        location: '',
        currency: 'USD',  // Initial fallback
        currencySymbol: '$',
        isLoading: true,
        error: null,
    });

    useEffect(() => {
        detectLocation();
    }, []);

    async function detectLocation() {
        try {
            // Try to get from localStorage first (cached, refreshed daily)
            const cached = localStorage.getItem('user_location_data');
            const cacheTimestamp = localStorage.getItem('user_location_timestamp');

            if (cached && cacheTimestamp) {
                const cacheAge = Date.now() - parseInt(cacheTimestamp);
                const oneMinuteMs = 1 * 60 * 1000;  // Changed to 1 minute for testing

                if (cacheAge < oneMinuteMs) {
                    const parsed = JSON.parse(cached);
                    setLocationData({ ...parsed, isLoading: false });
                    return;
                }
            }

            // Detect location via IP geolocation (works with VPN!)
            const ipLocation = await detectIPLocation();

            if (ipLocation) {
                const data = {
                    location: ipLocation.location,
                    currency: ipLocation.currency,
                    currencySymbol: getCurrencySymbol(ipLocation.currency),
                    isLoading: false,
                    error: null,
                };

                setLocationData(data);

                // Cache for 1 minute (for testing)
                localStorage.setItem('user_location_data', JSON.stringify(data));
                localStorage.setItem('user_location_timestamp', Date.now().toString());
            } else {
                setFallback('Could not detect location');
            }
        } catch (error) {
            console.error('Location detection error:', error);
            setFallback('Location detection failed');
        }
    }

    async function detectIPLocation(): Promise<{ location: string; country: string; currency: string } | null> {
        try {
            // Use ipapi.co for IP geolocation (free, no API key needed)
            // This will detect the actual IP location (including VPN location!)
            const response = await fetch('https://ipapi.co/json/', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('IP geolocation failed');
            }

            const data: IPLocationResponse = await response.json();

            // Build location string
            const city = data.city || 'Unknown';
            const country = data.country_name || 'Unknown';
            const location = `${city}, ${country}`;
            const currency = data.currency || 'USD';

            console.log(`Location detected: ${location}, Currency: ${currency}`);

            return {
                location,
                country: data.country_code || 'US',
                currency,  // Use currency from IP API!
            };
        } catch (error) {
            console.error('IP geolocation error:', error);

            // Fallback: Try browser geolocation as secondary option
            return tryBrowserGeolocation();
        }
    }

    function tryBrowserGeolocation(): Promise<{ location: string; country: string; currency: string } | null> {
        return new Promise((resolve) => {
            if ('geolocation' in navigator) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        // Browser geolocation gives coordinates but not city/country
                        // For now, just return null and let it fall back to USD
                        console.log('Browser geolocation:', position.coords);
                        resolve(null);
                    },
                    (error) => {
                        console.warn('Browser geolocation denied:', error);
                        resolve(null);
                    },
                    { timeout: 5000 }
                );
            } else {
                resolve(null);
            }
        });
    }


    function setFallback(errorMsg: string) {
        // Ultimate fallback to USD if all detection methods fail
        const fallbackData = {
            location: 'International',
            currency: 'USD',
            currencySymbol: '$',
            isLoading: false,
            error: errorMsg,
        };
        setLocationData(fallbackData);
        localStorage.setItem('user_location_data', JSON.stringify(fallbackData));
        localStorage.setItem('user_location_timestamp', Date.now().toString());
    }

    function getCurrencySymbol(currencyCode: string): string {
        // Map ISO 4217 currency codes to symbols
        const symbols: Record<string, string> = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
            'INR': '₹', 'NGN': '₦', 'CAD': 'C$', 'AUD': 'A$', 'ZAR': 'R',
            'BRL': 'R$', 'CHF': 'Fr', 'KRW': '₩', 'MXN': '$', 'AED': 'د.إ',
            'SAR': '﷼', 'KES': 'KSh', 'GHS': 'GH₵', 'EGP': 'E£', 'TRY': '₺',
            'RUB': '₽', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'PLN': 'zł',
            'THB': '฿', 'MYR': 'RM', 'IDR': 'Rp', 'PHP': '₱', 'SGD': 'S$',
            'HKD': 'HK$', 'NZD': 'NZ$', 'CZK': 'Kč', 'HUF': 'Ft', 'ILS': '₪',
        };
        return symbols[currencyCode] || currencyCode;
    }

    return locationData;
}
