/**
 * FoodCostAnalysisPage - Analyse complète du food cost
 *
 * Implémentation selon RESTAURANT_OVERVIEW_ENDPOINTS.md
 * Affiche l'analyse du food cost avec recommandations et tendances.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  RefreshCw,
  Download,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  Target,
  PieChart,
  BarChart3,
  Calendar,
} from 'lucide-react';
import clsx from 'clsx';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  Area,
  ComposedChart,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { fetchRestaurantFoodCostAnalysis } from '@/api/client.js';
import Card, { CardHeader, CardContent } from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Badge from '@/components/ui/Badge.jsx';
import { Skeleton } from '@/components/ui/Skeleton.jsx';

// ============================================================================
// CONFIG
// ============================================================================

const PERIOD_OPTIONS = [
  { value: '7d', label: '7 jours' },
  { value: '30d', label: '30 jours' },
  { value: '90d', label: '90 jours' },
  { value: '1y', label: '1 an' },
];

const RECOMMENDATION_PRIORITY = {
  high: { color: 'rose', icon: AlertTriangle, label: 'Haute priorité' },
  medium: { color: 'amber', icon: Lightbulb, label: 'Moyenne priorité' },
  low: { color: 'blue', icon: Lightbulb, label: 'Information' },
};

// 32 couleurs distinctes pour les catégories
const CATEGORY_COLORS = [
  '#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#EC4899', '#84CC16',
  '#F97316', '#6366F1', '#14B8A6', '#E11D48', '#0EA5E9', '#A855F7', '#22C55E', '#EAB308',
  '#7C3AED', '#F43F5E', '#0D9488', '#2563EB', '#C026D3', '#65A30D', '#DC2626', '#0891B2',
  '#9333EA', '#16A34A', '#CA8A04', '#4F46E5', '#DB2777', '#059669', '#D97706', '#7C2D12',
];

// ============================================================================
// METRIC CARD COMPONENT
// ============================================================================

function MetricCard({ title, value, suffix, target, icon: Icon, isGood, isLoading }) {
  if (isLoading) {
    return <Skeleton className="h-28" />;
  }

  const isAboveTarget = target !== undefined && value > target;

  return (
    <Card padding="md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{title}</p>
          <div className="flex items-baseline gap-1">
            <span className={clsx(
              'text-3xl font-bold',
              isGood ? 'text-emerald-400' : isAboveTarget ? 'text-rose-400' : 'text-white'
            )}>
              {typeof value === 'number' ? value.toFixed(1) : value}
            </span>
            {suffix && <span className="text-sm text-slate-400">{suffix}</span>}
          </div>
          {target !== undefined && (
            <p className={clsx(
              'text-xs mt-1',
              isAboveTarget ? 'text-rose-400' : 'text-emerald-400'
            )}>
              Cible: {target}%
              {isAboveTarget ? (
                <span className="ml-1">({(value - target).toFixed(1)}% au-dessus)</span>
              ) : (
                <span className="ml-1">({(target - value).toFixed(1)}% en-dessous)</span>
              )}
            </p>
          )}
        </div>
        {Icon && (
          <div className={clsx(
            'p-2 rounded-lg',
            isGood ? 'bg-emerald-500/20' : isAboveTarget ? 'bg-rose-500/20' : 'bg-slate-500/20'
          )}>
            <Icon className={clsx(
              'w-5 h-5',
              isGood ? 'text-emerald-400' : isAboveTarget ? 'text-rose-400' : 'text-slate-400'
            )} />
          </div>
        )}
      </div>
    </Card>
  );
}

// ============================================================================
// CATEGORY CHART COMPONENT
// ============================================================================

function CategoryChart({ data = [], isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <CardHeader title="Food Cost par catégorie" />
        <Skeleton className="h-64" />
      </Card>
    );
  }

  const chartData = data.map((cat, idx) => ({
    ...cat,
    fill: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
  }));

  return (
    <Card padding="lg">
      <CardHeader
        title="Food Cost par catégorie"
        description="Comparaison du food cost par catégorie de plats"
      />
      <CardContent>
        {chartData.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">Aucune donnée disponible</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="categorie"
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
              />
              <YAxis
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
                formatter={(value) => [`${value.toFixed(1)}%`, 'Food Cost']}
              />
              <Bar
                dataKey="avg_food_cost_pct"
                name="Food Cost %"
                radius={[4, 4, 0, 0]}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// TREND CHART COMPONENT
// ============================================================================

function TrendChart({ data = [], targetFoodCost, isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <CardHeader title="Évolution du Food Cost" />
        <Skeleton className="h-64" />
      </Card>
    );
  }

  return (
    <Card padding="lg">
      <CardHeader
        title="Évolution du Food Cost"
        description="Tendance sur les derniers mois"
      />
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">Aucune donnée disponible</p>
        ) : (
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="foodCostGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="period"
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
              />
              <YAxis
                domain={[0, Math.max(50, targetFoodCost + 20)]}
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
                formatter={(value) => [`${value.toFixed(1)}%`, 'Food Cost']}
              />
              <Area
                type="monotone"
                dataKey="food_cost_pct"
                stroke="none"
                fill="url(#foodCostGradient)"
              />
              <Line
                type="monotone"
                dataKey="food_cost_pct"
                stroke="#8B5CF6"
                strokeWidth={2}
                dot={{ fill: '#8B5CF6', strokeWidth: 0 }}
                activeDot={{ fill: '#8B5CF6', strokeWidth: 2, stroke: '#fff', r: 5 }}
              />
              {/* Target line */}
              {targetFoodCost && (
                <Line
                  type="linear"
                  dataKey={() => targetFoodCost}
                  stroke="#F59E0B"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Cible"
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        )}

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-4 text-xs text-slate-400">
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-violet-500 rounded" />
            Food Cost réel
          </span>
          {targetFoodCost && (
            <span className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-amber-500 rounded" style={{ backgroundImage: 'repeating-linear-gradient(90deg, #F59E0B, #F59E0B 3px, transparent 3px, transparent 6px)' }} />
              Cible ({targetFoodCost}%)
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// RECOMMENDATIONS COMPONENT
// ============================================================================

function RecommendationsPanel({ recommendations = [], isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <CardHeader title="Recommandations" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card padding="lg">
      <CardHeader
        title="Recommandations"
        description="Actions suggérées pour optimiser votre food cost"
      />
      <CardContent>
        {recommendations.length === 0 ? (
          <div className="text-center py-8">
            <div className="p-3 rounded-full bg-emerald-500/10 w-fit mx-auto mb-3">
              <Target className="w-6 h-6 text-emerald-400" />
            </div>
            <p className="text-sm text-slate-400">Aucune recommandation pour le moment</p>
            <p className="text-xs text-slate-500 mt-1">Votre food cost est sous contrôle</p>
          </div>
        ) : (
          <div className="space-y-3">
            {recommendations.map((rec, idx) => {
              const config = RECOMMENDATION_PRIORITY[rec.priority] || RECOMMENDATION_PRIORITY.low;
              const Icon = config.icon;

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className={clsx(
                    'p-4 rounded-lg border',
                    `bg-${config.color}-500/10`,
                    `border-${config.color}-500/30`
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className={clsx('p-2 rounded-lg', `bg-${config.color}-500/20`)}>
                      <Icon className={clsx('w-4 h-4', `text-${config.color}-400`)} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'info'}>
                          {config.label}
                        </Badge>
                        {rec.category && (
                          <span className="text-xs text-slate-400">{rec.category}</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-200">{rec.message}</p>
                      {rec.estimated_impact && (
                        <p className="text-xs text-slate-400 mt-1">
                          Impact estimé: {rec.estimated_impact}
                        </p>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function FoodCostAnalysisPage() {
  const [period, setPeriod] = useState('30d');
  const [targetFoodCost, setTargetFoodCost] = useState(30);

  // Query
  const analysisQuery = useQuery({
    queryKey: ['restaurant', 'food-cost-analysis', period, targetFoodCost],
    queryFn: () => fetchRestaurantFoodCostAnalysis({ period, target_food_cost: targetFoodCost }),
  });

  const data = analysisQuery.data || {};
  const {
    global_food_cost_pct = 0,
    target_food_cost_pct = targetFoodCost,
    by_category = [],
    trend = [],
    recommendations = [],
  } = data;

  const isAboveTarget = global_food_cost_pct > target_food_cost_pct;

  const handleExport = () => {
    const csvContent = [
      ['Catégorie', 'Food Cost %', 'Nb Plats'],
      ...by_category.map((cat) => [
        cat.categorie,
        cat.avg_food_cost_pct.toFixed(1),
        cat.plat_count,
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `food-cost-analysis-${period}-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">restaurant</p>
          <h1 className="text-2xl font-semibold text-white">Analyse Food Cost</h1>
          <p className="text-sm text-slate-400">
            Analysez et optimisez votre coût matière
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Period Selector */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PERIOD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Target Input */}
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-slate-400" />
            <input
              type="number"
              min="0"
              max="100"
              value={targetFoodCost}
              onChange={(e) => setTargetFoodCost(Number(e.target.value))}
              className="w-20 px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-slate-400">% cible</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => analysisQuery.refetch()}
            loading={analysisQuery.isFetching}
            iconOnly
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-1" />
            Exporter
          </Button>
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          title="Food Cost Global"
          value={global_food_cost_pct}
          suffix="%"
          target={target_food_cost_pct}
          icon={PieChart}
          isGood={!isAboveTarget}
          isLoading={analysisQuery.isLoading}
        />
        <MetricCard
          title="Cible"
          value={target_food_cost_pct}
          suffix="%"
          icon={Target}
          isGood={true}
          isLoading={analysisQuery.isLoading}
        />
        <MetricCard
          title="Catégories analysées"
          value={by_category.length}
          icon={BarChart3}
          isLoading={analysisQuery.isLoading}
        />
        <MetricCard
          title="Recommandations"
          value={recommendations.length}
          icon={Lightbulb}
          isLoading={analysisQuery.isLoading}
        />
      </div>

      {/* Status Banner */}
      {!analysisQuery.isLoading && (
        <Card
          padding="md"
          className={clsx(
            isAboveTarget ? 'bg-rose-500/10 border-rose-500/30' : 'bg-emerald-500/10 border-emerald-500/30'
          )}
        >
          <div className="flex items-center gap-3">
            {isAboveTarget ? (
              <>
                <TrendingUp className="w-5 h-5 text-rose-400" />
                <div>
                  <p className="font-medium text-white">Food cost au-dessus de la cible</p>
                  <p className="text-sm text-slate-400">
                    Votre food cost actuel ({global_food_cost_pct.toFixed(1)}%) dépasse la cible de {(global_food_cost_pct - target_food_cost_pct).toFixed(1)}%.
                    Consultez les recommandations ci-dessous.
                  </p>
                </div>
              </>
            ) : (
              <>
                <TrendingDown className="w-5 h-5 text-emerald-400" />
                <div>
                  <p className="font-medium text-white">Food cost sous contrôle</p>
                  <p className="text-sm text-slate-400">
                    Votre food cost actuel ({global_food_cost_pct.toFixed(1)}%) est en-dessous de la cible.
                    Continuez ainsi !
                  </p>
                </div>
              </>
            )}
          </div>
        </Card>
      )}

      {/* Charts Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        <CategoryChart data={by_category} isLoading={analysisQuery.isLoading} />
        <TrendChart data={trend} targetFoodCost={target_food_cost_pct} isLoading={analysisQuery.isLoading} />
      </div>

      {/* Recommendations */}
      <RecommendationsPanel recommendations={recommendations} isLoading={analysisQuery.isLoading} />
    </div>
  );
}
