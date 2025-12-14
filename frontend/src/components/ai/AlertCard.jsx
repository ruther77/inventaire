import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Clock, CheckCircle, X, ChevronRight, Lightbulb } from 'lucide-react';
import clsx from 'clsx';
import QuickAction, { QuickActionGroup } from './QuickAction.jsx';

/**
 * AlertCard - Carte d'alerte actionnable avec suggestion IA
 */
export default function AlertCard({
  id,
  severity = 'medium', // 'urgent', 'medium', 'info'
  title,
  description,
  suggestion,
  actions = [],
  timestamp,
  onAction,
  onDismiss,
  className,
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  const severityConfig = {
    urgent: {
      icon: AlertTriangle,
      color: 'rose',
      label: 'URGENT',
      bgClass: 'bg-rose-500/10 border-rose-500/30',
      iconClass: 'text-rose-400',
      labelClass: 'bg-rose-500/20 text-rose-400',
    },
    medium: {
      icon: Clock,
      color: 'amber',
      label: 'MOYEN',
      bgClass: 'bg-amber-500/10 border-amber-500/30',
      iconClass: 'text-amber-400',
      labelClass: 'bg-amber-500/20 text-amber-400',
    },
    info: {
      icon: Lightbulb,
      color: 'blue',
      label: 'INFO',
      bgClass: 'bg-blue-500/10 border-blue-500/30',
      iconClass: 'text-blue-400',
      labelClass: 'bg-blue-500/20 text-blue-400',
    },
  };

  const config = severityConfig[severity];
  const SeverityIcon = config.icon;

  const handleAction = async (action) => {
    if (action.onClick) {
      setIsProcessing(true);
      try {
        await action.onClick();
        if (action.dismissOnComplete) {
          setIsDismissed(true);
        }
      } finally {
        setIsProcessing(false);
      }
    }
    if (onAction) {
      onAction(action.id, id);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    if (onDismiss) {
      onDismiss(id);
    }
  };

  if (isDismissed) return null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      className={clsx(
        'relative rounded-xl border p-4',
        'transition-all duration-200',
        config.bgClass,
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={clsx('p-2 rounded-lg', config.labelClass)}>
          <SeverityIcon className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={clsx(
              'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
              config.labelClass
            )}>
              {config.label}
            </span>
            {timestamp && (
              <span className="text-[11px] text-slate-500">{timestamp}</span>
            )}
          </div>

          <h4 className="font-medium text-white text-sm">{title}</h4>
          {description && (
            <p className="text-xs text-slate-400 mt-1">{description}</p>
          )}
        </div>

        <button
          onClick={handleDismiss}
          className="p-1 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Suggestion IA */}
      {suggestion && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-3 flex items-start gap-2 p-2 rounded-lg bg-white/5"
        >
          <Lightbulb className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-slate-300">{suggestion}</p>
        </motion.div>
      )}

      {/* Actions */}
      {actions.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {actions.map((action, index) => (
            <QuickAction
              key={action.id || index}
              icon={action.icon}
              label={action.label}
              variant={action.variant || (index === 0 ? 'primary' : 'default')}
              size="sm"
              onClick={() => handleAction(action)}
              loading={isProcessing && action.id === 'primary'}
              disabled={isProcessing}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

/**
 * AlertList - Liste d'alertes avec animations
 */
export function AlertList({ alerts, onAction, onDismiss, className, maxVisible = 5 }) {
  const [showAll, setShowAll] = useState(false);
  const visibleAlerts = showAll ? alerts : alerts.slice(0, maxVisible);
  const hiddenCount = alerts.length - maxVisible;

  return (
    <div className={clsx('space-y-3', className)}>
      <AnimatePresence mode="popLayout">
        {visibleAlerts.map((alert) => (
          <AlertCard
            key={alert.id}
            {...alert}
            onAction={onAction}
            onDismiss={onDismiss}
          />
        ))}
      </AnimatePresence>

      {!showAll && hiddenCount > 0 && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowAll(true)}
          className="w-full py-2 text-sm text-slate-400 hover:text-white flex items-center justify-center gap-1 rounded-lg hover:bg-white/5 transition-colors"
        >
          Voir {hiddenCount} alerte{hiddenCount > 1 ? 's' : ''} de plus
          <ChevronRight className="w-4 h-4" />
        </motion.button>
      )}
    </div>
  );
}
