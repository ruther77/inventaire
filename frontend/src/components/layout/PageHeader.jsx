/**
 * PageHeader - En-tête de page unifié avec gradient et actions
 * Design Next-Gen 2025
 */

import { motion } from 'framer-motion';
import clsx from 'clsx';

export default function PageHeader({
  title,
  subtitle,
  icon: Icon,
  gradient = 'from-blue-500 to-purple-600',
  actions,
  badge,
  stats,
  className,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'relative overflow-hidden rounded-2xl',
        'bg-gradient-to-br from-slate-800/80 to-slate-900/80',
        'border border-white/10',
        'p-6',
        className
      )}
    >
      {/* Background gradient effect */}
      <div
        className={clsx(
          'absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl opacity-20',
          `bg-gradient-to-br ${gradient}`
        )}
        style={{ transform: 'translate(30%, -50%)' }}
      />

      <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          {Icon && (
            <div className={clsx(
              'p-3 rounded-xl',
              `bg-gradient-to-br ${gradient}`
            )}>
              <Icon className="w-6 h-6 text-white" />
            </div>
          )}

          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white">{title}</h1>
              {badge && (
                <span className={clsx(
                  'px-2.5 py-1 rounded-full text-xs font-medium',
                  'bg-white/10 text-white/80'
                )}>
                  {badge}
                </span>
              )}
            </div>
            {subtitle && (
              <p className="text-sm text-slate-400 mt-1">{subtitle}</p>
            )}
          </div>
        </div>

        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>

      {/* Stats row */}
      {stats && stats.length > 0 && (
        <div className="relative mt-6 pt-6 border-t border-white/10">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-center sm:text-left"
              >
                <p className="text-xs text-slate-500 uppercase tracking-wider">
                  {stat.label}
                </p>
                <p className={clsx(
                  'text-xl font-bold mt-0.5',
                  stat.color || 'text-white'
                )}>
                  {stat.value}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
