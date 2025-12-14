/**
 * StatCard - Carte de statistique avec animation et tendance
 * Design Next-Gen 2025
 */

import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import clsx from 'clsx';

export default function StatCard({
  label,
  value,
  previousValue,
  trend,
  trendLabel,
  icon: Icon,
  color = 'blue', // 'blue', 'emerald', 'amber', 'rose', 'violet'
  size = 'md', // 'sm', 'md', 'lg'
  onClick,
  className,
}) {
  // Calcul automatique du trend si previousValue fourni
  const calculatedTrend = trend ?? (previousValue && previousValue !== 0
    ? ((value - previousValue) / Math.abs(previousValue)) * 100
    : null);

  const isPositive = calculatedTrend > 0;
  const isNegative = calculatedTrend < 0;
  const TrendIcon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;

  const colorClasses = {
    blue: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/20',
      icon: 'text-blue-400',
      glow: 'rgba(59, 130, 246, 0.3)',
    },
    emerald: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      icon: 'text-emerald-400',
      glow: 'rgba(16, 185, 129, 0.3)',
    },
    amber: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      icon: 'text-amber-400',
      glow: 'rgba(245, 158, 11, 0.3)',
    },
    rose: {
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20',
      icon: 'text-rose-400',
      glow: 'rgba(244, 63, 94, 0.3)',
    },
    violet: {
      bg: 'bg-violet-500/10',
      border: 'border-violet-500/20',
      icon: 'text-violet-400',
      glow: 'rgba(139, 92, 246, 0.3)',
    },
  };

  const sizeClasses = {
    sm: {
      padding: 'p-3',
      label: 'text-[10px]',
      value: 'text-lg',
      icon: 'w-4 h-4',
      iconWrapper: 'p-1.5',
    },
    md: {
      padding: 'p-4',
      label: 'text-xs',
      value: 'text-2xl',
      icon: 'w-5 h-5',
      iconWrapper: 'p-2',
    },
    lg: {
      padding: 'p-6',
      label: 'text-sm',
      value: 'text-3xl',
      icon: 'w-6 h-6',
      iconWrapper: 'p-3',
    },
  };

  const colors = colorClasses[color];
  const sizes = sizeClasses[size];

  return (
    <motion.div
      onClick={onClick}
      className={clsx(
        'relative rounded-xl border overflow-hidden',
        'backdrop-blur-sm',
        colors.bg,
        colors.border,
        sizes.padding,
        onClick && 'cursor-pointer',
        className
      )}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={onClick ? {
        scale: 1.02,
        boxShadow: `0 0 30px -5px ${colors.glow}`,
      } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className={clsx(
            'uppercase tracking-wider text-slate-400 mb-1',
            sizes.label
          )}>
            {label}
          </p>
          <p className={clsx('font-bold text-white', sizes.value)}>
            {value}
          </p>

          {/* Trend indicator */}
          {calculatedTrend !== null && (
            <div className={clsx(
              'flex items-center gap-1 mt-2',
              isPositive ? 'text-emerald-400' : isNegative ? 'text-rose-400' : 'text-slate-400'
            )}>
              <TrendIcon className="w-3 h-3" />
              <span className="text-xs font-medium">
                {isPositive ? '+' : ''}{calculatedTrend.toFixed(1)}%
              </span>
              {trendLabel && (
                <span className="text-xs text-slate-500 ml-1">{trendLabel}</span>
              )}
            </div>
          )}
        </div>

        {Icon && (
          <div className={clsx(
            'rounded-lg',
            colors.bg,
            sizes.iconWrapper
          )}>
            <Icon className={clsx(sizes.icon, colors.icon)} />
          </div>
        )}
      </div>
    </motion.div>
  );
}

/**
 * StatCardGrid - Grille de StatCards
 */
export function StatCardGrid({ children, columns = 4, className }) {
  return (
    <div className={clsx(
      'grid gap-4',
      columns === 2 && 'grid-cols-1 sm:grid-cols-2',
      columns === 3 && 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
      columns === 4 && 'grid-cols-2 sm:grid-cols-2 lg:grid-cols-4',
      columns === 5 && 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5',
      columns === 6 && 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6',
      className
    )}>
      {children}
    </div>
  );
}

/**
 * MiniStat - Version mini inline
 */
export function MiniStat({ label, value, trend, color = 'blue' }) {
  const colorClasses = {
    blue: 'text-blue-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    rose: 'text-rose-400',
    violet: 'text-violet-400',
  };

  return (
    <div className="flex items-center gap-3">
      <div>
        <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
        <p className={clsx('text-lg font-bold', colorClasses[color])}>{value}</p>
      </div>
      {trend !== undefined && (
        <span className={clsx(
          'text-xs font-medium',
          trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-rose-400' : 'text-slate-400'
        )}>
          {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
        </span>
      )}
    </div>
  );
}
