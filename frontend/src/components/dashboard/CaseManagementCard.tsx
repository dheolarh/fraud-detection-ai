import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ExternalLink, CheckCircle, RotateCcw, Plus, Pencil, ChevronLeft, ChevronRight, X, Briefcase, Filter, Layers } from 'lucide-react';
import { toast } from 'sonner';
import { TransactionSelectorModal } from '@/components/modals/TransactionSelectorModal';
import { cn } from '@/lib/utils';
import api from '@/lib/api';

export function CaseManagementCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [addCaseModalOpen, setAddCaseModalOpen] = useState(false);
  const [transactionSelectorOpen, setTransactionSelectorOpen] = useState(false);
  const [resolveConfirmOpen, setResolveConfirmOpen] = useState(false);
  const [caseToResolve, setCaseToResolve] = useState<string | null>(null);
  const [editingCaseId, setEditingCaseId] = useState<string | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [statusSort, setStatusSort] = useState<string>('all');
  const [prioritySort, setPrioritySort] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  const [newCase, setNewCase] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    affectedTransactions: [] as Array<{ id: string; type: string }>
  });

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const data = await api.getCases();
      setCases(data);
    } catch (error) {
      console.error('Failed to fetch cases:', error);
      toast.error('Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const isResolved = status === 'resolved';
    return (
      <div className={`px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-widest border ${
        isResolved ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-primary/10 text-primary border-primary/20'
      }`}>
        {status}
      </div>
    );
  };

  const getPriorityBadge = (priority: string) => {
     const colors: Record<string, string> = {
        critical: 'bg-red-500 text-white shadow-[0_0_10px_rgba(239,68,68,0.4)]',
        high: 'bg-red-400 text-white shadow-[0_0_8px_rgba(239,68,68,0.2)]',
        medium: 'bg-amber-400 text-black',
        low: 'bg-blue-400/20 text-blue-400 border border-blue-400/20'
     };
     return <div className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest ${colors[priority]}`}>{priority}</div>;
  };

  const handleResolveClick = (caseId: string) => {
    setCaseToResolve(caseId);
    setResolveConfirmOpen(true);
  };

  const handleResolveConfirm = async () => {
    if (!caseToResolve) return;
    try {
      await api.resolveCase(caseToResolve);
      toast.success(`Case ${caseToResolve} has been resolved`);
      fetchCases();
    } catch (error) {
      toast.error('Failed to resolve case');
    } finally {
      setResolveConfirmOpen(false);
      setCaseToResolve(null);
    }
  };

  const handleReopenCase = async (caseId: string) => {
    try {
      await api.reopenCase(caseId);
      toast.info(`Case ${caseId} has been reopened`);
      fetchCases();
    } catch (error) {
      toast.error('Failed to reopen case');
    }
  };

  const handleEditCase = (caseItem: any) => {
    setIsEditMode(true);
    setEditingCaseId(caseItem.case_id);
    setNewCase({
      title: caseItem.title,
      description: caseItem.description,
      priority: caseItem.priority,
      affectedTransactions: caseItem.affected_transactions || []
    });
    setAddCaseModalOpen(true);
  };

  const handleAddCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCase.title || !newCase.description) {
      toast.error('Please fill in title and description');
      return;
    }
    try {
      if (isEditMode && editingCaseId) {
        await api.updateCase(editingCaseId, {
          title: newCase.title,
          description: newCase.description,
          priority: newCase.priority,
          affected_transactions: newCase.affectedTransactions
        });
        toast.success('Case updated successfully');
      } else {
        await api.createCase({
          title: newCase.title,
          description: newCase.description,
          priority: newCase.priority,
          affected_transactions: newCase.affectedTransactions
        });
        toast.success('Case created successfully');
      }
      fetchCases();
      handleModalClose();
    } catch (error) {
      toast.error(isEditMode ? 'Failed to update case' : 'Failed to create case');
    }
  };

  const handleTransactionSelection = (selected: Array<{ id: string; type: string }>) => {
    setNewCase({ ...newCase, affectedTransactions: selected });
  };

  const removeTransaction = (id: string) => {
    setNewCase({
      ...newCase,
      affectedTransactions: newCase.affectedTransactions.filter(t => t.id !== id)
    });
  };

  const handleModalClose = () => {
    setAddCaseModalOpen(false);
    setIsEditMode(false);
    setEditingCaseId(null);
    setNewCase({ title: '', description: '', priority: 'medium', affectedTransactions: [] });
  };

  const sortedCases = useMemo(() => {
    let sorted = [...cases];
    if (statusSort !== 'all') sorted = sorted.filter(c => c.status === statusSort);
    if (prioritySort !== 'all') sorted = sorted.filter(c => c.priority === prioritySort);
    return sorted;
  }, [cases, statusSort, prioritySort]);

  const totalPages = Math.ceil(sortedCases.length / itemsPerPage);
  const paginatedCases = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedCases.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedCases, currentPage]);

  if (loading) return (
     <Card className="glass-panel card-shadow-lg col-span-1 md:col-span-2 lg:col-span-4 animate-pulse">
        <CardContent className="h-64 flex items-center justify-center">
           <Layers className="h-6 w-6 text-muted-foreground/30 animate-spin" />
        </CardContent>
     </Card>
  );

  return (
    <Card className="glass-panel card-shadow-lg col-span-1 md:col-span-2 lg:col-span-4 overflow-hidden border-white/5">
      <CardHeader className="pb-3 bg-white/[0.01] border-b border-white/5">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
               <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center border border-white/10">
                  <Briefcase className="h-4 w-4 text-primary/60" />
               </div>
               <CardTitle className="text-sm font-bold font-display uppercase tracking-widest text-muted-foreground">
                Case Management
              </CardTitle>
            </div>
            <Button size="sm" onClick={() => setAddCaseModalOpen(true)} className="h-9 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-[10px] rounded-xl hover:shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-all">
              <Plus className="h-3.5 w-3.5 mr-2" />
              New Case File
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 items-center">
            <Select value={statusSort} onValueChange={(value) => { setStatusSort(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-[140px] h-9 text-xs bg-white/5 border-white/5 rounded-xl font-bold uppercase tracking-widest">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent className="glass-panel border-white/10">
                <SelectItem value="all">Global State</SelectItem>
                <SelectItem value="open">Open Case</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>

            <Select value={prioritySort} onValueChange={(value) => { setPrioritySort(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-[140px] h-9 text-xs bg-white/5 border-white/5 rounded-xl font-bold uppercase tracking-widest">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent className="glass-panel border-white/10">
                <SelectItem value="all">Global Priority</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-[350px] overflow-y-auto scrollbar-thin">
          <Table>
            <TableHeader className="sticky top-0 bg-background/80 backdrop-blur-md z-20">
              <TableRow className="border-b border-white/5 hover:bg-transparent">
                <TableHead className="text-[10px] font-black uppercase tracking-widest h-12 pl-6">ID / Title</TableHead>
                <TableHead className="text-[10px] font-black uppercase tracking-widest h-12">Priority / State</TableHead>
                <TableHead className="text-[10px] font-black uppercase tracking-widest h-12">Attached Items</TableHead>
                <TableHead className="text-[10px] font-black uppercase tracking-widest h-12 text-right pr-6">Management</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedCases.map((caseItem) => (
                <TableRow key={caseItem.case_id} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors group">
                  <TableCell className="pl-6 py-4">
                     <div className="flex flex-col gap-0.5">
                        <span className="text-xs font-bold font-mono text-white/90 truncate max-w-[150px]">{caseItem.case_id}</span>
                        <span className="text-xs font-bold text-muted-foreground/60 truncate max-w-[180px] font-display">{caseItem.title}</span>
                     </div>
                  </TableCell>
                  <TableCell className="py-4">
                     <div className="flex flex-col items-start gap-2">
                        {getPriorityBadge(caseItem.priority)}
                        {getStatusBadge(caseItem.status)}
                     </div>
                  </TableCell>
                  <TableCell className="py-4">
                     <div className="flex items-center gap-2">
                        <div className="h-7 px-2.5 rounded-lg bg-white/5 border border-white/5 flex items-center justify-center text-[10px] font-black text-primary/80">
                           {caseItem.affected_transactions?.length || 0} ITEMS
                        </div>
                     </div>
                  </TableCell>
                  <TableCell className="text-right pr-6 py-4">
                     <div className="flex items-center justify-end gap-2">
                        {caseItem.status === 'resolved' ? (
                          <Button variant="outline" size="sm" onClick={() => handleReopenCase(caseItem.case_id)} className="h-8 px-3 text-[9px] font-black uppercase tracking-tighter bg-white/5 border-white/10 hover:bg-white/10 transition-all rounded-xl">
                            <RotateCcw className="h-3 w-3 mr-1.5" />
                            Reopen
                          </Button>
                        ) : (
                          <Button variant="outline" size="sm" onClick={() => handleResolveClick(caseItem.case_id)} className="h-8 px-3 text-[9px] font-black uppercase tracking-tighter bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20 transition-all rounded-xl">
                            <CheckCircle className="h-3 w-3 mr-1.5" />
                            Resolve
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={() => handleEditCase(caseItem)} className="h-8 w-8 p-0 hover:bg-white/10 transition-all rounded-xl">
                          <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
                        </Button>
                     </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-white/5 bg-white/[0.01]">
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                   Directory Page {currentPage} of {totalPages}
                </span>
                <div className="flex items-center gap-1.5">
                   <Button variant="outline" size="sm" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} className="h-8 w-8 p-0 bg-white/5 border-white/5 hover:bg-white/10 disabled:opacity-20 rounded-lg">
                      <ChevronLeft className="h-3 w-3" />
                   </Button>
                   <Button variant="outline" size="sm" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="h-8 w-8 p-0 bg-white/5 border-white/5 hover:bg-white/10 disabled:opacity-20 rounded-lg">
                      <ChevronRight className="h-3 w-3" />
                   </Button>
                </div>
            </div>
        )}
      </CardContent>

      {/* Add/Edit Case Modal */}
      <Dialog open={addCaseModalOpen} onOpenChange={handleModalClose}>
        <DialogContent className="max-w-md max-h-[90vh] glass-panel border-white/10 p-0 overflow-hidden shadow-2xl flex flex-col">
          <div className="p-5 bg-white/[0.02] border-b border-white/5">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold font-display uppercase tracking-widest text-white">
                 {isEditMode ? 'Modify Case File' : 'Establish New Case'}
              </DialogTitle>
              <DialogDescription className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 pt-1">
                Investigation Unit Database Entry
              </DialogDescription>
            </DialogHeader>
          </div>

          <form onSubmit={handleAddCase} className="p-6 space-y-5 overflow-y-auto scrollbar-thin">
            <div className="space-y-1.5">
              <Label htmlFor="title" className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Case Designation</Label>
              <Input id="title" placeholder="Brief signal description..." value={newCase.title} onChange={(e) => setNewCase({ ...newCase, title: e.target.value })} className="h-10 bg-white/5 border-white/5 focus:bg-white/10 rounded-xl text-sm font-bold transition-all" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="description" className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Intelligence Summary</Label>
              <textarea id="description" placeholder="Provide detailed audit context..." value={newCase.description} onChange={(e) => setNewCase({ ...newCase, description: e.target.value })} className="w-full min-h-[80px] p-3 text-sm font-bold bg-white/5 border border-white/5 focus:bg-white/10 rounded-xl transition-all resize-none scrollbar-none" />
            </div>

            <div className="space-y-1.5">
              <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Priority Index</Label>
              <div className="grid grid-cols-4 gap-2">
                {['low', 'medium', 'high', 'critical'].map((priority) => (
                  <button key={priority} type="button" onClick={() => setNewCase({ ...newCase, priority: priority as any })}
                    className={cn(
                      "h-8 text-[9px] font-black uppercase tracking-widest rounded-xl border border-white/5 transition-all",
                      newCase.priority === priority 
                        ? (priority === 'critical' ? 'bg-red-500 text-white shadow-[0_0_15px_rgba(239,68,68,0.3)]' : 
                          priority === 'high' ? 'bg-red-400 text-white' : 
                          priority === 'medium' ? 'bg-amber-400 text-black' : 'bg-primary text-primary-foreground')
                        : "bg-white/5 hover:bg-white/10 text-muted-foreground"
                    )}
                  >
                    {priority}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2.5">
              <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground pl-1">Target Assets</Label>
              <Button type="button" variant="outline" onClick={() => setTransactionSelectorOpen(true)} className="w-full h-10 bg-white/5 border-dashed border-white/10 hover:bg-white/10 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all">
                Select Transactions ({newCase.affectedTransactions.length})
              </Button>

              {newCase.affectedTransactions.length > 0 && (
                <div className="glass-panel border-white/5 rounded-xl p-2.5 max-h-28 overflow-y-auto scrollbar-thin space-y-1.5">
                  {newCase.affectedTransactions.map((txn) => (
                    <div key={txn.id} className="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/5 group">
                      <span className="text-[10px] font-black font-mono text-white/60 tracking-wider">SIG-{txn.id}</span>
                      <button type="button" onClick={() => removeTransaction(txn.id)} className="h-5 w-5 flex items-center justify-center hover:bg-red-500/20 hover:text-red-400 rounded-md transition-colors">
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="button" variant="ghost" onClick={handleModalClose} className="flex-1 h-11 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-white/5 transition-all">
                Abondon
              </Button>
              <Button type="submit" className="flex-1 h-11 bg-primary text-primary-foreground text-[10px] font-black uppercase tracking-widest rounded-xl shadow-lg transition-all">
                {isEditMode ? 'Commit Changes' : 'Authorize Case'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Resolve Confirmation Modal */}
      <Dialog open={resolveConfirmOpen} onOpenChange={setResolveConfirmOpen}>
        <DialogContent className="max-w-sm glass-panel border-white/10 p-6 shadow-2xl">
          <DialogHeader className="space-y-3">
            <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto">
               <CheckCircle className="h-6 w-6 text-emerald-400" />
            </div>
            <DialogTitle className="text-center font-display font-black uppercase tracking-widest text-lg">Resolve Registry</DialogTitle>
            <DialogDescription className="text-center text-xs font-medium leading-relaxed opacity-70">
              Confirm resolution of this investigative file. Associated behavioral signals will be archived in the system registry.
            </DialogDescription>
          </DialogHeader>
          <div className="flex gap-3 mt-6">
            <Button variant="ghost" onClick={() => setResolveConfirmOpen(false)} className="flex-1 h-10 text-[10px] font-black uppercase tracking-widest rounded-xl">
              Abort
            </Button>
            <Button onClick={handleResolveConfirm} className="flex-1 h-10 bg-emerald-500 text-white font-black uppercase tracking-widest rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.25)]">
              Yes, Resolve
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <TransactionSelectorModal
        open={transactionSelectorOpen}
        onClose={() => setTransactionSelectorOpen(false)}
        onConfirm={handleTransactionSelection}
        userId={userId}
        initialSelected={newCase.affectedTransactions}
      />
    </Card>
  );
}
