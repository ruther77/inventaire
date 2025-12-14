import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Package,
  DollarSign,
  Users,
  ChevronDown,
  ChevronUp,
  Check,
  X,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';
import ConfidenceBadge from './ConfidenceBadge.jsx';
import QuickAction, { QuickActionGroup } from './QuickAction.jsx';

/**
 * SuggestionCard - Recommandation IA avec impact prévu et actions
 */
export default function SuggestionCard({
  id,
  type = 'optimization', // 'optimization', 'stock', 'pricing', 'supplier'
  title,
  description,
  impact,
  confidence = 0.85,
  details,
  actions = [],
  onAction,
  onDismiss,
  className,
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isApplied, setIsApplied] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const typeConfig = {
    optimization: {
      icon: TrendingUp,
      color: 'emerald',
      label: 'Optimisation Marge',
      gradient: 'from-emerald-500/20 to-teal-500/10',
    },
    stock: {
      icon: Package,
      color: 'blue',
      label: 'Optimisation Stock',
      gradient: 'from-blue-500/20 to-cyan-500/10',
    },
    pricing: {
      icon: DollarSign,
      color: 'amber',
      label: 'Ajustement Prix',
      gradient: 'from-amber-500/20 to-orange-500/10',
    },
    supplier: {
      icon: Users,
      color: 'violet',
      label: 'Scoring Fournisseur',
      gradient: 'from-violet-500/20 to-purple-500/10',
    },
  };

  const config = typeConfig[type];
  const TypeIcon = config.icon;

  const handleApply = async () => {
    setIsProcessing(true);
    try {
      // Simuler un délai de traitement
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setIsApplied(true);
      if (onAction) {
        onAction('apply', id);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDismiss = () => {
    if (onDismiss) {
      onDismiss(id);
    }
  };

  const colorClasses = {
    emerald: {
      icon: 'text-emerald-400',
      label: 'bg-emerald-500/20 text-emerald-400',
      impact: 'text-emerald-400',
    },
    blue: {
      icon: 'text-blue-400',
      label: 'bg-blue-500/20 text-blue-400',
      impact: 'text-blue-400',
    },
    amber: {
      icon: 'text-amber-400',
      label: 'bg-amber-500/20 text-amber-400',
      impact: 'text-amber-400',
    },
    violet: {
      icon: 'text-violet-400',
      label: 'bg-violet-500/20 text-violet-400',
      impact: 'text-violet-400',
    },
  };

  const colors = colorClasses[config.color];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'relative rounded-xl border border-white/10 overflow-hidden',
        'bg-gradient-to-br',
        config.gradient,
        isApplied && 'opacity-60',
        className
      )}
    >
      {/* Header avec icône et badge */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className={clsx('p-2 rounded-lg bg-white/10', colors.icon)}>
              <TypeIcon className="w-5 h-5" />
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={clsx(
                  'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                  colors.label
                )}>
                  {config.label}
                </span>
                <ConfidenceBadge value={confidence} size="sm" showLabel={false} />
              </div>

              <h4 className="font-medium text-white">{title}</h4>
              {description && (
                <p className="text-sm text-slate-400 mt-1">{description}</p>
              )}
            </div>
          </div>

          {/* Impact prévu */}
          {impact && (
            <div className="text-right flex-shrink-0">
              <p className="text-xs text-slate-500 mb-0.5">Impact</p>
              <p className={clsx('font-bold text-lg', colors.impact)}>
                {impact.value}
              </p>
              <p className="text-[11px] text-slate-500">{impact.period}</p>
            </div>
          )}
        </div>

        {/* Zone dépliable avec détails */}
        <AnimatePresence>
          {isExpanded && details && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="mt-4 pt-4 border-t border-white/10">
                {/* Table de détails si fournie */}
                {details.table && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-slate-500 text-xs">
                          {details.table.headers.map((header, i) => (
                            <th key={i} className="pb-2 pr-4 font-medium">{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {details.table.rows.map((row, i) => (
                          <tr key={i} className="border-t border-white/5">
                            {row.map((cell, j) => (
                              <td key={j} className="py-2 pr-4 text-slate-300">{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Texte explicatif */}
                {details.explanation && (
                  <div className="flex items-start gap-2 mt-3 p-3 rounded-lg bg-white/5">
                    <Sparkles className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-slate-300">{details.explanation}</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Actions */}
        <div className="mt-4 flex items-center justify-between">
          <QuickActionGroup>
            {!isApplied ? (
              <>
                <QuickAction
                  icon={Check}
                  label="Appliquer"
                  variant="success"
                  size="sm"
                  onClick={handleApply}
                  loading={isProcessing}
                />
                {actions.map((action, index) => (
                  <QuickAction
                    key={action.id || index}
                    icon={action.icon}
                    label={action.label}
                    variant="default"
                    size="sm"
                    onClick={() => onAction && onAction(action.id, id)}
                    disabled={isProcessing}
                  />
                ))}
                <QuickAction
                  icon={X}
                  label="Ignorer"
                  variant="default"
                  size="sm"
                  onClick={handleDismiss}
                  disabled={isProcessing}
                />
              </>
            ) : (
              <span className="inline-flex items-center gap-1 text-sm text-emerald-400">
                <Check className="w-4 h-4" />
                Appliqué
              </span>
            )}
          </QuickActionGroup>

          {details && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Réduire
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Détails
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Badge "IA" */}
      <div className="absolute top-2 right-2">
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-400 text-[10px] font-medium">
          <Sparkles className="w-3 h-3" />
          IA
        </span>
      </div>
    </motion.div>
  );
}

/**
 * SuggestionList - Liste de suggestions avec compteur
 */
export function SuggestionList({ suggestions, onAction, onDismiss, title, className }) {
  const [visibleSuggestions, setVisibleSuggestions] = useState(suggestions);

  const handleDismiss = (id) => {
    setVisibleSuggestions((prev) => prev.filter((s) => s.id !== id));
    if (onDismiss) {
      onDismiss(id);
    }
  };

  return (
    <div className={className}>
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-400" />
            {title}
          </h3>
          <span className="text-sm text-slate-400">
            {visibleSuggestions.length} suggestion{visibleSuggestions.length > 1 ? 's' : ''}
          </span>
        </div>
      )}

      <div className="space-y-4">
        <AnimatePresence mode="popLayout">
          {visibleSuggestions.map((suggestion) => (
            <SuggestionCard
              key={suggestion.id}
              {...suggestion}
              onAction={onAction}
              onDismiss={handleDismiss}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
