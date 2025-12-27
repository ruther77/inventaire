/**
 * SupplierDetailsPage - Détails complets d'un fournisseur
 *
 * Implémentation exacte selon SUPPLIER_SCORING_FRONTEND_INTEGRATION.md
 * Affiche les scores détaillés, historique, livraisons, incidents et recommandations.
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Truck,
  AlertTriangle,
  FileText,
  Lightbulb,
  Clock,
  RefreshCw,
  DollarSign,
  Star,
  Package,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import clsx from 'clsx';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
  ComposedChart,
} from 'recharts';
import { useSupplierDetails, useSupplierHistoryById } from '@/hooks/useSupplierScoring.js';
import { useProducts } from '@/hooks/useProducts.js';
import Card, { CardHeader, CardContent } from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Badge from '@/components/ui/Badge.jsx';
import { Skeleton } from '@/components/ui/Skeleton.jsx';

// ============================================================================
// CONFIG
// ============================================================================

const GRADE_CONFIG = {
  A: { color: 'emerald', label: 'Excellent', bg: 'bg-emerald-500', text: 'text-emerald-400' },
  B: { color: 'blue', label: 'Bon', bg: 'bg-blue-500', text: 'text-blue-400' },
  C: { color: 'amber', label: 'Moyen', bg: 'bg-amber-500', text: 'text-amber-400' },
  D: { color: 'orange', label: 'Faible', bg: 'bg-orange-500', text: 'text-orange-400' },
  F: { color: 'rose', label: 'Critique', bg: 'bg-rose-500', text: 'text-rose-400' },
};

const TREND_CONFIG = {
  improving: { icon: TrendingUp, color: 'text-emerald-400', label: 'En amélioration' },
  stable: { icon: BarChart3, color: 'text-slate-400', label: 'Stable' },
  declining: { icon: TrendingDown, color: 'text-rose-400', label: 'En déclin' },
  up: { icon: TrendingUp, color: 'text-emerald-400', label: 'En hausse' },
  down: { icon: TrendingDown, color: 'text-rose-400', label: 'En baisse' },
};

const DIMENSION_LABELS = {
  price_stability: { label: 'Stabilité prix', icon: DollarSign },
  delivery_reliability: { label: 'Fiabilité livraison', icon: Truck },
  invoice_accuracy: { label: 'Précision factures', icon: FileText },
  stock_accuracy: { label: 'Précision stock', icon: BarChart3 },
  payment_terms: { label: 'Conditions paiement', icon: Clock },
  responsiveness: { label: 'Réactivité', icon: Clock },
  product_quality: { label: 'Qualité produits', icon: Star },
};

const TABS = [
  { id: 'overview', label: 'Vue d\'ensemble', icon: BarChart3 },
  { id: 'products', label: 'Produits', icon: Package },
  { id: 'history', label: 'Historique', icon: Clock },
  { id: 'deliveries', label: 'Livraisons', icon: Truck },
  { id: 'issues', label: 'Incidents', icon: AlertTriangle },
  { id: 'statistics', label: 'Statistiques', icon: FileText },
];

// ============================================================================
// HEADER COMPONENT
// ============================================================================

function SupplierHeader({ details, isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-40" />
          </div>
          <Skeleton className="h-20 w-32" />
        </div>
      </Card>
    );
  }

  const score = details?.current_score || {};
  const config = GRADE_CONFIG[score.grade] || GRADE_CONFIG.C;
  const trendConfig = TREND_CONFIG[score.trend];
  const TrendIcon = trendConfig?.icon;

  return (
    <Card padding="lg">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{details?.supplier_name}</h1>
          <div className="flex items-center gap-4 mt-2">
            <span className={clsx('text-5xl font-bold', config.text)}>
              {score.grade || 'C'}
            </span>
            <div className="flex flex-col">
              <span className="text-2xl font-semibold text-white">
                {(score.overall_score || 0).toFixed(1)}/100
              </span>
              {TrendIcon && (
                <span className={clsx('flex items-center gap-1 text-sm', trendConfig.color)}>
                  <TrendIcon className="w-4 h-4" />
                  {trendConfig.label}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className={clsx('px-6 py-4 rounded-xl', `bg-${config.color}-500/20`)}>
          <p className="text-sm text-slate-400">Performance</p>
          <p className={clsx('text-3xl font-bold', config.text)}>{config.label}</p>
        </div>
      </div>
    </Card>
  );
}

// ============================================================================
// DIMENSION SCORES COMPONENT
// ============================================================================

function DimensionScores({ dimensions = {} }) {
  const getScoreColor = (score) => {
    if (score >= 80) return 'emerald';
    if (score >= 60) return 'blue';
    if (score >= 40) return 'amber';
    return 'rose';
  };

  return (
    <Card padding="lg">
      <CardHeader title="Scores par dimension" />
      <CardContent>
        <div className="space-y-4">
          {Object.entries(dimensions).map(([key, value]) => {
            const dim = DIMENSION_LABELS[key] || { label: key, icon: BarChart3 };
            const Icon = dim.icon;
            const color = getScoreColor(value);

            return (
              <div key={key} className="flex items-center gap-4">
                <div className={clsx('p-2 rounded-lg', `bg-${color}-500/20`)}>
                  <Icon className={clsx('w-4 h-4', `text-${color}-400`)} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-300">{dim.label}</span>
                    <span className={clsx('text-sm font-medium', `text-${color}-400`)}>
                      {value.toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${value}%` }}
                      transition={{ duration: 0.5 }}
                      className={clsx('h-full rounded-full', `bg-${color}-500`)}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// HISTORY CHART COMPONENT
// ============================================================================

function HistoryChart({ history = [], isLoading }) {
  if (isLoading) {
    return (
      <Card padding="lg">
        <CardHeader title="Évolution du score" />
        <Skeleton className="h-64" />
      </Card>
    );
  }

  const chartData = history.map((item) => ({
    date: item.date,
    score: item.score,
  })).reverse();

  return (
    <Card padding="lg">
      <CardHeader title="Évolution du score" description="Historique des 12 derniers mois" />
      <CardContent>
        {chartData.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">Aucun historique disponible</p>
        ) : (
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                tickFormatter={(v) => {
                  try {
                    return new Date(v).toLocaleDateString('fr-FR', { month: 'short' });
                  } catch {
                    return v;
                  }
                }}
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
                labelFormatter={(v) => {
                  try {
                    return new Date(v).toLocaleDateString('fr-FR');
                  } catch {
                    return v;
                  }
                }}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="none"
                fill="url(#scoreGradient)"
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#8B5CF6"
                strokeWidth={2}
                dot={{ fill: '#8B5CF6', strokeWidth: 0 }}
                activeDot={{ fill: '#8B5CF6', strokeWidth: 2, stroke: '#fff', r: 5 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// DELIVERIES LIST COMPONENT
// ============================================================================

function DeliveriesList({ deliveries = [] }) {
  return (
    <Card padding="lg">
      <CardHeader title="Livraisons récentes" />
      <CardContent>
        {deliveries.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">Aucune livraison enregistrée</p>
        ) : (
          <div className="space-y-3">
            {deliveries.map((delivery, idx) => (
              <div
                key={delivery.id || idx}
                className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-white/5"
              >
                <div className="flex items-center gap-3">
                  <Truck className={clsx(
                    'w-5 h-5',
                    delivery.delay_days <= 0 ? 'text-emerald-400' : 'text-rose-400'
                  )} />
                  <div>
                    <p className="text-sm text-white">Livraison #{delivery.id || idx + 1}</p>
                    <p className="text-xs text-slate-400">
                      Prévu: {delivery.expected_date || '-'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {delivery.delay_days <= 0 ? (
                    <Badge variant="success">À l'heure</Badge>
                  ) : (
                    <Badge variant="danger">+{delivery.delay_days}j retard</Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// ISSUES LIST COMPONENT
// ============================================================================

function IssuesList({ issues = [] }) {
  const severityConfig = {
    high: { label: 'Critique', variant: 'danger' },
    medium: { label: 'Moyen', variant: 'warning' },
    low: { label: 'Mineur', variant: 'info' },
  };

  return (
    <Card padding="lg">
      <CardHeader title="Incidents récents" />
      <CardContent>
        {issues.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">Aucun incident enregistré</p>
        ) : (
          <div className="space-y-3">
            {issues.map((issue, idx) => {
              const config = severityConfig[issue.severity] || severityConfig.low;
              return (
                <div
                  key={issue.id || idx}
                  className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-white/5"
                >
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    <div>
                      <p className="text-sm text-white">{issue.issue_type || 'Incident'}</p>
                      <p className="text-xs text-slate-400">
                        {issue.created_at || '-'}
                      </p>
                    </div>
                  </div>
                  <Badge variant={config.variant}>{config.label}</Badge>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// STATISTICS PANEL COMPONENT
// ============================================================================

function StatisticsPanel({ statistics = {} }) {
  const stats = [
    { label: 'Commandes totales', value: statistics.total_orders || 0 },
    { label: 'Factures analysées', value: statistics.total_invoices || 0 },
    { label: 'Valeur moyenne commande', value: `${(statistics.average_order_value || 0).toFixed(0)}€` },
    { label: 'Durée partenariat', value: `${statistics.partnership_duration_days || 0} jours` },
  ];

  return (
    <Card padding="lg">
      <CardHeader title="Statistiques" />
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {stats.map(({ label, value }) => (
            <div key={label} className="p-4 bg-slate-800/50 rounded-lg border border-white/5">
              <p className="text-sm text-slate-400 mb-1">{label}</p>
              <p className="text-xl font-semibold text-white">{value}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// PRODUCTS LIST COMPONENT
// ============================================================================

function ProductsList({ supplierName }) {
  const [page, setPage] = useState(1);
  const perPage = 20;

  const productsQuery = useProducts({
    page,
    per_page: perPage,
    fournisseur: supplierName,
  });

  // Hook normalisé: data = tableau, meta = {total, page, per_page}
  const products = productsQuery.data || [];
  const total = productsQuery.meta?.total || products.length;
  const totalPages = Math.ceil(total / perPage);

  const formatCurrency = (value) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value || 0);

  const getStockStatus = (product) => {
    if (!product.stock_actuel && product.stock_actuel !== 0) return 'unknown';
    if (product.stock_actuel <= 0) return 'rupture';
    if (product.stock_actuel <= (product.seuil_alerte || 5)) return 'low';
    return 'ok';
  };

  const statusConfig = {
    ok: { label: 'En stock', variant: 'success' },
    low: { label: 'Stock bas', variant: 'warning' },
    rupture: { label: 'Rupture', variant: 'danger' },
    unknown: { label: '-', variant: 'neutral' },
  };

  if (productsQuery.isLoading) {
    return (
      <Card padding="lg">
        <CardHeader title="Produits fournis" />
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card padding="lg">
      <CardHeader
        title="Produits fournis"
        description={`${total} produit${total > 1 ? 's' : ''} de ce fournisseur`}
      />
      <CardContent>
        {products.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">
            Aucun produit trouvé pour ce fournisseur
          </p>
        ) : (
          <>
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {products.map((product, idx) => {
                const status = getStockStatus(product);
                const config = statusConfig[status];

                return (
                  <motion.div
                    key={product.id || idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(idx * 0.03, 0.3) }}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-white/5 hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-blue-500/20">
                        <Package className="w-4 h-4 text-blue-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white truncate max-w-[300px]">
                          {product.nom}
                        </p>
                        <p className="text-xs text-slate-400">
                          {product.categorie || 'Sans catégorie'}
                          {product.codes?.length > 0 && ` • ${product.codes[0]}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm font-semibold text-white">
                          {formatCurrency(product.prix_achat)}
                        </p>
                        <p className="text-xs text-slate-400">
                          Stock: {product.stock_actuel ?? '-'}
                        </p>
                      </div>
                      <Badge variant={config.variant}>{config.label}</Badge>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
                <span className="text-sm text-slate-400">
                  Page {page} sur {totalPages}
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// RECOMMENDATIONS COMPONENT
// ============================================================================

function RecommendationsPanel({ recommendations = [] }) {
  if (recommendations.length === 0) return null;

  return (
    <Card padding="lg">
      <CardHeader title="Recommandations" />
      <CardContent>
        <div className="space-y-3">
          {recommendations.map((rec, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg"
            >
              <Lightbulb className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-slate-200">{rec}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function SupplierDetailsPage() {
  const { supplierId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const id = Number(supplierId);

  // Queries
  const detailsQuery = useSupplierDetails(id);
  const historyQuery = useSupplierHistoryById(id, { limit: 30 });

  const details = detailsQuery.data?.data || detailsQuery.data || {};
  const history = historyQuery.data?.data?.history || historyQuery.data?.history || [];

  const currentScore = details.current_score || {};

  return (
    <div className="flex flex-col gap-6">
      {/* Back Button */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/intelligence/scoring/suppliers')}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour à la liste
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => detailsQuery.refetch()}
          loading={detailsQuery.isFetching}
          iconOnly
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Header */}
      <SupplierHeader details={details} isLoading={detailsQuery.isLoading} />

      {/* Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap',
                activeTab === tab.id
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
        >
          {activeTab === 'overview' && (
            <div className="grid gap-6 lg:grid-cols-2">
              <DimensionScores dimensions={currentScore.dimensions || {}} />
              <HistoryChart history={history} isLoading={historyQuery.isLoading} />
              {details.recommendations?.length > 0 && (
                <div className="lg:col-span-2">
                  <RecommendationsPanel recommendations={details.recommendations} />
                </div>
              )}
            </div>
          )}

          {activeTab === 'products' && (
            <ProductsList supplierName={details.supplier_name} />
          )}

          {activeTab === 'history' && (
            <HistoryChart history={history} isLoading={historyQuery.isLoading} />
          )}

          {activeTab === 'deliveries' && (
            <DeliveriesList deliveries={details.recent_deliveries || []} />
          )}

          {activeTab === 'issues' && (
            <IssuesList issues={details.recent_issues || []} />
          )}

          {activeTab === 'statistics' && (
            <StatisticsPanel statistics={details.statistics || {}} />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
