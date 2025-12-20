/**
 * PageLayout - Layout wrapper unifié pour toutes les pages
 *
 * Applique le design system dark theme (2025 Next-Gen) de manière consistante.
 * Utilise les mêmes patterns que newCMS pour l'uniformité.
 */

import { motion } from 'framer-motion';
import clsx from 'clsx';

/**
 * Header de page avec icône, titre, description et actions
 */
export function PageHeader({
  icon: Icon,
  title,
  description,
  actions = [],
  badge,
  className,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'rounded-2xl border border-white/10 bg-gradient-to-br from-slate-800/50 to-slate-900/50 px-6 py-5',
        className
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          {Icon && (
            <div className="rounded-xl bg-white/5 p-3 border border-white/10">
              <Icon className="h-6 w-6 text-white" />
            </div>
          )}
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">{title}</h1>
              {badge && (
                <span className={clsx(
                  'px-2.5 py-0.5 rounded-full text-xs font-medium',
                  badge.variant === 'success' && 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
                  badge.variant === 'warning' && 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
                  badge.variant === 'error' && 'bg-rose-500/20 text-rose-400 border border-rose-500/30',
                  badge.variant === 'info' && 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
                  (!badge.variant || badge.variant === 'default') && 'bg-white/10 text-slate-300 border border-white/10'
                )}>
                  {badge.label}
                </span>
              )}
            </div>
            {description && (
              <p className="text-sm text-slate-400 mt-1">{description}</p>
            )}
          </div>
        </div>

        {actions.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            {actions.map((action, idx) => {
              const ActionIcon = action.icon;
              return (
                <button
                  key={action.label || idx}
                  onClick={action.onClick}
                  disabled={action.disabled}
                  className={clsx(
                    'flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-150',
                    action.primary
                      ? 'bg-gradient-to-r from-blue-500 to-violet-500 text-white hover:from-blue-400 hover:to-violet-400 shadow-lg shadow-blue-500/25'
                      : action.danger
                        ? 'bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 border border-rose-500/30'
                        : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white border border-white/10',
                    action.disabled && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  {ActionIcon && <ActionIcon className="h-4 w-4" />}
                  {action.label}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </motion.div>
  );
}

/**
 * Section card avec titre optionnel
 */
export function PageSection({
  title,
  description,
  icon: Icon,
  actions = [],
  children,
  className,
  noPadding = false,
  variant = 'default', // 'default' | 'elevated' | 'transparent'
}) {
  const variantStyles = {
    default: 'bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10',
    elevated: 'bg-slate-800/80 border border-white/15 shadow-lg',
    transparent: 'bg-white/5 border border-white/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'rounded-2xl',
        variantStyles[variant],
        !noPadding && 'p-6',
        className
      )}
    >
      {(title || actions.length > 0) && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {Icon && <Icon className="h-5 w-5 text-slate-400" />}
            <div>
              {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
              {description && <p className="text-sm text-slate-400">{description}</p>}
            </div>
          </div>
          {actions.length > 0 && (
            <div className="flex items-center gap-2">
              {actions.map((action, idx) => {
                const ActionIcon = action.icon;
                return (
                  <button
                    key={action.label || idx}
                    onClick={action.onClick}
                    className={clsx(
                      'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all',
                      action.primary
                        ? 'bg-blue-500 text-white hover:bg-blue-400'
                        : 'bg-white/5 text-slate-300 hover:bg-white/10'
                    )}
                  >
                    {ActionIcon && <ActionIcon className="h-3.5 w-3.5" />}
                    {action.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
      {children}
    </motion.div>
  );
}

/**
 * Grid layout pour KPIs/stats
 */
export function StatsGrid({ children, columns = 4, className }) {
  return (
    <div
      className={clsx(
        'grid gap-4',
        columns === 2 && 'grid-cols-1 sm:grid-cols-2',
        columns === 3 && 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
        columns === 4 && 'grid-cols-2 sm:grid-cols-2 lg:grid-cols-4',
        columns === 5 && 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5',
        className
      )}
    >
      {children}
    </div>
  );
}

/**
 * Stat card individuel
 */
export function StatCard({
  label,
  value,
  unit,
  trend,
  trendLabel,
  icon: Icon,
  status, // 'success' | 'warning' | 'error' | 'info' | 'neutral'
  onClick,
  className,
}) {
  const statusStyles = {
    success: 'border-emerald-500/30 bg-emerald-500/5',
    warning: 'border-amber-500/30 bg-amber-500/5',
    error: 'border-rose-500/30 bg-rose-500/5',
    info: 'border-blue-500/30 bg-blue-500/5',
    neutral: 'border-white/10 bg-white/5',
  };

  const trendColor = trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-rose-400' : 'text-slate-400';

  return (
    <motion.div
      whileHover={onClick ? { scale: 1.02, y: -2 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      onClick={onClick}
      className={clsx(
        'relative p-4 rounded-xl border transition-all duration-200',
        statusStyles[status || 'neutral'],
        onClick && 'cursor-pointer hover:border-white/20',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
            {label}
          </p>
          <p className="text-2xl font-bold text-white">
            {value}
            {unit && <span className="text-lg font-normal text-slate-400 ml-1">{unit}</span>}
          </p>
          {(trend !== null && trend !== undefined) && (
            <div className={clsx('flex items-center gap-1 mt-2', trendColor)}>
              <span className="text-xs font-medium">
                {trend > 0 ? '+' : ''}{typeof trend === 'number' ? trend.toFixed(1) : trend}%
              </span>
              {trendLabel && <span className="text-xs text-slate-500">{trendLabel}</span>}
            </div>
          )}
        </div>
        {Icon && (
          <div className="p-2 rounded-lg bg-white/5">
            <Icon className="h-5 w-5 text-slate-400" />
          </div>
        )}
      </div>
    </motion.div>
  );
}

/**
 * Empty state component
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}) {
  return (
    <div className={clsx('text-center py-12', className)}>
      {Icon && (
        <div className="mx-auto w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
          <Icon className="h-8 w-8 text-slate-500" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      {description && <p className="text-sm text-slate-400 mb-4 max-w-md mx-auto">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500 text-white text-sm font-medium hover:bg-blue-400 transition-colors"
        >
          {action.icon && <action.icon className="h-4 w-4" />}
          {action.label}
        </button>
      )}
    </div>
  );
}

/**
 * Loading skeleton pour les pages
 */
export function PageSkeleton({ rows = 3 }) {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="h-24 bg-slate-800/50 rounded-2xl" />

      {/* Stats grid skeleton */}
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-slate-800/50 rounded-xl" />
        ))}
      </div>

      {/* Content skeleton */}
      {[...Array(rows)].map((_, i) => (
        <div key={i} className="h-48 bg-slate-800/50 rounded-2xl" />
      ))}
    </div>
  );
}

/**
 * Main page layout wrapper
 */
export default function PageLayout({ children, className }) {
  return (
    <div className={clsx('min-h-screen p-6 space-y-6', className)}>
      <div className="max-w-7xl mx-auto space-y-6">
        {children}
      </div>
    </div>
  );
}

// Re-export tout pour faciliter les imports
export { default } from './PageLayout.jsx';
