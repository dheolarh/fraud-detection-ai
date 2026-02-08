import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useSuspicionLevel } from '@/hooks/useData';
import { AlertTriangle, TrendingUp } from 'lucide-react';

export function ActivityScoreCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const { suspicionLevel, description, flaggedCount, averageRiskScore, loading } = useSuspicionLevel(userId);

  const circumference = 2 * Math.PI * 60;
  const strokeDashoffset = circumference - (suspicionLevel / 5) * circumference;

  const getScoreColor = () => {
    if (suspicionLevel === 0) return 'text-success';
    if (suspicionLevel <= 2) return 'text-success';
    if (suspicionLevel <= 3) return 'text-warning';
    return 'text-destructive';
  };

  const getStrokeColor = () => {
    if (suspicionLevel === 0) return 'hsl(var(--success))';
    if (suspicionLevel <= 2) return 'hsl(var(--success))';
    if (suspicionLevel <= 3) return 'hsl(var(--warning))';
    return 'hsl(var(--destructive))';
  };

  const getRiskLevel = () => {
    if (suspicionLevel === 0) return { label: 'No Suspicion', color: 'text-success' };
    if (suspicionLevel <= 2) return { label: 'Low Suspicion', color: 'text-success' };
    if (suspicionLevel <= 3) return { label: 'Moderate Suspicion', color: 'text-warning' };
    return { label: 'High Suspicion', color: 'text-destructive' };
  };

  const riskLevel = getRiskLevel();

  if (loading) {
    return (
      <Card className="card-shadow">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">
            Suspicion Level
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <p className="text-sm text-muted-foreground">Loading...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="card-shadow">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          Suspicion Level
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center py-4">
        <div className="relative">
          <svg className="w-36 h-36 transform -rotate-90">
            <circle
              cx="72"
              cy="72"
              r="60"
              fill="none"
              stroke="hsl(var(--muted))"
              strokeWidth="12"
            />
            <circle
              cx="72"
              cy="72"
              r="60"
              fill="none"
              stroke={getStrokeColor()}
              strokeWidth="12"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-bold ${getScoreColor()}`}>
              {suspicionLevel}
            </span>
            <span className="text-xs text-muted-foreground">/ 5</span>
          </div>
        </div>

        <div className="mt-4 text-center">
          <p className={`text-sm font-medium ${riskLevel.color}`}>
            {riskLevel.label}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        </div>

        {/* Additional Metrics */}
        <div className="w-full mt-4 pt-4 border-t border-border space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <span>Flagged Transactions</span>
            </div>
            <span className="font-semibold text-foreground">{flaggedCount || 0}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
