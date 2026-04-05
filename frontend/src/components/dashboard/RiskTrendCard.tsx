import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Activity, ShieldAlert } from 'lucide-react';
import { useRiskTrend } from '@/hooks/useData';

export function RiskTrendCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const {
    avgRiskScore7d,
    avgRiskScore30d,
    flaggedCount7d,
    flaggedCount30d,
    trend,
    loading,
  } = useRiskTrend(userId);

  const delta = avgRiskScore7d - avgRiskScore30d;
  const isUp = trend === 'up';
  const isDown = trend === 'down';

  const TrendIcon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;

  const trendLabel = isUp ? 'Increasing Risk' : isDown ? 'Improving Trend' : 'Stable Risk';
  const trendClass = isUp
    ? 'text-red-500'
    : isDown
      ? 'text-emerald-500'
      : 'text-muted-foreground';
      
  const glowClass = isUp 
    ? 'shadow-[0_0_15px_rgba(239,68,68,0.3)] border-red-500/20 bg-red-500/10'
    : isDown
      ? 'shadow-[0_0_15px_rgba(16,185,129,0.3)] border-emerald-500/20 bg-emerald-500/10'
      : 'border-white/10 bg-white/5';

  if (loading) {
    return (
      <Card className="glass-panel card-shadow-lg animate-pulse h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Risk Trend</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-20">
          <Activity className="h-6 w-6 text-muted-foreground/30 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-panel card-shadow-lg overflow-hidden h-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold font-display uppercase tracking-widest text-muted-foreground flex items-center gap-2">
            <ShieldAlert className="h-4 w-4" />
            Risk Index
          </CardTitle>
          <div className={`p-1.5 rounded-lg border ${glowClass}`}>
            <TrendIcon className={`h-4 w-4 ${trendClass}`} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-end justify-between">
          <div className="space-y-1">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Avg Fraud Score</p>
            <div className="flex items-baseline gap-2">
               <p className={`text-3xl font-bold font-display tracking-tight ${trendClass}`}>
                {avgRiskScore7d.toFixed(1)}%
              </p>
              <span className={`text-xs font-semibold ${trendClass}`}>
                {delta >= 0 ? '+' : ''}{delta.toFixed(1)}%
              </span>
            </div>
          </div>
          <Badge variant="outline" className="text-[10px] bg-white/5 border-white/10 rounded-full h-5 px-3">
            7 Days Active
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 group hover:bg-white/[0.04] transition-all">
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mb-1">Weekly</p>
            <p className="text-lg font-bold font-display text-white">{avgRiskScore7d.toFixed(1)}%</p>
            <div className="flex items-center gap-1.5 mt-1.5">
               <div className="h-1 w-1 rounded-full bg-red-400" />
               <p className="text-[10px] text-muted-foreground font-medium">{flaggedCount7d} Flagged</p>
            </div>
          </div>
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 group hover:bg-white/[0.04] transition-all">
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold mb-1">Monthly</p>
            <p className="text-lg font-bold font-display text-muted-foreground">{avgRiskScore30d.toFixed(1)}%</p>
             <div className="flex items-center gap-1.5 mt-1.5">
               <div className="h-1 w-1 rounded-full bg-muted-foreground/30" />
               <p className="text-[10px] text-muted-foreground font-medium">{flaggedCount30d} Reports</p>
            </div>
          </div>
        </div>

        <div className={`pt-4 border-t border-white/10 flex items-center justify-center`}>
           <div className={`px-4 py-2 rounded-xl text-xs font-bold font-display uppercase tracking-wider ${trendClass} bg-current/5 border border-current/10 flex items-center gap-2`}>
              <div className={`h-1.5 w-1.5 rounded-full bg-current animate-pulse shadow-sm`} />
              {trendLabel}
           </div>
        </div>
      </CardContent>
    </Card>
  );
}
