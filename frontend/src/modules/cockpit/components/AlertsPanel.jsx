/**
 * AlertsPanel - Panneau d'alertes critiques
 *
 * Composant du plan de restructuration 2025-12 pour le Cockpit Central.
 * Affiche les alertes actives avec actions rapides.
 */

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Bell,
  BellOff,
  ChevronRight,
  Eye,
  Package,
  Wallet,
  BarChart3,
  Zap,
} from 'lucide-react';
import clsx from 'clsx';

import { fetchCockpitAlerts, acknowledgeCockpitAlert } from '../../../api/client.js';

// ============================================================================
// UTILITIES
// ============================================================================

const getSeverityConfig = (severity) => {
  const configs = {
    critical: {
      color: 'rose',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/30',
      text: 'text-rose-400',
      icon: XCircle,
      label: 'Critique',
    },
    warning: {
      color: 'amber',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      text: 'text-amber-400',
      icon: AlertTriangle,
      label: 'Attention',
    },
    info: {
      color: 'blue',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      icon: Bell,
      label: 'Info',
    },
  };
  return configs[severity] || configs.info;
};

const getCategoryIcon = (category) => {
  const icons = {
    stock: Package,
    finance: Wallet,
    margin: BarChart3,
    anomaly: AlertTriangle,
  };
  return icons[category] || AlertTriangle;
};

const getCategoryPath = (category, entityType, entityId) => {
  const paths = {
    stock: '/operations/catalogue',
    finance: '/finances/tresorerie',
    margin: '/intelligence/marges',
    anomaly: '/intelligence/anomalies',
  };
  return paths[category] || '/';
};

// ============================================================================
// ALERT ITEM COMPONENT
// ============================================================================

function AlertItem({ alert, onAcknowledge, onView }) {
  const config = getSeverityConfig(alert.severity);
  const CategoryIcon = getCategoryIcon(alert.category);
  const SeverityIcon = config.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={clsx(
        'p-3 rounded-lg border',
        config.bg,
        config.border
      )}
    >
      <div className="flex items-start gap-3">
        {/* Severity Icon */}
        <div className={clsx('p-1.5 rounded-full', config.bg)}>
          <SeverityIcon className={clsx('w-4 h-4', config.text)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <CategoryIcon className="w-3 h-3 text-slate-400" />
            <span className="text-xs text-slate-500 uppercase tracking-wide">
              {alert.category}
            </span>
            <span className={clsx('text-xs px-1.5 py-0.5 rounded', config.bg, config.text)}>
              {config.label}
            </span>
          </div>

          <p className="text-sm font-medium text-white mt-1 truncate">
            {alert.title}
          </p>

          {alert.message && (
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
              {alert.message}
            </p>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => onView?.(alert)}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <Eye className="w-3 h-3" />
              Détails
            </button>

            {!alert.acknowledged && (
              <button
                onClick={() => onAcknowledge?.(alert.id)}
                className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
              >
                <CheckCircle className="w-3 h-3" />
                Traiter
              </button>
            )}
          </div>
        </div>

        {/* Time */}
        <div className="text-xs text-slate-500 whitespace-nowrap">
          {new Date(alert.created_at).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </motion.div>
  );
}

// ============================================================================
// ALERTS PANEL COMPONENT
// ============================================================================

export default function AlertsPanel({
  alerts: initialAlerts,
  maxVisible = 5,
  showViewAll = true,
  onViewAll,
  className,
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState('all'); // all, critical, warning

  // Requête alertes si pas de données initiales
  const { data, isLoading } = useQuery({
    queryKey: ['cockpit-alerts'],
    queryFn: () => fetchCockpitAlerts({}),
    enabled: !initialAlerts,
    staleTime: 30000,
    refetchInterval: 30000,
  });

  // Mutation pour acquitter une alerte
  const acknowledgeMutation = useMutation({
    mutationFn: acknowledgeCockpitAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cockpit-alerts'] });
      queryClient.invalidateQueries({ queryKey: ['cockpit-overview'] });
    },
  });

  // Utiliser les alertes initiales ou celles de la requête
  const alerts = useMemo(() => {
    const source = initialAlerts || data?.items || data || [];

    // Filtrer par sévérité
    let filtered = source;
    if (filter === 'critical') {
      filtered = source.filter((a) => a.severity === 'critical');
    } else if (filter === 'warning') {
      filtered = source.filter((a) => a.severity === 'warning');
    }

    // Trier par sévérité puis par date
    filtered.sort((a, b) => {
      const severityOrder = { critical: 0, warning: 1, info: 2 };
      const aSev = severityOrder[a.severity] ?? 3;
      const bSev = severityOrder[b.severity] ?? 3;
      if (aSev !== bSev) return aSev - bSev;
      return new Date(b.created_at) - new Date(a.created_at);
    });

    return filtered.slice(0, maxVisible);
  }, [initialAlerts, data, filter, maxVisible]);

  const criticalCount = useMemo(() => {
    const source = initialAlerts || data?.items || data || [];
    return source.filter((a) => a.severity === 'critical').length;
  }, [initialAlerts, data]);

  const totalCount = useMemo(() => {
    const source = initialAlerts || data?.items || data || [];
    return source.length;
  }, [initialAlerts, data]);

  const handleView = (alert) => {
    const path = alert.action_url || getCategoryPath(alert.category);
    navigate(path);
  };

  const handleAcknowledge = (alertId) => {
    if (!acknowledgeMutation.isPending) {
      acknowledgeMutation.mutate(alertId);
    }
  };

  if (isLoading && !initialAlerts) {
    return (
      <div className={clsx('p-4 rounded-2xl bg-slate-800/50 animate-pulse', className)}>
        <div className="h-8 bg-slate-700/50 rounded mb-4 w-1/3" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-slate-700/50 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={clsx(
      'p-4 rounded-2xl',
      'bg-gradient-to-br from-slate-800/50 to-slate-900/50',
      'border border-white/10',
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {totalCount > 0 ? (
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          ) : (
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          )}
          <h3 className="font-semibold text-white">
            {totalCount > 0 ? 'Alertes actives' : 'Tout est en ordre'}
          </h3>
          {totalCount > 0 && (
            <span className="text-sm text-slate-400">({totalCount})</span>
          )}
          {criticalCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-rose-500/20 text-rose-400">
              {criticalCount} critique{criticalCount > 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Filtres */}
        {totalCount > 0 && (
          <div className="flex items-center gap-1">
            {['all', 'critical', 'warning'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={clsx(
                  'px-2 py-1 text-xs rounded transition-colors',
                  filter === f
                    ? 'bg-white/10 text-white'
                    : 'text-slate-400 hover:text-white'
                )}
              >
                {f === 'all' ? 'Tous' : f === 'critical' ? 'Critiques' : 'Attention'}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Alerts List */}
      {alerts.length > 0 ? (
        <div className="space-y-2">
          <AnimatePresence mode="popLayout">
            {alerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                onView={handleView}
                onAcknowledge={handleAcknowledge}
              />
            ))}
          </AnimatePresence>
        </div>
      ) : (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
          <p className="text-sm text-slate-400">Aucune alerte active</p>
          <p className="text-xs text-slate-500 mt-1">
            Le système surveille vos opérations en continu
          </p>
        </div>
      )}

      {/* View All Link */}
      {showViewAll && totalCount > maxVisible && (
        <button
          onClick={onViewAll || (() => navigate('/intelligence/anomalies'))}
          className="mt-4 w-full py-2 text-sm text-slate-400 hover:text-white flex items-center justify-center gap-1 transition-colors"
        >
          Voir toutes les alertes
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// Export named
export { AlertItem };
