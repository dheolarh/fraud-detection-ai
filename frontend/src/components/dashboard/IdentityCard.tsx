import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';
import { DateRange } from 'react-day-picker';
import { cn } from '@/lib/utils';
import { useAccountBalance, useBankCurrency } from '@/hooks/useData';
import { formatCurrency } from '@/utils/currency';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

export function IdentityCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  // Dynamically fetch bank's currency from banking backend
  const { currency: bankCurrency } = useBankCurrency();

  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: new Date(2023, 0, 1),  // Jan 1, 2023 (month 0 = January)
    to: new Date(2026, 0, 31),   // Jan 31, 2026
  });

  // Convert dates to ISO format for API
  const fromDate = dateRange?.from ? dateRange.from.toISOString().split('T')[0] : undefined;
  const toDate = dateRange?.to ? dateRange.to.toISOString().split('T')[0] : undefined;

  const { accountBalance, totalIn, totalOut, loading, error } = useAccountBalance(userId, fromDate, toDate);


  return (
    <Card className="card-shadow">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          Identity
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && (
          <p className="text-sm text-muted-foreground">Loading account data...</p>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load account data: {error}
            </AlertDescription>
          </Alert>
        )}

        {!loading && !error && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">User ID</p>
                <p className="text-sm font-medium font-mono">{userId}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Account Balance</p>
                <p className="text-sm font-semibold text-foreground">
                  {formatCurrency(accountBalance, bankCurrency)}
                </p>
              </div>
            </div>

            <div>
              <p className="text-xs text-muted-foreground mb-2">Date Range</p>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal text-xs",
                      !dateRange && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-3 w-3" />
                    {dateRange?.from ? (
                      dateRange.to ? (
                        <>
                          {format(dateRange.from, "LLL dd, y")} - {format(dateRange.to, "LLL dd, y")}
                        </>
                      ) : (
                        format(dateRange.from, "LLL dd, y")
                      )
                    ) : (
                      <span>Pick a date range</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    initialFocus
                    mode="range"
                    defaultMonth={dateRange?.from}
                    selected={dateRange}
                    onSelect={setDateRange}
                    numberOfMonths={2}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="grid grid-cols-1 gap-4 pt-2">
              <div className="bg-success/10 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-muted-foreground">Total In</span>
                </div>
                <p className="text-lg font-semibold text-success">
                  {formatCurrency(totalIn, bankCurrency)}
                </p>
              </div>
              <div className="bg-destructive/10 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-muted-foreground">Total Out</span>
                </div>
                <p className="text-lg font-semibold text-destructive">
                  {formatCurrency(totalOut, bankCurrency)}
                </p>
              </div>
            </div>

          </>
        )}
      </CardContent>
    </Card>
  );
}
