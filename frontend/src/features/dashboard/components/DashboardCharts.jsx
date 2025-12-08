import { useMemo, useState, lazy, Suspense } from 'react';
import Card from '../../../components/ui/Card.jsx';
import { ChartSkeleton } from '../../../components/ui/Skeleton.jsx';
import { EmptyData } from '../../../components/ui/EmptyState.jsx';

// Lazy load Recharts pour optimiser le bundle
const LazyAreaChart = lazy(() =>
  import('recharts').then((m) => ({ default: m.AreaChart }))
);
const LazyBarChart = lazy(() =>
  import('recharts').then((m) => ({ default: m.BarChart }))
);
const LazyResponsiveContainer = lazy(() =>
  import('recharts').then((m) => ({ default: m.ResponsiveContainer }))
);

// Import synchrone des composants légers de Recharts
import {
  Area,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
  AreaChart,
  BarChart,
} from 'recharts';

/**
 * WeeklyFlowsChart - Graphique des flux hebdomadaires (entrées/sorties)
 * Pattern: Lazy loading, window selector, responsive
 */
export function WeeklyFlowsChart({
  data,
  loading = false,
  windowOptions = [4, 8, 12, 20],
  defaultWindow = 8,
}) {
  const [window, setWindow] = useState(defaultWindow);

  const chartData = useMemo(() => {
    if (!data?.length) return [];
    return data.slice(-window).map((entry) => ({
      ...entry,
      label: new Date(entry.semaine).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
      }),
      entrees: Number(entry.entrees) || 0,
      sorties: Number(entry.sorties) || 0,
      net: (Number(entry.entrees) || 0) - (Number(entry.sorties) || 0),
    }));
  }, [data, window]);

  if (loading) {
    return (
      <ChartContainer title="Flux hebdomadaires">
        <ChartSkeleton />
      </ChartContainer>
    );
  }

  if (!chartData.length) {
    return (
      <ChartContainer title="Flux hebdomadaires">
        <EmptyData />
      </ChartContainer>
    );
  }

  return (
    <ChartContainer
      title="Flux hebdomadaires"
      action={
        <WindowSelector
          value={window}
          options={windowOptions}
          onChange={setWindow}
        />
      }
    >
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorEntrees" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorSorties" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              width={40}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              height={36}
              iconType="circle"
              iconSize={8}
              formatter={(value) => (
                <span className="text-xs text-slate-600">{value}</span>
              )}
            />
            <Area
              type="monotone"
              dataKey="entrees"
              name="Entrées"
              stroke="#0ea5e9"
              strokeWidth={2}
              fill="url(#colorEntrees)"
            />
            <Area
              type="monotone"
              dataKey="sorties"
              name="Sorties"
              stroke="#f97316"
              strokeWidth={2}
              fill="url(#colorSorties)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  );
}

/**
 * CategoryStockChart - Graphique des stocks par catégorie
 * Pattern: Horizontal bars, sorted, limited
 */
export function CategoryStockChart({ data, loading = false, limit = 6 }) {
  const chartData = useMemo(() => {
    if (!data?.length) return [];

    const totals = data.reduce((acc, product) => {
      const key = product.categorie || 'NC';
      acc[key] = (acc[key] || 0) + (Number(product.stock_actuel) || 0);
      return acc;
    }, {});

    return Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([label, qty]) => ({ label, qty }));
  }, [data, limit]);

  if (loading) {
    return (
      <ChartContainer title="Stocks par catégorie">
        <ChartSkeleton />
      </ChartContainer>
    );
  }

  if (!chartData.length) {
    return (
      <ChartContainer title="Stocks par catégorie">
        <EmptyData />
      </ChartContainer>
    );
  }

  return (
    <ChartContainer title="Stocks par catégorie" subtitle="Mix catalogue">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={true} vertical={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              tickFormatter={(value) => value.toLocaleString('fr-FR')}
            />
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              width={55}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: '#f1f5f9' }}
            />
            <Bar
              dataKey="qty"
              name="Stock (unités)"
              fill="#6366f1"
              radius={[0, 4, 4, 0]}
              maxBarSize={24}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  );
}

/**
 * ChartContainer - Wrapper pour les graphiques avec header
 */
function ChartContainer({ title, subtitle, action, children }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          {subtitle && (
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
              {subtitle}
            </p>
          )}
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

/**
 * WindowSelector - Sélecteur de fenêtre temporelle
 */
function WindowSelector({ value, options, onChange }) {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-500">
      <span>Fenêtre</span>
      <select
        className="rounded-full border border-slate-200 bg-white px-2 py-1 text-xs focus:border-brand-400 focus:outline-none focus:ring-1 focus:ring-brand-200"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt} sem.
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * CustomTooltip - Tooltip personnalisé pour les graphiques
 */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg bg-slate-900 px-3 py-2 text-xs text-white shadow-lg">
      <p className="font-medium mb-1">{label}</p>
      {payload.map((entry, index) => (
        <p key={index} className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-slate-300">{entry.name}:</span>
          <span className="font-medium">
            {Number(entry.value).toLocaleString('fr-FR')}
          </span>
        </p>
      ))}
    </div>
  );
}

/**
 * DashboardChartsGrid - Layout grille pour les graphiques
 */
export default function DashboardChartsGrid({
  weeklyData,
  products,
  loading = false,
}) {
  return (
    <Card className="grid gap-8 lg:grid-cols-2 p-6">
      <WeeklyFlowsChart data={weeklyData} loading={loading} />
      <CategoryStockChart data={products} loading={loading} />
    </Card>
  );
}
