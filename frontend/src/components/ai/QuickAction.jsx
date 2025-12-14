import { motion } from 'framer-motion';
import clsx from 'clsx';

/**
 * QuickAction - Bouton d'action rapide avec icône et état de chargement
 */
export default function QuickAction({
  icon: Icon,
  label,
  onClick,
  variant = 'default',
  size = 'md',
  loading = false,
  disabled = false,
  badge,
  className,
}) {
  const variants = {
    default: 'bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border-white/10',
    primary: 'bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 hover:text-blue-300 border-blue-500/30',
    success: 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 hover:text-emerald-300 border-emerald-500/30',
    warning: 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 hover:text-amber-300 border-amber-500/30',
    danger: 'bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 hover:text-rose-300 border-rose-500/30',
  };

  const sizes = {
    sm: 'px-2 py-1 text-xs gap-1',
    md: 'px-3 py-1.5 text-sm gap-1.5',
    lg: 'px-4 py-2 text-base gap-2',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || loading}
      className={clsx(
        'relative inline-flex items-center justify-center rounded-lg border font-medium',
        'transition-all duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
    >
      {loading ? (
        <div className={clsx('animate-spin rounded-full border-2 border-current border-t-transparent', iconSizes[size])} />
      ) : Icon ? (
        <Icon className={iconSizes[size]} />
      ) : null}

      <span>{label}</span>

      {badge && (
        <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
          {badge}
        </span>
      )}
    </motion.button>
  );
}

/**
 * QuickActionGroup - Groupe de boutons d'action
 */
export function QuickActionGroup({ children, className }) {
  return (
    <div className={clsx('flex flex-wrap items-center gap-2', className)}>
      {children}
    </div>
  );
}
