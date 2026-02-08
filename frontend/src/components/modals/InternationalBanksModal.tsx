import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send } from 'lucide-react';
import { toast } from 'sonner';
import { BankFormData, TransactionCategory } from '@/types/transaction';
import internationalBankLogo from '@/assets/internationalBank.png';
import { CountryDropdown } from '@/components/ui/CountryDropdown';
import { AccountGenerator } from '@/components/ui/AccountGenerator';
import { formatCurrency } from '@/utils/currency';

// Transaction categories
const categories: TransactionCategory[] = ['Shopping', 'Bills', 'Transfer', 'Salary', 'Entertainment', 'Food', 'Travel', 'Healthcare', 'Other'];

interface InternationalBankModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSendTransaction: (data: any) => void;
}

export function InternationalBankModal({ open, onOpenChange, onSendTransaction }: InternationalBankModalProps) {
  // Fixed HooverBank receiver (where money goes TO)
  const HOOVER_USER_ID = 'HOV-2426-1226';
  const HOOVER_USER_NAME = 'John Steward';
  const HOOVER_CURRENCY = 'GBP';

  // Sender details (random generated)
  const [senderCountry, setSenderCountry] = useState('');
  const [senderCurrency, setSenderCurrency] = useState('USD');
  const [senderName, setSenderName] = useState('');
  const [senderId, setSenderId] = useState('');

  const [amount, setAmount] = useState<number>(0);
  const [category, setCategory] = useState<TransactionCategory>('Transfer');
  const [narration, setNarration] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!senderCountry) {
      toast.error('Please select sender country');
      return;
    }
    if (!senderName || !senderId) {
      toast.error('Please generate sender details');
      return;
    }
    if (amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      // EXCHANGE RATE BRIDGE: Convert to GBP before sending to HooverBank
      let convertedAmount = amount;
      let finalCurrency = HOOVER_CURRENCY; // GBP

      if (senderCurrency !== HOOVER_CURRENCY) {
        // Import exchange rate service
        const { convertCurrency } = await import('@/lib/exchangeRate');

        try {
          // Use live API to convert (supports ALL world currencies)
          convertedAmount = await convertCurrency(amount, senderCurrency, HOOVER_CURRENCY);
          console.log(`Exchange Rate Bridge (Live API): ${amount.toLocaleString()} ${senderCurrency} → ${convertedAmount.toFixed(2)} ${HOOVER_CURRENCY}`);
        } catch (error) {
          console.error('Exchange rate conversion failed:', error);
          toast.error(`Failed to convert ${senderCurrency} to ${HOOVER_CURRENCY}`);
          return;
        }
      }

      // Create transaction data with CONVERTED amount
      const transactionData = {
        sender_id: senderId,
        sender_name: senderName,
        receiver_id: HOOVER_USER_ID,
        receiver_name: HOOVER_USER_NAME,
        amount: convertedAmount,  // Send converted amount
        currency: finalCurrency,  // Send GBP
        category: category,
        location: senderCountry,  // Sender's country
        narration: `${amount.toLocaleString()} ${senderCurrency} from ${senderName}`,  // Show original in narration
        transaction_flow: 'incoming'  // Incoming to HooverBank
      };

      // Send transaction
      await onSendTransaction(transactionData);

      toast.success('Transaction sent successfully', {
        description: `${formatCurrency(amount, senderCurrency)} sent to ${HOOVER_USER_NAME}`,
      });

      // Reset form
      setAmount(0);
      setNarration('');
      // Keep sender details (they might be locked)

      onOpenChange(false);
    } catch (error) {
      console.error('Transaction error:', error);
      toast.error('Failed to send transaction');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <img src={internationalBankLogo} alt="International Bank" className="h-10 w-auto" />
            <div>
              <DialogTitle className="text-internationalBank">International Banks</DialogTitle>
              <DialogDescription className="text-xs">
                Send money to HooverBank
              </DialogDescription>
            </div>
          </div>

          {/* Receiver Info Card (Fixed - HooverBank User) */}
          <div className="bg-muted/30 rounded-lg p-2 mt-2">
            <p className="text-xs font-semibold text-muted-foreground mb-1">Sending To:</p>
            <div className="flex items-center justify-between text-xs">
              <div>
                <span className="font-mono font-medium">{HOOVER_USER_ID}</span>
                <span className="mx-1">•</span>
                <span className="font-medium">{HOOVER_USER_NAME}</span>
              </div>
              <span className="text-muted-foreground">HooverBank (UK)</span>
            </div>
          </div>
        </DialogHeader>

        <ScrollArea className="h-[350px] pr-4">
          <form onSubmit={handleSubmit} className="space-y-4 mx-4 mt-4">
            {/* Sender Country */}
            <div className="space-y-2">
              <Label className="text-sm">Sender Country</Label>
              <CountryDropdown
                value={senderCountry}
                onChange={(country, currency) => {
                  setSenderCountry(country);
                  setSenderCurrency(currency);
                }}
                placeholder="Select sender's country"
              />
            </div>

            {/* Sender Name */}
            <AccountGenerator
              type="name"
              prefix="INT"
              value={senderName}
              onChange={setSenderName}
              label="Sender Name"
            />

            {/* Sender ID */}
            <AccountGenerator
              type="account"
              prefix="INT"
              value={senderId}
              onChange={setSenderId}
              label="Sender Account ID"
            />

            {/* Amount */}
            <div className="space-y-2">
              <Label htmlFor="amount" className="text-sm">
                Amount {senderCurrency ? `(${senderCurrency})` : ''}
              </Label>
              <Input
                id="amount"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={amount || ''}
                onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
              />
              {amount > 0 && senderCurrency !== HOOVER_CURRENCY && (
                <p className="text-xs text-muted-foreground">
                  Will be converted to {HOOVER_CURRENCY} for HooverBank
                </p>
              )}
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category" className="text-sm">Category</Label>
              <Select
                value={category}
                onValueChange={(value) => setCategory(value as TransactionCategory)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Narration (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="narration" className="text-sm">Narration (Optional)</Label>
              <Input
                id="narration"
                placeholder="Enter transaction description"
                value={narration}
                onChange={(e) => setNarration(e.target.value)}
                maxLength={100}
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-internationalBank hover:bg-internationalBank-secondary text-primary-foreground"
            >
              <Send className="h-4 w-4 mr-2" />
              Send to Hoover Bank
            </Button>
          </form>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}