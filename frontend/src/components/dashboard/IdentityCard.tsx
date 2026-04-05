import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon, TrendingUp, TrendingDown, Clock, CreditCard } from 'lucide-react';
import { format } from 'date-fns';
import { DateRange } from 'react-day-picker';
import { cn } from '@/lib/utils';
import { useAccountBalance, useBankCurrency } from '@/hooks/useData';
import { formatCurrency } from '@/utils/currency';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

export function IdentityCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const { currency: bankCurrency } = useBankCurrency();

  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: new Date(2021, 0, 1),
    to: new Date(2026, 11, 31),
  });

  const fromDate = dateRange?.from ? dateRange.from.toISOString().split('T')[0] : undefined;
  const toDate = dateRange?.to ? dateRange.to.toISOString().split('T')[0] : undefined;

  const { accountBalance, totalIn, totalOut, loading, error } = useAccountBalance(userId, fromDate, toDate);

  return (
    <Card className="glass-panel card-shadow-lg overflow-hidden border-white/5 bg-white/[0.02]">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold font-display uppercase tracking-widest text-muted-foreground flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            Wallet Summary
          </CardTitle>
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {loading && (
          <div className="flex flex-col gap-4 animate-pulse">
            <div className="h-4 bg-white/5 rounded w-1/2" />
            <div className="h-8 bg-white/5 rounded w-full" />
            <div className="h-20 bg-white/5 rounded w-full" />
          </div>
        )}

        {error && (
          <Alert variant="destructive" className="bg-destructive/10 border-destructive/20 text-destructive text-xs">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {!loading && !error && (
          <>
            <div className="space-y-1">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Total Liquidity</p>
              <p className="text-3xl font-bold font-display tracking-tight text-white text-glow-blue">
                {formatCurrency(accountBalance, bankCurrency)}
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Date Scope</p>
                <Clock className="h-3 w-3 text-muted-foreground" />
              </div>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-medium text-xs bg-white/5 border-white/10 hover:bg-white/10 transition-all rounded-xl h-10",
                      !dateRange && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-3.5 w-3.5 text-primary/60" />
                    {dateRange?.from ? (
                      dateRange.to ? (
                        <>
                          {format(dateRange.from, "MMM dd, y")} - {format(dateRange.to, "MMM dd, y")}
                        </>
                      ) : (
                        format(dateRange.from, "MMM dd, y")
                      )
                    ) : (
                      <span>Select Window</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0 bg-background/95 backdrop-blur-xl border-white/10 shadow-2xl" align="start">
                  <Calendar
                    initialFocus
                    mode="range"
                    defaultMonth={dateRange?.from}
                    selected={dateRange}
                    onSelect={setDateRange}
                    numberOfMonths={1}
                    className="rounded-xl border-none"
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="grid grid-cols-1 gap-3 pt-2">
              <div className="relative group">
                <div className="absolute inset-0 bg-emerald-500/10 blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative glass-panel rounded-2xl p-4 border-emerald-500/10 hover:border-emerald-500/20 transition-all">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-emerald-400/80 uppercase tracking-widest font-bold">Total Inflow</span>
                    <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                  </div>
                  <p className="text-xl font-bold font-display text-emerald-400">
                    {formatCurrency(totalIn, bankCurrency)}
                  </p>
                </div>
              </div>

              <div className="relative group">
                <div className="absolute inset-0 bg-red-500/10 blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative glass-panel rounded-2xl p-4 border-red-500/10 hover:border-red-500/20 transition-all">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-red-400/80 uppercase tracking-widest font-bold">Total Outflow</span>
                    <TrendingDown className="h-3.5 w-3.5 text-red-400" />
                  </div>
                  <p className="text-xl font-bold font-display text-red-400">
                    {formatCurrency(totalOut, bankCurrency)}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
