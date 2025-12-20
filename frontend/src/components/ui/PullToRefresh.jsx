/**
 * PullToRefresh - Component wrapper for pull-to-refresh functionality
 *
 * Features:
 * - Pull down gesture detection
 * - Animated loading spinner
 * - Callback for refresh action
 * - Works with any scrollable content
 * - Proper iOS/Android feel with natural physics
 * - Visual feedback during pull
 *
 * @example
 * <PullToRefresh onRefresh={async () => await fetchData()}>
 *   <div>Your scrollable content</div>
 * </PullToRefresh>
 *
 * @example With custom indicator
 * <PullToRefresh
 *   onRefresh={handleRefresh}
 *   renderIndicator={(state, progress) => (
 *     <CustomLoadingIndicator state={state} progress={progress} />
 *   )}
 * >
 *   <Content />
 * </PullToRefresh>
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Check, ArrowDown } from 'lucide-react';
import clsx from 'clsx';
import { usePullToRefresh, PULL_STATES } from '../../hooks/usePullToRefresh.js';

export function PullToRefresh({
  children,
  onRefresh,
  threshold = 80,
  maxPull = 120,
  disabled = false,
  className,
  contentClassName,
  renderIndicator,
  indicatorClassName,
  showText = true,
}) {
  const {
    pullState,
    pullProgress,
    pullDistance,
    handlers,
    containerRef,
  } = usePullToRefresh({
    onRefresh,
    threshold,
    maxPull,
    disabled,
  });

  // Default indicator renderer
  const defaultIndicator = (state, progress) => (
    <div className={clsx(
      'flex flex-col items-center justify-center gap-2 py-4',
      indicatorClassName
    )}>
      <motion.div
        animate={{
          rotate: state === PULL_STATES.PULLING ? progress * 180 : 0,
          scale: state === PULL_STATES.REFRESHING ? 1 : Math.min(progress * 1.2, 1),
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {state === PULL_STATES.REFRESHING && (
          <Loader2 className="h-6 w-6 text-brand-500 animate-spin" />
        )}
        {state === PULL_STATES.DONE && (
          <Check className="h-6 w-6 text-emerald-500" />
        )}
        {(state === PULL_STATES.PULLING || state === PULL_STATES.READY) && (
          <ArrowDown
            className={clsx(
              'h-6 w-6 transition-colors',
              state === PULL_STATES.READY ? 'text-brand-500' : 'text-slate-400'
            )}
          />
        )}
      </motion.div>

      {showText && (
        <AnimatePresence mode="wait">
          <motion.div
            key={state}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="text-sm font-medium text-slate-600"
          >
            {state === PULL_STATES.PULLING && 'Tirez pour rafraîchir'}
            {state === PULL_STATES.READY && 'Relâchez pour rafraîchir'}
            {state === PULL_STATES.REFRESHING && 'Chargement...'}
            {state === PULL_STATES.DONE && 'Rafraîchi !'}
          </motion.div>
        </AnimatePresence>
      )}

      {/* Progress bar */}
      <div className="w-16 h-1 bg-slate-200 rounded-full overflow-hidden">
        <motion.div
          className={clsx(
            'h-full rounded-full',
            state === PULL_STATES.READY ? 'bg-brand-500' : 'bg-slate-400'
          )}
          style={{ width: `${progress * 100}%` }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        />
      </div>
    </div>
  );

  const indicator = renderIndicator ? renderIndicator(pullState, pullProgress) : defaultIndicator(pullState, pullProgress);

  return (
    <div
      ref={containerRef}
      className={clsx('relative overflow-auto', className)}
      {...handlers}
    >
      {/* Pull indicator */}
      <motion.div
        className="absolute inset-x-0 top-0 z-10 bg-white/90 backdrop-blur-sm"
        initial={false}
        animate={{
          height: pullDistance,
          opacity: pullDistance > 0 ? 1 : 0,
        }}
        style={{
          marginTop: -threshold,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        <div className="h-full flex items-end justify-center pb-2">
          {indicator}
        </div>
      </motion.div>

      {/* Content */}
      <motion.div
        className={contentClassName}
        animate={{
          y: pullState === PULL_STATES.REFRESHING ? threshold * 0.5 : 0,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {children}
      </motion.div>
    </div>
  );
}

/**
 * PullToRefreshIndicator - Standalone indicator component for custom layouts
 */
export function PullToRefreshIndicator({
  state = PULL_STATES.IDLE,
  progress = 0,
  className,
  showText = true,
  size = 'md',
}) {
  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  const iconSize = iconSizes[size] || iconSizes.md;

  return (
    <div className={clsx('flex flex-col items-center justify-center gap-2', className)}>
      <motion.div
        animate={{
          rotate: state === PULL_STATES.PULLING ? progress * 180 : 0,
          scale: state === PULL_STATES.REFRESHING ? 1 : Math.min(progress * 1.2, 1),
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {state === PULL_STATES.REFRESHING && (
          <Loader2 className={clsx(iconSize, 'text-brand-500 animate-spin')} />
        )}
        {state === PULL_STATES.DONE && (
          <Check className={clsx(iconSize, 'text-emerald-500')} />
        )}
        {(state === PULL_STATES.PULLING || state === PULL_STATES.READY) && (
          <ArrowDown
            className={clsx(
              iconSize,
              'transition-colors',
              state === PULL_STATES.READY ? 'text-brand-500' : 'text-slate-400'
            )}
          />
        )}
      </motion.div>

      {showText && (
        <AnimatePresence mode="wait">
          <motion.div
            key={state}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className={clsx(
              'font-medium text-slate-600',
              size === 'sm' && 'text-xs',
              size === 'md' && 'text-sm',
              size === 'lg' && 'text-base'
            )}
          >
            {state === PULL_STATES.PULLING && 'Tirez pour rafraîchir'}
            {state === PULL_STATES.READY && 'Relâchez pour rafraîchir'}
            {state === PULL_STATES.REFRESHING && 'Chargement...'}
            {state === PULL_STATES.DONE && 'Rafraîchi !'}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}

/**
 * PullToRefreshSimple - Simplified version without animations for better performance
 */
export function PullToRefreshSimple({
  children,
  onRefresh,
  threshold = 80,
  disabled = false,
  className,
}) {
  const {
    pullState,
    pullDistance,
    handlers,
    containerRef,
  } = usePullToRefresh({
    onRefresh,
    threshold,
    disabled,
  });

  const isActive = pullDistance > 0;

  return (
    <div
      ref={containerRef}
      className={clsx('relative overflow-auto', className)}
      {...handlers}
    >
      {/* Simple indicator */}
      {isActive && (
        <div
          className="absolute inset-x-0 top-0 z-10 bg-white/90 flex items-center justify-center"
          style={{ height: pullDistance }}
        >
          {pullState === PULL_STATES.REFRESHING ? (
            <Loader2 className="h-5 w-5 text-brand-500 animate-spin" />
          ) : (
            <ArrowDown className="h-5 w-5 text-slate-400" />
          )}
        </div>
      )}

      {/* Content */}
      <div style={{ transform: pullState === PULL_STATES.REFRESHING ? `translateY(${threshold * 0.5}px)` : 'none' }}>
        {children}
      </div>
    </div>
  );
}

export default PullToRefresh;
