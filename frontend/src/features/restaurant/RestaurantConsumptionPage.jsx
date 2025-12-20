/**
 * RestaurantConsumptionPage - Analyse avancée des consommations restaurant
 *
 * Dashboard complet avec:
 * - KPIs principaux et métriques avancées
 * - Insights intelligents et alertes
 * - Graphiques (répartition, top produits, catégories détaillées)
 * - Table interactive avec recherche, tri et filtres
 * - Export CSV
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RefreshCw,
  Download,
  Search,
  TrendingUp,
  TrendingDown,
  Package,
  DollarSign,
  PieChart as PieChartIcon,
  BarChart3,
  ShoppingCart,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Filter,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Target,
  Zap,
  Activity,
  Layers,
  Eye,
  EyeOff,
  Info,
  CheckCircle,
  XCircle,
  Calendar,
} from 'lucide-react';
import clsx from 'clsx';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Treemap,
} from 'recharts';
import { useRestaurantConsumptions } from '../../hooks/useRestaurant.js';
import Card, { CardHeader, CardContent } from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Badge from '@/components/ui/Badge.jsx';
import { Skeleton } from '@/components/ui/Skeleton.jsx';

// ============================================================================
// CONFIG
// ============================================================================

const currency = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' });
const number = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const percentFmt = new Intl.NumberFormat('fr-FR', { style: 'percent', minimumFractionDigits: 1 });

// Options de période
const PERIOD_OPTIONS = [
  { value: 'all', label: 'Tout (historique)' },
  { value: '7d', label: '7 derniers jours' },
  { value: '30d', label: '30 derniers jours' },
  { value: '90d', label: '3 mois' },
  { value: '1y', label: '1 an' },
];

// Palette de couleurs cohérente
const CATEGORY_COLORS = [
  '#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#EC4899', '#84CC16',
  '#F97316', '#6366F1', '#14B8A6', '#E11D48', '#0EA5E9', '#A855F7', '#22C55E', '#EAB308',
  '#7C3AED', '#F43F5E', '#0D9488', '#2563EB', '#C026D3', '#65A30D', '#DC2626', '#0891B2',
];

const INSIGHT_TYPES = {
  warning: { color: 'amber', icon: AlertTriangle, bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/30' },
  danger: { color: 'rose', icon: XCircle, bgColor: 'bg-rose-500/10', borderColor: 'border-rose-500/30' },
  success: { color: 'emerald', icon: CheckCircle, bgColor: 'bg-emerald-500/10', borderColor: 'border-emerald-500/30' },
  info: { color: 'blue', icon: Info, bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/30' },
};

// ============================================================================
// METRIC CARD COMPONENT
// ============================================================================

function MetricCard({ title, value, subtitle, icon: Icon, trend, trendLabel, color = 'slate', isLoading, compact = false }) {
  if (isLoading) {
    return <Skeleton className={compact ? 'h-20' : 'h-28'} />;
  }

  const colorClasses = {
    emerald: 'bg-emerald-500/20 text-emerald-400',
    blue: 'bg-blue-500/20 text-blue-400',
    amber: 'bg-amber-500/20 text-amber-400',
    violet: 'bg-violet-500/20 text-violet-400',
    rose: 'bg-rose-500/20 text-rose-400',
    slate: 'bg-slate-500/20 text-slate-400',
    cyan: 'bg-cyan-500/20 text-cyan-400',
  };

  return (
    <Card padding={compact ? 'sm' : 'md'}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className={clsx('text-slate-400', compact ? 'text-xs' : 'text-sm')}>{title}</p>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className={clsx('font-bold text-white', compact ? 'text-xl' : 'text-2xl')}>{value}</span>
            {trend !== undefined && (
              <span className={clsx(
                'flex items-center text-xs font-medium',
                trend >= 0 ? 'text-emerald-400' : 'text-rose-400'
              )}>
                {trend >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                {Math.abs(trend).toFixed(1)}%
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
          {trendLabel && <p className="text-xs text-slate-400 mt-1">{trendLabel}</p>}
        </div>
        {Icon && (
          <div className={clsx('p-2 rounded-xl', colorClasses[color])}>
            <Icon className={clsx(compact ? 'w-4 h-4' : 'w-5 h-5')} />
          </div>
        )}
      </div>
    </Card>
  );
}

// ============================================================================
// INSIGHTS PANEL
// ============================================================================

function InsightsPanel({ insights = [], isLoading }) {
  const [expanded, setExpanded] = useState(true);

  if (isLoading) {
    return (
      <Card padding="lg">
        <Skeleton className="h-32" />
      </Card>
    );
  }

  if (insights.length === 0) {
    return null;
  }

  return (
    <Card padding="md">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-500/20">
            <Lightbulb className="w-4 h-4 text-amber-400" />
          </div>
          <h3 className="font-medium text-white">Insights & Alertes</h3>
          <Badge variant="warning" size="sm">{insights.length}</Badge>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="grid gap-3 mt-4 sm:grid-cols-2 lg:grid-cols-3">
              {insights.map((insight, idx) => {
                const config = INSIGHT_TYPES[insight.type] || INSIGHT_TYPES.info;
                const Icon = config.icon;
                return (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={clsx(
                      'p-3 rounded-lg border',
                      config.bgColor,
                      config.borderColor
                    )}
                  >
                    <div className="flex gap-2">
                      <Icon className={clsx('w-4 h-4 mt-0.5 flex-shrink-0', `text-${config.color}-400`)} />
                      <div>
                        <p className="text-sm font-medium text-white">{insight.title}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{insight.description}</p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

// ============================================================================
// CATEGORY BREAKDOWN CARD
// ============================================================================

function CategoryBreakdownCard({ data = [], isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <Skeleton className="h-64" />
      </Card>
    );
  }

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <Card padding="lg">
      <CardHeader
        title="Répartition par catégorie"
        description={`${data.length} catégories • ${currency.format(total)} au total`}
      />
      <CardContent>
        <div className="space-y-3">
          {data.slice(0, 8).map((cat, idx) => {
            const percent = total > 0 ? (cat.value / total) * 100 : 0;
            return (
              <div key={cat.name} className="group">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                    />
                    <span className="text-sm text-slate-200 truncate max-w-[140px]">{cat.name}</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-slate-400">{percent.toFixed(1)}%</span>
                    <span className="font-medium text-white w-20 text-right">{currency.format(cat.value)}</span>
                  </div>
                </div>
                <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percent}%` }}
                    transition={{ duration: 0.5, delay: idx * 0.05 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                  />
                </div>
              </div>
            );
          })}
          {data.length > 8 && (
            <p className="text-xs text-slate-500 text-center pt-2">
              +{data.length - 8} autres catégories
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// CATEGORY PIE CHARTS (Boissons & Aliments)
// ============================================================================

// Catégories classées comme boissons
const BOISSONS_CATEGORIES = [
  'Bières',
  'Vins rouges',
  'Vins blancs',
  'Vins rosés',
  'Spiritueux',
  'Softs / Énergisants',
  'Eaux',
  'Apéritifs / Fortifiés',
  'Effervescents / Champagne',
  'Champagnes',
  'Cocktails',
  'Jus',
  'Sirops',
];

const BOISSONS_COLORS = [
  '#f59e0b', // Bières - amber
  '#991b1b', // Vins rouges - dark red
  '#fef3c7', // Vins blancs - cream
  '#fda4af', // Vins rosés - pink
  '#7c3aed', // Spiritueux - purple
  '#06b6d4', // Softs - cyan
  '#67e8f9', // Eaux - light cyan
  '#8b5cf6', // Apéritifs - violet
  '#fcd34d', // Champagne - gold
  '#a855f7', // Cocktails
  '#fb923c', // Jus
  '#f472b6', // Sirops
];

const ALIMENTS_COLORS = [
  '#ef4444', // Viandes - red
  '#22c55e', // Légumes - green
  '#0ea5e9', // Poissons - blue
  '#f97316', // Conserves - orange
  '#eab308', // Huiles - yellow
  '#ec4899', // Épices - pink
  '#14b8a6', // Surgelés - teal
  '#a3e635', // Fruits - lime
  '#c084fc', // Épicerie sucrée - purple
  '#fbbf24', // Pâtes/Riz - amber
  '#6366f1', // Laits/Crèmes - indigo
  '#10b981', // Produits du monde - emerald
];

function SplitDonutCharts({ data = [], isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <CardHeader title="Distribution des coûts" />
        <Skeleton className="h-64" />
      </Card>
    );
  }

  if (data.length === 0) {
    return null;
  }

  // Séparer les données en boissons et aliments
  const boissonsData = data.filter(d =>
    BOISSONS_CATEGORIES.some(cat =>
      d.name.toLowerCase().includes(cat.toLowerCase()) ||
      cat.toLowerCase().includes(d.name.toLowerCase())
    )
  );

  const alimentsData = data.filter(d =>
    !BOISSONS_CATEGORIES.some(cat =>
      d.name.toLowerCase().includes(cat.toLowerCase()) ||
      cat.toLowerCase().includes(d.name.toLowerCase())
    )
  );

  const boissonsTotal = boissonsData.reduce((sum, d) => sum + d.value, 0);
  const alimentsTotal = alimentsData.reduce((sum, d) => sum + d.value, 0);
  const grandTotal = boissonsTotal + alimentsTotal;

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.[0]) return null;
    const { name, value, percent: pct } = payload[0].payload;
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 shadow-lg">
        <p className="font-medium text-white">{name}</p>
        <p className="text-sm text-slate-300">{currency.format(value)}</p>
        <p className="text-xs text-slate-400">{(pct * 100).toFixed(1)}%</p>
      </div>
    );
  };

  const renderDonut = (chartData, colors, title, total, sectionTotal) => {
    const topCategory = chartData[0];
    const percentOfTotal = grandTotal > 0 ? ((sectionTotal / grandTotal) * 100).toFixed(0) : 0;

    return (
      <div className="flex-1">
        <div className="text-center mb-2">
          <h4 className="text-sm font-medium text-white">{title}</h4>
          <p className="text-xs text-slate-400">{chartData.length} catégories • {percentOfTotal}% du total</p>
        </div>
        <div className="relative">
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                dataKey="value"
                nameKey="name"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-lg font-bold text-white">{currency.format(sectionTotal)}</span>
          </div>
        </div>
        {topCategory && (
          <div className="mt-2 p-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: colors[0] }}
                />
                <span className="text-slate-300 truncate max-w-[100px]">{topCategory.name}</span>
              </div>
              <Badge variant="secondary" size="sm">
                {sectionTotal > 0 ? ((topCategory.value / sectionTotal) * 100).toFixed(0) : 0}%
              </Badge>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <Card padding="lg">
      <CardHeader
        title="Distribution des coûts"
        description={`Total: ${currency.format(grandTotal)} • Boissons vs Aliments`}
      />
      <CardContent>
        <div className="flex gap-6">
          {renderDonut(boissonsData, BOISSONS_COLORS, '🍺 Boissons', grandTotal, boissonsTotal)}
          {renderDonut(alimentsData, ALIMENTS_COLORS, '🍽️ Aliments', grandTotal, alimentsTotal)}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// TOP PRODUCTS BAR CHART
// ============================================================================

function TopProductsChart({ data = [], isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <CardHeader title="Top produits" />
        <Skeleton className="h-72" />
      </Card>
    );
  }

  if (data.length === 0) {
    return null;
  }

  return (
    <Card padding="lg">
      <CardHeader
        title="Top 10 produits consommés"
        description="Produits générant le plus de coût matière"
      />
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 5, bottom: 5 }}
          >
            <defs>
              <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#8B5CF6" />
                <stop offset="100%" stopColor="#6366F1" />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
            <XAxis
              type="number"
              tickFormatter={(v) => `${v.toFixed(0)}€`}
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
              axisLine={{ stroke: '#374151' }}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={130}
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
              axisLine={{ stroke: '#374151' }}
              tickFormatter={(v) => v.length > 20 ? v.substring(0, 20) + '...' : v}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
              }}
              formatter={(value) => [currency.format(value), 'Coût']}
            />
            <Bar
              dataKey="cost"
              fill="url(#barGradient)"
              radius={[0, 6, 6, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// PLAT CONSUMPTION TREEMAP
// ============================================================================

function PlatConsumptionTreemap({ data = [], isLoading }) {
  if (isLoading || data.length === 0) return null;

  const CustomizedContent = ({ root, depth, x, y, width, height, index, name, value }) => {
    if (width < 40 || height < 30) return null;

    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
          stroke="#1F2937"
          strokeWidth={2}
          rx={4}
        />
        {width > 60 && height > 35 && (
          <>
            <text
              x={x + width / 2}
              y={y + height / 2 - 6}
              textAnchor="middle"
              fill="#fff"
              fontSize={11}
              fontWeight="500"
            >
              {name?.length > 12 ? name.substring(0, 12) + '...' : name}
            </text>
            <text
              x={x + width / 2}
              y={y + height / 2 + 10}
              textAnchor="middle"
              fill="rgba(255,255,255,0.7)"
              fontSize={10}
            >
              {currency.format(value)}
            </text>
          </>
        )}
      </g>
    );
  };

  return (
    <Card padding="lg">
      <CardHeader
        title="Carte des consommations par plat"
        description="Taille proportionnelle au coût de chaque plat"
      />
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <Treemap
            data={data}
            dataKey="value"
            nameKey="name"
            aspectRatio={4 / 3}
            stroke="#1F2937"
            content={<CustomizedContent />}
          />
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// SORTABLE TABLE HEADER
// ============================================================================

function SortableHeader({ label, sortKey, currentSort, onSort, align = 'left' }) {
  const isActive = currentSort.key === sortKey;
  const Icon = isActive && currentSort.direction === 'desc' ? ChevronDown : ChevronUp;

  return (
    <th
      className={clsx(
        'px-4 py-3 cursor-pointer hover:bg-slate-700/50 transition-colors select-none',
        align === 'right' && 'text-right'
      )}
      onClick={() => onSort(sortKey)}
    >
      <div className={clsx('flex items-center gap-1', align === 'right' && 'justify-end')}>
        {label}
        <Icon className={clsx('w-3 h-3', isActive ? 'text-blue-400' : 'text-slate-500')} />
      </div>
    </th>
  );
}

// ============================================================================
// CONSUMPTION TABLE
// ============================================================================

function ConsumptionTable({ data = [], isLoading }) {
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [sort, setSort] = useState({ key: 'cost_spent', direction: 'desc' });

  const categories = useMemo(() => {
    const cats = [...new Set(data.map(d => d.epicerie_categorie).filter(Boolean))];
    return cats.sort();
  }, [data]);

  const filteredData = useMemo(() => {
    let result = [...data];

    if (search) {
      const searchLower = search.toLowerCase();
      result = result.filter(
        (d) =>
          d.epicerie_nom?.toLowerCase().includes(searchLower) ||
          d.restaurant_plat?.toLowerCase().includes(searchLower)
      );
    }

    if (categoryFilter !== 'all') {
      result = result.filter((d) => d.epicerie_categorie === categoryFilter);
    }

    if (showLowStockOnly) {
      result = result.filter((d) => (d.stock_after_sales ?? 0) < 5);
    }

    result.sort((a, b) => {
      const aVal = a[sort.key] ?? 0;
      const bVal = b[sort.key] ?? 0;
      if (typeof aVal === 'string') {
        return sort.direction === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      return sort.direction === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return result;
  }, [data, search, categoryFilter, showLowStockOnly, sort]);

  const handleSort = (key) => {
    setSort((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
  };

  if (isLoading) {
    return <Skeleton className="h-96" />;
  }

  return (
    <Card padding="none">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-4 border-b border-slate-700/50">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher un produit ou plat..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Toutes catégories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
        <Button
          variant={showLowStockOnly ? 'danger' : 'ghost'}
          size="sm"
          onClick={() => setShowLowStockOnly(!showLowStockOnly)}
        >
          <AlertTriangle className="w-4 h-4 mr-1" />
          Stock faible
        </Button>
        <Badge variant="info" className="ml-auto">
          {filteredData.length} / {data.length} produit{data.length > 1 ? 's' : ''}
        </Badge>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-800/50 text-xs uppercase tracking-wider text-slate-400 sticky top-0">
            <tr>
              <SortableHeader label="Plat" sortKey="restaurant_plat" currentSort={sort} onSort={handleSort} />
              <SortableHeader label="Produit Épicerie" sortKey="epicerie_nom" currentSort={sort} onSort={handleSort} />
              <SortableHeader label="Catégorie" sortKey="epicerie_categorie" currentSort={sort} onSort={handleSort} />
              <SortableHeader label="Qté" sortKey="quantity_consumed" currentSort={sort} onSort={handleSort} align="right" />
              <SortableHeader label="Coût" sortKey="cost_spent" currentSort={sort} onSort={handleSort} align="right" />
              <SortableHeader label="Stock" sortKey="stock_after_sales" currentSort={sort} onSort={handleSort} align="right" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  Aucun résultat pour cette recherche
                </td>
              </tr>
            ) : (
              filteredData.map((entry, idx) => {
                const isLowStock = (entry.stock_after_sales ?? 0) < 5;
                return (
                  <motion.tr
                    key={`${entry.produit_restaurant_id}-${entry.produit_epicerie_id}-${idx}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: Math.min(idx * 0.01, 0.3) }}
                    className={clsx(
                      'hover:bg-slate-800/30 transition-colors',
                      isLowStock && 'bg-rose-500/5'
                    )}
                  >
                    <td className="px-4 py-3">
                      <span className="font-medium text-white">
                        {entry.restaurant_plat ?? '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <span className="text-slate-200">{entry.epicerie_nom}</span>
                        <span className="text-xs text-slate-500 ml-2">#{entry.produit_epicerie_id}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="secondary" size="sm">
                        {entry.epicerie_categorie || '—'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-300">
                      {number.format(entry.quantity_consumed)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-semibold text-amber-400">
                        {currency.format(entry.cost_spent)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <span className={clsx(
                          'font-mono',
                          isLowStock ? 'text-rose-400 font-semibold' : 'text-slate-300'
                        )}>
                          {number.format(entry.stock_after_sales)}
                        </span>
                        {isLowStock && (
                          <AlertTriangle className="w-4 h-4 text-rose-400" />
                        )}
                      </div>
                    </td>
                  </motion.tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function RestaurantConsumptionPage() {
  const [period, setPeriod] = useState('all');
  const { data: rawData = [], isLoading, refetch, isFetching } = useRestaurantConsumptions(period);

  // Calculs des métriques avancées
  const metrics = useMemo(() => {
    if (!rawData.length) return null;

    const totalCost = rawData.reduce((sum, d) => sum + (d.cost_spent || 0), 0);
    const totalQuantity = rawData.reduce((sum, d) => sum + (d.quantity_consumed || 0), 0);
    const totalBottles = rawData.reduce((sum, d) => sum + (d.bottles_required || 0), 0);
    const uniqueProducts = new Set(rawData.map((d) => d.produit_epicerie_id)).size;
    const uniquePlats = new Set(rawData.map((d) => d.produit_restaurant_id).filter(Boolean)).size;
    const uniqueCategories = new Set(rawData.map((d) => d.epicerie_categorie).filter(Boolean)).size;
    const lowStockCount = rawData.filter((d) => (d.stock_after_sales ?? 0) < 5).length;

    // Coût moyen par ligne (moyenne pondérée plus pertinente)
    const avgCostPerLine = rawData.length > 0 ? totalCost / rawData.length : 0;

    // Coût moyen par unité consommée
    const avgCostPerUnit = totalQuantity > 0 ? totalCost / totalQuantity : 0;

    // Top catégorie
    const categoryTotals = rawData.reduce((acc, d) => {
      const cat = d.epicerie_categorie || 'Non catégorisé';
      acc[cat] = (acc[cat] || 0) + (d.cost_spent || 0);
      return acc;
    }, {});
    const topCategory = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1])[0];

    // Produit le plus consommé (par coût)
    const productTotals = rawData.reduce((acc, d) => {
      const name = d.epicerie_nom || 'Inconnu';
      acc[name] = (acc[name] || 0) + (d.cost_spent || 0);
      return acc;
    }, {});
    const topProduct = Object.entries(productTotals).sort((a, b) => b[1] - a[1])[0];

    return {
      totalCost,
      totalQuantity,
      totalBottles,
      uniqueProducts,
      uniquePlats,
      uniqueCategories,
      lowStockCount,
      avgCostPerLine,
      avgCostPerUnit,
      topCategory: topCategory ? { name: topCategory[0], value: topCategory[1] } : null,
      topProduct: topProduct ? { name: topProduct[0], value: topProduct[1] } : null,
      // Nombre de lignes pour info
      totalLines: rawData.length,
    };
  }, [rawData]);

  // Génération des insights intelligents
  const insights = useMemo(() => {
    if (!metrics) return [];

    const result = [];

    // Alertes stock faible
    if (metrics.lowStockCount > 0) {
      result.push({
        type: metrics.lowStockCount > 5 ? 'danger' : 'warning',
        title: `${metrics.lowStockCount} produit${metrics.lowStockCount > 1 ? 's' : ''} en stock faible`,
        description: 'Passez commande pour éviter les ruptures',
      });
    }

    // Info sur la couverture des mappings
    // Note: 153 plats total, 90 mappés, 137 vendus selon DB
    if (metrics.uniquePlats < 100) {
      result.push({
        type: 'info',
        title: `${metrics.uniquePlats} plats avec mapping & ventes`,
        description: 'Certains plats vendus n\'ont pas de correspondance épicerie',
      });
    }

    // Concentration des coûts
    if (metrics.topCategory && metrics.totalCost > 0) {
      const topPercent = (metrics.topCategory.value / metrics.totalCost) * 100;
      if (topPercent > 30) {
        result.push({
          type: 'info',
          title: `${metrics.topCategory.name} = ${topPercent.toFixed(0)}% des coûts`,
          description: 'Catégorie dominante dans vos consommations',
        });
      }
    }

    // Top produit
    if (metrics.topProduct && metrics.totalCost > 0) {
      const topProdPercent = (metrics.topProduct.value / metrics.totalCost) * 100;
      if (topProdPercent > 10) {
        result.push({
          type: 'success',
          title: `Top produit: ${metrics.topProduct.name.substring(0, 25)}...`,
          description: `${currency.format(metrics.topProduct.value)} (${topProdPercent.toFixed(1)}% du total)`,
        });
      }
    }

    // Coût moyen par unité élevé
    if (metrics.avgCostPerUnit > 20) {
      result.push({
        type: 'warning',
        title: `Coût unitaire moyen: ${currency.format(metrics.avgCostPerUnit)}`,
        description: 'Produits à forte valeur unitaire',
      });
    }

    return result;
  }, [metrics]);

  // Données pour les graphiques
  const categoryData = useMemo(() => {
    if (!rawData.length) return [];

    const byCategory = rawData.reduce((acc, d) => {
      const cat = d.epicerie_categorie || 'Non catégorisé';
      if (!acc[cat]) acc[cat] = 0;
      acc[cat] += d.cost_spent || 0;
      return acc;
    }, {});

    const total = Object.values(byCategory).reduce((a, b) => a + b, 0);

    return Object.entries(byCategory)
      .map(([name, value]) => ({ name, value, percent: value / total }))
      .sort((a, b) => b.value - a.value);
  }, [rawData]);

  const topProductsData = useMemo(() => {
    if (!rawData.length) return [];

    const byProduct = rawData.reduce((acc, d) => {
      const name = d.epicerie_nom || 'Inconnu';
      if (!acc[name]) acc[name] = 0;
      acc[name] += d.cost_spent || 0;
      return acc;
    }, {});

    return Object.entries(byProduct)
      .map(([name, cost]) => ({ name, cost }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 10);
  }, [rawData]);

  const platData = useMemo(() => {
    if (!rawData.length) return [];

    const byPlat = rawData.reduce((acc, d) => {
      const name = d.restaurant_plat || 'Sans plat';
      if (!acc[name]) acc[name] = 0;
      acc[name] += d.cost_spent || 0;
      return acc;
    }, {});

    return Object.entries(byPlat)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 15);
  }, [rawData]);

  // Export CSV
  const handleExport = () => {
    const headers = ['Plat', 'Produit Épicerie', 'Catégorie', 'Quantité', 'Coût', 'Stock restant'];
    const rows = rawData.map((d) => [
      d.restaurant_plat || '',
      d.epicerie_nom || '',
      d.epicerie_categorie || '',
      d.quantity_consumed?.toFixed(2) || '0',
      d.cost_spent?.toFixed(2) || '0',
      d.stock_after_sales?.toFixed(2) || '0',
    ]);

    const csvContent = [headers.join(';'), ...rows.map((r) => r.join(';'))].join('\n');
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `consommations-restaurant-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">restaurant</p>
          <h1 className="text-2xl font-semibold text-white">Analyse des Consommations</h1>
          <p className="text-sm text-slate-400 mt-1">
            Vue complète du coût matière • Correspondance plats → produits Épicerie
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {/* Period Selector */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PERIOD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            loading={isFetching}
            iconOnly
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="primary" size="sm" onClick={handleExport} disabled={!rawData.length}>
            <Download className="h-4 w-4 mr-1" />
            Exporter
          </Button>
        </div>
      </div>

      {/* Primary Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Coût matière total"
          value={metrics ? currency.format(metrics.totalCost) : '—'}
          subtitle={metrics ? `Sur ${metrics.totalLines} lignes de conso` : undefined}
          icon={DollarSign}
          color="amber"
          isLoading={isLoading}
        />
        <MetricCard
          title="Plats mappés & vendus"
          value={metrics?.uniquePlats ?? '—'}
          subtitle={metrics?.topCategory ? `Top: ${metrics.topCategory.name}` : undefined}
          icon={Activity}
          color="violet"
          isLoading={isLoading}
        />
        <MetricCard
          title="Coût moyen / unité"
          value={metrics ? currency.format(metrics.avgCostPerUnit) : '—'}
          subtitle="Par unité consommée"
          icon={Target}
          color="blue"
          isLoading={isLoading}
        />
        <MetricCard
          title="Alertes stock"
          value={metrics?.lowStockCount ?? '—'}
          subtitle="Produits < 5 unités"
          icon={AlertTriangle}
          color={metrics?.lowStockCount > 0 ? 'rose' : 'emerald'}
          isLoading={isLoading}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <MetricCard
          title="Quantité conso"
          value={metrics ? number.format(metrics.totalQuantity) : '—'}
          icon={Package}
          color="cyan"
          compact
          isLoading={isLoading}
        />
        <MetricCard
          title="Bouteilles req."
          value={metrics ? number.format(metrics.totalBottles) : '—'}
          icon={ShoppingCart}
          color="emerald"
          compact
          isLoading={isLoading}
        />
        <MetricCard
          title="Produits épicerie"
          value={metrics?.uniqueProducts ?? '—'}
          icon={BarChart3}
          color="blue"
          compact
          isLoading={isLoading}
        />
        <MetricCard
          title="Catégories"
          value={metrics?.uniqueCategories ?? '—'}
          icon={Layers}
          color="violet"
          compact
          isLoading={isLoading}
        />
        <MetricCard
          title="Coût moy / ligne"
          value={metrics ? currency.format(metrics.avgCostPerLine) : '—'}
          icon={Zap}
          color="amber"
          compact
          isLoading={isLoading}
        />
        <MetricCard
          title="Lignes conso"
          value={metrics?.totalLines ?? 0}
          icon={Eye}
          color="slate"
          compact
          isLoading={isLoading}
        />
      </div>

      {/* Insights */}
      <InsightsPanel insights={insights} isLoading={isLoading} />

      {/* Charts Row 1 - Distribution Boissons / Aliments */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SplitDonutCharts data={categoryData} isLoading={isLoading} />
        <CategoryBreakdownCard data={categoryData} isLoading={isLoading} />
      </div>

      {/* Charts Row 2 */}
      <div className="grid gap-6 lg:grid-cols-2">
        <TopProductsChart data={topProductsData} isLoading={isLoading} />
        <PlatConsumptionTreemap data={platData} isLoading={isLoading} />
      </div>

      {/* Detailed Table */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-slate-400" />
          Détail complet des consommations
        </h2>
        <ConsumptionTable data={rawData} isLoading={isLoading} />
      </div>
    </div>
  );
}
