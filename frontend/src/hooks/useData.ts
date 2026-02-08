/**
 * Custom React Hooks for Data Fetching
 */

import { useState, useEffect } from 'react';
import api from '@/lib/api';

export function useTransactions(
    userId: string,
    page: number = 1,
    direction?: string,
    minAmount?: number,
    maxAmount?: number,
    country?: string,
    pollInterval: number = 10000,
    limit: number = 20
) {
    const [transactions, setTransactions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const getRecentTransactions = async (): Promise<any[]> => {
        return api.getRecentTransactions(userId, limit, page, direction, minAmount, maxAmount, country);
    };

    useEffect(() => {
        const fetchTransactions = async () => {
            try {
                const data = await getRecentTransactions();
                setTransactions(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch transactions');
            } finally {
                setLoading(false);
            }
        };

        fetchTransactions();
        const interval = setInterval(fetchTransactions, pollInterval);

        return () => clearInterval(interval);
    }, [userId, page, direction, minAmount, maxAmount, country, pollInterval, limit]);

    return { transactions, loading, error };
}

export function useAccountBalance(userId: string, fromDate?: string, toDate?: string, pollInterval: number = 5000) {
    const [accountBalance, setAccountBalance] = useState<number>(0);
    const [totalIn, setTotalIn] = useState<number>(0);
    const [totalOut, setTotalOut] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchBalance = async () => {
            try {
                const data = await api.getAccountBalance(userId, fromDate, toDate);
                setAccountBalance(data.account_balance);
                setTotalIn(data.total_in);
                setTotalOut(data.total_out);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch balance');
            } finally {
                setLoading(false);
            }
        };

        fetchBalance();
        const interval = setInterval(fetchBalance, pollInterval);

        return () => clearInterval(interval);
    }, [userId, fromDate, toDate, pollInterval]);

    return { accountBalance, totalIn, totalOut, loading, error };
}

export function useFraudAlerts(userId: string, pollInterval: number = 5000) {
    const [alerts, setAlerts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                const data = await api.getFraudAlerts(userId);
                setAlerts(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
            } finally {
                setLoading(false);
            }
        };

        fetchAlerts();
        const interval = setInterval(fetchAlerts, pollInterval);

        return () => clearInterval(interval);
    }, [userId, pollInterval]);

    return { alerts, loading, error };
}

export function useFraudStats(userId: string, pollInterval: number = 30000) {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await api.getFraudStats(userId);
                setStats(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch stats');
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, pollInterval);

        return () => clearInterval(interval);
    }, [userId, pollInterval]);

    return { stats, loading, error };
}

export function useGeoAnalytics(userId: string, pollInterval: number = 30000) {
    const [geoData, setGeoData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchGeoAnalytics = async () => {
            try {
                const data = await api.getGeoAnalytics(userId, 10);
                setGeoData(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch geo analytics');
            } finally {
                setLoading(false);
            }
        };

        fetchGeoAnalytics();
        const interval = setInterval(fetchGeoAnalytics, pollInterval);

        return () => clearInterval(interval);
    }, [userId, pollInterval]);

    return { geoData, loading, error };
}

export function useSuspicionLevel(userId: string, pollInterval: number = 5000) {
    const [suspicionLevel, setSuspicionLevel] = useState<number>(0);
    const [description, setDescription] = useState<string>('No suspicious activity');
    const [flaggedCount, setFlaggedCount] = useState<number>(0);
    const [averageRiskScore, setAverageRiskScore] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchSuspicionLevel = async () => {
            try {
                // Use proper fraud detection endpoint (uses fraud_config thresholds)
                const data = await api.getSuspicionLevel(userId);

                setSuspicionLevel(data.suspicion_level);
                setDescription(data.description);
                setFlaggedCount(data.flagged_count);
                // Convert from 0-1 scale to 0-100 scale for display
                setAverageRiskScore(data.average_risk_score * 100);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch suspicion level');
            } finally {
                setLoading(false);
            }
        };

        fetchSuspicionLevel();
        const interval = setInterval(fetchSuspicionLevel, pollInterval);

        return () => clearInterval(interval);
    }, [userId, pollInterval]);

    return { suspicionLevel, description, flaggedCount, averageRiskScore, loading, error };
}

export function useBankCurrency() {
    const [currency, setCurrency] = useState<string>('GBP'); // Default to GBP
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchBankCurrency = async () => {
            try {
                const data = await api.getBankLocation();
                setCurrency(data.currency);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch bank currency');
                // Keep default GBP on error
            } finally {
                setLoading(false);
            }
        };

        fetchBankCurrency();
    }, []);

    return { currency, loading, error };
}

export function useCombinedAnomalies(userId: string, pollInterval: number = 5000) {
    const [anomalies, setAnomalies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAnomalies = async () => {
            try {
                // Fetch both fraud alerts, suspicious logins, and resolved cases
                const [fraudAlerts, suspiciousLogins, cases] = await Promise.all([
                    api.getFraudAlerts(userId),
                    api.getSuspiciousLogins(userId),
                    api.getCases('resolved')
                ]);

                // Helper function to parse timestamps
                const parseTimestamp = (timestamp: string | undefined): number => {
                    if (!timestamp) return 0;

                    try {
                        // Try parsing as ISO format first
                        let date = new Date(timestamp);

                        // If invalid, try parsing auth log format: "December 27, 2025 at 15:25 UTC"
                        if (isNaN(date.getTime())) {
                            const cleaned = timestamp.replace(' UTC', '').replace(' at ', ' ');
                            date = new Date(cleaned);
                        }

                        return isNaN(date.getTime()) ? 0 : date.getTime();
                    } catch {
                        return 0;
                    }
                };

                // Create a set of anomaly IDs that are in resolved cases
                const resolvedAnomalyIds = new Set<string>();
                cases.forEach((caseItem: any) => {
                    const affectedTransactions = caseItem.affected_transactions || [];
                    affectedTransactions.forEach((txn: any) => {
                        resolvedAnomalyIds.add(txn.id);
                    });
                });

                // Filter out anomalies that are in resolved cases
                const filteredFraudAlerts = fraudAlerts.filter(
                    (alert: any) => !resolvedAnomalyIds.has(alert.transaction_id)
                );

                const filteredSuspiciousLogins = suspiciousLogins.filter(
                    (login: any) => !resolvedAnomalyIds.has(login.id)
                );

                // Merge and sort by timestamp (most recent first)
                const combined = [...filteredFraudAlerts, ...filteredSuspiciousLogins].sort((a, b) => {
                    const dateA = parseTimestamp(a.timestamp);
                    const dateB = parseTimestamp(b.timestamp);
                    return dateB - dateA;
                });

                setAnomalies(combined);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch anomalies');
            } finally {
                setLoading(false);
            }
        };

        fetchAnomalies();
        const interval = setInterval(fetchAnomalies, pollInterval);

        return () => clearInterval(interval);
    }, [userId, pollInterval]);

    return { anomalies, loading, error };
}

