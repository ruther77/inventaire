import { useMemo } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp, TrendingDown, Target } from 'lucide-react';

/**
 * FoodCostAnalysisPanel - Panneau d'analyse du food cost
 *
 * Props:
 * - data: {
 *     evolution: Array<{date, food_cost_pct, objectif}>,
 *     current: number,
 *     objectif: number,
 *     by_category: Array<{category, food_cost_pct, count}>
 *   }
 * - isLoading: boolean
 */
export default function FoodCostAnalysisPanel({ data = {}, isLoading = false }) {
  const { evolution = [], current = 0, objectif = 30, by_category = [] } = data;

  const ecartObjectif = useMemo(() => {
    return current - objectif;
  }, [current, objectif]);

  const trend = useMemo(() => {
    if (evolution.length < 2) return 0;
    const last = evolution[evolution.length - 1]?.food_cost_pct || 0;
    const previous = evolution[evolution.length - 2]?.food_cost_pct || 0;
    return last - previous;
  }, [evolution]);

  const formatPercent = (value) => `${value?.toFixed(1) || 0}%`;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-400">Food Cost Analysis</p>
              <h3 className="text-lg font-semibold text-slate-900">Chargement...</h3>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-400">Food Cost Analysis</p>
            <h3 className="text-lg font-semibold text-slate-900">Évolution & Objectifs</h3>
          </div>
          <div className="flex items-center gap-4">
            {/* Écart objectif */}
            <div className="text-right">
              <p className="text-xs text-slate-500">Écart objectif</p>
              <p className={`text-lg font-semibold ${ecartObjectif > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {ecartObjectif > 0 ? '+' : ''}{formatPercent(ecartObjectif)}
              </p>
            </div>

            {/* Tendance */}
            <div className="flex items-center gap-2">
              {trend > 0 ? (
                <TrendingUp className="w-5 h-5 text-rose-600" />
              ) : trend < 0 ? (
                <TrendingDown className="w-5 h-5 text-emerald-600" />
              ) : (
                <div className="w-5 h-5" />
              )}
              <div>
                <p className="text-xs text-slate-500">Tendance</p>
                <p className={`text-sm font-semibold ${trend > 0 ? 'text-rose-600' : trend < 0 ? 'text-emerald-600' : 'text-slate-600'}`}>
                  {trend > 0 ? '+' : ''}{formatPercent(trend)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Graphique d'évolution */}
        <div className="mb-6">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={evolution} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="date"
                stroke="#64748b"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                stroke="#64748b"
                style={{ fontSize: '12px' }}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                }}
                formatter={(value) => [`${value.toFixed(1)}%`, '']}
              />
              <Legend />

              {/* Ligne d'objectif */}
              <ReferenceLine
                y={objectif}
                stroke="#10b981"
                strokeDasharray="5 5"
                label={{ value: `Objectif ${objectif}%`, position: 'right', fill: '#10b981', fontSize: 12 }}
              />

              {/* Ligne de food cost réel */}
              <Line
                type="monotone"
                dataKey="food_cost_pct"
                stroke="#f43f5e"
                strokeWidth={2}
                name="Food Cost %"
                dot={{ fill: '#f43f5e', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Breakdown par catégorie */}
        {by_category.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-4 h-4 text-slate-400" />
              <h4 className="text-sm font-semibold text-slate-700">Par catégorie</h4>
            </div>

            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {by_category.map((cat, idx) => {
                const color = cat.food_cost_pct < 30
                  ? 'emerald'
                  : cat.food_cost_pct <= 35
                    ? 'amber'
                    : 'rose';

                return (
                  <div
                    key={idx}
                    className={`rounded-xl border border-${color}-200 bg-${color}-50/30 p-3`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-slate-900">{cat.category || 'Non catégorisé'}</p>
                      <p className={`text-lg font-semibold text-${color}-600`}>
                        {formatPercent(cat.food_cost_pct)}
                      </p>
                    </div>
                    <p className="text-xs text-slate-500">{cat.count} plats</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
