import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bell, Lock, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { TransactionCategory, HooverNotification } from '@/types/transaction';
import hooverLogo from '@/assets/hoover.png';
import { useUserLocation } from '@/hooks/useUserLocation';
import { formatCurrency } from '@/utils/currency';
import { CountryDropdown } from '@/components/ui/CountryDropdown';
import { AccountGenerator } from '@/components/ui/AccountGenerator';
import { useAccountBalance } from '@/hooks/useData';

// Transaction categories
const categories: TransactionCategory[] = ['Shopping', 'Bills', 'Transfer', 'Salary', 'Entertainment', 'Food', 'Travel', 'Healthcare', 'Other'];

interface HooverBankModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  notifications?: HooverNotification[];
  onSendTransaction: (data: any) => void;
  isAccountFrozen: boolean;
}

// Mock credentials
const VALID_CREDENTIALS = {
  username: 'hoover_admin',
  password: 'hoover123'
};

type TabType = 'send' | 'notifications';

export function HooverBankModal({ open, onOpenChange, notifications = [], onSendTransaction, isAccountFrozen }: HooverBankModalProps) {
  // Fixed HooverBank user identity
  const HOOVER_USER_ID = 'HOV-2426-1226';
  const HOOVER_USER_NAME = 'John Steward';

  // Fixed bank details (UK Bank)
  const BANK_CURRENCY = 'GBP';
  const BANK_COUNTRY = 'United Kingdom';

  const { accountBalance } = useAccountBalance(HOOVER_USER_ID);

  // Get user's current location from IP/VPN (for transaction tracking only)
  const { location: userLocation, isLoading: locationLoading } = useUserLocation();

  // Login state
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [activeTab, setActiveTab] = useState<TabType>('send');

  // Transaction details
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
      // Call banking backend API for authentication
      const response = await fetch('http://localhost:8001/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          password,
          device_id: `browser_${Date.now()}`, // Generate device ID
          location: userLocation // Send user's detected location
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setIsLoggedIn(true);
        toast.success('Welcome to Hoover Bank');
        // Store token if needed
        localStorage.setItem('hoover_token', data.token);
      } else {
        const error = await response.json();
        setLoginError(error.detail || 'Invalid username or password');
        toast.error('Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError('Connection error. Please try again.');
      toast.error('Connection error');
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUsername('');
    setPassword('');
    setLoginError('');
    setActiveTab('send');
    toast.info('Logged out of Hoover Bank');
  };

  const handleSendTransaction = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!destinationCountry) {
      toast.error('Please select a destination country');
      return;
    }
    if (!receiverName || !receiverId) {
      toast.error('Please generate receiver details');
      return;
    }
    if (amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    // Create transaction data
    const transactionData = {
      sender_id: HOOVER_USER_ID,
      sender_name: HOOVER_USER_NAME,
      receiver_id: receiverId,
      receiver_name: receiverName,
      amount: amount,
      currency: BANK_CURRENCY,  // Always GBP for UK bank
      category: category,
      location: destinationCountry,  // Destination country (where money is going)
      narration: narration || `Transfer to ${receiverName}`,
      transaction_flow: 'outgoing'  // Outgoing from HooverBank
    };

    onSendTransaction(transactionData);

    toast.success('Transaction sent successfully', {
      description: `${formatCurrency(amount, BANK_CURRENCY)} to ${receiverName}`,
    });

    // Reset form
    setAmount(0);
    setNarration('');
    // Keep destination and receiver details (they might be locked)
  };

  const handleClose = (openState: boolean) => {
    if (!openState) {
      // Auto logout when closing modal
      setIsLoggedIn(false);
      setUsername('');
      setPassword('');
      setLoginError('');
      setActiveTab('send');
    }
    onOpenChange(openState);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 mb-2">
              <img src={hooverLogo} alt="Hoover Bank" className="h-10 w-auto" />
              <div>
                <div className="flex items-center gap-2">
                  <DialogTitle className="text-hoover">Hoover Bank</DialogTitle>
                  <span className="text-xs text-muted-foreground">
                    {BANK_COUNTRY} • {BANK_CURRENCY}
                  </span>
                </div>
                {isLoggedIn ? (
                  <DialogDescription className="text-xs space-y-1">
                    <div>
                      <span className="font-mono font-medium">{HOOVER_USER_ID}</span>
                      <span className="mx-1">•</span>
                      <span className="font-medium">{HOOVER_USER_NAME}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        {locationLoading ? 'Detecting location...' : `Current Location: ${userLocation}`}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 font-semibold">
                      Balance: {formatCurrency(accountBalance, BANK_CURRENCY)}
                    </div>
                  </DialogDescription>
                ) : (
                  <DialogDescription>Login to access your account</DialogDescription>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        {!isLoggedIn ? (
          <form onSubmit={handleLogin} className="space-y-4 py-4">
            <div className="flex items-center justify-center mb-6">
              <div className="bg-hoover/10 p-4 rounded-full">
                <Lock className="h-8 w-8 text-hoover" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm">Username</Label>
              <Input
                id="username"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {loginError && (
              <p className="text-sm text-destructive text-center">{loginError}</p>
            )}

            <Button type="submit" className="w-full bg-hoover hover:bg-hoover-secondary text-primary-foreground">
              <Lock className="h-4 w-4 mr-2" />
              Login to Hoover Bank
            </Button>

            <p className="text-xs text-muted-foreground text-center pt-2">
              Demo credentials: hoover_admin / hoover123
            </p>
          </form>
        ) : (
          <div className="relative space-y-4">
            {/* Disable interaction when account is frozen */}
            <div className={isAccountFrozen && isLoggedIn ? 'pointer-events-none' : ''}>
              {/* Tab Buttons */}
              <div className="flex gap-2 p-1 bg-muted rounded-lg">
                <button
                  type="button"
                  onClick={() => setActiveTab('send')}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'send'
                    ? 'bg-background text-hoover shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                  <Send className="h-4 w-4" />
                  Send Transaction
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('notifications')}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'notifications'
                    ? 'bg-background text-hoover shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                  <Bell className="h-4 w-4" />
                  Notifications
                  {notifications.length > 0 && (
                    <Badge variant="secondary" className="text-xs ml-1">{notifications.length}</Badge>
                  )}
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === 'send' ? (
                <ScrollArea className="h-[400px] pr-4">
                  <form onSubmit={handleSendTransaction} className="space-y-4 mx-4 mt-4">
                    {/* Destination Country */}
                    <div className="space-y-2">
                      <Label className="text-sm">Destination Country</Label>
                      <CountryDropdown
                        value={destinationCountry}
                        onChange={(country, currency) => {
                          setDestinationCountry(country);
                          setDestinationCurrency(currency);
                        }}
                        placeholder="Select destination country"
                      />
                    </div>

                    {/* Receiver Name */}
                    <AccountGenerator
                      type="name"
                      prefix="EXT"
                      value={receiverName}
                      onChange={setReceiverName}
                      label="Receiver Name"
                    />

                    {/* Receiver ID */}
                    <AccountGenerator
                      type="account"
                      prefix="EXT"
                      value={receiverId}
                      onChange={setReceiverId}
                      label="Receiver Account ID"
                    />

                    {/* Amount */}
                    <div className="space-y-2">
                      <Label htmlFor="amount" className="text-sm">Amount ({BANK_CURRENCY})</Label>
                      <Input
                        id="amount"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        value={amount || ''}
                        onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                      />
                      <p className="text-xs text-muted-foreground">
                        Available: {formatCurrency(accountBalance, BANK_CURRENCY)}
                      </p>
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

                    <Button type="submit" className="w-full bg-hoover hover:bg-hoover-secondary text-primary-foreground">
                      <Send className="h-4 w-4 mr-2" />
                      Send Transaction
                    </Button>
                  </form>
                </ScrollArea>
              ) : (
                <ScrollArea className="h-[320px] scrollbar-thin mt-4">
                  {notifications.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                      <Bell className="h-8 w-8 mb-2 opacity-50" />
                      <p className="text-sm">No incoming transactions</p>
                      <p className="text-xs">Transactions from International Bank will appear here</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {notifications.map((notification) => (
                        <div
                          key={notification.id}
                          className={`p-3 rounded-lg border ${notification.read ? 'bg-muted/50' : 'bg-hoover/5 border-hoover/20'
                            }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant="outline" className="text-xs">
                              {notification.transaction.category}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {format(new Date(notification.receivedAt), 'HH:mm')}
                            </span>
                          </div>
                          <p className="text-sm font-medium">
                            {formatCurrency(notification.transaction.amount, BANK_CURRENCY)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            From: {notification.transaction.senderId} • {notification.transaction.location}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              )}
            </div>

            {/* Frozen Account Overlay */}
            {isAccountFrozen && isLoggedIn && (
              <div className="absolute inset-0 flex items-center justify-center z-50 bg-background/80">
                <div className="bg-card border-2 border-destructive rounded-lg p-4 shadow-2xl max-w-xs mx-4">
                  <div className="flex flex-col items-center text-center space-y-3">
                    <div className="bg-destructive/10 p-3 rounded-full">
                      <AlertTriangle className="h-8 w-8 text-destructive" />
                    </div>

                    <div className="space-y-1">
                      <h3 className="text-base font-bold text-destructive">Account Frozen</h3>
                      <p className="text-xs text-muted-foreground">
                        Your account has been frozen. Please contact support for assistance.
                      </p>
                    </div>

                    <div className="w-full space-y-2 text-left bg-muted/50 p-3 rounded-lg">
                      <div className="space-y-1">
                        <p className="text-xs font-semibold text-foreground">Support Email</p>
                        <p className="text-sm text-hoover font-mono">support@hooverbank.com</p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-xs font-semibold text-foreground">Support Number</p>
                        <p className="text-sm text-hoover font-mono">+1 (800) 555-0199</p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-xs font-semibold text-foreground">Support Address</p>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          123 Banking Street<br />
                          Financial District<br />
                          New York, NY 10005
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}