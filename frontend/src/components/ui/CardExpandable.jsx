/**
 * CardExpandable - Carte avec contenu expandable
 * Phase 4 - UX_NEXT_GEN_2025.md
 *
 * Permet d'afficher un résumé compact et d'expandre pour voir les détails
 * Utilisé pour Intelligence, Alertes, Recommandations
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronUp,
  X,
  Maximize2,
  Minimize2,
  MoreHorizontal,
} from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// EXPANDABLE CARD
// ============================================================================

export default function CardExpandable({
  // Content
  title,
  subtitle,
  icon: Icon,
  summary,
  children,

  // Actions
  actions,
  onDismiss,
  onExpand,

  // Style
  variant = 'default', // default, success, warning, error, info
  size = 'md', // sm, md, lg
  className,

  // Behavior
  defaultExpanded = false,
  expandable = true,
  collapsible = true,
  fullscreenMode = false,
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const contentRef = useRef(null);
  const [contentHeight, setContentHeight] = useState(0);

  // Measure content height for smooth animation
  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [children, isExpanded]);

  const handleExpand = () => {
    if (!expandable && !isExpanded) return;
    if (!collapsible && isExpanded) return;

    setIsExpanded(!isExpanded);
    onExpand?.(!isExpanded);
  };

  const handleFullscreen = (e) => {
    e.stopPropagation();
    setIsFullscreen(!isFullscreen);
  };

  // Variant styles
  const variantStyles = {
    default: {
      card: 'bg-white border-slate-200',
      icon: 'bg-slate-100 text-slate-600',
      accent: 'border-l-slate-400',
    },
    success: {
      card: 'bg-emerald-50/50 border-emerald-200',
      icon: 'bg-emerald-100 text-emerald-600',
      accent: 'border-l-emerald-500',
    },
    warning: {
      card: 'bg-amber-50/50 border-amber-200',
      icon: 'bg-amber-100 text-amber-600',
      accent: 'border-l-amber-500',
    },
    error: {
      card: 'bg-red-50/50 border-red-200',
      icon: 'bg-red-100 text-red-600',
      accent: 'border-l-red-500',
    },
    info: {
      card: 'bg-blue-50/50 border-blue-200',
      icon: 'bg-blue-100 text-blue-600',
      accent: 'border-l-blue-500',
    },
  };

  const sizeStyles = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-5',
  };

  const styles = variantStyles[variant] || variantStyles.default;

  // Fullscreen portal
  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className={clsx(
            'w-full max-w-4xl max-h-[90vh] overflow-auto',
            'bg-white rounded-xl shadow-2xl border',
            styles.card
          )}
        >
          <div className="sticky top-0 bg-white border-b border-slate-100 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {Icon && (
                <div className={clsx('p-2 rounded-lg', styles.icon)}>
                  <Icon className="w-5 h-5" />
                </div>
              )}
              <div>
                <h3 className="font-semibold text-slate-900">{title}</h3>
                {subtitle && (
                  <p className="text-sm text-slate-500">{subtitle}</p>
                )}
              </div>
            </div>
            <button
              onClick={handleFullscreen}
              className="p-2 rounded-lg hover:bg-slate-100 text-slate-500"
            >
              <Minimize2 className="w-5 h-5" />
            </button>
          </div>
          <div className="p-4">{children}</div>
          {actions && (
            <div className="sticky bottom-0 bg-slate-50 border-t border-slate-100 px-4 py-3 flex justify-end gap-2">
              {actions}
            </div>
          )}
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      layout
      className={clsx(
        'rounded-xl border border-l-4',
        styles.card,
        styles.accent,
        'transition-shadow hover:shadow-md',
        className
      )}
    >
      {/* Header - Always visible */}
      <div
        className={clsx(
          'flex items-start gap-3 cursor-pointer',
          sizeStyles[size]
        )}
        onClick={handleExpand}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleExpand();
          }
        }}
      >
        {/* Icon */}
        {Icon && (
          <div className={clsx('p-2 rounded-lg flex-shrink-0', styles.icon)}>
            <Icon className="w-4 h-4" />
          </div>
        )}

        {/* Title & Summary */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-slate-900 truncate">{title}</h4>
            {subtitle && (
              <span className="text-xs text-slate-500 truncate">{subtitle}</span>
            )}
          </div>
          {summary && !isExpanded && (
            <p className="text-sm text-slate-600 mt-1 line-clamp-2">
              {summary}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {fullscreenMode && (
            <button
              onClick={handleFullscreen}
              className="p-1.5 rounded hover:bg-slate-100 text-slate-400"
              title="Plein écran"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          )}
          {onDismiss && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDismiss();
              }}
              className="p-1.5 rounded hover:bg-red-100 text-slate-400 hover:text-red-500"
              title="Fermer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {expandable && (
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="w-5 h-5 text-slate-400" />
            </motion.div>
          )}
        </div>
      </div>

      {/* Expandable Content */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div
              ref={contentRef}
              className={clsx(
                'border-t border-slate-100',
                sizeStyles[size]
              )}
            >
              {children}
            </div>

            {/* Footer Actions */}
            {actions && (
              <div className="border-t border-slate-100 px-4 py-3 bg-slate-50/50 flex justify-end gap-2">
                {actions}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ============================================================================
// CARD EXPANDABLE GROUP - Pour grouper plusieurs cartes
// ============================================================================

export function CardExpandableGroup({
  children,
  accordion = false, // Only one open at a time
  className,
}) {
  const [openIndex, setOpenIndex] = useState(null);

  if (accordion) {
    // Clone children and manage expansion state
    return (
      <div className={clsx('space-y-3', className)}>
        {Array.isArray(children) ? children.map((child, index) => {
          if (!child) return null;
          return (
            <div key={index}>
              {/* Clone with controlled expansion */}
              {child.props && (
                <CardExpandable
                  {...child.props}
                  defaultExpanded={openIndex === index}
                  onExpand={(expanded) => {
                    setOpenIndex(expanded ? index : null);
                    child.props.onExpand?.(expanded);
                  }}
                />
              )}
            </div>
          );
        }) : children}
      </div>
    );
  }

  return <div className={clsx('space-y-3', className)}>{children}</div>;
}

// ============================================================================
// RECOMMENDATION CARD - Variante spécialisée pour les recommandations IA
// ============================================================================

export function RecommendationCard({
  title,
  description,
  impact,
  confidence,
  type = 'optimization', // optimization, warning, action, info
  onApply,
  onDismiss,
  onDetails,
  children,
  className,
}) {
  const typeConfig = {
    optimization: {
      icon: '💡',
      variant: 'info',
      label: 'Optimisation',
    },
    warning: {
      icon: '⚠️',
      variant: 'warning',
      label: 'Attention',
    },
    action: {
      icon: '⚡',
      variant: 'success',
      label: 'Action',
    },
    info: {
      icon: 'ℹ️',
      variant: 'default',
      label: 'Information',
    },
  };

  const config = typeConfig[type] || typeConfig.info;

  return (
    <CardExpandable
      title={
        <span className="flex items-center gap-2">
          <span>{config.icon}</span>
          {title}
        </span>
      }
      subtitle={impact && (
        <span className="text-emerald-600 font-medium">{impact}</span>
      )}
      summary={description}
      variant={config.variant}
      onDismiss={onDismiss}
      className={className}
      actions={
        <>
          {onDetails && (
            <button
              onClick={onDetails}
              className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Détails
            </button>
          )}
          {onApply && (
            <button
              onClick={onApply}
              className="px-3 py-1.5 text-sm bg-brand-500 text-white hover:bg-brand-600 rounded-lg transition-colors"
            >
              Appliquer
            </button>
          )}
        </>
      }
    >
      {/* Confidence indicator */}
      {confidence !== undefined && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Confiance IA</span>
            <span>{Math.round(confidence * 100)}%</span>
          </div>
          <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all',
                confidence >= 0.9
                  ? 'bg-emerald-500'
                  : confidence >= 0.7
                  ? 'bg-amber-500'
                  : 'bg-red-500'
              )}
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
        </div>
      )}

      {children}
    </CardExpandable>
  );
}

// ============================================================================
// ALERT CARD - Variante pour les alertes
// ============================================================================

export function AlertCard({
  title,
  message,
  severity = 'info', // info, warning, error, critical
  timestamp,
  source,
  onAcknowledge,
  onDismiss,
  onAction,
  actionLabel = 'Résoudre',
  children,
  className,
}) {
  const severityConfig = {
    info: {
      variant: 'info',
      icon: 'ℹ️',
      bgPulse: false,
    },
    warning: {
      variant: 'warning',
      icon: '⚠️',
      bgPulse: false,
    },
    error: {
      variant: 'error',
      icon: '🔴',
      bgPulse: false,
    },
    critical: {
      variant: 'error',
      icon: '🚨',
      bgPulse: true,
    },
  };

  const config = severityConfig[severity] || severityConfig.info;

  return (
    <CardExpandable
      title={
        <span className="flex items-center gap-2">
          <span className={config.bgPulse ? 'animate-pulse' : ''}>{config.icon}</span>
          {title}
        </span>
      }
      subtitle={timestamp && (
        <span className="text-slate-400">
          {new Date(timestamp).toLocaleString('fr-FR')}
        </span>
      )}
      summary={message}
      variant={config.variant}
      onDismiss={onDismiss}
      className={clsx(
        config.bgPulse && 'ring-2 ring-red-400 ring-opacity-50',
        className
      )}
      actions={
        <>
          {onAcknowledge && (
            <button
              onClick={onAcknowledge}
              className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Accusé
            </button>
          )}
          {onAction && (
            <button
              onClick={onAction}
              className="px-3 py-1.5 text-sm bg-brand-500 text-white hover:bg-brand-600 rounded-lg transition-colors"
            >
              {actionLabel}
            </button>
          )}
        </>
      }
    >
      {source && (
        <div className="text-xs text-slate-500 mb-2">
          Source: {source}
        </div>
      )}
      {children}
    </CardExpandable>
  );
}
