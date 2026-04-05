import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useSuspicionLevel } from '@/hooks/useData';
import { ShieldCheck, ShieldAlert, Zap } from 'lucide-react';

export function ActivityScoreCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const { suspicionLevel, description, flaggedCount, averageRiskScore, loading } = useSuspicionLevel(userId);

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (suspicionLevel / 5) * circumference;

  const getScoreColor = () => {
    if (suspicionLevel <= 2) return 'text-emerald-400';
    if (suspicionLevel <= 3) return 'text-amber-400';
    return 'text-red-500';
  };

  const getStrokeColor = () => {
    if (suspicionLevel <= 2) return 'hsl(142, 76%, 36%)';
    if (suspicionLevel <= 3) return 'hsl(38, 92%, 50%)';
    return 'hsl(0, 72%, 51%)';
  };
  
  const getGlowColor = () => {
    if (suspicionLevel <= 2) return 'shadow-[0_0_20px_rgba(16,185,129,0.3)]';
    if (suspicionLevel <= 3) return 'shadow-[0_0_20px_rgba(251,191,36,0.3)]';
    return 'shadow-[0_0_20px_rgba(239,68,68,0.3)]';
  };

  const riskLevel = (() => {
    if (suspicionLevel <= 1) return { label: 'Secured', icon: ShieldCheck, color: 'text-emerald-400' };
    if (suspicionLevel <= 2) return { label: 'Monitored', icon: ShieldCheck, color: 'text-emerald-400' };
    if (suspicionLevel <= 3) return { label: 'Suspicious', icon: ShieldAlert, color: 'text-amber-400' };
    return { label: 'Critical', icon: ShieldAlert, color: 'text-red-500' };
  })();

  const StatusIcon = riskLevel.icon;

  if (loading) {
    return (
      <Card className="glass-panel card-shadow-lg animate-pulse h-full">
         <CardHeader className="pb-3">
          <CardTitle className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Activity Pulse</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-20">
          <div className="h-32 w-32 rounded-full border-4 border-white/5 border-t-primary/20 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-panel card-shadow-lg overflow-hidden h-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold font-display uppercase tracking-widest text-muted-foreground flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Activity Pulse
          </CardTitle>
          <div className={`p-1 rounded-full bg-white/5 border border-white/10`}>
             <StatusIcon className={`h-3.5 w-3.5 ${riskLevel.color}`} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center py-2 space-y-6">
        <div className="relative group">
          {/* Outer Ring Glow */}
          <div className={`absolute inset-0 rounded-full blur-2xl opacity-20 transition-all duration-1000 ${suspicionLevel > 3 ? 'bg-red-500' : 'bg-emerald-500'}`} />
          
          <svg className="w-36 h-36 transform -rotate-90 relative z-10">
            <circle
              cx="72"
              cy="72"
              r={radius}
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="10"
            />
            <circle
              cx="72"
              cy="72"
              r={radius}
              fill="none"
              stroke={getStrokeColor()}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
              filter="drop-shadow(0 0 8px rgba(255,255,255,0.1))"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
            <span className={`text-4xl font-bold font-display tracking-tight transition-colors ${getScoreColor()}`}>
              {suspicionLevel}
            </span>
            <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest">/ 5 Factor</span>
          </div>
        </div>

        <div className="text-center space-y-1">
          <p className={`text-xs font-bold font-display uppercase tracking-wider ${riskLevel.color}`}>
            {riskLevel.label}
          </p>
          <p className="text-[11px] text-muted-foreground leading-relaxed px-4 opacity-80">
            {description}
          </p>
        </div>

        <div className="w-full pt-4 border-t border-white/5 space-y-3">
          <div className="flex items-center justify-between text-[11px] font-bold p-2.5 rounded-xl bg-white/[0.02] border border-white/5">
            <span className="text-muted-foreground uppercase tracking-widest">Flagged Txns</span>
            <span className={`px-2 py-0.5 rounded-md ${flaggedCount > 0 ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
              {flaggedCount || 0}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
