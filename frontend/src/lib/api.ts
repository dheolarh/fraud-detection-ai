/**
 * API Service
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface LoginCredentials {
    username: string;
    password: string;
}

interface LoginResponse {
    access_token?: string;  // Fraud backend format
    token?: string;          // Banking backend format
    token_type: string;
    user_id: string;
    username: string;
    account_balance?: number;  // Banking backend includes this
    is_frozen?: boolean;       // Banking backend includes this
}

interface TransactionRequest {
    sender_id: string;
    receiver_id: string;
    amount: number;
    category: string;
    location: string;
    narration: string;
}

class ApiService {
    private token: string | null = null;

    constructor() {
        this.token = localStorage.getItem('auth_token');
    }

    private getHeaders(): HeadersInit {
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            // Handle Pydantic validation errors
            if (error.detail && Array.isArray(error.detail)) {
                const messages = error.detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join(', ');
                throw new Error(messages);
            }
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    }

    async login(credentials: LoginCredentials): Promise<LoginResponse> {
        // Call banking backend for authentication (port 8001)
        // Banking backend logs all login attempts to hooverbank.auth_logs
        const BANKING_API_URL = 'http://localhost:8001';

        const response = await fetch(`${BANKING_API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials),
        });

        const data = await this.handleResponse<LoginResponse>(response);
        this.token = data.access_token || data.token; // Handle both token formats
        localStorage.setItem('auth_token', this.token);
        localStorage.setItem('user_id', data.user_id);
        localStorage.setItem('username', data.username);

        return data;
    }

    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('username');
    }

    async getAccountBalance(userId: string, fromDate?: string, toDate?: string): Promise<{ account_balance: number; total_in: number; total_out: number }> {
        let url = `${API_BASE_URL}/api/account/balance/${userId}`;
        const params = new URLSearchParams();
        if (fromDate) params.append('from_date', fromDate);
        if (toDate) params.append('to_date', toDate);
        if (params.toString()) url += `?${params.toString()}`;

        const response = await fetch(url, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<{ account_balance: number; total_in: number; total_out: number }>(response);
    }

    async getRecentTransactions(
        userId: string,
        limit: number = 20,
        page: number = 1,
        direction?: string,
        minAmount?: number,
        maxAmount?: number,
        country?: string
    ): Promise<any[]> {
        let url = `${API_BASE_URL}/api/transaction/recent/${userId}?limit=${limit}&page=${page}`;
        if (direction) url += `&direction=${direction}`;
        if (minAmount !== undefined) url += `&min_amount=${minAmount}`;
        if (maxAmount !== undefined) url += `&max_amount=${maxAmount}`;
        if (country) url += `&country=${encodeURIComponent(country)}`;

        const response = await fetch(url, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any[]>(response);
    }

    async sendTransaction(transaction: TransactionRequest): Promise<any> {
        const BANKING_API_URL = 'http://localhost:8001';
        const response = await fetch(`${BANKING_API_URL}/api/transactions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(transaction),
        });
        return this.handleResponse<any>(response);
    }

    async getFraudAlerts(userId: string): Promise<any[]> {
        const response = await fetch(`${API_BASE_URL}/api/fraud/alerts/${userId}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any[]>(response);
    }

    async getFraudStats(userId: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/fraud/stats/${userId}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any>(response);
    }

    async getTransactionById(transactionId: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/transaction/${transactionId}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any>(response);
    }

    async getGeoAnalytics(userId: string, limit: number = 10): Promise<any[]> {
        const response = await fetch(`${API_BASE_URL}/api/transaction/geo-analytics/${userId}?limit=${limit}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any[]>(response);
    }

    async getSuspicionLevel(userId: string): Promise<{ suspicion_level: number; description: string; flagged_count: number; average_risk_score: number }> {
        const response = await fetch(`${API_BASE_URL}/api/fraud/suspicion-level/${userId}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<{ suspicion_level: number; description: string; flagged_count: number; average_risk_score: number }>(response);
    }

    async getBankLocation(): Promise<{ country: string; currency: string; bank_name: string }> {
        const BANKING_API_URL = 'http://localhost:8001';
        const response = await fetch(`${BANKING_API_URL}/api/bank/location`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<{ country: string; currency: string; bank_name: string }>(response);
    }

    async getCountries(userId: string): Promise<string[]> {
        const response = await fetch(`${API_BASE_URL}/api/transaction/countries/${userId}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<string[]>(response);
    }

    async getSuspiciousLogins(userId: string): Promise<any[]> {
        const response = await fetch(`${API_BASE_URL}/api/suspicious-logins/${userId}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any[]>(response);
    }

    // Case Management APIs
    async getAvailableTransactions(userId: string): Promise<any[]> {
        const response = await fetch(`${API_BASE_URL}/api/cases/available-transactions/${userId}`, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any[]>(response);
    }

    async createCase(caseData: {
        title: string;
        description: string;
        priority: string;
        affected_transactions: Array<{ id: string; type: string }>;
    }): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/cases`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(caseData),
        });
        return this.handleResponse<any>(response);
    }

    async getCases(status?: string): Promise<any[]> {
        const url = status ? `${API_BASE_URL}/api/cases?status=${status}` : `${API_BASE_URL}/api/cases`;
        const response = await fetch(url, {
            headers: this.getHeaders(),
        });
        return this.handleResponse<any[]>(response);
    }

    async updateCase(caseId: string, caseData: {
        title: string;
        description: string;
        priority: string;
        affected_transactions: Array<{ id: string; type: string }>;
    }): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/cases/${caseId}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(caseData),
        });
        return this.handleResponse<any>(response);
    }

    async resolveCase(caseId: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/cases/${caseId}/resolve`, {
            method: 'PUT',
            headers: this.getHeaders(),
        });
        return this.handleResponse<any>(response);
    }

    async reopenCase(caseId: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api/cases/${caseId}/reopen`, {
            method: 'PUT',
            headers: this.getHeaders(),
        });
        return this.handleResponse<any>(response);
    }
}

export const api = new ApiService();
export default api;
