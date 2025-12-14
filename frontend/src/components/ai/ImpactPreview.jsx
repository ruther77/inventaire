import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, ArrowRight } from 'lucide-react';
import clsx from 'clsx';

/**
 * ImpactPreview - Prévisualisation de l'impact d'une action
 */
export default function ImpactPreview({
  before,
  after,
  label,
  unit = '€',
  trend, // 'up', 'down', 'neutral'
  period,
  className,
}) {
  const diff = after - before;
  const percentChange = before !== 0 ? ((after - before) / Math.abs(before)) * 100 : 0;
  const isPositive = diff > 0;
  const isNeutral = diff === 0;

  const TrendIcon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;
  const trendColor = isNeutral
    ? 'text-slate-400'
    : isPositive
      ? 'text-emerald-400'
      : 'text-rose-400';

  return (
    <div className={clsx('p-4 rounded-xl bg-white/5 border border-white/10', className)}>
      {label && (
        <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider">{label}</p>
      )}

      <div className="flex items-center justify-between gap-4">
        {/* Avant */}
        <div className="text-center">
          <p className="text-[11px] text-slate-500 mb-1">Avant</p>
          <p className="text-lg font-mono text-slate-400">
            {typeof before === 'number' ? before.toLocaleString('fr-FR') : before}
            {unit && <span className="text-sm ml-0.5">{unit}</span>}
          </p>
        </div>

        {/* Flèche */}
        <div className="flex flex-col items-center">
          <ArrowRight className="w-5 h-5 text-slate-600" />
        </div>

        {/* Après */}
        <div className="text-center">
          <p className="text-[11px] text-slate-500 mb-1">Après</p>
          <p className="text-lg font-mono text-white font-semibold">
            {typeof after === 'number' ? after.toLocaleString('fr-FR') : after}
            {unit && <span className="text-sm ml-0.5">{unit}</span>}
          </p>
        </div>

        {/* Différence */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={clsx(
            'flex flex-col items-center p-2 rounded-lg',
            isNeutral ? 'bg-slate-500/10' : isPositive ? 'bg-emerald-500/10' : 'bg-rose-500/10'
          )}
        >
          <TrendIcon className={clsx('w-4 h-4 mb-1', trendColor)} />
          <p className={clsx('text-sm font-bold font-mono', trendColor)}>
            {isPositive ? '+' : ''}{diff.toLocaleString('fr-FR')}{unit}
          </p>
          <p className={clsx('text-[10px]', trendColor)}>
            {isPositive ? '+' : ''}{percentChange.toFixed(1)}%
          </p>
        </motion.div>
      </div>

      {period && (
        <p className="text-center text-[11px] text-slate-500 mt-3">{period}</p>
      )}
    </div>
  );
}

/**
 * ImpactGrid - Grille de plusieurs impacts
 */
export function ImpactGrid({ impacts, className }) {
  return (
    <div className={clsx('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4', className)}>
      {impacts.map((impact, index) => (
        <motion.div
          key={impact.id || index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <ImpactPreview {...impact} />
        </motion.div>
      ))}
    </div>
  );
}

/**
 * MiniImpact - Version compacte pour les listes
 */
export function MiniImpact({ value, unit = '€', isPositive = true, className }) {
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;
  const color = isPositive ? 'text-emerald-400' : 'text-rose-400';

  return (
    <span className={clsx('inline-flex items-center gap-1 font-mono text-sm', color, className)}>
      <TrendIcon className="w-3 h-3" />
      {isPositive ? '+' : ''}{value}{unit}
    </span>
  );
}
