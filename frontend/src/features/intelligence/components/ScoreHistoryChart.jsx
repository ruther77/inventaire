import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Skeleton } from '../../../components/ui/Skeleton.jsx';
import Card from '../../../components/ui/Card.jsx';

/**
 * ScoreHistoryChart - Graphique de l'évolution des scores dans le temps
 */
export default function ScoreHistoryChart({ data = [], loading = false }) {
  if (loading) {
    return (
      <Card padding="lg">
        <Skeleton className="h-8 w-48 mb-4" />
        <Skeleton className="h-64 w-full" />
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card padding="lg">
        <div className="flex flex-col items-center justify-center h-64 text-slate-400">
          <svg
            className="h-12 w-12 mb-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
            />
          </svg>
          <p className="text-sm">Aucune donnée historique disponible</p>
        </div>
      </Card>
    );
  }

  // Transform data for recharts
  const chartData = data.map((item) => ({
    date: new Date(item.calculated_at).toLocaleDateString('fr-FR', {
      month: 'short',
      day: 'numeric',
    }),
    'Score Global': Math.round((item.overall_score || 0) * 100),
    'Prix': Math.round((item.price_stability_score || 0) * 100),
    'Livraison': Math.round((item.delivery_reliability_score || 0) * 100),
    'Factures': Math.round((item.invoice_accuracy_score || 0) * 100),
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-panel p-3 border border-white/10">
          <p className="text-sm font-medium text-white mb-2">{label}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center justify-between gap-4 text-xs">
              <span style={{ color: entry.color }}>{entry.name}:</span>
              <span className="font-semibold text-white">{entry.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card padding="lg">
      <h3 className="text-lg font-semibold text-white mb-6">
        Évolution des Scores (12 derniers mois)
      </h3>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
          <XAxis
            dataKey="date"
            stroke="rgba(255, 255, 255, 0.3)"
            tick={{ fill: 'rgba(255, 255, 255, 0.6)', fontSize: 12 }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="rgba(255, 255, 255, 0.3)"
            tick={{ fill: 'rgba(255, 255, 255, 0.6)', fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
            formatter={(value) => <span className="text-sm text-slate-300">{value}</span>}
          />
          <Line
            type="monotone"
            dataKey="Score Global"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="Prix"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 3 }}
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="Livraison"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ fill: '#f59e0b', r: 3 }}
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="Factures"
            stroke="#ec4899"
            strokeWidth={2}
            dot={{ fill: '#ec4899', r: 3 }}
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Score Global', color: 'bg-blue-500' },
          { label: 'Prix', color: 'bg-emerald-500' },
          { label: 'Livraison', color: 'bg-amber-500' },
          { label: 'Factures', color: 'bg-pink-500' },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${item.color}`} />
            <span className="text-xs text-slate-400">{item.label}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
