import { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { AlertTriangle, Menu, User, Wallet } from 'lucide-react';
import fraudLogo from '@/assets/fraud.png';
import { useAccountBalance, useBankCurrency } from '@/hooks/useData';
import { formatCurrency } from '@/utils/currency';

interface HeaderProps {
  onOpenInternational: () => void;
  onOpenHoover: () => void;
  isAccountFrozen: boolean;
  setIsAccountFrozen: (frozen: boolean) => void;
}

export function Header({ onOpenInternational, onOpenHoover, isAccountFrozen, setIsAccountFrozen }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  
  const { currency: bankCurrency } = useBankCurrency();
  const { accountBalance } = useAccountBalance(userId);

  const BankButtons = () => (
    <div className="flex flex-col md:flex-row gap-2 md:gap-3">
      <Button
        onClick={() => {
          onOpenInternational();
          setMobileMenuOpen(false);
        }}
        className="bg-internationalBank/10 text-internationalBank border border-internationalBank/20 hover:bg-internationalBank/20 transition-all duration-300 font-medium h-9"
      >
        International Banks
      </Button>

      <Button
        onClick={() => {
          onOpenHoover();
          setMobileMenuOpen(false);
        }}
        className="bg-hoover/10 text-hoover border border-hoover/20 hover:bg-hoover/20 transition-all duration-300 font-medium h-9"
      >
        Hoover Bank
      </Button>
    </div>
  );

  const FreezeToggle = () => (
    <div className={`flex items-center gap-3 px-3.5 py-1.5 rounded-full border transition-all duration-500 shadow-lg ${
      isAccountFrozen 
        ? 'bg-destructive/10 border-destructive/30 ring-4 ring-destructive/5' 
        : 'bg-emerald-500/5 border-emerald-500/20'
    }`}>
      <div className="flex items-center gap-2">
        <div className={`h-1.5 w-1.5 rounded-full animate-pulse shadow-[0_0_8px_currentColor] ${
          isAccountFrozen ? 'text-destructive bg-destructive' : 'text-emerald-500 bg-emerald-500'
        }`} />
        <span className={`text-[10px] uppercase tracking-widest font-black transition-colors duration-300 ${
          isAccountFrozen ? 'text-destructive' : 'text-emerald-500/80'
        }`}>
          {isAccountFrozen ? 'Frozen' : 'Active'}
        </span>
      </div>
      <Switch
        checked={isAccountFrozen}
        onCheckedChange={setIsAccountFrozen}
        className="scale-75 data-[state=checked]:bg-destructive transition-all duration-500 ease-in-out hover:scale-90 active:scale-75 shadow-lg"
      />
    </div>
  );

  const UserProfile = () => (
    <div className="flex items-center gap-3 pl-4 border-l border-white/10 ml-2">
      <div className="flex flex-col items-end hidden lg:flex">
        <span className="text-sm font-semibold font-display">John Steward</span>
        <span className="text-[10px] font-mono text-muted-foreground leading-none">{userId}</span>
      </div>
      <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border border-white/10 flex items-center justify-center text-primary/60 shadow-lg">
        <User className="h-5 w-5" />
      </div>
    </div>
  );

  const BalanceDisplay = () => (
    <div className="hidden lg:flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors cursor-default shadow-sm">
      <Wallet className="h-4 w-4 text-primary/60" />
      <span className="text-sm font-bold font-display text-glow-blue">
        {formatCurrency(accountBalance, bankCurrency)}
      </span>
    </div>
  );

  return (
    <header className="fixed top-0 left-0 right-0 z-50 m-2 md:m-4">
      <div className="glass-panel rounded-2xl px-4 md:px-6 py-2.5 md:py-3 max-w-[1400px] mx-auto flex items-center justify-between shadow-2xl relative overflow-hidden">
        {/* Decorative backdrop glow */}
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-blue-500/5 via-transparent to-red-500/5 pointer-events-none" />
        
        <div className="flex items-center gap-4 relative z-10">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center border border-white/10 shadow-inner">
              <img src={fraudLogo} alt="Fraud AI" className="h-6 w-6 object-contain" />
            </div>
            <div className="hidden sm:block leading-tight">
              <h1 className="text-lg font-bold font-display tracking-tight text-white">Fraud AI</h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-medium">Sentinel Core v2.4</p>
            </div>
          </div>
          
          <BalanceDisplay />
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-2 relative z-10">
          <BankButtons />
          <div className="flex items-center gap-4 ml-2">
            <FreezeToggle />
            <UserProfile />
          </div>
        </div>

        {/* Mobile Hamburger Menu */}
        <div className="flex items-center gap-3 md:hidden relative z-10">
          <BalanceDisplay />
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] border-l border-white/10 bg-background/95 backdrop-blur-xl">
              <div className="flex flex-col gap-6 mt-10">
                <div className="flex items-center gap-3 p-4 rounded-2xl bg-white/5 border border-white/10">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary/60">
                    <User className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold font-display">John Steward</h3>
                    <p className="text-xs font-mono text-muted-foreground">{userId}</p>
                  </div>
                </div>
                
                <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10">
                  <p className="text-xs text-muted-foreground mb-1">Total Balance</p>
                  <p className="text-2xl font-bold font-display text-glow-blue">
                    {formatCurrency(accountBalance, bankCurrency)}
                  </p>
                </div>

                <div className="space-y-3">
                  <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground px-2">Internal Banking</p>
                  <div className="flex flex-col gap-2">
                     <BankButtons />
                  </div>
                </div>

                <div className="pt-6 border-t border-white/10">
                   <div className="flex items-center justify-between p-2">
                      <span className="text-sm font-medium">Account Status</span>
                      <FreezeToggle />
                   </div>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
