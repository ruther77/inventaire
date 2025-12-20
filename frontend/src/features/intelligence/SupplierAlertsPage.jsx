/**
 * SupplierAlertsPage - Alertes fournisseurs
 *
 * Implémentation exacte selon SUPPLIER_SCORING_FRONTEND_INTEGRATION.md
 * Affiche les alertes avec filtres et possibilité d'acquittement.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  RefreshCw,
  Filter,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  ChevronRight,
  Bell,
  BellOff,
} from 'lucide-react';
import clsx from 'clsx';
import { useSupplierAlerts, useAcknowledgeAlert } from '@/hooks/useSupplierScoring.js';
import Card, { CardHeader, CardContent } from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Badge from '@/components/ui/Badge.jsx';
import { Skeleton } from '@/components/ui/Skeleton.jsx';

// ============================================================================
// CONFIG
// ============================================================================

const SEVERITY_CONFIG = {
  critical: {
    label: 'Critique',
    icon: AlertTriangle,
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
    text: 'text-rose-400',
    badgeVariant: 'danger',
  },
  warning: {
    label: 'Attention',
    icon: AlertCircle,
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    badgeVariant: 'warning',
  },
  info: {
    label: 'Info',
    icon: AlertCircle,
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    badgeVariant: 'info',
  },
};

const ALERT_TYPE_CONFIG = {
  score_drop: {
    label: 'Baisse de score',
    icon: TrendingDown,
    color: 'rose',
  },
  delivery_issues: {
    label: 'Problèmes livraison',
    icon: AlertTriangle,
    color: 'orange',
  },
  quality_degradation: {
    label: 'Qualité dégradée',
    icon: AlertCircle,
    color: 'amber',
  },
  price_spike: {
    label: 'Hausse de prix',
    icon: TrendingUp,
    color: 'purple',
  },
};

// ============================================================================
// FILTER COMPONENT
// ============================================================================

function FiltersPanel({ filters, onFiltersChange }) {
  return (
    <Card padding="md">
      <div className="flex flex-wrap items-center gap-4">
        {/* Severity Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Sévérité:</label>
          <select
            value={filters.severity || ''}
            onChange={(e) => onFiltersChange({ ...filters, severity: e.target.value || undefined })}
            className="px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Toutes</option>
            <option value="critical">Critique</option>
            <option value="warning">Attention</option>
            <option value="info">Info</option>
          </select>
        </div>

        {/* Acknowledged Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Statut:</label>
          <select
            value={filters.acknowledged === undefined ? '' : filters.acknowledged.toString()}
            onChange={(e) => {
              const val = e.target.value;
              onFiltersChange({
                ...filters,
                acknowledged: val === '' ? undefined : val === 'true',
              });
            }}
            className="px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Toutes</option>
            <option value="false">Non acquittées</option>
            <option value="true">Acquittées</option>
          </select>
        </div>
      </div>
    </Card>
  );
}

// ============================================================================
// ALERT CARD COMPONENT
// ============================================================================

function AlertCard({ alert, onAcknowledge, onViewSupplier }) {
  const severityConfig = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
  const typeConfig = ALERT_TYPE_CONFIG[alert.alert_type] || {
    label: alert.alert_type,
    icon: AlertCircle,
    color: 'slate',
  };

  const SeverityIcon = severityConfig.icon;
  const TypeIcon = typeConfig.icon;

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'p-4 rounded-xl border',
        severityConfig.bg,
        severityConfig.border,
        alert.acknowledged && 'opacity-60'
      )}
    >
      <div className="flex items-start gap-4">
        {/* Severity Icon */}
        <div className={clsx('p-2 rounded-lg', severityConfig.bg)}>
          <SeverityIcon className={clsx('w-5 h-5', severityConfig.text)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <Badge variant={severityConfig.badgeVariant}>{severityConfig.label}</Badge>
            <Badge variant="default" className={clsx(`bg-${typeConfig.color}-500/20`, `text-${typeConfig.color}-400`)}>
              <TypeIcon className="w-3 h-3 mr-1" />
              {typeConfig.label}
            </Badge>
            {alert.acknowledged && (
              <Badge variant="success">
                <CheckCircle className="w-3 h-3 mr-1" />
                Acquittée
              </Badge>
            )}
          </div>

          {/* Supplier */}
          <p className="text-sm text-slate-400 mb-1">
            {alert.supplier_name}
          </p>

          {/* Message */}
          <p className="text-white font-medium">{alert.message}</p>

          {/* Details */}
          {alert.details && (
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              {Object.entries(alert.details).map(([key, value]) => (
                <div key={key} className="bg-white/5 rounded px-2 py-1">
                  <span className="text-slate-500">{key}: </span>
                  <span className="text-white">{String(value)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <Clock className="w-3 h-3" />
              {formatDate(alert.created_at)}
            </div>

            <div className="flex items-center gap-2">
              {!alert.acknowledged && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onAcknowledge(alert.alert_id)}
                  className="text-emerald-400 hover:bg-emerald-500/10"
                >
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Acquitter
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onViewSupplier(alert.supplier_id)}
              >
                Voir fournisseur
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ============================================================================
// SUMMARY CARDS
// ============================================================================

function SummaryCards({ totalCount, unacknowledgedCount, isLoading }) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card padding="md">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-slate-500/20">
            <Bell className="w-5 h-5 text-slate-400" />
          </div>
          <div>
            <p className="text-3xl font-bold text-white">{totalCount}</p>
            <p className="text-sm text-slate-400">Alertes totales</p>
          </div>
        </div>
      </Card>

      <Card padding="md" className="bg-amber-500/10 border-amber-500/30">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-amber-500/20">
            <AlertCircle className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <p className="text-3xl font-bold text-amber-400">{unacknowledgedCount}</p>
            <p className="text-sm text-slate-400">Non acquittées</p>
          </div>
        </div>
      </Card>

      <Card padding="md" className="bg-emerald-500/10 border-emerald-500/30">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-emerald-500/20">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-3xl font-bold text-emerald-400">
              {totalCount - unacknowledgedCount}
            </p>
            <p className="text-sm text-slate-400">Acquittées</p>
          </div>
        </div>
      </Card>
    </div>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function SupplierAlertsPage() {
  const navigate = useNavigate();

  // Filters state
  const [filters, setFilters] = useState({
    severity: undefined,
    acknowledged: undefined,
    limit: 100,
  });

  // Query
  const alertsQuery = useSupplierAlerts(filters);

  // Mutation pour acquitter une alerte
  const acknowledgeMutation = useAcknowledgeAlert();

  const data = alertsQuery.data?.data || alertsQuery.data || {};
  const alerts = data.alerts || [];
  const totalCount = data.total_count || 0;
  const unacknowledgedCount = data.unacknowledged_count || 0;

  const handleAcknowledge = async (alertId) => {
    try {
      await acknowledgeMutation.mutateAsync(alertId);
    } catch (error) {
      console.error('Erreur lors de l\'acquittement de l\'alerte:', error);
    }
  };

  const handleViewSupplier = (supplierId) => {
    if (supplierId) {
      navigate(`/intelligence/scoring/suppliers/${supplierId}`);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/intelligence/scoring')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
            <h1 className="text-2xl font-semibold text-white">Alertes Fournisseurs</h1>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => alertsQuery.refetch()}
            loading={alertsQuery.isFetching}
            iconOnly
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <SummaryCards
        totalCount={totalCount}
        unacknowledgedCount={unacknowledgedCount}
        isLoading={alertsQuery.isLoading}
      />

      {/* Filters */}
      <FiltersPanel filters={filters} onFiltersChange={setFilters} />

      {/* Alerts List */}
      <Card padding="lg">
        <CardHeader
          title="Liste des alertes"
          description={`${alerts.length} alerte${alerts.length > 1 ? 's' : ''} trouvée${alerts.length > 1 ? 's' : ''}`}
        />
        <CardContent>
          {alertsQuery.isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-12">
              <div className="p-4 rounded-full bg-emerald-500/10 w-fit mx-auto mb-4">
                <BellOff className="w-8 h-8 text-emerald-400" />
              </div>
              <p className="text-slate-400">Aucune alerte trouvée</p>
              <p className="text-xs text-slate-500 mt-1">
                {filters.severity || filters.acknowledged !== undefined
                  ? 'Essayez de modifier les filtres'
                  : 'Le système surveille vos fournisseurs en continu'}
              </p>
            </div>
          ) : (
            <AnimatePresence>
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <AlertCard
                    key={alert.alert_id}
                    alert={alert}
                    onAcknowledge={handleAcknowledge}
                    onViewSupplier={handleViewSupplier}
                  />
                ))}
              </div>
            </AnimatePresence>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
