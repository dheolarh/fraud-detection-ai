import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AlertTriangle, ChevronLeft, ChevronRight, AlertCircle, Eye, Info, ShieldAlert, Fingerprint, Activity } from 'lucide-react';
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
    if (score >= 90) return <div className="h-2 w-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse" />;
    if (score >= 70) return <div className="h-2 w-2 rounded-full bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.6)]" />;
    if (score >= 30) return <div className="h-2 w-2 rounded-full bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.5)]" />;
    return <div className="h-2 w-2 rounded-full bg-blue-400 shadow-[0_0_6px_rgba(96,165,250,0.5)]" />;
  };

  const getVerdictBadge = (verdict: string) => {
    const isFlaged = verdict === 'FLAGGED' || verdict === 'Critical';
    const isMonitored = verdict === 'MONITORED';
    
    return (
      <div className={`px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-widest border ${
        isFlaged ? 'bg-red-500/10 text-red-500 border-red-500/20' : 
        isMonitored ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 
        'bg-white/5 text-muted-foreground border-white/10'
      }`}>
        {verdict}
      </div>
    );
  };

  const formatTimestamp = (timestamp: string | undefined) => {
    if (!timestamp) return 'N/A';
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

  const sortedAnomalies = useMemo(() => {
    if (!alerts) return [];
    let sorted = [...alerts];
    if (prioritySort === 'critical') sorted = sorted.filter((a: any) => a.risk_score >= 90);
    else if (prioritySort === 'high') sorted = sorted.filter((a: any) => a.risk_score >= 70 && a.risk_score < 90);
    else if (prioritySort === 'medium') sorted = sorted.filter((a: any) => a.risk_score >= 30 && a.risk_score < 70);
    else if (prioritySort === 'low') sorted = sorted.filter((a: any) => a.risk_score < 30);
    return sorted;
  }, [alerts, prioritySort]);

  const totalPages = Math.ceil(sortedAnomalies.length / itemsPerPage);
  const paginatedAnomalies = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedAnomalies.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedAnomalies, currentPage]);

  if (loading) {
    return (
      <Card className="glass-panel card-shadow-lg col-span-1 md:col-span-2 lg:col-span-4 animate-pulse">
        <CardContent className="h-64 flex items-center justify-center">
           <Activity className="h-6 w-6 text-muted-foreground/30 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="glass-panel card-shadow-lg col-span-1 md:col-span-2 lg:col-span-4 overflow-hidden border-white/5">
        <CardHeader className="pb-3 bg-white/[0.01] border-b border-white/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
               <div className="h-8 w-8 rounded-lg bg-red-500/10 flex items-center justify-center border border-red-500/20">
                  <ShieldAlert className="h-4 w-4 text-red-400" />
               </div>
               <CardTitle className="text-sm font-bold font-display uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Badge variant="destructive" className="h-4 w-4 p-0 flex items-center justify-center text-[8px] font-black shadow-[0_0_8px_rgba(239,68,68,0.4)]">
                   {sortedAnomalies.length}
                </Badge>
                Anomalies Matrix
              </CardTitle>
            </div>

            <Select value={prioritySort} onValueChange={(value) => { setPrioritySort(value); setCurrentPage(1); }}>
              <SelectTrigger className="w-[140px] h-9 text-xs bg-white/5 border-white/5 rounded-xl font-bold uppercase tracking-widest">
                <SelectValue placeholder="Priority Level" />
              </SelectTrigger>
              <SelectContent className="glass-panel border-white/10">
                <SelectItem value="all">Global Feed</SelectItem>
                <SelectItem value="critical">Critical (90+)</SelectItem>
                <SelectItem value="high">High Risk (70+)</SelectItem>
                <SelectItem value="medium">Medium (30+)</SelectItem>
                <SelectItem value="low">Sub-Risk {"(<30)"}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-[350px] overflow-y-auto scrollbar-thin">
            <Table>
              <TableHeader className="sticky top-0 bg-background/80 backdrop-blur-md z-20">
                <TableRow className="border-b border-white/5 hover:bg-transparent">
                  <TableHead className="text-[10px] font-black uppercase tracking-widest h-12 pl-6">Signal ID</TableHead>
                  <TableHead className="text-[10px] font-black uppercase tracking-widest h-12">Value / Location</TableHead>
                  <TableHead className="text-[10px] font-black uppercase tracking-widest h-12">Signal Identity</TableHead>
                  <TableHead className="text-[10px] font-black uppercase tracking-widest h-12 text-right pr-6">Status / Risk</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedAnomalies.map((anomaly: any) => (
                  <TableRow key={anomaly.transaction_id || anomaly.id} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors group">
                    <TableCell className="pl-6 py-4">
                       <div className="flex flex-col gap-0.5">
                          <span className="text-xs font-bold font-mono text-white/90">{anomaly.transaction_id ? `HOV-${anomaly.transaction_id}` : anomaly.id}</span>
                          <span className="text-[10px] font-bold text-muted-foreground/50 uppercase tracking-widest">{formatTimestamp(anomaly.timestamp)}</span>
                       </div>
                    </TableCell>
                    <TableCell className="py-4">
                       <div className="flex flex-col gap-0.5">
                          <span className={`text-xs font-bold ${anomaly.type === 'Login' ? 'text-primary/60' : 'text-red-400 font-display'}`}>
                             {anomaly.type === 'Login' ? 'Auth Verification' : (anomaly.formatted_amount || `${currency} ${anomaly.amount?.toFixed(2) || '0.00'}`)}
                          </span>
                          <span className="text-[10px] font-bold text-muted-foreground/50 uppercase tracking-widest truncate max-w-[150px]">{anomaly.location || 'Unknown Node'}</span>
                       </div>
                    </TableCell>
                    <TableCell className="py-4">
                       <div className="flex items-center gap-2">
                          <div className="p-1.5 rounded-lg bg-white/5 border border-white/5">
                             {anomaly.type === 'Login' ? <Fingerprint className="h-3.5 w-3.5 text-primary/60" /> : <AlertTriangle className="h-3.5 w-3.5 text-red-400" />}
                          </div>
                          <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{anomaly.type || 'Transaction Anomaly'}</span>
                       </div>
                    </TableCell>
                    <TableCell className="text-right pr-6 py-4">
                       <div className="flex flex-col items-end gap-2">
                          {getVerdictBadge(anomaly.verdict || anomaly.type || anomaly.anomaly_type)}
                          <div className="flex items-center gap-2">
                             <span className="text-[10px] font-black text-muted-foreground/40 italic">{anomaly.risk_score || 0}% RAW</span>
                             {getRiskBadge(anomaly.risk_score || 0)}
                          </div>
                          <Button variant="ghost" size="sm" onClick={() => setSelectedAnomaly(anomaly)} className="h-6 px-2 text-[9px] font-black uppercase tracking-widest hover:bg-primary/10 hover:text-primary transition-all">
                             View Analytics
                             <Eye className="h-3 w-3 ml-1.5" />
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
                   Page {currentPage} of {totalPages}
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
      </Card>

      <Dialog open={!!selectedAnomaly} onOpenChange={() => setSelectedAnomaly(null)}>
        <DialogContent className="max-w-md glass-panel border-white/10 p-0 overflow-hidden shadow-2xl">
          <div className="bg-red-500/10 p-6 border-b border-red-500/20">
             <DialogHeader>
               <DialogTitle className="flex items-center gap-3 text-red-400 font-display text-xl uppercase tracking-widest font-black">
                 <ShieldAlert className="h-6 w-6" />
                 Signal Breakdown
               </DialogTitle>
               <DialogDescription className="text-red-400/60 font-bold uppercase tracking-widest text-[10px] pt-1">
                 Sentinel Threat Intelligence Report
               </DialogDescription>
             </DialogHeader>
          </div>

          {selectedAnomaly && (
            <div className="p-6 space-y-8 bg-white/[0.02]">
              <div className="grid grid-cols-2 gap-6 pb-2">
                <div className="space-y-1">
                  <p className="text-muted-foreground text-[10px] font-black uppercase tracking-widest">Signal Identifier</p>
                  <p className="font-mono font-bold text-sm text-white">{selectedAnomaly.transaction_id ? `HOV-${selectedAnomaly.transaction_id}` : selectedAnomaly.id}</p>
                </div>
                {selectedAnomaly.type !== 'Login' && (
                  <div className="space-y-1">
                    <p className="text-muted-foreground text-[10px] font-black uppercase tracking-widest">Involved Asset</p>
                    <p className="font-bold text-sm font-display text-white">{selectedAnomaly.formatted_amount || `${currency} ${selectedAnomaly.amount?.toFixed(2) || '0.00'}`}</p>
                  </div>
                )}
                <div className="space-y-1">
                  <p className="text-muted-foreground text-[10px] font-black uppercase tracking-widest">Temporal Stamp</p>
                  <p className="text-sm font-bold text-white/80">{formatTimestamp(selectedAnomaly.timestamp)}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground text-[10px] font-black uppercase tracking-widest">Geographic Node</p>
                  <p className="text-sm font-bold text-white/80">{selectedAnomaly.location || 'Unknown'}</p>
                </div>
              </div>

              <div className="relative group">
                 <div className="absolute inset-0 bg-white/5 blur-xl group-hover:bg-white/10 transition-all rounded-3xl" />
                 <div className="relative p-5 glass-panel rounded-2xl border-white/5 space-y-4">
                    <div className="flex items-center justify-between border-b border-white/5 pb-3">
                       <div className="flex items-center gap-2">
                          <Info className="h-4 w-4 text-primary/60" />
                          <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Expert Evaluation</span>
                       </div>
                       <Badge variant="outline" className={`text-[10px] font-black uppercase tracking-widest border-white/10 ${selectedAnomaly.risk_score >= 90 ? 'bg-red-500/10 text-red-400' : 'bg-primary/10 text-primary'}`}>
                          {selectedAnomaly.risk_score}% Severity
                       </Badge>
                    </div>
                    <p className="text-sm text-gray-200 leading-relaxed font-bold italic opaity-90">
                       " {selectedAnomaly.explanation_text || 'Automated detection flagged this sequence as highly irregular relative to established behavioral patterns.'} "
                    </p>
                 </div>
              </div>

              <div className="flex gap-3">
                 <Button onClick={() => setSelectedAnomaly(null)} className="flex-1 h-12 bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-bold uppercase tracking-widest rounded-xl transition-all">
                    Acknowledge
                 </Button>
                 <Button onClick={() => { /* Potential escalation logic */ }} className="flex-1 h-12 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 text-xs font-bold uppercase tracking-widest rounded-xl transition-all">
                    Escalate Case
                 </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
