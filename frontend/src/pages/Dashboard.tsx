import { useState } from 'react';
import { Header } from '@/components/dashboard/Header';
import { IdentityCard } from '@/components/dashboard/IdentityCard';
import { ActivityScoreCard } from '@/components/dashboard/ActivityScoreCard';
import { RiskTrendCard } from '@/components/dashboard/RiskTrendCard';
import { TransactionFeedCard } from '@/components/dashboard/TransactionFeedCard';
import { AnomaliesCard } from '@/components/dashboard/AnomaliesCard';
import { GeoAnalyticsCard } from '@/components/dashboard/GeoAnalyticsCard';
import { CaseManagementCard } from '@/components/dashboard/CaseManagementCard';
import { InternationalBankModal } from '@/components/modals/InternationalBanksModal';
import { HooverBankModal } from '@/components/modals/HooverBankModal';
import { HooverNotification } from '@/types/transaction';
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
    .filter(tx => tx.sender_id === userId || tx.receiver_id === userId)
    .slice(0, 15)
    .map((tx, index) => ({
      id: tx.transaction_id.toString(),
      transaction: {
        id: tx.transaction_id.toString(),
        senderId: tx.sender_id,
        receiverId: tx.receiver_id,
        amount: tx.amount_in_bank_currency || tx.amount,
        currency: tx.bank_currency || tx.currency || 'GBP',
        date: tx.timestamp,
        category: tx.category,
        location: tx.location,
        narration: tx.narration || '',
        senderBank: 'Unknown',
        receiverBank: 'Unknown',
        status: tx.status === 'blocked' ? 'flagged' : 'completed' as const
      },
      receivedAt: tx.timestamp,
      read: index >= 5 
    }));

  const handleInternationalSend = async (data: any) => {
    try {
      await api.sendTransaction(data);
    } catch (error: any) {
      toast.error('Transaction Failed', {
        description: error.message || 'Transaction could not be completed'
      });
      console.error('Transaction error:', error);
      throw error;
    }
  };

  const handleHooverSend = async (data: any) => {
    try {
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
    <div className="min-h-screen bg-[#0A0A0B] relative selection:bg-primary/20 selection:text-primary overflow-x-hidden">
      {/* Background ambient glows */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/5 blur-[120px] rounded-full" />
        <div className="absolute top-[20%] right-[-5%] w-[30%] h-[30%] bg-red-500/5 blur-[100px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[20%] w-[50%] h-[50%] bg-blue-600/5 blur-[150px] rounded-full" />
      </div>

      <Header
        onOpenInternational={() => setInternationalModalOpen(true)}
        onOpenHoover={() => setHooverModalOpen(true)}
        isAccountFrozen={isAccountFrozen}
        setIsAccountFrozen={setIsAccountFrozen}
      />

      {/* Spacer for fixed header */}
      <div className="h-24 md:h-28" />

      <main className="container mx-auto px-4 md:px-6 pb-20 relative z-10 max-w-[1440px]">
        {/* Bento Grid Top Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 lg:gap-8 mb-8">
           <div className="lg:col-span-2">
              <IdentityCard />
           </div>
           <ActivityScoreCard />
           <RiskTrendCard />
           <GeoAnalyticsCard />
        </div>

        {/* Full-Width Components Column */}
        <div className="space-y-6 md:space-y-10">
          <TransactionFeedCard />
          <AnomaliesCard />
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
