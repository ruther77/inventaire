/**
 * HealthScore - Score de santé global du business
 *
 * Composant du plan de restructuration 2025-12 pour le Cockpit Central.
 * Affiche un score consolidé avec breakdown par domaine.
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Package,
  Wallet,
  TrendingUp,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// UTILITIES
// ============================================================================

const getHealthStatus = (score) => {
  if (score >= 80) return { status: 'healthy', label: 'Excellent', color: 'emerald' };
  if (score >= 60) return { status: 'good', label: 'Bon', color: 'blue' };
  if (score >= 40) return { status: 'warning', label: 'Attention', color: 'amber' };
  return { status: 'critical', label: 'Critique', color: 'rose' };
};

const getStatusIcon = (status) => {
  const icons = {
    healthy: CheckCircle,
    good: CheckCircle,
    warning: AlertTriangle,
    critical: XCircle,
  };
  return icons[status] || Activity;
};

const getDomainIcon = (domain) => {
  const icons = {
    stock: Package,
    finance: Wallet,
    margins: TrendingUp,
    suppliers: Users,
  };
  return icons[domain] || Activity;
};

const getDomainLabel = (domain) => {
  const labels = {
    stock: 'Stock',
    finance: 'Trésorerie',
    margins: 'Marges',
    suppliers: 'Fournisseurs',
  };
  return labels[domain] || domain;
};

// ============================================================================
// GAUGE COMPONENT
// ============================================================================

function HealthGauge({ score, size = 'lg', showLabel = true }) {
  const { status, label, color } = getHealthStatus(score);
  const StatusIcon = getStatusIcon(status);

  const sizeConfig = {
    sm: { width: 80, stroke: 6, fontSize: 'text-lg' },
    md: { width: 120, stroke: 8, fontSize: 'text-2xl' },
    lg: { width: 160, stroke: 10, fontSize: 'text-4xl' },
  };

  const { width, stroke, fontSize } = sizeConfig[size];
  const radius = (width - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  const colorClasses = {
    emerald: { stroke: 'stroke-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-500/20' },
    blue: { stroke: 'stroke-blue-500', text: 'text-blue-400', bg: 'bg-blue-500/20' },
    amber: { stroke: 'stroke-amber-500', text: 'text-amber-400', bg: 'bg-amber-500/20' },
    rose: { stroke: 'stroke-rose-500', text: 'text-rose-400', bg: 'bg-rose-500/20' },
  };

  const colors = colorClasses[color] || colorClasses.blue;

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width, height: width }}>
        {/* Background circle */}
        <svg className="absolute inset-0" width={width} height={width}>
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            className="text-white/10"
          />
        </svg>

        {/* Progress circle */}
        <svg
          className="absolute inset-0 -rotate-90"
          width={width}
          height={width}
        >
          <motion.circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            strokeLinecap="round"
            className={colors.stroke}
            initial={{ strokeDasharray: `0 ${circumference}` }}
            animate={{ strokeDasharray: `${progress} ${circumference}` }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            className={clsx('font-bold', fontSize, 'text-white')}
          >
            {Math.round(score)}
          </motion.span>
          {showLabel && (
            <span className={clsx('text-xs font-medium', colors.text)}>
              {label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// DOMAIN METRIC COMPONENT
// ============================================================================

function DomainMetric({ domain, score, trend }) {
  const { color } = getHealthStatus(score);
  const Icon = getDomainIcon(domain);
  const label = getDomainLabel(domain);

  const colorClasses = {
    emerald: 'text-emerald-400',
    blue: 'text-blue-400',
    amber: 'text-amber-400',
    rose: 'text-rose-400',
  };

  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-slate-400" />
        <span className="text-sm text-slate-300">{label}</span>
      </div>

      <div className="flex items-center gap-2">
        <span className={clsx('text-sm font-medium', colorClasses[color])}>
          {Math.round(score)}%
        </span>

        {/* Mini progress bar */}
        <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${score}%` }}
            transition={{ duration: 0.5 }}
            className={clsx(
              'h-full rounded-full',
              color === 'emerald' && 'bg-emerald-500',
              color === 'blue' && 'bg-blue-500',
              color === 'amber' && 'bg-amber-500',
              color === 'rose' && 'bg-rose-500'
            )}
          />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// HEALTH SCORE PANEL COMPONENT
// ============================================================================

export default function HealthScorePanel({
  score = 0,
  breakdown = {},
  showBreakdown = true,
  title = 'Santé Business',
  className,
}) {
  const { status, label, color } = useMemo(() => getHealthStatus(score), [score]);

  // Default breakdown if not provided
  const domains = useMemo(() => {
    if (Object.keys(breakdown).length > 0) {
      return breakdown;
    }
    // Fallback: derive from overall score with some variation
    return {
      stock: score + Math.random() * 10 - 5,
      margins: score + Math.random() * 10 - 5,
      finance: score + Math.random() * 10 - 5,
      suppliers: score + Math.random() * 10 - 5,
    };
  }, [breakdown, score]);

  return (
    <div className={clsx(
      'p-4 rounded-2xl',
      'bg-gradient-to-br from-slate-800/50 to-slate-900/50',
      'border border-white/10',
      className
    )}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">{title}</h3>
      </div>

      {/* Gauge */}
      <div className="flex justify-center mb-6">
        <HealthGauge score={score} size="lg" />
      </div>

      {/* Breakdown */}
      {showBreakdown && (
        <div className="border-t border-white/10 pt-4">
          <p className="text-xs text-slate-500 mb-2">Par domaine</p>
          <div className="space-y-1">
            {Object.entries(domains).map(([domain, domainScore]) => (
              <DomainMetric
                key={domain}
                domain={domain}
                score={Math.max(0, Math.min(100, domainScore))}
              />
            ))}
          </div>
        </div>
      )}

      {/* Bottom summary */}
      <div className={clsx(
        'mt-4 p-3 rounded-lg',
        color === 'emerald' && 'bg-emerald-500/10',
        color === 'blue' && 'bg-blue-500/10',
        color === 'amber' && 'bg-amber-500/10',
        color === 'rose' && 'bg-rose-500/10'
      )}>
        <p className={clsx(
          'text-sm',
          color === 'emerald' && 'text-emerald-400',
          color === 'blue' && 'text-blue-400',
          color === 'amber' && 'text-amber-400',
          color === 'rose' && 'text-rose-400'
        )}>
          {status === 'healthy' && 'Votre activité est en excellente santé. Continuez ainsi !'}
          {status === 'good' && 'Bonne performance globale. Quelques optimisations possibles.'}
          {status === 'warning' && 'Attention requise sur certains indicateurs.'}
          {status === 'critical' && 'Actions urgentes nécessaires pour améliorer la situation.'}
        </p>
      </div>
    </div>
  );
}

// Export named components
export { HealthGauge, DomainMetric };
