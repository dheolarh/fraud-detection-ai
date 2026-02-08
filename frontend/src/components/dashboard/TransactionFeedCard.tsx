import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Download, ChevronLeft, ChevronRight, AlertCircle, Filter, X, CalendarIcon } from 'lucide-react';
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

  // Use server-side filtering and pagination
  const direction = directionFilter === 'all' ? undefined : directionFilter;
  const minAmt = minAmount ? parseFloat(minAmount) : undefined;
  const maxAmt = maxAmount ? parseFloat(maxAmount) : undefined;
  const country = countryFilter === 'all' ? undefined : countryFilter;

  // Fetch more transactions when searching or filtering to enable global search
  // Otherwise use pagination with 20 per page
  const hasSearchOrFilters = Boolean(searchQuery.trim() || dateRange || sortBy !== 'date-desc');
  const fetchLimit = hasSearchOrFilters ? 1000 : 20;
  const pageToFetch = hasSearchOrFilters ? 1 : currentPage;

  const { transactions: allTransactions, loading, error } = useTransactions(userId, pageToFetch, direction, minAmt, maxAmt, country, 10000, fetchLimit);

  // Client-side search and date filtering
  const filteredTransactions = useMemo(() => {
    if (!allTransactions) return allTransactions;

    let filtered = allTransactions;

    // Search filter - fixed to handle null values
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

    // Date range filter
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
  }, [allTransactions, searchQuery, dateRange, hasSearchOrFilters, fetchLimit, pageToFetch]);

  // Sorting
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

  // Format currency using transaction's actual currency field
  const formatTransactionAmount = (transaction: any) => {
    // Use converted amount if available, otherwise use original amount
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
        return <Badge variant="outline" className="bg-success/10 text-success border-success/20 text-xs">Completed</Badge>;
      case 'pending':
        return <Badge variant="outline" className="bg-warning/10 text-warning border-warning/20 text-xs">Pending</Badge>;
      case 'flagged':
        return <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 text-xs">Flagged</Badge>;
      default:
        return null;
    }
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Sender Name', 'Sender ID', 'Receiver Name', 'Receiver ID', 'Amount', 'Date', 'Location', 'Category', 'Narration', 'Status'];
    const csvContent = [
      headers.join(','),
      ...transactions.map(t =>
        [t.transaction_id, t.sender_name, t.sender_id, t.receiver_name, t.receiver_id, t.amount, t.timestamp, t.location, t.category, `"${t.narration}"`, t.status].join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'transactions.csv';
    a.click();
    window.URL.revokeObjectURL(url);

    toast.success('CSV exported successfully');
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [directionFilter, minAmount, maxAmount, countryFilter, dateRange, sortBy, searchQuery]);

  // Fetch countries list on mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const countryList = await api.getCountries(userId);
        setCountries(countryList);
      } catch (err) {
        console.error('Failed to fetch countries:', err);
      }
    };
    fetchCountries();
  }, [userId]);

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
      <Card className="card-shadow col-span-1 md:col-span-2 lg:col-span-4">
        <CardContent className="p-6 text-center text-muted-foreground">
          Loading transactions...
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="card-shadow col-span-1 md:col-span-2 lg:col-span-4">
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load transactions: {error}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="card-shadow col-span-1 md:col-span-2 lg:col-span-4">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold">
              Transactions Feed
            </CardTitle>
            <Button variant="outline" size="sm" onClick={handleExportCSV} className="text-xs">
              <Download className="h-3 w-3 mr-1" />
              Export CSV
            </Button>
          </div>

          {/* Search and Filter */}
          <div className="flex flex-wrap gap-2 items-center">
            <Input
              type="text"
              placeholder="Search by ID, name, category..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-[220px] h-8 text-xs"
            />

            <Popover open={filterOpen} onOpenChange={setFilterOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="h-8 text-xs">
                  <Filter className="h-3 w-3 mr-1" />
                  Filters
                  {hasActiveFilters && (
                    <Badge variant="secondary" className="ml-2 h-4 px-1 text-[10px]">
                      {[directionFilter !== 'all', minAmount || maxAmount, countryFilter !== 'all', dateRange, sortBy !== 'date-desc'].filter(Boolean).length}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80" align="start">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-sm">Filters</h4>
                    {hasActiveFilters && (
                      <Button variant="ghost" size="sm" onClick={clearFilters} className="h-6 text-xs">
                        <X className="h-3 w-3 mr-1" />
                        Clear All
                      </Button>
                    )}
                  </div>

                  {/* Direction Filter */}
                  <div className="space-y-2">
                    <label className="text-xs font-medium">Direction</label>
                    <Select value={directionFilter} onValueChange={setDirectionFilter}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Transactions</SelectItem>
                        <SelectItem value="incoming">Incoming</SelectItem>
                        <SelectItem value="outgoing">Outgoing</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Amount Range */}
                  <div className="space-y-2">
                    <label className="text-xs font-medium">Amount Range</label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        placeholder="Min"
                        value={minAmount}
                        onChange={(e) => setMinAmount(e.target.value)}
                        className="h-8 text-xs"
                      />
                      <span className="text-xs text-muted-foreground">to</span>
                      <Input
                        type="number"
                        placeholder="Max"
                        value={maxAmount}
                        onChange={(e) => setMaxAmount(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>

                  {/* Country Filter */}
                  <div className="space-y-2">
                    <label className="text-xs font-medium">Country</label>
                    <CountryDropdown
                      value={countryFilter === 'all' ? '' : countryFilter}
                      onChange={(country, currency) => setCountryFilter(country || 'all')}
                      placeholder="All Countries"
                      className="h-8 text-xs"
                    />
                  </div>

                  {/* Date Range */}
                  <div className="space-y-2">
                    <label className="text-xs font-medium">Date Range</label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className={cn(
                            "w-full justify-start text-left font-normal h-8 text-xs",
                            !dateRange && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-3 w-3" />
                          {dateRange?.from ? (
                            dateRange.to ? (
                              <>
                                {format(dateRange.from, "MMM dd")} - {format(dateRange.to, "MMM dd, y")}
                              </>
                            ) : (
                              format(dateRange.from, "MMM dd, y")
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

                  {/* Sort By */}
                  <div className="space-y-2">
                    <label className="text-xs font-medium">Sort By</label>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="date-desc">Date (Newest First)</SelectItem>
                        <SelectItem value="date-asc">Date (Oldest First)</SelectItem>
                        <SelectItem value="amount-desc">Amount (High to Low)</SelectItem>
                        <SelectItem value="amount-asc">Amount (Low to High)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[280px] overflow-y-auto overflow-x-auto">
          <Table className="min-w-[600px]">
            <TableHeader>
              <TableRow>
                <TableHead className="text-xs">ID</TableHead>
                <TableHead className="text-xs">Sender Name</TableHead>
                <TableHead className="text-xs">Sender ID</TableHead>
                <TableHead className="text-xs">Receiver Name</TableHead>
                <TableHead className="text-xs">Receiver ID</TableHead>
                <TableHead className="text-xs">Amount</TableHead>
                <TableHead className="text-xs">Date (UTC)</TableHead>
                <TableHead className="text-xs">Location</TableHead>
                <TableHead className="text-xs">Category</TableHead>
                <TableHead className="text-xs">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions && transactions.map((transaction: any) => (
                <TableRow key={transaction.transaction_id} className="text-xs">
                  <TableCell className="font-mono text-xs">{transaction.transaction_id}</TableCell>
                  <TableCell className="max-w-[120px] truncate">{transaction.sender_name || 'N/A'}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">{transaction.sender_id}</TableCell>
                  <TableCell className="max-w-[120px] truncate">{transaction.receiver_name || 'N/A'}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">{transaction.receiver_id}</TableCell>
                  <TableCell className={`font-medium ${transaction.transaction_flow === 'incoming' ? 'text-success' : 'text-destructive'
                    }`}>
                    {formatTransactionAmount(transaction)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {format(new Date(transaction.timestamp), 'MMM dd, HH:mm')}
                  </TableCell>
                  <TableCell>{transaction.location}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs">{transaction.category}</Badge>
                  </TableCell>
                  <TableCell>{getStatusBadge(transaction.status || 'completed')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-muted-foreground">
            {hasSearchOrFilters && transactions ? `Showing ${transactions.length} results` : ''}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1 || hasSearchOrFilters}
              className="h-8 text-xs"
            >
              <ChevronLeft className="h-3 w-3" />
            </Button>
            <span className="text-xs text-muted-foreground">
              {hasSearchOrFilters ? 'All Results' : `Page ${currentPage}`}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => p + 1)}
              disabled={!transactions || transactions.length < 20 || hasSearchOrFilters}
              className="h-8 text-xs"
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
