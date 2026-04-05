import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Search, X, Filter, CalendarIcon, Activity, CheckCircle2, AlertCircle, Fingerprint, ShieldAlert } from 'lucide-react';
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

    const filteredTransactions = useMemo(() => {
        let filtered = [...allTransactions];
        if (typeFilter !== 'all') filtered = filtered.filter(txn => txn.type === typeFilter);
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(txn =>
                txn.id.toLowerCase().includes(query) ||
                txn.location?.toLowerCase().includes(query) ||
                txn.display_type.toLowerCase().includes(query)
            );
        }
        if (minAmount) filtered = filtered.filter(txn => !txn.amount || txn.amount >= parseFloat(minAmount));
        if (maxAmount) filtered = filtered.filter(txn => !txn.amount || txn.amount <= parseFloat(maxAmount));
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
        filtered.sort((a, b) => {
            switch (sortBy) {
                case 'date-desc': return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
                case 'date-asc': return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
                case 'amount-desc': return (b.amount || 0) - (a.amount || 0);
                case 'amount-asc': return (a.amount || 0) - (b.amount || 0);
                case 'risk-desc': return (b.risk_score || 0) - (a.risk_score || 0);
                case 'risk-asc': return (a.risk_score || 0) - (b.risk_score || 0);
                default: return 0;
            }
        });
        return filtered;
    }, [allTransactions, typeFilter, searchQuery, minAmount, maxAmount, dateRange, sortBy]);

    const toggleSelection = (txn: Transaction) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(txn.id)) newSelected.delete(txn.id);
        else newSelected.add(txn.id);
        setSelectedIds(newSelected);
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === filteredTransactions.length) setSelectedIds(new Set());
        else setSelectedIds(new Set(filteredTransactions.map(t => t.id)));
    };

    const handleConfirm = () => {
        const selected = allTransactions.filter(t => selectedIds.has(t.id)).map(t => ({ id: t.id, type: t.type }));
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
        } catch { return 'N/A'; }
    };

    const getRiskGlow = (score?: number) => {
        if (!score) return null;
        if (score >= 80) return <div className="h-1.5 w-1.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse" />;
        if (score >= 50) return <div className="h-1.5 w-1.5 rounded-full bg-amber-500 shadow-[0_0_6px_rgba(251,191,36,0.4)]" />;
        return <div className="h-1.5 w-1.5 rounded-full bg-blue-500/40" />;
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[90vh] glass-panel border-white/10 p-0 overflow-hidden flex flex-col shadow-2xl">
                <div className="p-6 bg-white/[0.02] border-b border-white/5">
                   <DialogHeader>
                      <DialogTitle className="text-xl font-bold font-display uppercase tracking-widest text-white flex items-center gap-3">
                         <Activity className="h-5 w-5 text-primary/60" />
                         Asset Selection Feed
                      </DialogTitle>
                      <DialogDescription className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 pt-1">
                         Sentinel Network Activity Logger
                      </DialogDescription>
                   </DialogHeader>
                </div>

                <div className="p-6 flex-1 flex flex-col gap-6 overflow-hidden">
                    <div className="flex gap-3">
                        <div className="relative flex-1 group">
                           <Search className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                           <Input
                              placeholder="Locate Signal Identifier..."
                              value={searchQuery}
                              onChange={(e) => setSearchQuery(e.target.value)}
                              className="pl-10 h-10 bg-white/5 border-white/ client-focus:bg-white/10 rounded-xl font-bold text-sm transition-all"
                           />
                           {searchQuery && (
                              <button onClick={() => setSearchQuery('')} className="absolute right-3.5 top-3">
                                 <X className="h-4 w-4 text-muted-foreground hover:text-white" />
                              </button>
                           )}
                        </div>

                        <Popover open={filterOpen} onOpenChange={setFilterOpen}>
                            <PopoverTrigger asChild>
                                <Button variant="outline" className="h-10 text-[10px] font-black uppercase tracking-widest bg-white/5 border-white/10 rounded-xl px-4 transition-all">
                                    <Filter className="h-3.5 w-3.5 mr-2" />
                                    Signals Suite
                                    {hasActiveFilters && (
                                        <div className="ml-2 h-4 w-4 rounded-full bg-primary text-black flex items-center justify-center text-[8px] font-black">
                                            {[typeFilter !== 'all', directionFilter !== 'all', minAmount || maxAmount, dateRange, sortBy !== 'date-desc'].filter(Boolean).length}
                                        </div>
                                    )}
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 glass-panel border-white/10 shadow-2xl p-4 rounded-2xl" align="end">
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between pb-2 border-b border-white/5">
                                       <h4 className="font-bold font-display text-[10px] uppercase tracking-widest">Feed Logic</h4>
                                       {hasActiveFilters && (
                                          <Button variant="ghost" size="sm" onClick={clearFilters} className="h-6 text-[8px] font-black uppercase tracking-tighter">Reset</Button>
                                       )}
                                    </div>

                                    <div className="space-y-4 pt-1">
                                       <div className="grid grid-cols-3 gap-1.5 p-1 rounded-xl bg-white/5 border border-white/5">
                                          {['all', 'transaction', 'login'].map((type) => (
                                             <button key={type} onClick={() => setTypeFilter(type as any)} className={`h-8 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${typeFilter === type ? 'bg-primary text-black shadow-lg' : 'text-muted-foreground hover:bg-white/5'}`}>
                                                {type === 'transaction' ? 'Txns' : type === 'login' ? 'Auth' : 'Global'}
                                             </button>
                                          ))}
                                       </div>

                                       <div className="space-y-1.5">
                                          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground pl-1">Value Bounds</label>
                                          <div className="flex items-center gap-2">
                                             <Input type="number" placeholder="Min" value={minAmount} onChange={(e) => setMinAmount(e.target.value)} className="h-8 text-xs bg-white/5 border-white/5 rounded-lg" />
                                             <Input type="number" placeholder="Max" value={maxAmount} onChange={(e) => setMaxAmount(e.target.value)} className="h-8 text-xs bg-white/5 border-white/5 rounded-lg" />
                                          </div>
                                       </div>

                                       <div className="space-y-1.5">
                                          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground pl-1">Temporal Sweep</label>
                                          <Popover>
                                             <PopoverTrigger asChild>
                                                <Button variant="outline" className={cn("w-full justify-start text-left font-bold h-8 text-[10px] uppercase bg-white/5 border-white/5 rounded-lg", !dateRange && "text-muted-foreground")}>
                                                   <CalendarIcon className="mr-2 h-3.5 w-3.5 text-primary/60" />
                                                   {dateRange?.from ? (dateRange.to ? <>{format(dateRange.from, "MMM dd")} - {format(dateRange.to, "MMM dd")}</> : format(dateRange.from, "MMM dd")) : <span>Select Window</span>}
                                                </Button>
                                             </PopoverTrigger>
                                             <PopoverContent className="w-auto p-0 glass-panel border-white/10" align="start">
                                                <Calendar initialFocus mode="range" defaultMonth={dateRange?.from} selected={dateRange} onSelect={setDateRange} numberOfMonths={1} className="rounded-xl border-none" />
                                             </PopoverContent>
                                          </Popover>
                                       </div>

                                       <div className="space-y-1.5">
                                          <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground pl-1">Ordering Matrix</label>
                                          <Select value={sortBy} onValueChange={setSortBy}>
                                             <SelectTrigger className="h-8 text-xs bg-white/5 border-white/5 rounded-lg">
                                                <SelectValue />
                                             </SelectTrigger>
                                             <SelectContent className="glass-panel border-white/10">
                                                <SelectItem value="date-desc">Newest Recorded</SelectItem>
                                                <SelectItem value="amount-desc">Top Value</SelectItem>
                                                <SelectItem value="risk-desc">Highest Severity</SelectItem>
                                             </SelectContent>
                                          </Select>
                                       </div>
                                    </div>
                                </div>
                            </PopoverContent>
                        </Popover>
                    </div>

                    <div className="flex items-center justify-between px-2">
                        <div className="flex items-center gap-3">
                           <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5 group cursor-pointer hover:bg-white/10 transition-all" onClick={toggleSelectAll}>
                              <Checkbox checked={selectedIds.size === filteredTransactions.length && filteredTransactions.length > 0} className="rounded-md h-4 w-4 border-white/20 data-[state=checked]:bg-primary data-[state=checked]:text-black" />
                              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground group-hover:text-white transition-colors">Select Page ({filteredTransactions.length})</span>
                           </div>
                        </div>
                        <div className="px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 flex items-center gap-2">
                           <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                           <span className="text-[10px] font-black uppercase tracking-widest text-primary">{selectedIds.size} Captured</span>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto scrollbar-thin rounded-2xl border border-white/5 bg-white/[0.01]">
                        {loading ? (
                            <div className="flex items-center justify-center h-64">
                                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/30 animate-pulse">Scanning Grid...</p>
                            </div>
                        ) : filteredTransactions.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-64 opacity-20">
                                <Activity className="h-8 w-8 mb-3" />
                                <p className="text-[10px] font-black uppercase tracking-widest">No Signals Found</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-white/[0.02]">
                                {filteredTransactions.map((txn) => (
                                    <div key={txn.id} className={`flex items-center gap-4 p-4 hover:bg-white/[0.03] cursor-pointer transition-all ${selectedIds.has(txn.id) ? 'bg-primary/[0.02]' : ''}`} onClick={() => toggleSelection(txn)}>
                                        <Checkbox checked={selectedIds.has(txn.id)} className="rounded-md h-5 w-5 border-white/10 data-[state=checked]:bg-primary data-[state=checked]:text-black" />
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-3 mb-1.5">
                                                <span className="font-mono text-sm font-bold text-white/90 tracking-tight">{txn.id}</span>
                                                <div className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest border border-white/10 flex items-center gap-1.5 ${txn.type === 'login' ? 'bg-indigo-500/10 text-indigo-400' : 'bg-white/5 text-muted-foreground'}`}>
                                                   {txn.type === 'login' ? <Fingerprint className="h-2.5 w-2.5" /> : <Activity className="h-2.5 w-2.5" />}
                                                   {txn.display_type}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                {txn.amount && (
                                                    <span className="text-xs font-bold font-display text-white">
                                                        {txn.currency} {txn.amount.toLocaleString()}
                                                    </span>
                                                )}
                                                <div className="flex items-center gap-2">
                                                   <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/50">{txn.location}</span>
                                                   <div className="h-0.5 w-0.5 rounded-full bg-white/10" />
                                                   <span className="text-[10px] font-bold text-muted-foreground/40 italic">{formatTimestamp(txn.timestamp)}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end gap-1.5">
                                           <span className="text-[10px] font-black uppercase tracking-tighter text-muted-foreground/30 italic">Severity Index</span>
                                           <div className="flex items-center gap-2">
                                              <span className="text-xs font-black text-glow-blue">{txn.risk_score || 0}%</span>
                                              {getRiskGlow(txn.risk_score)}
                                           </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-6 bg-white/[0.02] border-t border-white/5 flex gap-3">
                   <Button variant="ghost" onClick={onClose} className="flex-1 h-12 text-[11px] font-black uppercase tracking-widest rounded-xl hover:bg-white/5 transition-all">
                      Discard Feed
                   </Button>
                   <Button onClick={handleConfirm} disabled={selectedIds.size === 0} className="flex-2 h-12 bg-primary text-black text-[11px] font-black uppercase tracking-widest rounded-xl shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-all flex items-center justify-center gap-2 px-8">
                      <CheckCircle2 className="h-4 w-4" />
                      Authorize Capture ({selectedIds.size})
                   </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
