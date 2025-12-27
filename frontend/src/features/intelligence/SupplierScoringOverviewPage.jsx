/**
 * Page Vue d'Ensemble du Scoring Fournisseurs.
 *
 * Cette page permet de visualiser et analyser la performance globale des fournisseurs.
 * Elle affiche:
 * - Les métriques clés (nombre total, score moyen, tendance globale)
 * - La distribution des fournisseurs par grade (A, B, C, D, F)
 * - Le top 5 des meilleurs fournisseurs
 * - Le bottom 5 des fournisseurs à surveiller
 * - Les alertes actives nécessitant une attention
 *
 * Fonctionnalités principales:
 * - Visualisation de la répartition des grades avec barres de progression
 * - Recalcul manuel des scores pour tous les fournisseurs
 * - Navigation rapide vers le détail d'un fournisseur
 * - Affichage des tendances (amélioration, stable, déclin)
 * - Badges de grade colorés pour identification rapide
 * - Cartes métriques animées avec indicateurs de tendance
 *
 * Implémentation conforme à SUPPLIER_SCORING_FRONTEND_INTEGRATION.md
 *
 * @component
 *
 * @example
 * <SupplierScoringOverviewPage />
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Users,
  TrendingUp,
  TrendingDown,
  Award,
  AlertTriangle,
  RefreshCw,
  ChevronRight,
  BarChart3,
} from 'lucide-react';
import clsx from 'clsx';
import {
  useSupplierScoringOverview,
  useSupplierAlerts,
  useRecalculateScores,
} from '@/hooks/useSupplierScoring.js';
import Card, { CardHeader, CardContent } from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Badge from '@/components/ui/Badge.jsx';
import { Skeleton } from '@/components/ui/Skeleton.jsx';

// ============================================================================
// GRADE CONFIG
// ============================================================================

const GRADE_CONFIG = {
  A: { color: 'emerald', label: 'Excellent', bg: 'bg-emerald-500', text: 'text-emerald-400' },
  B: { color: 'blue', label: 'Bon', bg: 'bg-blue-500', text: 'text-blue-400' },
  C: { color: 'amber', label: 'Moyen', bg: 'bg-amber-500', text: 'text-amber-400' },
  D: { color: 'orange', label: 'Faible', bg: 'bg-orange-500', text: 'text-orange-400' },
  F: { color: 'rose', label: 'Critique', bg: 'bg-rose-500', text: 'text-rose-400' },
};

const TREND_ICONS = {
  improving: { icon: TrendingUp, color: 'text-emerald-400', label: 'En hausse' },
  stable: { icon: BarChart3, color: 'text-slate-400', label: 'Stable' },
  declining: { icon: TrendingDown, color: 'text-rose-400', label: 'En baisse' },
  up: { icon: TrendingUp, color: 'text-emerald-400', label: 'En hausse' },
  down: { icon: TrendingDown, color: 'text-rose-400', label: 'En baisse' },
};

// ============================================================================
// METRIC CARD COMPONENT
// ============================================================================

function MetricCard({ title, value, suffix, icon: Icon, trend, variant = 'default', isLoading }) {
  const variantStyles = {
    default: 'bg-slate-800/50 border-white/10',
    success: 'bg-emerald-500/10 border-emerald-500/30',
    warning: 'bg-amber-500/10 border-amber-500/30',
    danger: 'bg-rose-500/10 border-rose-500/30',
  };

  const trendConfig = trend ? TREND_ICONS[trend] : null;
  const TrendIcon = trendConfig?.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'p-4 rounded-xl border transition-all',
        variantStyles[variant]
      )}
    >
      {isLoading ? (
        <Skeleton className="h-20" />
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">{title}</span>
            {Icon && <Icon className="w-5 h-5 text-slate-500" />}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{value}</span>
            {suffix && <span className="text-sm text-slate-400">{suffix}</span>}
          </div>
          {trendConfig && TrendIcon && (
            <div className={clsx('flex items-center gap-1 mt-2 text-xs', trendConfig.color)}>
              <TrendIcon className="w-3 h-3" />
              <span>{trendConfig.label}</span>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}

// ============================================================================
// GRADE DISTRIBUTION COMPONENT
// ============================================================================

function GradeDistribution({ distribution = {}, total = 0, isLoading }) {
  const grades = ['A', 'B', 'C', 'D', 'F'];

  return (
    <Card padding="lg">
      <CardHeader title="Distribution des grades" description="Répartition des fournisseurs par niveau de performance" />
      <CardContent>
        {isLoading ? (
          <div className="flex gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="flex-1 h-24" />
            ))}
          </div>
        ) : (
          <div className="flex gap-4">
            {grades.map((grade) => {
              const count = distribution[grade] || 0;
              const percentage = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
              const config = GRADE_CONFIG[grade];

              return (
                <motion.div
                  key={grade}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex-1 text-center"
                >
                  <div
                    className={clsx(
                      'text-4xl font-bold mb-2',
                      config.text
                    )}
                  >
                    {grade}
                  </div>
                  <div className="text-2xl font-semibold text-white">{count}</div>
                  <div className="text-xs text-slate-400">{percentage}%</div>
                  <div className="mt-2 h-1 rounded-full bg-slate-700 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.5, delay: 0.2 }}
                      className={clsx('h-full rounded-full', config.bg)}
                    />
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
// SUPPLIER LIST COMPONENT
// ============================================================================

function SupplierList({ suppliers = [], title, variant = 'default', onSupplierClick, isLoading }) {
  const variantStyles = {
    default: '',
    success: 'border-emerald-500/30',
    danger: 'border-rose-500/30',
  };

  const itemVariants = {
    default: 'hover:bg-white/5',
    success: 'bg-emerald-500/5 hover:bg-emerald-500/10',
    danger: 'bg-rose-500/5 hover:bg-rose-500/10',
  };

  if (isLoading) {
    return (
      <Card padding="lg" className={variantStyles[variant]}>
        <CardHeader title={title} />
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card padding="lg" className={variantStyles[variant]}>
      <CardHeader title={title} />
      <CardContent>
        {suppliers.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-4">Aucun fournisseur</p>
        ) : (
          <div className="space-y-2">
            {suppliers.map((supplier, idx) => {
              const config = GRADE_CONFIG[supplier.grade] || GRADE_CONFIG.C;
              const TrendIcon = supplier.trend ? TREND_ICONS[supplier.trend]?.icon : null;
              const trendColor = supplier.trend ? TREND_ICONS[supplier.trend]?.color : '';

              return (
                <motion.div
                  key={supplier.supplier_id || supplier.supplier_name || idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  onClick={() => onSupplierClick?.(supplier)}
                  className={clsx(
                    'flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors',
                    itemVariants[variant],
                    'border border-white/5'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={clsx(
                        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white',
                        config.bg
                      )}
                    >
                      {supplier.grade || 'C'}
                    </div>
                    <div>
                      <p className="font-medium text-white">{supplier.supplier_name || supplier.name}</p>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span>Score: {(supplier.overall_score || supplier.score || 0).toFixed(0)}</span>
                        {TrendIcon && (
                          <span className={clsx('flex items-center gap-0.5', trendColor)}>
                            <TrendIcon className="w-3 h-3" />
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500" />
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
// ALERTS SUMMARY COMPONENT
// ============================================================================

function AlertsSummary({ summary = {}, isLoading, onViewAll }) {
  const alertTypes = [
    { key: 'score_drop', label: 'Baisse de score', icon: TrendingDown, color: 'rose' },
    { key: 'delivery_issues', label: 'Problèmes livraison', icon: AlertTriangle, color: 'orange' },
    { key: 'quality_degradation', label: 'Qualité dégradée', icon: AlertTriangle, color: 'amber' },
    { key: 'price_spike', label: 'Hausse de prix', icon: TrendingUp, color: 'purple' },
  ];

  const totalAlerts = Object.values(summary).reduce((acc, val) => acc + (val || 0), 0);

  return (
    <Card padding="lg">
      <CardHeader
        title="Alertes fournisseurs"
        description={`${totalAlerts} alerte${totalAlerts > 1 ? 's' : ''} active${totalAlerts > 1 ? 's' : ''}`}
        action={
          <Button variant="ghost" size="sm" onClick={() => recalcMutation.mutate()}>
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        }
      />
      <CardContent>
        {isLoading ? (
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {alertTypes.map(({ key, label, icon: Icon, color }) => {
              const count = summary[key] || 0;
              return (
                <div
                  key={key}
                  className={clsx(
                    'p-3 rounded-lg border',
                    count > 0 ? `bg-${color}-500/10 border-${color}-500/30` : 'bg-slate-800/50 border-white/10'
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className={clsx('w-4 h-4', count > 0 ? `text-${color}-400` : 'text-slate-500')} />
                    <span className={clsx('text-lg font-bold', count > 0 ? `text-${color}-400` : 'text-slate-400')}>
                      {count}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{label}</p>
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
// MAIN PAGE COMPONENT
// ============================================================================

export default function SupplierScoringOverviewPage() {
  const navigate = useNavigate();

  // Queries
  const overviewQuery = useSupplierScoringOverview();
  const alertsQuery = useSupplierAlerts({ limit: 10 });
  const recalculateMutation = useRecalculateScores();

  const overview = overviewQuery.data || {};
  const isLoading = overviewQuery.isLoading;

  const {
    total_suppliers = 0,
    average_score = 0,
    score_distribution = {},
    top_suppliers = [],
    bottom_suppliers = [],
    trends = {},
    alerts_summary = {},
  } = overview;

  const handleSupplierClick = (supplier) => {
    const id = supplier.supplier_id || supplier.id;
    if (id) {
      navigate(`/intelligence/scoring/suppliers/${id}`);
    }
  };

  const handleRecalculate = () => {
    recalculateMutation.mutate({ force: false });
  };

  const handleViewAllAlerts = () => {
    navigate('/intelligence/scoring/alerts');
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
          <h1 className="text-2xl font-semibold text-white">Scoring Fournisseurs</h1>
          <p className="text-sm text-slate-400">
            Vue d'ensemble des performances et notation de vos fournisseurs
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => overviewQuery.refetch()}
            loading={overviewQuery.isFetching}
            iconOnly
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRecalculate}
            loading={recalculateMutation.isPending}
          >
            Recalculer les scores
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate('/intelligence/scoring/suppliers')}
          >
            Voir tous les fournisseurs
          </Button>
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          title="Fournisseurs"
          value={total_suppliers}
          icon={Users}
          isLoading={isLoading}
        />
        <MetricCard
          title="Score moyen"
          value={average_score.toFixed(1)}
          suffix="/100"
          icon={Award}
          trend={trends.overall_trend}
          isLoading={isLoading}
        />
        <MetricCard
          title="En amélioration"
          value={trends.improving_count || 0}
          icon={TrendingUp}
          variant="success"
          isLoading={isLoading}
        />
        <MetricCard
          title="En déclin"
          value={trends.declining_count || 0}
          icon={TrendingDown}
          variant="danger"
          isLoading={isLoading}
        />
      </div>

      {/* Grade Distribution */}
      <GradeDistribution
        distribution={score_distribution}
        total={total_suppliers}
        isLoading={isLoading}
      />

      {/* Top/Bottom Suppliers + Alerts */}
      <div className="grid gap-6 lg:grid-cols-3">
        <SupplierList
          suppliers={top_suppliers.slice(0, 5)}
          title="Top 5 fournisseurs"
          variant="success"
          onSupplierClick={(supplier) => navigate(`/intelligence/scoring/suppliers/${supplier.supplier_id || supplier.id}`)}
        />
        <SupplierList
          suppliers={bottom_suppliers.slice(0, 5)}
          title="5 fournisseurs à améliorer"
          variant="danger"
          onSupplierClick={handleSupplierClick}
          isLoading={isLoading}
        />
        <AlertsSummary
          summary={alerts_summary}
          isLoading={alertsQuery.isLoading}
          onViewAll={() => navigate('/intelligence/scoring/alerts')}
        />
      </div>
    </div>
  );
}
