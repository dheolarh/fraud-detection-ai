import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bell, Lock, Eye, EyeOff, AlertTriangle, ShieldCheck, User, LogOut, MapPin, Loader2, Wallet } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { TransactionCategory, HooverNotification } from '@/types/transaction';
import hooverLogo from '@/assets/hoover.png';
import { useUserLocation } from '@/hooks/useUserLocation';
import { formatCurrency } from '@/utils/currency';
import { CountryDropdown } from '@/components/ui/CountryDropdown';
import { AccountGenerator } from '@/components/ui/AccountGenerator';
import { useAccountBalance } from '@/hooks/useData';
import { cn } from '@/lib/utils';

const categories: TransactionCategory[] = ['Shopping', 'Bills', 'Transfer', 'Salary', 'Entertainment', 'Food', 'Travel', 'Healthcare', 'Other'];

interface HooverBankModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  notifications?: HooverNotification[];
  onSendTransaction: (data: any) => void;
  isAccountFrozen: boolean;
}

type TabType = 'send' | 'notifications';

export function HooverBankModal({ open, onOpenChange, notifications = [], onSendTransaction, isAccountFrozen }: HooverBankModalProps) {
  const HOOVER_USER_ID = 'HOV-2426-1226';
  const HOOVER_USER_NAME = 'John Steward';
  const BANK_CURRENCY = 'GBP';
  const BANK_COUNTRY = 'United Kingdom';

  const { accountBalance } = useAccountBalance(HOOVER_USER_ID);
  const { location: userLocation, isLoading: locationLoading } = useUserLocation();

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [activeTab, setActiveTab] = useState<TabType>('send');

  const [destinationCountry, setDestinationCountry] = useState('');
  const [destinationCurrency, setDestinationCurrency] = useState('USD');
  const [receiverName, setReceiverName] = useState('');
  const [receiverId, setReceiverId] = useState('');
  const [amount, setAmount] = useState<number>(0);
  const [category, setCategory] = useState<TransactionCategory>('Transfer');
  const [narration, setNarration] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const response = await fetch('http://localhost:8001/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, device_id: `browser_${Date.now()}`, location: userLocation }),
      });
      if (response.ok) {
        const data = await response.json();
        setIsLoggedIn(true);
        toast.success('Access Granted', { description: `Welcome back, ${HOOVER_USER_NAME}` });
        localStorage.setItem('hoover_token', data.token);
      } else {
        const error = await response.json();
        setLoginError(error.detail || 'Access Denied: Invalid Credentials');
        toast.error('Authentication Failed');
      }
    } catch (error) { setLoginError('Matrix Connection Offline'); toast.error('Connection error'); }
  };

  const handleLogout = () => {
    setIsLoggedIn(false); setUsername(''); setPassword(''); setLoginError(''); setActiveTab('send');
    toast.info('Session Terminated');
  };

  const handleSendTransaction = (e: React.FormEvent) => {
    e.preventDefault();
    if (!destinationCountry) { toast.error('Select Destination'); return; }
    if (!receiverName || !receiverId) { toast.error('Generate Receiver'); return; }
    if (amount <= 0) { toast.error('Invalid Amount'); return; }

    const transactionData = {
      sender_id: HOOVER_USER_ID, 
      sender_name: HOOVER_USER_NAME, 
      receiver_id: receiverId, 
      receiver_name: receiverName,
      amount, 
      currency: BANK_CURRENCY, 
      category: category,
      location: destinationCountry, 
      narration: narration || `Transfer to ${receiverName}`,
      transaction_flow: 'outgoing'
    };
    onSendTransaction(transactionData);
    setAmount(0); setNarration('');
  };

  const handleClose = (openState: boolean) => {
    if (!openState) { setIsLoggedIn(false); setUsername(''); setPassword(''); setLoginError(''); setActiveTab('send'); }
    onOpenChange(openState);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md max-h-[90vh] glass-panel border-white/10 p-0 overflow-hidden shadow-2xl flex flex-col">
        <div className="p-6 bg-white/[0.02] border-b border-white/5">
           <DialogHeader>
              <div className="flex items-center justify-between">
                 <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-xl bg-hoover/10 flex items-center justify-center border border-hoover/20 shadow-inner">
                       <img src={hooverLogo} alt="Hoover Bank" className="h-7 w-auto object-contain" />
                    </div>
                    <div>
                       <DialogTitle className="text-xl font-bold font-display uppercase tracking-widest text-white">Hoover Bank</DialogTitle>
                       <DialogDescription className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 pt-1">
                          {BANK_COUNTRY} • {BANK_CURRENCY} CORE
                       </DialogDescription>
                    </div>
                 </div>
                 {isLoggedIn && (
                   <Button variant="ghost" size="icon" onClick={handleLogout} className="h-8 w-8 rounded-full hover:bg-red-500/10 hover:text-red-400 transition-all">
                      <LogOut className="h-4 w-4" />
                   </Button>
                 )}
              </div>
           </DialogHeader>
        </div>

        {!isLoggedIn ? (
          <form onSubmit={handleLogin} className="px-8 py-6 space-y-5">
             <div className="flex flex-col items-center gap-3">
                <div className="relative">
                   <div className="absolute inset-0 bg-hoover/20 blur-2xl rounded-full" />
                   <div className="relative h-16 w-16 rounded-3xl bg-hoover/10 border border-hoover/20 flex items-center justify-center shadow-inner">
                      <Lock className="h-6 w-6 text-hoover" />
                   </div>
                </div>
                <div className="text-center">
                   <h3 className="text-lg font-bold font-display text-white uppercase tracking-wider">Vault Access</h3>
                   <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/50">Authorize session</p>
                </div>
             </div>
 
             <div className="space-y-3.5">
                <div className="space-y-1.5">
                   <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Registry Username</Label>
                   <Input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="john_steward" className="h-10 bg-white/5 border-white/5 focus:bg-white/10 rounded-xl font-bold transition-all text-xs text-white" />
                </div>
                <div className="space-y-1.5">
                   <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Encryption Key</Label>
                   <div className="relative group">
                      <Input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="h-10 bg-white/5 border-white/5 focus:bg-white/10 rounded-xl font-bold transition-all pr-10 text-xs text-white" />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-2.5 text-muted-foreground hover:text-white transition-colors">
                         {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </button>
                   </div>
                </div>
             </div>
 
             {loginError && <p className="text-[10px] font-black uppercase tracking-widest text-center text-red-400 bg-red-400/5 py-2 rounded-lg border border-red-400/10">{loginError}</p>}
 
             <Button type="submit" className="w-full h-11 bg-hoover hover:bg-hoover text-white text-[11px] font-black uppercase tracking-widest rounded-xl shadow-lg transition-all">
                Authorize Session
             </Button>
 
             <div className="p-3 rounded-2xl bg-white/[0.02] border border-dashed border-white/10 text-center">
                <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40 italic">Demo: john_steward / password</p>
             </div>
          </form>
        ) : (
          <div className="relative flex flex-col flex-1 min-h-0 overflow-hidden">
             {/* Floating User Details Card */}
             <div className="mx-6 mt-4 mb-2 p-5 rounded-2xl bg-white/[0.03] border border-white/10 space-y-5 shadow-inner flex-shrink-0">
                <div className="flex items-center justify-between">
                   <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-primary/10 border border-white/5 flex items-center justify-center p-0.5">
                         <div className="h-full w-full rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                            <User className="h-5 w-5 text-primary/60" />
                         </div>
                      </div>
                      <div>
                         <p className="text-sm font-bold font-display text-white">{HOOVER_USER_NAME}</p>
                         <p className="text-[10px] font-mono text-muted-foreground/60">{HOOVER_USER_ID}</p>
                      </div>
                   </div>
                   <div className="text-right">
                      <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/50 mb-0.5">Balance</p>
                      <p className="text-lg font-bold font-display text-glow-blue">{formatCurrency(accountBalance, BANK_CURRENCY)}</p>
                   </div>
                </div>

                <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-muted-foreground/40 px-1 border-t border-white/5 pt-4">
                   <div className="flex items-center gap-2">
                      <MapPin className="h-3 w-3" />
                      {locationLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : userLocation}
                   </div>
                   <div className="flex items-center gap-2 text-emerald-500/80">
                      <ShieldCheck className="h-3 w-3" />
                      SECURED NODE
                   </div>
                </div>

                <div className="flex gap-2 p-1 bg-black/20 border border-white/5 rounded-xl">
                   <button onClick={() => setActiveTab('send')} className={`flex-1 flex items-center justify-center gap-2 h-9 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'send' ? 'bg-primary text-black shadow-lg' : 'text-muted-foreground hover:bg-white/5'}`}>
                      <Send className="h-3.5 w-3.5" />
                      Dispatch
                   </button>
                   <button onClick={() => setActiveTab('notifications')} className={`flex-1 flex items-center justify-center gap-2 h-9 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all relative ${activeTab === 'notifications' ? 'bg-primary text-black shadow-lg' : 'text-muted-foreground hover:bg-white/5'}`}>
                      <Bell className="h-3.5 w-3.5" />
                      Log Feed
                      {notifications.length > 0 && <span className="absolute -top-2 -right-1.5 h-5 min-w-[20px] px-1.5 rounded-full bg-red-600 text-white text-[9px] flex items-center justify-center border-2 border-background font-black shadow-lg">{notifications.length}</span>}
                   </button>
                </div>
             </div>

             <div 
               style={{ height: '420px', overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column' }}
               className="flex-1 px-10 pb-12 scrollbar-none scrollbar-hide rounded-b-2xl mb-6"
             >
                <div className={cn("space-y-7 pt-5", isAccountFrozen && "opacity-20 pointer-events-none")}>
                   {activeTab === 'send' ? (
                      <form onSubmit={handleSendTransaction} className="space-y-6">
                         <div className="space-y-2">
                            <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Target Territory</Label>
                            <CountryDropdown value={destinationCountry} onChange={(country, currency) => { setDestinationCountry(country); setDestinationCurrency(currency); }} placeholder="Select Destination" className="h-11 bg-white/5 border-white/5 rounded-xl font-bold" />
                         </div>
                         <div className="grid grid-cols-1 gap-4">
                            <AccountGenerator type="name" prefix="EXT" value={receiverName} onChange={setReceiverName} label="Target Party" />
                            <AccountGenerator type="account" prefix="EXT" value={receiverId} onChange={setReceiverId} label="Target Registry ID" />
                         </div>
                         <div className="space-y-2">
                            <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Remit Quantum ({BANK_CURRENCY})</Label>
                            <div className="relative">
                               <Wallet className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground" />
                               <Input type="number" step="0.01" placeholder="0.00" value={amount || ''} onChange={(e) => setAmount(parseFloat(e.target.value) || 0)} className="h-11 pl-10 bg-white/5 border-white/5 rounded-xl font-bold font-display text-sm text-white" />
                            </div>
                         </div>
                         <div className="space-y-2">
                            <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Classification</Label>
                            <Select value={category} onValueChange={(value) => setCategory(value as TransactionCategory)}>
                               <SelectTrigger className="h-11 bg-white/5 border-white/5 rounded-xl font-bold">
                                  <SelectValue />
                               </SelectTrigger>
                               <SelectContent className="glass-panel border-white/10">
                                  {categories.map((cat) => <SelectItem key={cat} value={cat}>{cat}</SelectItem>)}
                                </SelectContent>
                            </Select>
                         </div>
                         <Input value={narration} onChange={(e) => setNarration(e.target.value)} placeholder="Audit narration (optional)" className="h-11 bg-white/5 border-white/5 rounded-xl text-xs font-bold text-white mb-2" />
                         <Button type="submit" className="w-full h-12 bg-hoover hover:bg-hoover text-white text-[11px] font-black uppercase tracking-widest rounded-xl shadow-lg mt-4">
                            Authorize Disbursement
                         </Button>
                      </form>
                   ) : (
                      <div className="space-y-4">
                         {notifications.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-20 opacity-20">
                               <Bell className="h-10 w-10 mb-4" />
                               <p className="text-[10px] font-black uppercase tracking-widest">Steady State: No Feed</p>
                            </div>
                         ) : (
                            notifications.map((not) => (
                               <div key={not.id} className={`p-4 rounded-2xl border transition-all ${not.read ? 'bg-white/[0.02] border-white/5' : 'bg-hoover/5 border-hoover/20 shadow-[0_0_15px_rgba(255,255,255,0.02)]'}`}>
                                  <div className="flex items-center justify-between mb-3">
                                     <div className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest border border-white/10 ${not.read ? 'text-muted-foreground' : 'text-hoover'}`}>{not.transaction.category}</div>
                                     <span className="text-[10px] font-bold text-muted-foreground/40 italic">{format(new Date(not.receivedAt), 'HH:mm')}</span>
                                  </div>
                                  <p className="text-lg font-bold font-display text-white mb-1">+{formatCurrency(not.transaction.amount, BANK_CURRENCY)}</p>
                                  <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60">{not.transaction.senderId} • {not.transaction.location}</p>
                               </div>
                            ))
                         )}
                      </div>
                   )}
                </div>
             </div>

             {isAccountFrozen && (
               <div className="absolute inset-0 z-[100] bg-background/95 backdrop-blur-xl flex items-center justify-center p-8 animate-in fade-in zoom-in duration-500">
                  <div className="glass-panel border-red-500/30 p-8 rounded-[2rem] shadow-2xl max-w-sm w-full space-y-8 flex flex-col items-center">
                     <div className="relative">
                        <div className="absolute inset-0 bg-red-500/20 blur-3xl animate-pulse rounded-full" />
                        <div className="relative h-20 w-20 rounded-3xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                           <AlertTriangle className="h-10 w-10 text-red-500" />
                        </div>
                     </div>

                     <div className="text-center space-y-2">
                        <h3 className="text-xl font-bold font-display text-red-500 uppercase tracking-widest">Registry Locked</h3>
                        <p className="text-xs font-bold text-muted-foreground/70 leading-relaxed uppercase tracking-widest px-4">Account restricted due to high-risk behavioral signal.</p>
                     </div>

                     <div className="w-full bg-white/[0.02] border border-white/5 rounded-2xl p-5 space-y-4">
                        <div className="space-y-1">
                           <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Secure Liaison</p>
                           <p className="text-sm font-bold font-mono text-white">support@hooverbank.com</p>
                        </div>
                        <div className="space-y-1">
                           <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40">Voice Verification</p>
                           <p className="text-sm font-bold font-mono text-white">+1 (800) 555-0199</p>
                        </div>
                     </div>

                     <Button onClick={() => onOpenChange(false)} className="w-full h-12 bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-black uppercase tracking-widest rounded-xl transition-all">Terminate Connection</Button>
                  </div>
               </div>
             )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
