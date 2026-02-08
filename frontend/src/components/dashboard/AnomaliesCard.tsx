import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AlertTriangle, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { useCombinedAnomalies, useBankCurrency } from '@/hooks/useData';
import { Alert, AlertDescription } from '@/components/ui/alert';

export function AnomaliesCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const { anomalies: alerts, loading, error } = useCombinedAnomalies(userId, 5000);
  const { currency } = useBankCurrency();

  const [selectedAnomaly, setSelectedAnomaly] = useState<any | null>(null);
  const [prioritySort, setPrioritySort] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const getRiskBadge = (score: number) => {
    if (score >= 70) {
      return <Badge className="bg-destructive text-destructive-foreground text-xs">Critical</Badge>;
    }
    if (score >= 30) {
      return <Badge className="bg-warning text-primary-foreground text-xs">High</Badge>;
    }
    return <Badge className="bg-info text-primary-foreground text-xs">Medium</Badge>;
  };

  const getVerdictBadge = (verdict: string) => {
    if (verdict === 'FLAGGED') {
      return <Badge className="bg-destructive text-destructive-foreground text-xs font-semibold">FLAGGED</Badge>;
    }
    if (verdict === 'MONITORED') {
      return <Badge className="bg-warning text-primary-foreground text-xs font-semibold">MONITORED</Badge>;
    }
    return <Badge variant="outline" className="text-xs">{verdict}</Badge>;
  };

  const formatTimestamp = (timestamp: string | undefined) => {
    if (!timestamp) return 'N/A';

    try {
      // Try parsing as ISO format first (transaction timestamps)
      let date = new Date(timestamp);

      // If invalid, try parsing the auth log format: "December 27, 2025 at 15:25 UTC"
      if (isNaN(date.getTime())) {
        const cleanedTimestamp = timestamp.replace(' UTC', '').replace(' at ', ' ');
        date = new Date(cleanedTimestamp);
      }

      // If still invalid, return N/A
      if (isNaN(date.getTime())) {
        return 'N/A';
      }

      return format(date, 'MMM dd, HH:mm');
    } catch (error) {
      return 'N/A';
    }
  };

  const sortedAnomalies = useMemo(() => {
    if (!alerts) return [];

    let sorted = [...alerts];

    // Filter based on risk score ranges
    if (prioritySort === 'critical') {
      sorted = sorted.filter((a: any) => a.risk_score >= 90);  // Critical: 90+
    } else if (prioritySort === 'high') {
      sorted = sorted.filter((a: any) => a.risk_score >= 70 && a.risk_score < 90);  // High: 70-89
    } else if (prioritySort === 'medium') {
      sorted = sorted.filter((a: any) => a.risk_score >= 50 && a.risk_score < 70);  // Medium: 50-69
    } else if (prioritySort === 'low') {
      sorted = sorted.filter((a: any) => a.risk_score < 50);  // Low: <50
    }
    // 'all' option shows everything

    return sorted;
  }, [alerts, prioritySort]);

  const totalPages = Math.ceil(sortedAnomalies.length / itemsPerPage);
  const paginatedAnomalies = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedAnomalies.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedAnomalies, currentPage]);

  if (loading) {
    return (
      <Card className="card-shadow col-span-1 md:col-span-2 lg:col-span-4">
        <CardContent className="p-6 text-center text-muted-foreground">
          Loading fraud alerts...
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
              Failed to load alerts: {error}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="card-shadow col-span-1 md:col-span-2 lg:col-span-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base font-semibold">
              Anomalies
              <Badge variant="destructive" className="ml-2 text-xs">{sortedAnomalies.length}</Badge>
            </CardTitle>

            <Select value={prioritySort} onValueChange={(value) => { setPrioritySort(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-[130px] h-8 text-xs">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="critical">Critical Priority</SelectItem>
                <SelectItem value="high">High Priority</SelectItem>
                <SelectItem value="medium">Medium Priority</SelectItem>
                <SelectItem value="low">Low Priority</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] overflow-y-auto overflow-x-auto">
            <Table className="min-w-[400px]">
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">ID</TableHead>
                  <TableHead className="text-xs">Amount</TableHead>
                  <TableHead className="text-xs">Date (UTC)</TableHead>
                  <TableHead className="text-xs">Location</TableHead>
                  <TableHead className="text-xs">IP Address</TableHead>
                  <TableHead className="text-xs">Verdict</TableHead>
                  <TableHead className="text-xs">Risk</TableHead>
                  <TableHead className="text-xs">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedAnomalies.map((anomaly: any) => (
                  <TableRow key={anomaly.transaction_id || anomaly.id} className="text-xs">
                    <TableCell className="font-mono text-xs">{anomaly.transaction_id || anomaly.id}</TableCell>
                    <TableCell className="font-medium text-destructive">
                      {anomaly.type === 'Login' ? 'N/A' : (anomaly.formatted_amount || `${currency} ${anomaly.amount?.toFixed(2) || '0.00'}`)}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-xs">
                      {formatTimestamp(anomaly.timestamp)}
                    </TableCell>
                    <TableCell className="text-xs">{anomaly.location || 'N/A'}</TableCell>
                    <TableCell className="text-xs font-mono">{anomaly.ip_address || 'N/A'}</TableCell>
                    <TableCell>{getVerdictBadge(anomaly.verdict || anomaly.type || anomaly.anomaly_type)}</TableCell>
                    <TableCell>{getRiskBadge(anomaly.risk_score || anomaly.final_risk_score || 0)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedAnomaly(anomaly)}
                        className="h-6 px-2"
                      >
                        Reason
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
      </Card>

      <Dialog open={!!selectedAnomaly} onOpenChange={() => setSelectedAnomaly(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Anomaly Details
            </DialogTitle>
            <DialogDescription>
              Why this transaction was flagged
            </DialogDescription>
          </DialogHeader>
          {selectedAnomaly && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground text-xs">{selectedAnomaly.type === 'Login' ? 'Login ID' : 'Transaction ID'}</p>
                  <p className="font-mono font-medium">{selectedAnomaly.transaction_id || selectedAnomaly.id}</p>
                </div>
                {selectedAnomaly.type !== 'Login' && (
                  <div>
                    <p className="text-muted-foreground text-xs">Amount</p>
                    <p className="font-semibold">{selectedAnomaly.formatted_amount || `${currency} ${selectedAnomaly.amount?.toFixed(2) || '0.00'}`}</p>
                  </div>
                )}
                <div>
                  <p className="text-muted-foreground text-xs">Date</p>
                  <p>{selectedAnomaly.timestamp ? (() => {
                    try {
                      let date = new Date(selectedAnomaly.timestamp);
                      if (isNaN(date.getTime())) {
                        const cleaned = selectedAnomaly.timestamp.replace(' UTC', '').replace(' at ', ' ');
                        date = new Date(cleaned);
                      }
                      return isNaN(date.getTime()) ? 'N/A' : format(date, 'PPp');
                    } catch {
                      return 'N/A';
                    }
                  })() : 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Location</p>
                  <p>{selectedAnomaly.location}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">IP Address</p>
                  <p className="font-mono">{selectedAnomaly.ip_address || 'N/A'}</p>
                </div>
              </div>

              <div className="pt-3 border-t border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline" className="text-xs">{selectedAnomaly.verdict || selectedAnomaly.category}</Badge>
                  {getRiskBadge(selectedAnomaly.risk_score || selectedAnomaly.final_risk_score || 0)}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {selectedAnomaly.explanation_text || 'Transaction flagged for review'}
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
