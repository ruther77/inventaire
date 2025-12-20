/**
 * AnomalyList - Liste des anomalies détectées
 *
 * Composant du plan de restructuration 2025-12 pour l'Intelligence Module.
 * Affiche les anomalies avec filtres et actions.
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  XCircle,
  AlertCircle,
  Info,
  ChevronRight,
  CheckCircle,
  Eye,
  Filter,
  Clock,
} from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// UTILITIES
// ============================================================================

const SEVERITY_CONFIG = {
  critical: {
    color: 'rose',
    icon: XCircle,
    label: 'Critique',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
    text: 'text-rose-400',
  },
  high: {
    color: 'orange',
    icon: AlertTriangle,
    label: 'Élevé',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
  },
  medium: {
    color: 'amber',
    icon: AlertCircle,
    label: 'Moyen',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
  },
  low: {
    color: 'blue',
    icon: Info,
    label: 'Faible',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
  },
};

const ANOMALY_TYPES = {
  price_spike: 'Pic de prix',
  duplicate_payment: 'Paiement dupliqué',
  unusual_amount: 'Montant inhabituel',
  missing_invoice: 'Facture manquante',
  stock_discrepancy: 'Écart de stock',
  margin_alert: 'Alerte marge',
  supplier_issue: 'Problème fournisseur',
};

const formatDate = (dateStr) => {
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

// ============================================================================
// ANOMALY ITEM COMPONENT
// ============================================================================

function AnomalyItem({ anomaly, onView, onResolve, expanded, onToggle }) {
  const config = SEVERITY_CONFIG[anomaly.severity] || SEVERITY_CONFIG.medium;
  const SeverityIcon = config.icon;
  const typeLabel = ANOMALY_TYPES[anomaly.anomaly_type] || anomaly.anomaly_type;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={clsx(
        'rounded-lg border overflow-hidden',
        config.bg,
        config.border,
        anomaly.resolved && 'opacity-60'
      )}
    >
      {/* Header (always visible) */}
      <div
        onClick={() => onToggle?.(anomaly.id)}
        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-white/5 transition-colors"
      >
        <div className={clsx('p-1.5 rounded-full', config.bg)}>
          <SeverityIcon className={clsx('w-4 h-4', config.text)} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={clsx('text-xs font-medium px-1.5 py-0.5 rounded', config.bg, config.text)}>
              {config.label}
            </span>
            <span className="text-xs text-slate-500">{typeLabel}</span>
          </div>
          <p className="text-sm font-medium text-white mt-1 truncate">
            {anomaly.title || anomaly.description}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {anomaly.resolved ? (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          ) : (
            <ChevronRight className={clsx(
              'w-4 h-4 text-slate-400 transition-transform',
              expanded && 'rotate-90'
            )} />
          )}
        </div>
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/10"
          >
            <div className="p-3 space-y-3">
              {/* Description */}
              {anomaly.description && (
                <p className="text-sm text-slate-300">{anomaly.description}</p>
              )}

              {/* Details */}
              {anomaly.details && (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {Object.entries(anomaly.details).map(([key, value]) => (
                    <div key={key} className="bg-white/5 rounded p-2">
                      <span className="text-slate-500">{key}:</span>
                      <span className="text-white ml-1">{String(value)}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Meta info */}
              <div className="flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDate(anomaly.detected_at || anomaly.created_at)}
                </div>

                {anomaly.confidence && (
                  <span>Confiance: {(anomaly.confidence * 100).toFixed(0)}%</span>
                )}
              </div>

              {/* Actions */}
              {!anomaly.resolved && (
                <div className="flex items-center gap-2 pt-2 border-t border-white/10">
                  <button
                    onClick={() => onView?.(anomaly)}
                    className="flex-1 flex items-center justify-center gap-1 py-2 text-xs text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 rounded transition-colors"
                  >
                    <Eye className="w-3 h-3" />
                    Détails
                  </button>
                  <button
                    onClick={() => onResolve?.(anomaly.id)}
                    className="flex-1 flex items-center justify-center gap-1 py-2 text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 rounded transition-colors"
                  >
                    <CheckCircle className="w-3 h-3" />
                    Résoudre
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ============================================================================
// ANOMALY LIST COMPONENT
// ============================================================================

export default function AnomalyList({
  anomalies = [],
  onView,
  onResolve,
  showFilters = true,
  maxVisible = 10,
  className,
}) {
  const [expandedId, setExpandedId] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [showResolved, setShowResolved] = useState(false);

  // Filtrer et trier les anomalies
  const filteredAnomalies = useMemo(() => {
    let filtered = anomalies;

    // Filtre par sévérité
    if (severityFilter !== 'all') {
      filtered = filtered.filter((a) => a.severity === severityFilter);
    }

    // Filtre resolved
    if (!showResolved) {
      filtered = filtered.filter((a) => !a.resolved);
    }

    // Trier par sévérité puis date
    filtered.sort((a, b) => {
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      const aSev = severityOrder[a.severity] ?? 4;
      const bSev = severityOrder[b.severity] ?? 4;
      if (aSev !== bSev) return aSev - bSev;
      return new Date(b.detected_at || b.created_at) - new Date(a.detected_at || a.created_at);
    });

    return filtered.slice(0, maxVisible);
  }, [anomalies, severityFilter, showResolved, maxVisible]);

  // Counts par sévérité
  const counts = useMemo(() => {
    const result = { all: 0, critical: 0, high: 0, medium: 0, low: 0 };
    anomalies.forEach((a) => {
      if (!a.resolved || showResolved) {
        result.all++;
        if (result[a.severity] !== undefined) {
          result[a.severity]++;
        }
      }
    });
    return result;
  }, [anomalies, showResolved]);

  const handleToggle = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className={clsx('p-4 rounded-2xl bg-slate-800/50 border border-white/10', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-white">Anomalies détectées</h3>
          <span className="text-sm text-slate-400">({counts.all})</span>
        </div>

        {showFilters && (
          <button
            onClick={() => setShowResolved((prev) => !prev)}
            className={clsx(
              'text-xs px-2 py-1 rounded transition-colors',
              showResolved ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'
            )}
          >
            {showResolved ? 'Masquer résolues' : 'Voir résolues'}
          </button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-1">
          {(['all', 'critical', 'high', 'medium', 'low']).map((severity) => {
            const config = severity === 'all' ? null : SEVERITY_CONFIG[severity];
            return (
              <button
                key={severity}
                onClick={() => setSeverityFilter(severity)}
                className={clsx(
                  'flex items-center gap-1 px-2 py-1 text-xs rounded whitespace-nowrap transition-colors',
                  severityFilter === severity
                    ? config
                      ? `${config.bg} ${config.text}`
                      : 'bg-white/10 text-white'
                    : 'text-slate-400 hover:text-white'
                )}
              >
                {severity === 'all' ? (
                  <>
                    <Filter className="w-3 h-3" />
                    Tous
                  </>
                ) : (
                  config && (
                    <>
                      <config.icon className="w-3 h-3" />
                      {config.label}
                    </>
                  )
                )}
                <span className="ml-1 opacity-70">({counts[severity]})</span>
              </button>
            );
          })}
        </div>
      )}

      {/* List */}
      {filteredAnomalies.length > 0 ? (
        <div className="space-y-2">
          <AnimatePresence mode="popLayout">
            {filteredAnomalies.map((anomaly) => (
              <AnomalyItem
                key={anomaly.id}
                anomaly={anomaly}
                expanded={expandedId === anomaly.id}
                onToggle={handleToggle}
                onView={onView}
                onResolve={onResolve}
              />
            ))}
          </AnimatePresence>
        </div>
      ) : (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
          <p className="text-sm text-slate-400">Aucune anomalie détectée</p>
          <p className="text-xs text-slate-500 mt-1">
            Le système surveille vos données en continu
          </p>
        </div>
      )}

      {/* More link */}
      {anomalies.length > maxVisible && (
        <button className="w-full mt-4 py-2 text-sm text-slate-400 hover:text-white flex items-center justify-center gap-1 transition-colors">
          Voir toutes les anomalies ({anomalies.length})
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// Export
export { AnomalyItem, SEVERITY_CONFIG, ANOMALY_TYPES };
