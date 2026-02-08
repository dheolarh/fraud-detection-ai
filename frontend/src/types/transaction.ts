export interface Transaction {
  id: string;
  amount: number;
  currency: string;  // ISO 4217 currency code (NGN, USD, GBP, etc.)
  date: string;
  location: string;
  category: TransactionCategory;
  narration: string;
  senderBank: string;
  receiverBank: string;
  senderId: string;
  receiverId: string;
  status: 'completed' | 'pending' | 'flagged';
}

export type TransactionCategory =
  | 'Shopping'
  | 'Bills'
  | 'Transfer'
  | 'Salary'
  | 'Entertainment'
  | 'Food'
  | 'Travel'
  | 'Healthcare'
  | 'Other';

export interface AnomalyTransaction extends Transaction {
  anomalyType: string;
  riskScore: number;
  description: string;
}

export interface Case {
  id: string;
  description: string;
  linkedTransactionId: string;
  status: 'open' | 'investigating' | 'resolved';
  createdAt: string;
  priority: 'low' | 'medium' | 'high';
}

export interface UserIdentity {
  userId: string;
  accountBalance: number;
  totalIn: number;
  totalOut: number;
}

export interface GeoData {
  country: string;
  volume: number;
  count: number;
  incoming: number;
  outgoing: number;
}

export interface HooverNotification {
  id: string;
  transaction: Transaction;
  receivedAt: string;
  read: boolean;
}

export interface BankFormData {
  bankName: string;
  senderId: string;
  location: string;
  amount: number;
  category: TransactionCategory;
}