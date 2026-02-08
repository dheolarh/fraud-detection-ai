import { useState } from 'react';
import { Header } from '@/components/dashboard/Header';
import { IdentityCard } from '@/components/dashboard/IdentityCard';
import { ActivityScoreCard } from '@/components/dashboard/ActivityScoreCard';
import { TransactionFeedCard } from '@/components/dashboard/TransactionFeedCard';
import { AnomaliesCard } from '@/components/dashboard/AnomaliesCard';
import { GeoAnalyticsCard } from '@/components/dashboard/GeoAnalyticsCard';
import { CaseManagementCard } from '@/components/dashboard/CaseManagementCard';
import { InternationalBankModal } from '@/components/modals/InternationalBanksModal';
import { HooverBankModal } from '@/components/modals/HooverBankModal';
import { BankFormData, HooverNotification } from '@/types/transaction';
import api from '@/lib/api';
import { toast } from 'sonner';
import { useTransactions } from '@/hooks/useData';

export default function Dashboard() {
  const [internationalBankModalOpen, setInternationalModalOpen] = useState(false);
  const [hooverModalOpen, setHooverModalOpen] = useState(false);
  const [isAccountFrozen, setIsAccountFrozen] = useState(false);

  // Fetch recent transactions for Hoover notifications
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const { transactions } = useTransactions(userId, 1); // Get recent transactions

  // Convert ALL transactions to notifications (both sent and received)
  const hooverNotifications: HooverNotification[] = transactions
    .filter(tx => tx.sender_id === userId || tx.receiver_id === userId) // Both sent and received
    .slice(0, 15) //
    .map((tx, index) => ({
      id: tx.transaction_id.toString(),
      transaction: {
        id: tx.transaction_id.toString(),
        senderId: tx.sender_id,
        receiverId: tx.receiver_id,
        amount: tx.amount_in_bank_currency || tx.amount,  // Use converted amount
        currency: tx.bank_currency || tx.currency || 'GBP',  // Use bank currency
        date: tx.timestamp,
        category: tx.category,
        location: tx.location,
        narration: tx.narration || '',
        senderBank: 'Unknown',
        receiverBank: 'Unknown',
        status: tx.status === 'blocked' ? 'flagged' : 'completed' as const
      },
      receivedAt: tx.timestamp,
      read: index >= 5 // Mark first 5 as unread
    }));

  const handleInternationalSend = async (data: any) => {
    try {
      // Pass through the complete data from the modal
      await api.sendTransaction(data);

      // Success - modal will show toast
    } catch (error: any) {
      toast.error('Transaction Failed', {
        description: error.message || 'Transaction could not be completed'
      });
      console.error('Transaction error:', error);
      throw error;  // Re-throw so modal knows it failed
    }
  };

  const handleHooverSend = async (data: any) => {
    try {
      // Pass through the complete data from the modal
      await api.sendTransaction(data);

      toast.success('Transaction Sent', {
        description: `Sent successfully`
      });

    } catch (error: any) {
      if (error.message.includes('blocked') || error.message.includes('frozen')) {
        toast.error('Transaction Blocked', {
          description: error.message
        });
        setIsAccountFrozen(true);
      } else {
        toast.error('Transaction Failed', {
          description: error.message || 'Transaction could not be completed'
        });
      }
      console.error('Transaction error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header
        onOpenInternational={() => setInternationalModalOpen(true)}
        onOpenHoover={() => setHooverModalOpen(true)}
        isAccountFrozen={isAccountFrozen}
        setIsAccountFrozen={setIsAccountFrozen}
      />

      {/* Spacer for fixed header */}
      <div className="h-20 md:h-24" />

      <main className="container mx-auto p-4 md:p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {/* Row 1: Identity, Activity Score, Geo Analytics */}
          <IdentityCard />
          <ActivityScoreCard />
          <GeoAnalyticsCard />

          {/* Row 2: Real-time Feed (full width) */}
          <TransactionFeedCard />

          {/* Row 3: Anomalies (full width) */}
          <AnomaliesCard />

          {/* Row 4: Case Management (full width) */}
          <CaseManagementCard />
        </div>
      </main>

      <InternationalBankModal
        open={internationalBankModalOpen}
        onOpenChange={setInternationalModalOpen}
        onSendTransaction={handleInternationalSend}
      />

      <HooverBankModal
        open={hooverModalOpen}
        onOpenChange={setHooverModalOpen}
        notifications={hooverNotifications}
        onSendTransaction={handleHooverSend}
        isAccountFrozen={isAccountFrozen}
      />
    </div>
  );
}
