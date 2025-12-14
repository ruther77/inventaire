import { motion } from 'framer-motion';
import clsx from 'clsx';

/**
 * ConfidenceBadge - Indicateur de confiance IA
 * Affiche le niveau de confiance avec une barre de progression et couleur
 */
export default function ConfidenceBadge({
  value,
  size = 'md',
  showLabel = true,
  showBar = true,
  className
}) {
  const percentage = Math.round(value * 100);

  // Déterminer le niveau et la couleur
  const getLevel = () => {
    if (percentage >= 90) return { level: 'high', color: 'emerald', label: 'Fiable' };
    if (percentage >= 70) return { level: 'medium', color: 'amber', label: 'À vérifier' };
    return { level: 'low', color: 'rose', label: 'Manuel' };
  };

  const { level, color, label } = getLevel();

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const barWidths = {
    sm: 'w-12',
    md: 'w-16',
    lg: 'w-20',
  };

  const colorClasses = {
    emerald: {
      bg: 'bg-emerald-500/20',
      text: 'text-emerald-400',
      bar: 'bg-emerald-500',
      glow: 'shadow-emerald-500/30',
    },
    amber: {
      bg: 'bg-amber-500/20',
      text: 'text-amber-400',
      bar: 'bg-amber-500',
      glow: 'shadow-amber-500/30',
    },
    rose: {
      bg: 'bg-rose-500/20',
      text: 'text-rose-400',
      bar: 'bg-rose-500',
      glow: 'shadow-rose-500/30',
    },
  };

  const colors = colorClasses[color];

  return (
    <div className={clsx('inline-flex items-center gap-2', className)}>
      {showBar && (
        <div className={clsx('h-1.5 rounded-full bg-white/10 overflow-hidden', barWidths[size])}>
          <motion.div
            className={clsx('h-full rounded-full', colors.bar)}
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      )}

      <span className={clsx(
        'inline-flex items-center gap-1 rounded-full font-medium',
        sizeClasses[size],
        colors.bg,
        colors.text
      )}>
        <span className="font-mono">{percentage}%</span>
        {showLabel && <span className="opacity-75">• {label}</span>}
      </span>
    </div>
  );
}
