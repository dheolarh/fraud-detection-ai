import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useGeoAnalytics, useBankCurrency } from '@/hooks/useData';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Globe2 } from 'lucide-react';
import { formatCurrencyCompact } from '@/utils/currency';

export function GeoAnalyticsCard() {
  const userId = localStorage.getItem('user_id') || 'HOV-2426-1226';
  const { geoData, loading, error } = useGeoAnalytics(userId, 30000);
  const { currency: bankCurrency } = useBankCurrency();

  const formatValue = (value: number) => {
    return formatCurrencyCompact(value, bankCurrency);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-panel p-3 rounded-xl border-white/10 shadow-2xl space-y-1">
          <p className="text-xs font-bold font-display uppercase tracking-wider text-white mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-3 justify-between">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="text-[10px] font-bold text-muted-foreground uppercase">{entry.name}</span>
              </div>
              <span className="text-xs font-bold text-white">{formatValue(entry.value)}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="glass-panel card-shadow-lg overflow-hidden h-full col-span-1 md:col-span-2 lg:col-span-4">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold font-display uppercase tracking-widest text-muted-foreground flex items-center gap-2">
            <Globe2 className="h-4 w-4" />
            Global Exposure
          </CardTitle>

          <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-sm bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.3)]"></div>
              <span className="text-muted-foreground">Inward</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-sm bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.3)]"></div>
              <span className="text-muted-foreground">Outward</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        {loading && (
          <div className="animate-pulse space-y-4 py-10">
             {[...Array(5)].map((_, i) => (
                <div key={i} className="flex gap-4">
                   <div className="h-4 bg-white/5 rounded w-20" />
                   <div className="h-4 bg-white/5 rounded flex-1" />
                </div>
             ))}
          </div>
        )}

        {error && (
          <Alert variant="destructive" className="bg-destructive/10 border-destructive/20 text-destructive text-xs">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>Failed to load geo analytics: {error}</AlertDescription>
          </Alert>
        )}

        {!loading && !error && geoData && geoData.length > 0 && (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={geoData} layout="vertical" margin={{ left: 10, right: 20, top: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.03)" />
              <XAxis
                type="number"
                tickFormatter={formatValue}
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)', fontWeight: 700 }}
              />
              <YAxis
                type="category"
                dataKey="country"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.8)', fontWeight: 700 }}
                width={80}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
              <Bar
                dataKey="incoming"
                stackId="a"
                fill="hsl(217, 91%, 60%)"
                radius={[2, 0, 0, 2]}
                name="Incoming"
                barSize={12}
              />
              <Bar
                dataKey="outgoing"
                stackId="a"
                fill="hsl(0, 72%, 51%)"
                radius={[0, 4, 4, 0]}
                name="Outgoing"
                barSize={12}
              />
            </BarChart>
          </ResponsiveContainer>
        )}

        {!loading && !error && (!geoData || geoData.length === 0) && (
          <div className="flex flex-col items-center justify-center py-20 bg-white/[0.02] rounded-2xl border border-dashed border-white/5">
             <Globe2 className="h-8 w-8 text-muted-foreground/30 mb-3" />
             <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground/50">Zero Global Footprint</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
