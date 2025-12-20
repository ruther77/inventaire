/**
 * KPIStream - Flux de KPIs en temps réel
 *
 * Composant du plan de restructuration 2025-12 pour le Cockpit Central.
 * Affiche les métriques clés avec streaming temps réel via SSE.
 */

import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Euro,
  Package,
  ShoppingCart,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import clsx from 'clsx';

import { fetchCockpitLiveKPIs } from '../../../api/client.js';

// ============================================================================
// UTILITIES
// ============================================================================

const formatValue = (value, unit) => {
  if (value === null || value === undefined) return '—';

  if (unit === '€' || unit === 'EUR') {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);
  }

  if (unit === '%') {
    return `${value.toFixed(1)}%`;
  }

  if (typeof value === 'number' && value >= 1000) {
    return new Intl.NumberFormat('fr-FR').format(value);
  }

  return value;
};

const getTrendIcon = (trend) => {
  if (trend > 0) return TrendingUp;
  if (trend < 0) return TrendingDown;
  return Minus;
};

const getTrendColor = (trend, inverse = false) => {
  const positive = inverse ? trend < 0 : trend > 0;
  const negative = inverse ? trend > 0 : trend < 0;

  if (positive) return 'text-emerald-400';
  if (negative) return 'text-rose-400';
  return 'text-slate-400';
};

const getStatusColors = (status) => {
  const colors = {
    success: 'border-emerald-500/30 bg-emerald-500/5',
    warning: 'border-amber-500/30 bg-amber-500/5',
    error: 'border-rose-500/30 bg-rose-500/5',
    info: 'border-blue-500/30 bg-blue-500/5',
    neutral: 'border-white/10 bg-white/5',
  };
  return colors[status] || colors.neutral;
};

const getKPIIcon = (label) => {
  const lower = (label || '').toLowerCase();
  if (lower.includes('ca') || lower.includes('revenu') || lower.includes('chiffre')) return Euro;
  if (lower.includes('stock') || lower.includes('rupture')) return Package;
  if (lower.includes('commande') || lower.includes('vente')) return ShoppingCart;
  if (lower.includes('alerte') || lower.includes('critique')) return AlertTriangle;
  return TrendingUp;
};

// ============================================================================
// KPI CARD COMPONENT
// ============================================================================

function KPICard({ kpi, onClick, animate = true }) {
  const {
    label,
    value,
    unit,
    trend,
    trend_direction,
    status = 'neutral',
    description,
  } = kpi;

  const TrendIcon = getTrendIcon(trend);
  const KPIIcon = getKPIIcon(label);
  const trendColor = getTrendColor(trend);
  const statusColors = getStatusColors(status);

  const displayValue = formatValue(value, unit);

  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 10 } : false}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={clsx(
        'relative p-4 rounded-xl border cursor-pointer',
        'transition-all duration-200',
        statusColors
      )}
    >
      {/* Icon */}
      <div className="flex items-center gap-2 mb-2">
        <KPIIcon className="w-4 h-4 text-slate-400" />
        <p className="text-xs text-slate-500 truncate">{label}</p>
      </div>

      {/* Value */}
      <p className="text-2xl font-bold text-white">{displayValue}</p>

      {/* Trend */}
      {trend !== null && trend !== undefined && (
        <div className={clsx('flex items-center gap-1 mt-2', trendColor)}>
          <TrendIcon className="w-3 h-3" />
          <span className="text-xs font-medium">
            {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
          </span>
          {trend_direction && (
            <span className="text-xs text-slate-500 ml-1">
              vs semaine préc.
            </span>
          )}
        </div>
      )}

      {/* Description tooltip */}
      {description && (
        <p className="text-xs text-slate-500 mt-1 truncate" title={description}>
          {description}
        </p>
      )}
    </motion.div>
  );
}

// ============================================================================
// KPISTREAM COMPONENT
// ============================================================================

export default function KPIStream({
  kpis: initialKpis,
  refreshInterval = 60000,
  maxVisible = 6,
  onKPIClick,
  className,
}) {
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Requête live KPIs si pas de données initiales
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['cockpit-live-kpis'],
    queryFn: fetchCockpitLiveKPIs,
    enabled: !initialKpis,
    staleTime: refreshInterval / 2,
    refetchInterval: refreshInterval,
    onSuccess: () => setLastUpdate(new Date()),
  });

  // Utiliser les KPIs initiaux ou ceux de la requête
  const kpis = useMemo(() => {
    const source = initialKpis || data?.kpis || [];
    return source.slice(0, maxVisible);
  }, [initialKpis, data, maxVisible]);

  if (error && !initialKpis) {
    return (
      <div className={clsx('p-4 rounded-xl bg-rose-500/10 border border-rose-500/20', className)}>
        <p className="text-sm text-rose-400">Erreur de chargement des KPIs</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1"
        >
          <RefreshCw className="w-3 h-3" />
          Réessayer
        </button>
      </div>
    );
  }

  if (isLoading && !initialKpis) {
    return (
      <div className={clsx('grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3', className)}>
        {[...Array(maxVisible)].map((_, i) => (
          <div key={i} className="h-24 bg-slate-800/50 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header avec dernière mise à jour */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-slate-500">
          Dernière mise à jour: {lastUpdate.toLocaleTimeString('fr-FR')}
        </p>
        <button
          onClick={() => refetch?.()}
          className="text-xs text-slate-400 hover:text-slate-300 flex items-center gap-1"
        >
          <RefreshCw className="w-3 h-3" />
          Actualiser
        </button>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <AnimatePresence mode="popLayout">
          {kpis.map((kpi, index) => (
            <KPICard
              key={kpi.label || index}
              kpi={kpi}
              onClick={() => onKPIClick?.(kpi)}
              animate
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

// Export named pour utilisation spécifique
export { KPICard };
