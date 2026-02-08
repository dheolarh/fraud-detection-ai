import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Search, X, Filter, CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';
import { DateRange } from 'react-day-picker';
import { cn } from '@/lib/utils';
import api from '@/lib/api';

interface Transaction {
    id: string;
    type: 'transaction' | 'login';
    display_type: string;
    amount?: number;
    currency?: string;
    location: string;
    timestamp: string;
    status?: string;
    risk_score?: number;
}

interface TransactionSelectorModalProps {
    open: boolean;
    onClose: () => void;
    onConfirm: (selected: Array<{ id: string; type: string }>) => void;
    userId: string;
    initialSelected?: Array<{ id: string; type: string }>;
}

export function TransactionSelectorModal({
    open,
    onClose,
    onConfirm,
    userId,
    initialSelected = []
}: TransactionSelectorModalProps) {
    const [allTransactions, setAllTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [typeFilter, setTypeFilter] = useState<'all' | 'transaction' | 'login'>('all');
    const [directionFilter, setDirectionFilter] = useState<'all' | 'incoming' | 'outgoing'>('all');
    const [minAmount, setMinAmount] = useState('');
    const [maxAmount, setMaxAmount] = useState('');
    const [dateRange, setDateRange] = useState<DateRange | undefined>();
    const [sortBy, setSortBy] = useState('date-desc');
    const [filterOpen, setFilterOpen] = useState(false);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(
        new Set(initialSelected.map(t => t.id))
    );

    useEffect(() => {
        if (open) {
            fetchTransactions();
        }
    }, [open, userId]);

    const fetchTransactions = async () => {
        setLoading(true);
        try {
            const data = await api.getAvailableTransactions(userId);
            setAllTransactions(data);
        } catch (error) {
            console.error('Failed to fetch transactions:', error);
        } finally {
            setLoading(false);
        }
    };

    // Apply all filters
    const filteredTransactions = useMemo(() => {
        let filtered = [...allTransactions];

        // Type filter
        if (typeFilter !== 'all') {
            filtered = filtered.filter(txn => txn.type === typeFilter);
        }

        // Search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(txn =>
                txn.id.toLowerCase().includes(query) ||
                txn.location?.toLowerCase().includes(query) ||
                txn.display_type.toLowerCase().includes(query)
            );
        }

        // Amount range filter (only for transactions with amounts)
        if (minAmount) {
            filtered = filtered.filter(txn => !txn.amount || txn.amount >= parseFloat(minAmount));
        }
        if (maxAmount) {
            filtered = filtered.filter(txn => !txn.amount || txn.amount <= parseFloat(maxAmount));
        }

        // Date range filter
        if (dateRange?.from || dateRange?.to) {
            filtered = filtered.filter(txn => {
                const txDate = new Date(txn.timestamp);
                if (dateRange.from && txDate < dateRange.from) return false;
                if (dateRange.to) {
                    const endOfDay = new Date(dateRange.to);
                    endOfDay.setHours(23, 59, 59, 999);
                    if (txDate > endOfDay) return false;
                }
                return true;
            });
        }

        // Sorting
        filtered.sort((a, b) => {
            switch (sortBy) {
                case 'date-desc':
                    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
                case 'date-asc':
                    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
                case 'amount-desc':
                    return (b.amount || 0) - (a.amount || 0);
                case 'amount-asc':
                    return (a.amount || 0) - (b.amount || 0);
                case 'risk-desc':
                    return (b.risk_score || 0) - (a.risk_score || 0);
                case 'risk-asc':
                    return (a.risk_score || 0) - (b.risk_score || 0);
                default:
                    return 0;
            }
        });

        return filtered;
    }, [allTransactions, typeFilter, searchQuery, minAmount, maxAmount, dateRange, sortBy]);

    const toggleSelection = (txn: Transaction) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(txn.id)) {
            newSelected.delete(txn.id);
        } else {
            newSelected.add(txn.id);
        }
        setSelectedIds(newSelected);
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === filteredTransactions.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(filteredTransactions.map(t => t.id)));
        }
    };

    const handleConfirm = () => {
        const selected = allTransactions
            .filter(t => selectedIds.has(t.id))
            .map(t => ({ id: t.id, type: t.type }));
        onConfirm(selected);
        onClose();
    };

    const clearFilters = () => {
        setTypeFilter('all');
        setDirectionFilter('all');
        setMinAmount('');
        setMaxAmount('');
        setDateRange(undefined);
        setSortBy('date-desc');
    };

    const hasActiveFilters = typeFilter !== 'all' || directionFilter !== 'all' || minAmount || maxAmount || dateRange || sortBy !== 'date-desc';

    const formatTimestamp = (timestamp: string) => {
        try {
            let date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                const cleaned = timestamp.replace(' UTC', '').replace(' at ', ' ');
                date = new Date(cleaned);
            }
            return isNaN(date.getTime()) ? 'N/A' : format(date, 'MMM dd, HH:mm');
        } catch {
            return 'N/A';
        }
    };

    const getRiskBadge = (score?: number) => {
        if (!score) return null;
        if (score >= 80) return <Badge variant="destructive" className="text-xs">Critical</Badge>;
        if (score >= 60) return <Badge className="bg-warning text-xs">High</Badge>;
        return <Badge className="bg-info text-xs">Medium</Badge>;
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle>Select Affected Transactions</DialogTitle>
                </DialogHeader>

                {/* Search and Filter Bar */}
                <div className="flex gap-2">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search by ID, location, or type..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                className="absolute right-3 top-1/2 transform -translate-y-1/2"
                            >
                                <X className="h-4 w-4 text-muted-foreground" />
                            </button>
                        )}
                    </div>

                    <Popover open={filterOpen} onOpenChange={setFilterOpen}>
                        <PopoverTrigger asChild>
                            <Button variant="outline" size="sm">
                                <Filter className="h-4 w-4 mr-2" />
                                Filters
                                {hasActiveFilters && (
                                    <Badge variant="secondary" className="ml-2 h-4 px-1 text-[10px]">
                                        {[typeFilter !== 'all', directionFilter !== 'all', minAmount || maxAmount, dateRange, sortBy !== 'date-desc'].filter(Boolean).length}
                                    </Badge>
                                )}
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-80" align="end">
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

                                {/* Type Filter */}
                                <div className="space-y-2">
                                    <label className="text-xs font-medium">Type</label>
                                    <div className="flex gap-2">
                                        <Button
                                            type="button"
                                            variant={typeFilter === 'all' ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => setTypeFilter('all')}
                                            className="flex-1 text-xs"
                                        >
                                            All
                                        </Button>
                                        <Button
                                            type="button"
                                            variant={typeFilter === 'transaction' ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => setTypeFilter('transaction')}
                                            className="flex-1 text-xs"
                                        >
                                            Transactions
                                        </Button>
                                        <Button
                                            type="button"
                                            variant={typeFilter === 'login' ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => setTypeFilter('login')}
                                            className="flex-1 text-xs"
                                        >
                                            Logins
                                        </Button>
                                    </div>
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
                                            <SelectItem value="risk-desc">Risk (High to Low)</SelectItem>
                                            <SelectItem value="risk-asc">Risk (Low to High)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </PopoverContent>
                    </Popover>
                </div>

                {/* Selection Info */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Checkbox
                            checked={selectedIds.size === filteredTransactions.length && filteredTransactions.length > 0}
                            onCheckedChange={toggleSelectAll}
                        />
                        <span className="text-sm text-muted-foreground">
                            Select All ({filteredTransactions.length})
                        </span>
                    </div>
                    <Badge variant="secondary">
                        {selectedIds.size} selected
                    </Badge>
                </div>

                {/* Transaction List */}
                <div className="flex-1 overflow-y-auto border rounded-lg">
                    {loading ? (
                        <div className="flex items-center justify-center h-64">
                            <p className="text-muted-foreground">Loading transactions...</p>
                        </div>
                    ) : filteredTransactions.length === 0 ? (
                        <div className="flex items-center justify-center h-64">
                            <p className="text-muted-foreground">No transactions found</p>
                        </div>
                    ) : (
                        <div className="divide-y">
                            {filteredTransactions.map((txn) => (
                                <div
                                    key={txn.id}
                                    className="flex items-center gap-3 p-3 hover:bg-muted/50 cursor-pointer"
                                    onClick={() => toggleSelection(txn)}
                                >
                                    <Checkbox
                                        checked={selectedIds.has(txn.id)}
                                        onCheckedChange={() => toggleSelection(txn)}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-mono text-sm font-medium">{txn.id}</span>
                                            <Badge variant="outline" className="text-xs">
                                                {txn.display_type}
                                            </Badge>
                                            {getRiskBadge(txn.risk_score)}
                                        </div>
                                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                            {txn.amount && (
                                                <span className="font-medium">
                                                    {txn.currency} {txn.amount.toFixed(2)}
                                                </span>
                                            )}
                                            <span>{txn.location}</span>
                                            <span>{formatTimestamp(txn.timestamp)}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button onClick={handleConfirm} disabled={selectedIds.size === 0}>
                        Confirm Selection ({selectedIds.size})
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
