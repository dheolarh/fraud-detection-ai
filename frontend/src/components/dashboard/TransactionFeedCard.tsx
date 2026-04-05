import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Download, ChevronLeft, ChevronRight, AlertCircle, Filter, X, CalendarIcon, ArrowUpRight, ArrowDownLeft, Search } from 'lucide-react';
import { format } from 'date-fns';
import { DateRange } from 'react-day-picker';
import { cn } from '@/lib/utils';
import { useTransactions } from '@/hooks/useData';
import api from '@/lib/api';
import { toast } from 'sonner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CountryDropdown } from '@/components/ui/CountryDropdown';

export function TransactionFeedCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const [directionFilter, setDirectionFilter] = useState<string>('all');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');
  const [countryFilter, setCountryFilter] = useState<string>('all');
  const [countries, setCountries] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('date-desc');
  const [dateRange, setDateRange] = useState<DateRange | undefined>();
  const [filterOpen, setFilterOpen] = useState(false);

  const direction = directionFilter === 'all' ? undefined : directionFilter;
  const minAmt = minAmount ? parseFloat(minAmount) : undefined;
  const maxAmt = maxAmount ? parseFloat(maxAmount) : undefined;
  const country = countryFilter === 'all' ? undefined : countryFilter;

  const hasSearchOrFilters = Boolean(searchQuery.trim() || dateRange || sortBy !== 'date-desc');
  const fetchLimit = hasSearchOrFilters ? 1000 : 20;
  const pageToFetch = hasSearchOrFilters ? 1 : currentPage;

  const { transactions: allTransactions, loading, error } = useTransactions(userId, pageToFetch, direction, minAmt, maxAmt, country, 10000, fetchLimit);

  const filteredTransactions = useMemo(() => {
    if (!allTransactions) return allTransactions;
    let filtered = allTransactions;

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((t: any) =>
        t.transaction_id?.toString().includes(query) ||
        (t.sender_name && t.sender_name.toLowerCase().includes(query)) ||
        (t.sender_id && t.sender_id.toLowerCase().includes(query)) ||
        (t.receiver_name && t.receiver_name.toLowerCase().includes(query)) ||
        (t.receiver_id && t.receiver_id.toLowerCase().includes(query)) ||
        (t.category && t.category.toLowerCase().includes(query))
      );
    }

    if (dateRange?.from || dateRange?.to) {
      filtered = filtered.filter((t: any) => {
        const txDate = new Date(t.timestamp);
        if (dateRange.from && txDate < dateRange.from) return false;
        if (dateRange.to) {
          const endOfDay = new Date(dateRange.to);
          endOfDay.setHours(23, 59, 59, 999);
          if (txDate > endOfDay) return false;
        }
        return true;
      });
    }

    return filtered;
  }, [allTransactions, searchQuery, dateRange]);

  const transactions = useMemo(() => {
    if (!filteredTransactions) return filteredTransactions;
    const sorted = [...filteredTransactions];

    switch (sortBy) {
      case 'date-desc':
        sorted.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        break;
      case 'date-asc':
        sorted.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        break;
      case 'amount-desc':
        sorted.sort((a, b) => b.amount - a.amount);
        break;
      case 'amount-asc':
        sorted.sort((a, b) => a.amount - b.amount);
        break;
    }

    return sorted;
  }, [filteredTransactions, sortBy]);

  const formatTransactionAmount = (transaction: any) => {
    const displayAmount = transaction.amount_in_bank_currency || transaction.amount;
    const displayCurrency = transaction.bank_currency || transaction.currency_code || transaction.currency || 'GBP';

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: displayCurrency,
    }).format(displayAmount);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold uppercase tracking-wider">
          <div className="h-1 w-1 rounded-full bg-emerald-400 animate-pulse" />
          Completed
        </div>;
      case 'pending':
        return <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold uppercase tracking-wider">
          <div className="h-1 w-1 rounded-full bg-amber-400" />
          Pending
        </div>;
      case 'flagged':
        return <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] font-bold uppercase tracking-wider shadow-[0_0_10px_rgba(239,68,68,0.2)]">
          <div className="h-1 w-1 rounded-full bg-red-400 animate-ping" />
          Flagged
        </div>;
      default:
        return null;
    }
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Sender Name', 'Sender ID', 'Receiver Name', 'Receiver ID', 'Amount', 'Date', 'Location', 'Category', 'Narration', 'Status'];
    const csvContent = [headers.join(','), ...transactions.map(t => [`HOV-${t.transaction_id}`, t.sender_name, t.sender_id, t.receiver_name, t.receiver_id, t.amount, t.timestamp, t.location, t.category, `"${t.narration}"`, t.status].join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'transactions.csv';
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('CSV exported successfully');
  };

  useEffect(() => {
    setCurrentPage(1);
  }, [directionFilter, minAmount, maxAmount, countryFilter, dateRange, sortBy, searchQuery]);

  const clearFilters = () => {
    setDirectionFilter('all');
    setMinAmount('');
    setMaxAmount('');
    setCountryFilter('all');
    setDateRange(undefined);
    setSortBy('date-desc');
    setCurrentPage(1);
  };

  const hasActiveFilters = directionFilter !== 'all' || minAmount || maxAmount || countryFilter !== 'all' || dateRange || sortBy !== 'date-desc';

  if (loading) {
     return (
        <Card className="glass-panel card-shadow-lg col-span-1 md:col-span-2 lg:col-span-4 animate-pulse">
           <CardContent className="h-96 flex items-center justify-center">
              <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground/40">Loading Ledger...</p>
           </CardContent>
        </Card>
     )
  }

  return (
    <Card className="glass-panel card-shadow-lg col-span-1 md:col-span-2 lg:col-span-4 overflow-hidden border-white/5">
      <CardHeader className="pb-3 bg-white/[0.01] border-b border-white/5">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center border border-white/10">
                <ArrowUpRight className="h-4 w-4 text-primary/60" />
              </div>
              <CardTitle className="text-sm font-bold font-display uppercase tracking-widest text-muted-foreground">
                Transaction Ledger
              </CardTitle>
            </div>
            <Button variant="outline" size="sm" onClick={handleExportCSV} className="text-[10px] font-bold uppercase tracking-widest h-8 bg-white/5 border-white/10 hover:bg-white/10 transition-all">
              <Download className="h-3 w-3 mr-1.5" />
              Export .CSV
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative group">
               <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground group-focus-within:text-primary transition-colors" />
               <Input
                type="text"
                placeholder="Search merchant, ID, category..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-[280px] h-9 text-xs pl-8 bg-white/5 border-white/10 focus:bg-white/10 focus:ring-1 focus:ring-primary/20 transition-all rounded-xl"
              />
            </div>

            <Popover open={filterOpen} onOpenChange={setFilterOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="h-9 text-xs font-bold uppercase tracking-widest bg-white/5 border-white/10 hover:bg-white/10 transition-all rounded-xl px-4">
                  <Filter className="h-3 w-3 mr-2" />
                  Filter Suite
                  {hasActiveFilters && (
                    <div className="ml-2 h-4 w-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[8px] font-black">
                      {[directionFilter !== 'all', minAmount || maxAmount, countryFilter !== 'all', dateRange, sortBy !== 'date-desc'].filter(Boolean).length}
                    </div>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 glass-panel border-white/10 shadow-2xl p-4 rounded-2xl" align="start">
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-white/5">
                    <h4 className="font-bold font-display text-xs uppercase tracking-widest">Filter Analytics</h4>
                    {hasActiveFilters && (
                      <Button variant="ghost" size="sm" onClick={clearFilters} className="h-6 text-[10px] uppercase font-black hover:text-red-400">
                        Reset All
                      </Button>
                    )}
                  </div>

                  <div className="space-y-4 pt-2">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Flow Direction</label>
                      <Select value={directionFilter} onValueChange={setDirectionFilter}>
                        <SelectTrigger className="h-9 text-xs bg-white/5 border-white/5 rounded-xl">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="glass-panel border-white/10">
                          <SelectItem value="all">Global Matrix</SelectItem>
                          <SelectItem value="incoming">Inward Flow</SelectItem>
                          <SelectItem value="outgoing">Outward Flow</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Monetary Threshold</label>
                      <div className="flex items-center gap-2">
                        <Input type="number" placeholder="Min" value={minAmount} onChange={(e) => setMinAmount(e.target.value)} className="h-9 text-xs bg-white/5 border-white/5 rounded-xl" />
                        <div className="h-px w-3 bg-white/10" />
                        <Input type="number" placeholder="Max" value={maxAmount} onChange={(e) => setMaxAmount(e.target.value)} className="h-9 text-xs bg-white/5 border-white/5 rounded-xl" />
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Temporal Window</label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" className={cn("w-full justify-start text-left font-medium h-9 text-xs bg-white/5 border-white/5 rounded-xl", !dateRange && "text-muted-foreground")}>
                            <CalendarIcon className="mr-2 h-3.5 w-3.5 text-primary/60" />
                            {dateRange?.from ? (
                              dateRange.to ? <>{format(dateRange.from, "MMM dd")} - {format(dateRange.to, "MMM dd, y")}</> : format(dateRange.from, "MMM dd, y")
                            ) : <span>Select Range</span>}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0 glass-panel border-white/10" align="start">
                          <Calendar initialFocus mode="range" defaultMonth={dateRange?.from} selected={dateRange} onSelect={setDateRange} numberOfMonths={1} className="rounded-xl border-none" />
                        </PopoverContent>
                      </Popover>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Ordering Strategy</label>
                      <Select value={sortBy} onValueChange={setSortBy}>
                        <SelectTrigger className="h-9 text-xs bg-white/5 border-white/5 rounded-xl">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="glass-panel border-white/10">
                          <SelectItem value="date-desc">Newest First</SelectItem>
                          <SelectItem value="date-asc">Oldest First</SelectItem>
                          <SelectItem value="amount-desc">Highest Value</SelectItem>
                          <SelectItem value="amount-asc">Lowest Value</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-[400px] overflow-y-auto scrollbar-thin">
          <Table className="relative">
            <TableHeader className="sticky top-0 bg-background/80 backdrop-blur-md z-20">
              <TableRow className="border-b border-white/5 hover:bg-transparent">
                <TableHead className="text-[10px] font-black uppercase tracking-widest h-12 pl-6">Identifier</TableHead>
                <TableHead className="text-[10px] font-black uppercase tracking-widest h-12">Merchant / Party</TableHead>
                <TableHead className="text-[10px] font-black uppercase tracking-widest h-12 text-right pr-6">Value / Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions && transactions.map((transaction: any) => (
                <TableRow key={transaction.transaction_id} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors group">
                  <TableCell className="pl-6 py-4">
                     <div className="flex flex-col gap-0.5">
                        <span className="text-xs font-bold font-display text-white">HOV-{transaction.transaction_id}</span>
                        <span className="text-[10px] font-mono text-muted-foreground/60">{format(new Date(transaction.timestamp), 'MMM dd, HH:mm')}</span>
                     </div>
                  </TableCell>
                  <TableCell className="py-4">
                     <div className="flex items-center gap-3">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center border border-white/5 ${transaction.transaction_flow === 'incoming' ? 'bg-emerald-500/5 text-emerald-400' : 'bg-red-500/5 text-red-400'}`}>
                           {transaction.transaction_flow === 'incoming' ? <ArrowDownLeft className="h-4 w-4" /> : <ArrowUpRight className="h-4 w-4" />}
                        </div>
                        <div className="flex flex-col gap-0.5">
                           <span className="text-xs font-bold text-gray-200 truncate max-w-[200px]">{transaction.receiver_name || transaction.sender_name || 'System Settlement'}</span>
                           <div className="flex items-center gap-2">
                              <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50">{transaction.category}</span>
                              <div className="w-1 h-1 rounded-full bg-white/10" />
                              <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50">{transaction.location}</span>
                           </div>
                        </div>
                     </div>
                  </TableCell>
                  <TableCell className="text-right pr-6 py-4">
                     <div className="flex flex-col items-end gap-1.5">
                        <span className={`text-sm font-bold font-display ${transaction.transaction_flow === 'incoming' ? 'text-emerald-400' : 'text-white'}`}>
                           {transaction.transaction_flow === 'incoming' ? '+' : '-'}{formatTransactionAmount(transaction)}
                        </span>
                        {getStatusBadge(transaction.status || 'completed')}
                     </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Improved Pagination Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/5 bg-white/[0.01]">
          <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
            {hasSearchOrFilters && transactions ? `${transactions.length} Entires Synced` : `Registry: Page ${currentPage}`}
          </span>
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1 || hasSearchOrFilters}
              className="h-8 w-8 p-0 bg-white/5 border-white/5 hover:bg-white/10 disabled:opacity-20 rounded-lg"
            >
              <ChevronLeft className="h-3 w-3" />
            </Button>
            <div className="h-8 px-3 rounded-lg bg-white/5 border border-white/5 flex items-center justify-center">
               <span className="text-xs font-bold text-primary">{currentPage}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => p + 1)}
              disabled={!transactions || transactions.length < 20 || hasSearchOrFilters}
              className="h-8 w-8 p-0 bg-white/5 border-white/5 hover:bg-white/10 disabled:opacity-20 rounded-lg"
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
