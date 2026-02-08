import { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { AlertTriangle, Menu } from 'lucide-react';
import fraudLogo from '@/assets/fraud.png';

interface HeaderProps {
  onOpenInternational: () => void;
  onOpenHoover: () => void;
  isAccountFrozen: boolean;
  setIsAccountFrozen: (frozen: boolean) => void;
}

export function Header({ onOpenInternational, onOpenHoover, isAccountFrozen, setIsAccountFrozen }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const BankButtons = () => (
    <>
      <Button
        onClick={() => {
          onOpenInternational();
          setMobileMenuOpen(false);
        }}
        className="bg-internationalBank text-primary-foreground hover:bg-internationalBank/90 transition-colors"
      >
        International Banks
      </Button>

      <Button
        onClick={() => {
          onOpenHoover();
          setMobileMenuOpen(false);
        }}
        className="bg-hoover text-primary-foreground hover:bg-hoover/90 transition-colors"
      >
        Hoover Bank
      </Button>
    </>
  );

  const FreezeToggle = () => (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        {isAccountFrozen && (
          <AlertTriangle className="h-4 w-4 text-warning" />
        )}
        <span className={`text-sm font-medium ${isAccountFrozen ? 'text-warning' : 'text-muted-foreground'}`}>
          {isAccountFrozen ? 'Account Frozen' : 'Freeze Account'}
        </span>
      </div>
      <Switch
        checked={isAccountFrozen}
        onCheckedChange={setIsAccountFrozen}
        className="data-[state=checked]:bg-destructive"
      />
    </div>
  );

  return (
    <header className="fixed top-0 left-0 right-0 z-50 m-3 md:m-4 bg-card card-shadow border border-border rounded-xl px-4 md:px-6 py-3 md:py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src={fraudLogo} alt="Fraud AI" className="h-8 md:h-10 w-auto" />
          <div>
            <h1 className="text-lg md:text-xl font-semibold text-foreground">Fraud AI</h1>
            <p className="text-xs text-muted-foreground hidden sm:block">Real-time Fraud Detection</p>
          </div>
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-4">
          <BankButtons />
          <div className="pl-4 border-l border-border">
            <FreezeToggle />
          </div>
        </div>

        {/* Mobile Hamburger Menu */}
        <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[280px]">
            <div className="flex flex-col gap-4 mt-8">
              <BankButtons />
              <div className="pt-4 border-t border-border">
                <FreezeToggle />
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
