import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Globe, Wallet, User as UserIcon, ArrowRightLeft, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { TransactionCategory } from '@/types/transaction';
import internationalBankLogo from '@/assets/internationalBank.png';
import { CountryDropdown } from '@/components/ui/CountryDropdown';
import { AccountGenerator } from '@/components/ui/AccountGenerator';
import { formatCurrency } from '@/utils/currency';

const categories: TransactionCategory[] = ['Shopping', 'Bills', 'Transfer', 'Salary', 'Entertainment', 'Food', 'Travel', 'Healthcare', 'Other'];

interface InternationalBankModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSendTransaction: (data: any) => void;
}

export function InternationalBankModal({ open, onOpenChange, onSendTransaction }: InternationalBankModalProps) {
  const HOOVER_USER_ID = 'HOV-2426-1226';
  const HOOVER_USER_NAME = 'John Steward';
  const HOOVER_CURRENCY = 'GBP';

  const [senderCountry, setSenderCountry] = useState('');
  const [senderCurrency, setSenderCurrency] = useState('USD');
  const [senderName, setSenderName] = useState('');
  const [senderId, setSenderId] = useState('');
  const [amount, setAmount] = useState<number>(0);
  const [category, setCategory] = useState<TransactionCategory>('Transfer');
  const [narration, setNarration] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!senderCountry) { toast.error('Please select sender country'); return; }
    if (!senderName || !senderId) { toast.error('Please generate sender details'); return; }
    if (amount <= 0) { toast.error('Please enter a valid amount'); return; }

    try {
      let convertedAmount = amount;
      const finalCurrency = HOOVER_CURRENCY;
      if (senderCurrency !== HOOVER_CURRENCY) {
        const { convertCurrency } = await import('@/lib/exchangeRate');
        try {
          convertedAmount = await convertCurrency(amount, senderCurrency, HOOVER_CURRENCY);
        } catch (error) {
          toast.error(`Failed to convert ${senderCurrency} to ${HOOVER_CURRENCY}`);
          return;
        }
      }

      const transactionData = {
        sender_id: senderId,
        sender_name: senderName,
        receiver_id: HOOVER_USER_ID,
        receiver_name: HOOVER_USER_NAME,
        amount: convertedAmount,
        currency: finalCurrency,
        category: category,
        location: senderCountry,
        narration: `${amount.toLocaleString()} ${senderCurrency} from ${senderName}`,
        transaction_flow: 'incoming'
      };

      await onSendTransaction(transactionData);
      toast.success('Transfer Authorized', { description: `${formatCurrency(amount, senderCurrency)} incoming to ${HOOVER_USER_NAME}` });
      setAmount(0);
      setNarration('');
      onOpenChange(false);
    } catch (error) { toast.error('Transfer Failed'); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md glass-panel border-white/10 p-0 overflow-hidden shadow-2xl">
        <div className="p-6 bg-white/[0.02] border-b border-white/5">
           <DialogHeader>
              <div className="flex items-center gap-4 mb-2">
                 <div className="h-12 w-12 rounded-xl bg-internationalBank/10 flex items-center justify-center border border-internationalBank/20 shadow-inner">
                    <Globe className="h-6 w-6 text-internationalBank" />
                 </div>
                 <div>
                    <DialogTitle className="text-xl font-bold font-display uppercase tracking-widest text-white">Global Gateway</DialogTitle>
                    <DialogDescription className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 pt-1">External Inward Remittance</DialogDescription>
                 </div>
              </div>
           </DialogHeader>
        </div>

        <ScrollArea className="h-[450px] scrollbar-thin">
           <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/5 space-y-4">
                 <div className="flex items-center justify-between border-b border-white/5 pb-3">
                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Target Identity</span>
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                 </div>
                 <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center border border-white/5">
                       <UserIcon className="h-5 w-5 text-primary/60" />
                    </div>
                    <div>
                       <p className="text-sm font-bold font-display text-white">{HOOVER_USER_NAME}</p>
                       <p className="text-[10px] font-mono text-muted-foreground">{HOOVER_USER_ID} • Hoover Bank (UK)</p>
                    </div>
                 </div>
              </div>

              <div className="space-y-4 pt-2">
                 <div className="space-y-2">
                    <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Origin Node</Label>
                    <CountryDropdown
                      value={senderCountry}
                      onChange={(country, currency) => { setSenderCountry(country); setSenderCurrency(currency); }}
                      placeholder="Select Sending Territory"
                      className="h-11 bg-white/5 border-white/5 rounded-xl font-bold transition-all"
                    />
                 </div>

                 <div className="grid grid-cols-1 gap-4">
                    <AccountGenerator type="name" prefix="INT" value={senderName} onChange={setSenderName} label="Originator Designation" />
                    <AccountGenerator type="account" prefix="INT" value={senderId} onChange={setSenderId} label="Originating Registry ID" />
                 </div>

                 <div className="space-y-2">
                    <Label htmlFor="amount" className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Quantum Value {senderCurrency ? `(${senderCurrency})` : ''}</Label>
                    <div className="relative group">
                       <Wallet className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                       <Input id="amount" type="number" step="0.01" placeholder="0.00" value={amount || ''} onChange={(e) => setAmount(parseFloat(e.target.value) || 0)} className="h-11 pl-10 bg-white/5 border-white/5 focus:bg-white/10 rounded-xl font-bold font-display text-sm transition-all" />
                    </div>
                    {amount > 0 && senderCurrency !== HOOVER_CURRENCY && (
                      <div className="flex items-center gap-2 px-2 py-1 rounded-lg bg-primary/5 border border-primary/10">
                         <ArrowRightLeft className="h-3 w-3 text-primary/60" />
                         <p className="text-[10px] font-bold text-primary/80 italic uppercase">Conversion logic applied to {HOOVER_CURRENCY}</p>
                      </div>
                    )}
                 </div>

                 <div className="space-y-2">
                    <Label htmlFor="category" className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">System Category</Label>
                    <Select value={category} onValueChange={(value) => setCategory(value as TransactionCategory)}>
                       <SelectTrigger className="h-11 bg-white/5 border-white/5 rounded-xl font-bold">
                          <SelectValue placeholder="Select classification" />
                       </SelectTrigger>
                       <SelectContent className="glass-panel border-white/10">
                          {categories.map((cat) => <SelectItem key={cat} value={cat}>{cat}</SelectItem>)}
                       </SelectContent>
                    </Select>
                 </div>

                 <div className="space-y-2">
                    <Label htmlFor="narration" className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Remittance Narrative</Label>
                    <Input id="narration" placeholder="Internal audit narration..." value={narration} onChange={(e) => setNarration(e.target.value)} maxLength={100} className="h-11 bg-white/5 border-white/5 focus:bg-white/10 rounded-xl font-bold text-xs transition-all" />
                 </div>
              </div>

              <div className="pt-6 border-t border-white/5 flex gap-3">
                 <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} className="flex-1 h-12 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-white/5 transition-all">Discard</Button>
                 <Button type="submit" className="flex-2 h-12 bg-internationalBank hover:bg-internationalBank text-white text-[10px] font-black uppercase tracking-widest rounded-xl shadow-lg transition-all px-8">
                    <Send className="h-4 w-4 mr-2" />
                    Authorize Transfer
                 </Button>
              </div>
           </form>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}