import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ExternalLink, CheckCircle, RotateCcw, Plus, Pencil, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { toast } from 'sonner';
import { TransactionSelectorModal } from '@/components/modals/TransactionSelectorModal';
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
    switch (status) {
      case 'open':
        return <Badge variant="outline" className="bg-info/10 text-info border-info/20 text-xs">Open</Badge>;
      case 'resolved':
        return <Badge variant="outline" className="bg-success/10 text-success border-success/20 text-xs">Resolved</Badge>;
      default:
        return null;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <Badge className="bg-destructive text-destructive-foreground text-xs">Critical</Badge>;
      case 'high':
        return <Badge className="bg-destructive text-destructive-foreground text-xs">High</Badge>;
      case 'medium':
        return <Badge className="bg-warning text-primary-foreground text-xs">Medium</Badge>;
      case 'low':
        return <Badge variant="secondary" className="text-xs">Low</Badge>;
      default:
        return null;
    }
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
      fetchCases(); // Refresh cases
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
      fetchCases(); // Refresh cases
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
        // Update existing case
        await api.updateCase(editingCaseId, {
          title: newCase.title,
          description: newCase.description,
          priority: newCase.priority,
          affected_transactions: newCase.affectedTransactions
        });
        toast.success('Case updated successfully');
      } else {
        // Create new case
        await api.createCase({
          title: newCase.title,
          description: newCase.description,
          priority: newCase.priority,
          affected_transactions: newCase.affectedTransactions
        });
        toast.success('Case created successfully');
      }

      fetchCases(); // Refresh cases
      setAddCaseModalOpen(false);
      setIsEditMode(false);
      setEditingCaseId(null);
      setNewCase({
        title: '',
        description: '',
        priority: 'medium',
        affectedTransactions: []
      });
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
    setNewCase({
      title: '',
      description: '',
      priority: 'medium',
      affectedTransactions: []
    });
  };

  const sortedCases = useMemo(() => {
    let sorted = [...cases];

    // Filter by status
    if (statusSort !== 'all') {
      sorted = sorted.filter(c => c.status === statusSort);
    }

    // Filter by priority
    if (prioritySort !== 'all') {
      sorted = sorted.filter(c => c.priority === prioritySort);
    }

    return sorted;
  }, [cases, statusSort, prioritySort]);

  const totalPages = Math.ceil(sortedCases.length / itemsPerPage);
  const paginatedCases = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedCases.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedCases, currentPage]);

  return (
    <Card className="card-shadow col-span-1 md:col-span-2 lg:col-span-4">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base font-semibold">
              Case Management
              <Badge variant="secondary" className="ml-2 text-xs">{sortedCases.length}</Badge>
            </CardTitle>
            <Button
              size="sm"
              onClick={() => setAddCaseModalOpen(true)}
              className="h-8 text-xs"
            >
              <Plus className="h-3 w-3 mr-1" />
              Add Case
            </Button>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-2 items-center">
            <Select value={statusSort} onValueChange={(value) => { setStatusSort(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-[140px] h-8 text-xs">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>

            <Select value={prioritySort} onValueChange={(value) => { setPrioritySort(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-[140px] h-8 text-xs">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priority</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>

            {(statusSort !== 'all' || prioritySort !== 'all') && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setStatusSort('all');
                  setPrioritySort('all');
                  setCurrentPage(1);
                }}
                className="h-8 text-xs"
              >
                Clear Filters
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] overflow-y-auto overflow-x-auto">
          <Table className="min-w-[400px]">
            <TableHeader>
              <TableRow>
                <TableHead className="text-xs">ID</TableHead>
                <TableHead className="text-xs">Title</TableHead>
                <TableHead className="text-xs">Priority</TableHead>
                <TableHead className="text-xs">Status</TableHead>
                <TableHead className="text-xs">Transactions</TableHead>
                <TableHead className="text-xs">Actions</TableHead>
                <TableHead className="text-xs"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedCases.map((caseItem) => (
                <TableRow key={caseItem.case_id} className="text-xs">
                  <TableCell className="font-mono text-xs">{caseItem.case_id}</TableCell>
                  <TableCell className="max-w-[180px] truncate">{caseItem.title}</TableCell>
                  <TableCell>{getPriorityBadge(caseItem.priority)}</TableCell>
                  <TableCell>{getStatusBadge(caseItem.status)}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs">
                      {caseItem.affected_transactions?.length || 0}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {caseItem.status === 'resolved' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReopenCase(caseItem.case_id)}
                        className="h-6 px-2 text-xs"
                      >
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Reopen
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolveClick(caseItem.case_id)}
                        className="h-6 px-2 text-xs bg-success/10 text-success border-success/20 hover:bg-success/20"
                      >
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Resolve
                      </Button>
                    )}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditCase(caseItem)}
                      className="h-6 px-2"
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-end gap-2 mt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="h-8 text-xs"
            >
              <ChevronLeft className="h-3 w-3" />
            </Button>
            <span className="text-xs text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="h-8 text-xs"
            >
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
        )}
      </CardContent>

      {/* Add/Edit Case Modal */}
      <Dialog open={addCaseModalOpen} onOpenChange={handleModalClose}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{isEditMode ? 'Edit Case' : 'Add New Case'}</DialogTitle>
            <DialogDescription>
              {isEditMode ? 'Update case details' : 'Create a new case for investigation'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleAddCase} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title" className="text-sm">Case Title</Label>
              <Input
                id="title"
                placeholder="Brief title for the case"
                value={newCase.title}
                onChange={(e) => setNewCase({ ...newCase, title: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm">Description</Label>
              <Input
                id="description"
                placeholder="Describe the case..."
                value={newCase.description}
                onChange={(e) => setNewCase({ ...newCase, description: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label className="text-sm">Priority</Label>
              <div className="flex gap-2">
                {['low', 'medium', 'high', 'critical'].map((priority) => (
                  <Button
                    key={priority}
                    type="button"
                    variant={newCase.priority === priority ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setNewCase({ ...newCase, priority: priority as any })}
                    className="flex-1 text-xs"
                  >
                    {priority.charAt(0).toUpperCase() + priority.slice(1)}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm">Affected Transactions</Label>
              <Button
                type="button"
                variant="outline"
                onClick={() => setTransactionSelectorOpen(true)}
                className="w-full"
              >
                Select Transactions ({newCase.affectedTransactions.length})
              </Button>

              {newCase.affectedTransactions.length > 0 && (
                <div className="border rounded-lg p-2 max-h-32 overflow-y-auto">
                  {newCase.affectedTransactions.map((txn) => (
                    <div key={txn.id} className="flex items-center justify-between py-1">
                      <span className="text-xs font-mono">{txn.id}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeTransaction(txn.id)}
                        className="h-5 w-5 p-0"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleModalClose}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button type="submit" className="flex-1">
                {isEditMode ? 'Update Case' : 'Create Case'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Resolve Confirmation Modal */}
      <Dialog open={resolveConfirmOpen} onOpenChange={setResolveConfirmOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Resolve Case</DialogTitle>
            <DialogDescription>
              Are you sure you want to resolve this case? Anomalies attached to this case will be hidden from the anomaly table.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResolveConfirmOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleResolveConfirm}>
              Yes, Resolve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Transaction Selector Modal */}
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
