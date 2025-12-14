/**
 * AIConfidenceBadge - Indicateur de confiance IA
 * Phase 4 - UX_NEXT_GEN_2025.md
 *
 * Affiche le niveau de confiance d'une prédiction/suggestion IA
 * avec visualisation progressive et explication contextuelle
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Info,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// CONFIDENCE BADGE
// ============================================================================

export default function AIConfidenceBadge({
  confidence, // 0-1
  label,
  showPercentage = true,
  showLabel = true,
  showTooltip = true,
  size = 'md', // sm, md, lg
  variant = 'default', // default, pill, compact, detailed
  explanation,
  factors, // [{ label: string, impact: 'positive' | 'negative' | 'neutral', weight: number }]
  className,
}) {
  const [showDetails, setShowDetails] = useState(false);

  // Normalize confidence to 0-1
  const normalizedConfidence = Math.min(1, Math.max(0, confidence));
  const percentage = Math.round(normalizedConfidence * 100);

  // Determine level
  const level = getConfidenceLevel(normalizedConfidence);

  // Size styles
  const sizeStyles = {
    sm: {
      badge: 'text-xs px-1.5 py-0.5 gap-1',
      icon: 'w-3 h-3',
      bar: 'h-1',
    },
    md: {
      badge: 'text-sm px-2 py-1 gap-1.5',
      icon: 'w-4 h-4',
      bar: 'h-1.5',
    },
    lg: {
      badge: 'text-base px-3 py-1.5 gap-2',
      icon: 'w-5 h-5',
      bar: 'h-2',
    },
  };

  const styles = sizeStyles[size] || sizeStyles.md;

  // Render based on variant
  if (variant === 'compact') {
    return (
      <span
        className={clsx(
          'inline-flex items-center gap-1 font-medium',
          level.textColor,
          className
        )}
        title={`Confiance IA: ${percentage}%`}
      >
        <Brain className={styles.icon} />
        {percentage}%
      </span>
    );
  }

  if (variant === 'pill') {
    return (
      <span
        className={clsx(
          'inline-flex items-center rounded-full font-medium',
          styles.badge,
          level.bgColor,
          level.textColor,
          className
        )}
      >
        <level.Icon className={styles.icon} />
        {showPercentage && <span>{percentage}%</span>}
        {showLabel && label && <span>{label}</span>}
      </span>
    );
  }

  if (variant === 'detailed') {
    return (
      <div className={clsx('space-y-2', className)}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={clsx('p-1.5 rounded-lg', level.bgColor)}>
              <Brain className={clsx('w-4 h-4', level.textColor)} />
            </div>
            <div>
              <span className="text-sm font-medium text-slate-900">
                Confiance IA
              </span>
              {label && (
                <span className="text-xs text-slate-500 ml-2">{label}</span>
              )}
            </div>
          </div>
          <span className={clsx('text-lg font-bold', level.textColor)}>
            {percentage}%
          </span>
        </div>

        {/* Progress bar */}
        <div className={clsx('rounded-full bg-slate-200 overflow-hidden', styles.bar)}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={clsx('h-full rounded-full', level.barColor)}
          />
        </div>

        {/* Level label */}
        <div className="flex items-center justify-between text-xs">
          <span className={level.textColor}>{level.label}</span>
          {explanation && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-slate-500 hover:text-slate-700 flex items-center gap-1"
            >
              <Info className="w-3 h-3" />
              Détails
            </button>
          )}
        </div>

        {/* Explanation */}
        <AnimatePresence>
          {showDetails && (explanation || factors) && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-2 border-t border-slate-100 space-y-2">
                {explanation && (
                  <p className="text-xs text-slate-600">{explanation}</p>
                )}
                {factors && factors.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-slate-700">
                      Facteurs de confiance:
                    </p>
                    {factors.map((factor, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-xs"
                      >
                        {factor.impact === 'positive' ? (
                          <TrendingUp className="w-3 h-3 text-emerald-500" />
                        ) : factor.impact === 'negative' ? (
                          <TrendingDown className="w-3 h-3 text-red-500" />
                        ) : (
                          <Minus className="w-3 h-3 text-slate-400" />
                        )}
                        <span className="text-slate-600">{factor.label}</span>
                        {factor.weight && (
                          <span className="text-slate-400 ml-auto">
                            {Math.round(factor.weight * 100)}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // Default variant
  return (
    <div
      className={clsx(
        'relative inline-flex items-center',
        className
      )}
      onMouseEnter={() => showTooltip && setShowDetails(true)}
      onMouseLeave={() => showTooltip && setShowDetails(false)}
    >
      <span
        className={clsx(
          'inline-flex items-center rounded-lg font-medium',
          styles.badge,
          level.bgColor,
          level.textColor
        )}
      >
        <level.Icon className={styles.icon} />
        {showPercentage && <span>{percentage}%</span>}
        {showLabel && label && <span className="ml-1">{label}</span>}
      </span>

      {/* Tooltip */}
      <AnimatePresence>
        {showDetails && showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50"
          >
            <div className="bg-slate-900 text-white text-xs rounded-lg px-3 py-2 max-w-xs shadow-lg">
              <div className="font-medium mb-1">
                Confiance IA: {level.label}
              </div>
              {explanation && (
                <p className="text-slate-300">{explanation}</p>
              )}
              {!explanation && (
                <p className="text-slate-300">
                  {level.description}
                </p>
              )}
              {/* Arrow */}
              <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================================
// CONFIDENCE LEVEL HELPER
// ============================================================================

function getConfidenceLevel(confidence) {
  if (confidence >= 0.9) {
    return {
      level: 'very_high',
      label: 'Très haute confiance',
      description: 'Prédiction très fiable basée sur des données solides',
      Icon: CheckCircle,
      textColor: 'text-emerald-700',
      bgColor: 'bg-emerald-100',
      barColor: 'bg-emerald-500',
    };
  }
  if (confidence >= 0.75) {
    return {
      level: 'high',
      label: 'Haute confiance',
      description: 'Prédiction fiable avec une bonne base de données',
      Icon: Sparkles,
      textColor: 'text-blue-700',
      bgColor: 'bg-blue-100',
      barColor: 'bg-blue-500',
    };
  }
  if (confidence >= 0.5) {
    return {
      level: 'medium',
      label: 'Confiance moyenne',
      description: 'Prédiction probable mais à vérifier',
      Icon: Brain,
      textColor: 'text-amber-700',
      bgColor: 'bg-amber-100',
      barColor: 'bg-amber-500',
    };
  }
  if (confidence >= 0.25) {
    return {
      level: 'low',
      label: 'Faible confiance',
      description: 'Prédiction incertaine, données insuffisantes',
      Icon: HelpCircle,
      textColor: 'text-orange-700',
      bgColor: 'bg-orange-100',
      barColor: 'bg-orange-500',
    };
  }
  return {
    level: 'very_low',
    label: 'Très faible confiance',
    description: 'Prédiction spéculative, à interpréter avec prudence',
    Icon: AlertTriangle,
    textColor: 'text-red-700',
    bgColor: 'bg-red-100',
    barColor: 'bg-red-500',
  };
}

// ============================================================================
// CONFIDENCE INDICATOR (Mini version for tables)
// ============================================================================

export function ConfidenceIndicator({
  confidence,
  size = 'sm',
  showValue = false,
}) {
  const percentage = Math.round(Math.min(1, Math.max(0, confidence)) * 100);
  const level = getConfidenceLevel(confidence);

  return (
    <div className="flex items-center gap-1.5">
      {/* Mini bar */}
      <div className={clsx(
        'w-12 h-1.5 rounded-full bg-slate-200 overflow-hidden',
        size === 'xs' && 'w-8 h-1'
      )}>
        <div
          className={clsx('h-full rounded-full transition-all', level.barColor)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showValue && (
        <span className={clsx(
          'font-medium',
          level.textColor,
          size === 'xs' ? 'text-[10px]' : 'text-xs'
        )}>
          {percentage}%
        </span>
      )}
    </div>
  );
}

// ============================================================================
// CONFIDENCE RING (Circular variant)
// ============================================================================

export function ConfidenceRing({
  confidence,
  size = 48,
  strokeWidth = 4,
  showIcon = true,
  showPercentage = true,
  className,
}) {
  const percentage = Math.round(Math.min(1, Math.max(0, confidence)) * 100);
  const level = getConfidenceLevel(confidence);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (confidence * circumference);

  return (
    <div className={clsx('relative inline-flex', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-slate-200"
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          className={level.textColor}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          style={{
            strokeDasharray: circumference,
          }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {showIcon && <level.Icon className={clsx('w-4 h-4', level.textColor)} />}
        {showPercentage && (
          <span className={clsx('text-xs font-bold', level.textColor)}>
            {percentage}%
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// AI SUGGESTION WRAPPER
// ============================================================================

export function AISuggestionWrapper({
  confidence,
  children,
  onAccept,
  onReject,
  onAdjust,
  showActions = true,
  className,
}) {
  const level = getConfidenceLevel(confidence);
  const percentage = Math.round(confidence * 100);

  return (
    <div
      className={clsx(
        'relative p-4 rounded-xl border-l-4 bg-gradient-to-r',
        level.level === 'very_high' && 'border-l-emerald-500 from-emerald-50/50 to-white',
        level.level === 'high' && 'border-l-blue-500 from-blue-50/50 to-white',
        level.level === 'medium' && 'border-l-amber-500 from-amber-50/50 to-white',
        level.level === 'low' && 'border-l-orange-500 from-orange-50/50 to-white',
        level.level === 'very_low' && 'border-l-red-500 from-red-50/50 to-white',
        'border border-slate-200',
        className
      )}
    >
      {/* AI Badge */}
      <div className="absolute -top-2 -right-2">
        <AIConfidenceBadge
          confidence={confidence}
          size="sm"
          variant="pill"
        />
      </div>

      {/* Content */}
      <div className="pr-16">
        {children}
      </div>

      {/* Actions */}
      {showActions && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-100">
          {onAccept && (
            <button
              onClick={onAccept}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-emerald-500 hover:bg-emerald-600 rounded-lg transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              Accepter
            </button>
          )}
          {onAdjust && (
            <button
              onClick={onAdjust}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
            >
              Ajuster
            </button>
          )}
          {onReject && (
            <button
              onClick={onReject}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              Ignorer
            </button>
          )}
        </div>
      )}
    </div>
  );
}
