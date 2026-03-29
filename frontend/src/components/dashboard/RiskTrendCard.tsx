import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
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
    ? 'text-destructive'
    : isDown
      ? 'text-success'
      : 'text-muted-foreground';

  if (loading) {
    return (
      <Card className="card-shadow">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">Risk Trend</CardTitle>
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
        <CardTitle className="text-base font-semibold">Risk Trend</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground">Average Risk</p>
            <p className="text-2xl font-bold">{avgRiskScore7d.toFixed(1)}%</p>
          </div>
          <Badge variant="outline" className="text-xs">
            7d
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-md border border-border p-3">
            <p className="text-xs text-muted-foreground">7d Avg</p>
            <p className="text-lg font-semibold">{avgRiskScore7d.toFixed(1)}%</p>
            <p className="text-xs text-muted-foreground mt-1">{flaggedCount7d} flagged</p>
          </div>
          <div className="rounded-md border border-border p-3">
            <p className="text-xs text-muted-foreground">30d Avg</p>
            <p className="text-lg font-semibold">{avgRiskScore30d.toFixed(1)}%</p>
            <p className="text-xs text-muted-foreground mt-1">{flaggedCount30d} flagged</p>
          </div>
        </div>

        <div className="pt-2 border-t border-border flex items-center justify-between">
          <div className={`flex items-center gap-1 text-sm font-medium ${trendClass}`}>
            <TrendIcon className="h-4 w-4" />
            <span>{trendLabel}</span>
          </div>
          <span className={`text-sm font-semibold ${trendClass}`}>
            {delta >= 0 ? '+' : ''}{delta.toFixed(1)}%
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
