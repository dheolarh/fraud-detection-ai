import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useGeoAnalytics, useBankCurrency } from '@/hooks/useData';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { formatCurrencyCompact } from '@/utils/currency';

export function GeoAnalyticsCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const { geoData, loading, error } = useGeoAnalytics(userId, 30000);
  const { currency: bankCurrency } = useBankCurrency();

  const formatValue = (value: number) => {
    return formatCurrencyCompact(value, bankCurrency);
  };

  return (
    <Card className="card-shadow col-span-1 md:col-span-2">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold">
            Geo-Analytics
          </CardTitle>

          {/* Color Legend */}
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm bg-[hsl(217,91%,60%)]"></div>
              <span className="text-muted-foreground">Incoming</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm bg-destructive"></div>
              <span className="text-muted-foreground">Outgoing</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading && (
          <p className="text-sm text-muted-foreground text-center py-20">Loading geo analytics...</p>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load geo analytics: {error}
            </AlertDescription>
          </Alert>
        )}

        {!loading && !error && geoData && geoData.length > 0 && (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={geoData} layout="vertical" margin={{ left: 20, right: 20 }}>
              <XAxis
                type="number"
                tickFormatter={formatValue}
                tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                type="category"
                dataKey="country"
                tick={{ fontSize: 10, fill: 'hsl(var(--foreground))' }}
                width={90}
              />
              <Tooltip
                formatter={(value: number) => formatValue(value)}
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Bar
                dataKey="incoming"
                stackId="a"
                fill="hsl(217, 91%, 60%)"
                radius={[0, 0, 0, 0]}
                name="Incoming"
              />
              <Bar
                dataKey="outgoing"
                stackId="a"
                fill="hsl(var(--destructive))"
                radius={[0, 4, 4, 0]}
                name="Outgoing"
              />
            </BarChart>
          </ResponsiveContainer>
        )}

        {!loading && !error && (!geoData || geoData.length === 0) && (
          <p className="text-sm text-muted-foreground text-center py-20">No transaction data available</p>
        )}
      </CardContent>
    </Card>
  );
}
