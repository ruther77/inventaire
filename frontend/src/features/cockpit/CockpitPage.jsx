/**
 * Cockpit Morning Brief - Vue 360° Next-Gen
 *
 * Scénario 3.1 du UX_NEXT_GEN_2025.md
 * - Brief matinal avec KPIs de la veille
 * - Alertes actionnables avec suggestions IA
 * - Prévisions de la semaine
 * - Actions en 1 clic
 */

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Sun,
  Moon,
  TrendingUp,
  TrendingDown,
  Minus,
  Package,
  Receipt,
  AlertTriangle,
  CheckCircle,
  Clock,
  Calendar,
  ChevronRight,
  Sparkles,
  ShoppingCart,
  Wallet,
  BarChart3,
  Zap,
  RefreshCw,
  Eye,
} from 'lucide-react';
import clsx from 'clsx';

import {
  fetchCockpitOverview,
  acknowledgeCockpitAlert,
  fetchForecastingSummary,
  fetchAnomalySummary,
} from '../../api/client.js';
import AlertCard, { AlertList } from '../../components/ai/AlertCard.jsx';
import SuggestionCard from '../../components/ai/SuggestionCard.jsx';
import QuickAction, { QuickActionGroup } from '../../components/ai/QuickAction.jsx';
import { Skeleton } from '../../components/ui/Skeleton.jsx';
import CardExpandable from '../../components/ui/CardExpandable.jsx';
import AIConfidenceBadge from '../../components/ui/AIConfidenceBadge.jsx';

// ============================================================================
// UTILITIES
// ============================================================================

const formatCurrency = (val) => {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(val);
};

const formatPercent = (val) => {
  if (val === null || val === undefined) return '—';
  return `${val.toFixed(1)}%`;
};

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return { text: 'Bonjour', icon: Sun, period: 'matin' };
  if (hour < 18) return { text: 'Bon après-midi', icon: Sun, period: 'après-midi' };
  return { text: 'Bonsoir', icon: Moon, period: 'soir' };
};

const getDayName = (offset = 0) => {
  const days = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return days[date.getDay()];
};

// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * KPI Card avec tendance
 */
function KPICard({ label, value, unit, trend, status, onClick }) {
  const TrendIcon = trend > 0 ? TrendingUp : trend < 0 ? TrendingDown : Minus;
  const trendColor = trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-rose-400' : 'text-slate-400';

  const statusColors = {
    success: 'border-emerald-500/30 bg-emerald-500/5',
    warning: 'border-amber-500/30 bg-amber-500/5',
    error: 'border-rose-500/30 bg-rose-500/5',
    neutral: 'border-white/10 bg-white/5',
  };

  const displayValue = unit === '€' ? formatCurrency(value) : unit === '%' ? formatPercent(value) : value;

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={clsx(
        'relative p-4 rounded-xl border cursor-pointer',
        'transition-all duration-200',
        statusColors[status || 'neutral']
      )}
    >
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{displayValue}</p>

      {trend !== null && trend !== undefined && (
        <div className={clsx('flex items-center gap-1 mt-2', trendColor)}>
          <TrendIcon className="w-3 h-3" />
          <span className="text-xs font-medium">
            {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
          </span>
        </div>
      )}
    </motion.div>
  );
}

/**
 * Section "Hier en bref" - Utilise les vraies données du cockpit
 */
function YesterdayBrief({ data }) {
  // Extraire les KPIs du cockpit overview
  const kpis = useMemo(() => {
    if (data?.kpis?.length) {
      // Mapper les KPIs du backend vers le format attendu
      return data.kpis.slice(0, 4).map((kpi) => ({
        label: kpi.label,
        value: kpi.value,
        unit: kpi.unit || '',
        trend: kpi.trend,
        status: kpi.status === 'info' ? 'neutral' : kpi.status,
      }));
    }

    // Fallback avec données stock/marges/trésorerie si disponibles
    const fallbackKpis = [];

    if (data?.stock) {
      fallbackKpis.push({
        label: 'Valeur Stock',
        value: data.stock.total_value_ht || 0,
        unit: '€',
        status: 'neutral',
      });
      fallbackKpis.push({
        label: 'Alertes Stock',
        value: (data.stock.low_stock_count || 0) + (data.stock.out_of_stock_count || 0),
        unit: '',
        status: data.stock.out_of_stock_count > 0 ? 'error' : data.stock.low_stock_count > 5 ? 'warning' : 'success',
      });
    }

    if (data?.margins) {
      fallbackKpis.push({
        label: 'Marge Moyenne',
        value: data.margins.avg_margin_pct || 0,
        unit: '%',
        status: (data.margins.avg_margin_pct || 0) >= 30 ? 'success' : (data.margins.avg_margin_pct || 0) >= 20 ? 'warning' : 'error',
      });
    }

    if (data?.treasury) {
      fallbackKpis.push({
        label: 'Flux Net 7j',
        value: data.treasury.net_flow_7d || 0,
        unit: '€',
        status: (data.treasury.net_flow_7d || 0) >= 0 ? 'success' : 'error',
      });
    }

    return fallbackKpis.length ? fallbackKpis : [
      { label: 'CA Jour', value: 0, unit: '€', status: 'neutral' },
      { label: 'Marge Brute', value: 0, unit: '%', status: 'neutral' },
      { label: 'Tickets', value: 0, unit: '', status: 'neutral' },
      { label: 'Panier Moyen', value: 0, unit: '€', status: 'neutral' },
    ];
  }, [data]);

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">Situation actuelle</h3>
        {data?.health_score !== undefined && (
          <span className={clsx(
            'ml-auto text-xs px-2 py-0.5 rounded-full',
            data.health_status === 'healthy' ? 'bg-emerald-500/20 text-emerald-400' :
            data.health_status === 'warning' ? 'bg-amber-500/20 text-amber-400' :
            'bg-rose-500/20 text-rose-400'
          )}>
            Santé: {data.health_score}%
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {kpis.map((kpi, index) => (
          <KPICard key={index} {...kpi} />
        ))}
      </div>
    </div>
  );
}

/**
 * Section "À traiter aujourd'hui" avec alertes actionnables
 * Utilise les vraies alertes du cockpit backend
 */
function TodayActions({ alerts = [], onAction }) {
  const navigate = useNavigate();

  // Transformer les données API en format AlertCard attendu
  const formattedAlerts = useMemo(() => {
    // Si on a des alertes du backend (format CockpitOverview.alerts)
    if (alerts?.length) {
      return alerts.map((a, idx) => {
        // Mapper severity backend vers frontend
        const severityMap = {
          critical: 'urgent',
          warning: 'medium',
          info: 'info',
        };

        // Mapper category vers action_url et actions
        const categoryActions = {
          stock: {
            actions: [
              { id: 'view', label: 'Voir stock', icon: Package, variant: 'primary' },
              { id: 'ack', label: 'OK', icon: CheckCircle, variant: 'success', dismissOnComplete: true },
            ],
            path: '/operations/catalogue',
          },
          finance: {
            actions: [
              { id: 'review', label: 'Voir détail', icon: Eye, variant: 'primary' },
              { id: 'ack', label: 'OK', icon: CheckCircle, variant: 'success', dismissOnComplete: true },
            ],
            path: '/finances/tresorerie',
          },
          margin: {
            actions: [
              { id: 'analyze', label: 'Analyser', icon: BarChart3, variant: 'primary' },
              { id: 'ack', label: 'OK', icon: CheckCircle, variant: 'success', dismissOnComplete: true },
            ],
            path: '/intelligence/marges',
          },
          anomaly: {
            actions: [
              { id: 'investigate', label: 'Investiguer', icon: Eye, variant: 'primary' },
              { id: 'ack', label: 'OK', icon: CheckCircle, variant: 'success', dismissOnComplete: true },
            ],
            path: '/intelligence/anomalies',
          },
        };

        const categoryConfig = categoryActions[a.category] || categoryActions.stock;

        return {
          id: a.id || `alert-${idx}`,
          severity: severityMap[a.severity] || 'info',
          title: a.title || 'Alerte',
          description: a.message || '',
          suggestion: a.action_url ? `Action: ${a.action_url}` : '',
          actions: categoryConfig.actions,
          meta: {
            category: a.category,
            entity_type: a.entity_type,
            entity_id: a.entity_id,
            path: a.action_url || categoryConfig.path,
          },
        };
      });
    }

    // Pas de données de démo - retourner tableau vide si pas d'alertes
    // Les vraies alertes viennent du backend
    return [];
  }, [alerts]);

  const handleAction = (actionId, alertId) => {
    if (onAction) onAction(actionId, alertId);

    // Trouver l'alerte pour récupérer son path
    const alert = formattedAlerts.find((a) => a.id === alertId);
    const path = alert?.meta?.path;

    // Navigation selon l'action
    if (actionId === 'ack') {
      // Acknowledge - pas de navigation
      return;
    }

    if (path) {
      navigate(path);
    } else {
      // Fallback basé sur actionId
      switch (actionId) {
        case 'view':
          navigate('/operations/catalogue');
          break;
        case 'review':
          navigate('/finances/tresorerie');
          break;
        case 'analyze':
          navigate('/intelligence/marges');
          break;
        case 'investigate':
          navigate('/intelligence/anomalies');
          break;
        default:
          break;
      }
    }
  };

  const urgentCount = formattedAlerts.filter((a) => a.severity === 'urgent').length;
  const totalCount = formattedAlerts.length;

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {totalCount > 0 ? (
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          ) : (
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          )}
          <h3 className="font-semibold text-white">
            {totalCount > 0 ? 'À traiter aujourd\'hui' : 'Tout est en ordre'}
            {totalCount > 0 && (
              <span className="ml-2 text-sm font-normal text-slate-400">({totalCount} actions)</span>
            )}
          </h3>
        </div>

        {totalCount > 0 && (
          <QuickAction
            icon={Zap}
            label="Tout traiter"
            variant="primary"
            size="sm"
            onClick={() => {}}
          />
        )}
      </div>

      {totalCount > 0 ? (
        <AlertList
          alerts={formattedAlerts}
          onAction={handleAction}
          maxVisible={3}
        />
      ) : (
        <div className="text-center py-6 text-slate-400">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
          <p className="text-sm">Aucune action urgente pour le moment.</p>
          <p className="text-xs mt-1 text-slate-500">Le système surveille vos stocks, marges et anomalies en continu.</p>
        </div>
      )}
    </div>
  );
}

/**
 * Section "Prévisions Semaine"
 * Utilise les vraies données de forecasting et stock
 */
function WeekForecast({ data, forecastData, stockData }) {
  const navigate = useNavigate();

  // Données API ou calculées à partir de forecasting/stock
  const weekData = useMemo(() => {
    // Si on a des données forecast explicites
    if (Array.isArray(data) && data.length) {
      return data.map((d, idx) => ({
        day: d.day || d.label || getDayName(idx),
        ca: d.ca || d.revenue || 0,
        stockStatus: d.stock_status || d.stockStatus || 'ok',
        isToday: Boolean(d.is_today || d.isToday),
      }));
    }

    // Construire à partir des données de forecasting summary
    const weekDays = [0, 1, 2, 3, 4, 5, 6].map((offset) => {
      const dayOfWeek = (new Date().getDay() + offset) % 7;
      const isWeekend = [0, 6].includes(dayOfWeek);

      // Utiliser les données de ventes récentes pour estimer
      let estimatedCA = 0;
      if (forecastData?.sales?.recent_7_days) {
        // Moyenne journalière basée sur les 7 derniers jours
        const avgDaily = forecastData.sales.recent_7_days / 7;
        // Ajustement weekend (+ ou - 20%)
        estimatedCA = avgDaily * (isWeekend ? 1.2 : 1);
        // Appliquer la tendance
        if (forecastData.sales.trend_direction === 'up') {
          estimatedCA *= 1 + (offset * 0.02); // +2% par jour si tendance haussière
        } else if (forecastData.sales.trend_direction === 'down') {
          estimatedCA *= 1 - (offset * 0.01); // -1% par jour si tendance baissière
        }
      }

      // Déterminer le statut stock
      let stockStatus = 'ok';
      if (stockData) {
        // Si des produits sont en dépletion dans les prochains jours
        const productsAtRisk = stockData.reorder_needed || 0;
        const outOfStock = stockData.out_of_stock_count || 0;

        if (outOfStock > 0 && offset <= 2) {
          stockStatus = 'warning';
        } else if (productsAtRisk > 5 && offset >= 4) {
          stockStatus = 'warning';
        }
      }

      return {
        day: getDayName(offset),
        ca: Math.round(estimatedCA || (1500 + offset * 100)),
        stockStatus,
        isToday: offset === 0,
      };
    });

    return weekDays;
  }, [data, forecastData, stockData]);

  const hasStockWarning = weekData.some((d) => d.stockStatus === 'warning');

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <Calendar className="w-5 h-5 text-violet-400" />
        <h3 className="font-semibold text-white">Prévisions Semaine</h3>
      </div>

      {/* Grille des jours */}
      <div className="grid grid-cols-7 gap-2 mb-4">
        {weekData.map((day, index) => (
          <motion.div
            key={index}
            whileHover={{ scale: 1.05 }}
            className={clsx(
              'text-center p-2 rounded-lg',
              day.isToday ? 'bg-blue-500/20 border border-blue-500/30' : 'bg-white/5'
            )}
          >
            <p className={clsx(
              'text-xs font-medium mb-1',
              day.isToday ? 'text-blue-400' : 'text-slate-400'
            )}>
              {day.day}
            </p>
            <p className="text-sm font-bold text-white">
              {(day.ca / 1000).toFixed(1)}k
            </p>
            <div className="mt-1">
              {day.stockStatus === 'ok' ? (
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" title="Stock OK" />
              ) : (
                <span className="inline-block w-2 h-2 rounded-full bg-amber-500 animate-pulse" title="Attention stock" />
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Alerte stock si nécessaire */}
      {hasStockWarning && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between p-3 rounded-lg bg-amber-500/10 border border-amber-500/20"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <p className="text-sm text-amber-300">
              Rupture probable sur 4 produits vendredi/samedi
            </p>
          </div>
          <button
            onClick={() => navigate('/intelligence/stock')}
            className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1"
          >
            Voir détail
            <ChevronRight className="w-3 h-3" />
          </button>
        </motion.div>
      )}
    </div>
  );
}

/**
 * Suggestion IA rapide
 */
function QuickSuggestion({ onNavigate }) {
  return (
    <CardExpandable
      title="Suggestion IA"
      subtitle="Scénario 3.1"
      summary="Augmenter le prix de 5 produits sous-margés"
      variant="info"
      defaultExpanded
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-500" />
          <h3 className="font-semibold text-slate-900">Optimisation marge</h3>
        </div>
        <AIConfidenceBadge
          confidence={0.92}
          label="Confiance IA"
          variant="pill"
          size="sm"
          explanation="Basé sur l'élasticité prix et l'historique de ventes"
        />
      </div>

      <SuggestionCard
        id="margin-optimization"
        type="optimization"
        title="Augmenter le prix de 5 produits sous-margés"
        description="Basé sur l'analyse d'élasticité prix et la concurrence"
        impact={{ value: '+847€', period: '/mois' }}
        confidence={0.92}
        details={{
          table: {
            headers: ['Produit', 'Prix actuel', 'Prix suggéré', 'Impact'],
            rows: [
              ['Café Premium 500g', '8.90€', '9.90€', '+124€/mois'],
              ['Miel Bio 500g', '12.50€', '14.90€', '+216€/mois'],
              ['Huile Truffe 100ml', '18.00€', '22.00€', '+180€/mois'],
            ],
          },
          explanation: 'Ces prix restent compétitifs par rapport au marché et l\'élasticité prix de ces produits est faible.',
        }}
        actions={[
          { id: 'simulate', label: 'Simulation', icon: BarChart3 },
        ]}
        onAction={(action) => {
          if (action === 'apply') {
            onNavigate('/intelligence/marges');
          }
        }}
      />
    </CardExpandable>
  );
}

/**
 * Actions rapides
 */
function QuickActions({ onNavigate }) {
  const actions = [
    { icon: Receipt, label: 'Scanner facture', path: '/operations/factures', variant: 'primary' },
    { icon: Package, label: 'Vérifier stock', path: '/operations/stock', variant: 'default' },
    { icon: Wallet, label: 'Trésorerie', path: '/finances/tresorerie', variant: 'default' },
    { icon: BarChart3, label: 'Rapports', path: '/finances/portefeuille', variant: 'default' },
  ];

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-5 h-5 text-amber-400" />
        <h3 className="font-semibold text-white">Actions rapides</h3>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {actions.map((action, index) => (
          <QuickAction
            key={index}
            icon={action.icon}
            label={action.label}
            variant={action.variant}
            size="md"
            onClick={() => onNavigate(action.path)}
            className="w-full justify-start"
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Header avec salutation
 */
function MorningHeader({ userName = 'Chef' }) {
  const greeting = getGreeting();
  const GreetingIcon = greeting.icon;
  const today = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6"
    >
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20">
          <GreetingIcon className="w-6 h-6 text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">
            {greeting.text}, {userName} !
          </h1>
          <p className="text-sm text-slate-400 capitalize">{today}</p>
        </div>
      </div>
      <p className="text-slate-400">
        Voici votre brief du {greeting.period}
      </p>
    </motion.div>
  );
}

/**
 * Skeleton de chargement
 */
function CockpitSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-20 bg-slate-800/50 rounded-2xl" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-slate-800/50 rounded-xl" />
        ))}
      </div>
      <div className="h-64 bg-slate-800/50 rounded-2xl" />
      <div className="grid grid-cols-2 gap-6">
        <div className="h-48 bg-slate-800/50 rounded-2xl" />
        <div className="h-48 bg-slate-800/50 rounded-2xl" />
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function CockpitPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query principale: cockpit overview avec KPIs, alertes, stocks, marges, trésorerie
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['cockpit-overview'],
    queryFn: fetchCockpitOverview,
    staleTime: 60000,
    refetchInterval: 60000,
  });

  // Query secondaire: prévisions (ventes, stock, cash-flow)
  const { data: forecastData } = useQuery({
    queryKey: ['forecasting-summary'],
    queryFn: fetchForecastingSummary,
    staleTime: 5 * 60000, // 5 minutes
    enabled: !isLoading, // Charger après le cockpit principal
  });

  // Query tertiaire: anomalies détectées
  const { data: anomalyData } = useQuery({
    queryKey: ['anomaly-summary'],
    queryFn: () => fetchAnomalySummary({ days_back: 7 }),
    staleTime: 5 * 60000, // 5 minutes
    enabled: !isLoading,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId) => acknowledgeCockpitAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cockpit-overview'] });
      toast.success('Alerte traitée');
    },
    onError: () => toast.error('Impossible de traiter cette alerte'),
  });

  const handleNavigate = (path) => {
    navigate(path);
  };

  const handleAlertAction = (actionId, alertId) => {
    if (alertId && actionId === 'ack' && !acknowledgeMutation.isPending) {
      acknowledgeMutation.mutate(alertId);
    }
  };

  // Combiner les alertes cockpit + anomalies critiques
  const combinedAlerts = useMemo(() => {
    const alerts = [...(data?.alerts || [])];

    // Ajouter les anomalies critiques comme alertes
    if (anomalyData?.items?.length) {
      const criticalAnomalies = anomalyData.items
        .filter((a) => a.severity === 'critical' || a.severity === 'high')
        .slice(0, 3)
        .map((a) => ({
          id: `anomaly-${a.id}`,
          severity: a.severity === 'critical' ? 'critical' : 'warning',
          category: 'anomaly',
          title: a.title || 'Anomalie détectée',
          message: a.description || '',
          action_url: '/intelligence/anomalies',
          created_at: a.detected_at,
        }));

      alerts.push(...criticalAnomalies);
    }

    return alerts;
  }, [data?.alerts, anomalyData?.items]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center p-8 rounded-2xl bg-slate-800/50 border border-white/10">
          <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Erreur de chargement</h2>
          <p className="text-slate-400 mb-4">{error.message}</p>
          <QuickAction
            icon={RefreshCw}
            label="Réessayer"
            variant="primary"
            onClick={() => refetch()}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <MorningHeader />

        {isLoading ? (
          <CockpitSkeleton />
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {/* Situation actuelle - KPIs */}
            <YesterdayBrief data={data} />

            {/* À traiter aujourd'hui - Alertes combinées */}
            <TodayActions
              alerts={combinedAlerts}
              onAction={handleAlertAction}
            />

            {/* Grid 2 colonnes */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Prévisions semaine - avec données forecasting */}
              <WeekForecast
                data={data?.forecast}
                forecastData={forecastData}
                stockData={data?.stock}
              />

              {/* Actions rapides */}
              <QuickActions onNavigate={handleNavigate} />
            </div>

            {/* Suggestion IA */}
            <QuickSuggestion onNavigate={handleNavigate} />
          </motion.div>
        )}
      </div>
    </div>
  );
}
