import { useState } from 'react';
import clsx from 'clsx';
import { ChevronDown, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { MetricCardSkeleton } from './Skeleton.jsx';

/**
 * MetricCard - Carte de métrique avec états loading, trend, onClick et expansion
 */
export default function MetricCard({
  label,
  value,
  hint,
  trend,
  trendLabel,
  loading = false,
  onClick,
  expandable = false,
  expandedContent,
  icon: Icon,
  status,
  className,
}) {
  const [expanded, setExpanded] = useState(false);

  // Afficher le skeleton si loading
  if (loading) {
    return <MetricCardSkeleton className={className} />;
  }

  // Déterminer la direction du trend
  const getTrendDirection = () => {
    if (!trend) return null;
    const numericTrend = typeof trend === 'string' ? parseFloat(trend) : trend;
    if (numericTrend > 0) return 'up';
    if (numericTrend < 0) return 'down';
    return 'neutral';
  };

  const trendDirection = getTrendDirection();

  const trendStyles = {
    up: 'bg-emerald-50 text-emerald-600',
    down: 'bg-rose-50 text-rose-600',
    neutral: 'bg-slate-100 text-slate-600',
  };

  const TrendIcon = {
    up: TrendingUp,
    down: TrendingDown,
    neutral: Minus,
  }[trendDirection];

  // Classes de statut optionnel
  const statusStyles = {
    success: 'border-l-4 border-l-emerald-500',
    warning: 'border-l-4 border-l-amber-500',
    error: 'border-l-4 border-l-rose-500',
    info: 'border-l-4 border-l-sky-500',
  };

  const isInteractive = onClick || expandable;

  const handleClick = () => {
    if (expandable) {
      setExpanded(!expanded);
    }
    onClick?.();
  };

  return (
    <div
      className={clsx(
        'metric group',
        status && statusStyles[status],
        isInteractive && 'cursor-pointer hover:shadow-md hover:border-slate-200 transition-all',
        className
      )}
      onClick={isInteractive ? handleClick : undefined}
      onKeyDown={isInteractive ? (e) => e.key === 'Enter' && handleClick() : undefined}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      aria-expanded={expandable ? expanded : undefined}
    >
      <div className="flex items-start justify-between">
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
          {label}
        </p>
        {Icon && (
          <div className="rounded-lg bg-slate-100 p-1.5 text-slate-500">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </div>
        )}
        {expandable && (
          <ChevronDown
            className={clsx(
              'h-4 w-4 text-slate-400 transition-transform',
              expanded && 'rotate-180'
            )}
            aria-hidden="true"
          />
        )}
      </div>

      <div className="flex items-end gap-3 mt-1">
        <p className="text-3xl font-semibold text-slate-900">{value}</p>
        {trend !== undefined && trend !== null && (
          <span
            className={clsx(
              'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold',
              trendStyles[trendDirection]
            )}
          >
            {TrendIcon && <TrendIcon className="h-3 w-3" aria-hidden="true" />}
            {typeof trend === 'number' ? `${trend > 0 ? '+' : ''}${trend}%` : trend}
          </span>
        )}
      </div>

      {(hint || trendLabel) && (
        <div className="flex items-center justify-between mt-1">
          {hint && <p className="text-sm text-slate-500">{hint}</p>}
          {trendLabel && (
            <p className="text-xs text-slate-400">{trendLabel}</p>
          )}
        </div>
      )}

      {/* Contenu expansible */}
      {expandable && expanded && expandedContent && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          {expandedContent}
        </div>
      )}
    </div>
  );
}

/**
 * MetricCardGroup - Groupe de MetricCards avec layout responsive
 */
export function MetricCardGroup({ children, columns = 4, className }) {
  const colClasses = {
    2: 'md:grid-cols-2',
    3: 'md:grid-cols-3',
    4: 'md:grid-cols-2 xl:grid-cols-4',
    5: 'md:grid-cols-3 xl:grid-cols-5',
  };

  return (
    <div className={clsx('grid gap-4', colClasses[columns], className)}>
      {children}
    </div>
  );
}

/**
 * CompactMetricCard - Version compacte pour les sidebars ou listes
 */
export function CompactMetricCard({ label, value, trend, className }) {
  const trendDirection = trend && (parseFloat(trend) > 0 ? 'up' : parseFloat(trend) < 0 ? 'down' : 'neutral');

  return (
    <div className={clsx('flex items-center justify-between py-2', className)}>
      <span className="text-sm text-slate-600">{label}</span>
      <div className="flex items-center gap-2">
        <span className="font-semibold text-slate-900">{value}</span>
        {trend && (
          <span
            className={clsx(
              'text-xs font-medium',
              trendDirection === 'up' && 'text-emerald-600',
              trendDirection === 'down' && 'text-rose-600',
              trendDirection === 'neutral' && 'text-slate-500'
            )}
          >
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}
