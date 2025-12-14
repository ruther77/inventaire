import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui';

/**
 * CostBreakdownChart - Graphique de décomposition des coûts par ingrédient
 *
 * Props:
 * - data: Array<{name, value, percentage, unite}>
 * - title: string
 * - isLoading: boolean
 */
export default function CostBreakdownChart({ data = [], title = 'Décomposition des coûts', isLoading = false }) {
  const COLORS = [
    '#f43f5e', // rose
    '#ec4899', // pink
    '#a855f7', // purple
    '#8b5cf6', // violet
    '#6366f1', // indigo
    '#3b82f6', // blue
    '#0ea5e9', // sky
    '#06b6d4', // cyan
    '#14b8a6', // teal
    '#10b981', // emerald
  ];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="text-sm font-semibold text-slate-900 mb-1">{item.name}</p>
          <p className="text-xs text-slate-600">
            Coût: <span className="font-semibold">{formatCurrency(item.value)}</span>
          </p>
          <p className="text-xs text-slate-600">
            Part: <span className="font-semibold">{item.percentage.toFixed(1)}%</span>
          </p>
          {item.unite && (
            <p className="text-xs text-slate-500 mt-1">Unité: {item.unite}</p>
          )}
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center">
            <p className="text-sm text-slate-500">Aucune donnée disponible</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      </CardHeader>
      <CardContent>
        <div className="grid lg:grid-cols-[1fr,300px] gap-6">
          {/* Graphique */}
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ percentage }) => `${percentage.toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Légende détaillée */}
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {data.map((item, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors"
              >
                <div
                  className="w-4 h-4 rounded-full flex-shrink-0"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">{item.name}</p>
                  <p className="text-xs text-slate-500">
                    {formatCurrency(item.value)} ({item.percentage.toFixed(1)}%)
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
