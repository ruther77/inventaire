/**
 * SwipeableRow - Advanced swipeable row component with gesture support
 *
 * Features:
 * - Swipe left/right to reveal actions (edit, delete, etc.)
 * - Spring animations with Framer Motion
 * - Touch-friendly with proper thresholds
 * - Auto-close when another row is swiped
 * - Haptic feedback
 * - Long press for context menu
 * - Visual feedback during swipe
 *
 * @example
 * <SwipeableRow
 *   id="row-1"
 *   leftActions={[{ label: 'Delete', icon: Trash, variant: 'danger', onAction: handleDelete }]}
 *   rightActions={[{ label: 'Edit', icon: Edit, variant: 'primary', onAction: handleEdit }]}
 *   onLongPress={() => setShowContextMenu(true)}
 * >
 *   <div>Row content</div>
 * </SwipeableRow>
 */

import { useState, useRef, useEffect, useCallback, createContext, useContext } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring } from 'framer-motion';
import clsx from 'clsx';
import { useGestures } from '../../hooks/useGestures.js';

const SWIPE_REVEAL_THRESHOLD = 80; // pixels to reveal action
const SWIPE_CONFIRM_THRESHOLD = 150; // pixels to auto-execute action
const SWIPE_VELOCITY_THRESHOLD = 0.5; // velocity for quick swipe

// Context for managing multiple swipeable rows
const SwipeableRowContext = createContext({
  activeRowId: null,
  setActiveRowId: () => {},
});

export const SwipeableRowProvider = ({ children }) => {
  const [activeRowId, setActiveRowId] = useState(null);

  return (
    <SwipeableRowContext.Provider value={{ activeRowId, setActiveRowId }}>
      {children}
    </SwipeableRowContext.Provider>
  );
};

const useSwipeableRowContext = () => {
  return useContext(SwipeableRowContext);
};

export function SwipeableRow({
  id, // Unique identifier for this row
  children,
  leftActions = [],
  rightActions = [],
  onLongPress,
  disabled = false,
  className,
  innerClassName,
  longPressActions = [],
  onSwipeStart,
  onSwipeEnd,
}) {
  const context = useSwipeableRowContext();
  const [offset, setOffset] = useState(0);
  const [isRevealed, setIsRevealed] = useState(false);
  const [revealedSide, setRevealedSide] = useState(null); // 'left' | 'right'
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);
  const x = useMotionValue(0);

  // Spring animation for smooth, natural movement
  const springX = useSpring(x, {
    stiffness: 300,
    damping: 30,
    mass: 0.8,
  });

  // Dynamic background color based on swipe direction and intensity
  const backgroundColor = useTransform(x, [-200, -80, 0, 80, 200], [
    'rgba(239, 68, 68, 0.25)', // red (left swipe - delete)
    'rgba(239, 68, 68, 0.1)',
    'rgba(0, 0, 0, 0)',
    'rgba(59, 130, 246, 0.1)',
    'rgba(59, 130, 246, 0.25)', // blue (right swipe - edit)
  ]);

  // Scale effect for revealed actions
  const actionScale = useTransform(x,
    [-SWIPE_CONFIRM_THRESHOLD, -SWIPE_REVEAL_THRESHOLD, 0, SWIPE_REVEAL_THRESHOLD, SWIPE_CONFIRM_THRESHOLD],
    [1.1, 1, 1, 1, 1.1]
  );

  const resetPosition = useCallback(() => {
    setOffset(0);
    setIsRevealed(false);
    setRevealedSide(null);
    setIsDragging(false);
    x.set(0);
    onSwipeEnd?.();
  }, [x, onSwipeEnd]);

  // Auto-close when another row is opened
  useEffect(() => {
    if (context && context.activeRowId !== null && context.activeRowId !== id && isRevealed) {
      resetPosition();
    }
  }, [context, id, isRevealed, resetPosition]);

  const executeAction = useCallback(
    (action) => {
      // Haptic feedback if available
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }

      action.onAction?.();
      resetPosition();
    },
    [resetPosition]
  );

  const handleSwipe = useCallback(
    (direction, delta, velocity = 0) => {
      if (disabled) return;

      const actions = direction === 'left' ? leftActions : rightActions;
      if (actions.length === 0) return;

      const absDelta = Math.abs(delta);
      const isQuickSwipe = velocity > SWIPE_VELOCITY_THRESHOLD;

      if (absDelta > SWIPE_CONFIRM_THRESHOLD || (isQuickSwipe && absDelta > SWIPE_REVEAL_THRESHOLD)) {
        // Auto-execute first action on strong swipe or quick swipe
        executeAction(actions[0]);
      } else if (absDelta > SWIPE_REVEAL_THRESHOLD) {
        // Reveal actions
        setIsRevealed(true);
        setRevealedSide(direction);
        setOffset(direction === 'left' ? -SWIPE_REVEAL_THRESHOLD : SWIPE_REVEAL_THRESHOLD);
        x.set(direction === 'left' ? -SWIPE_REVEAL_THRESHOLD : SWIPE_REVEAL_THRESHOLD);

        // Notify context that this row is active
        context?.setActiveRowId?.(id);
      } else {
        resetPosition();
      }
    },
    [disabled, leftActions, rightActions, executeAction, resetPosition, x, context, id]
  );

  const gestures = useGestures({
    onSwipeLeft: (e, data) => handleSwipe('left', data.deltaX, data.velocityX),
    onSwipeRight: (e, data) => handleSwipe('right', data.deltaX, data.velocityX),
    onLongPress: (e) => {
      if (disabled) return;

      // Haptic feedback
      if (navigator.vibrate) {
        navigator.vibrate([50, 30, 50]);
      }

      if (onLongPress) {
        onLongPress(e);
      }

      if (longPressActions.length > 0) {
        setShowContextMenu(true);
      }
    },
    disabled,
    swipeThreshold: 30, // Lower threshold for more responsive feel
    velocityThreshold: 0.2, // More sensitive velocity detection
  });

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowContextMenu(false);
        resetPosition();
      }
    };

    if (showContextMenu || isRevealed) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('touchstart', handleClickOutside);
      };
    }
  }, [showContextMenu, isRevealed, resetPosition]);

  return (
    <div ref={containerRef} className={clsx('relative overflow-hidden', className)}>
      {/* Action buttons background - Left (Swipe Right to reveal) */}
      <AnimatePresence>
        {isRevealed && revealedSide === 'right' && rightActions.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-y-0 left-0 flex items-center"
          >
            {rightActions.map((action, index) => (
              <button
                key={index}
                type="button"
                onClick={() => executeAction(action)}
                className={clsx(
                  'h-full px-4 flex items-center gap-2 text-sm font-medium transition-colors',
                  action.variant === 'danger' && 'bg-rose-500 hover:bg-rose-600 text-white',
                  action.variant === 'primary' && 'bg-blue-500 hover:bg-blue-600 text-white',
                  action.variant === 'success' && 'bg-emerald-500 hover:bg-emerald-600 text-white',
                  !action.variant && 'bg-slate-500 hover:bg-slate-600 text-white'
                )}
              >
                {action.icon && <action.icon className="h-4 w-4" />}
                {action.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action buttons background - Right (Swipe Left to reveal) */}
      <AnimatePresence>
        {isRevealed && revealedSide === 'left' && leftActions.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-y-0 right-0 flex items-center"
          >
            {leftActions.map((action, index) => (
              <button
                key={index}
                type="button"
                onClick={() => executeAction(action)}
                className={clsx(
                  'h-full px-4 flex items-center gap-2 text-sm font-medium transition-colors',
                  action.variant === 'danger' && 'bg-rose-500 hover:bg-rose-600 text-white',
                  action.variant === 'primary' && 'bg-blue-500 hover:bg-blue-600 text-white',
                  action.variant === 'success' && 'bg-emerald-500 hover:bg-emerald-600 text-white',
                  !action.variant && 'bg-slate-500 hover:bg-slate-600 text-white'
                )}
              >
                {action.icon && <action.icon className="h-4 w-4" />}
                {action.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content */}
      <motion.div
        {...gestures}
        drag={!disabled && (leftActions.length > 0 || rightActions.length > 0) ? 'x' : false}
        dragConstraints={{ left: -SWIPE_CONFIRM_THRESHOLD, right: SWIPE_CONFIRM_THRESHOLD }}
        dragElastic={0.2}
        dragMomentum={false}
        onDragStart={() => {
          setIsDragging(true);
          onSwipeStart?.();
        }}
        onDragEnd={(e, info) => {
          const delta = info.offset.x;
          const velocity = info.velocity.x;
          setIsDragging(false);

          if (Math.abs(delta) > SWIPE_REVEAL_THRESHOLD) {
            handleSwipe(delta < 0 ? 'left' : 'right', delta, Math.abs(velocity) / 1000);
          } else {
            resetPosition();
          }
        }}
        animate={{ x: offset }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        style={{
          x: isDragging ? x : springX,
          backgroundColor
        }}
        className={clsx(
          'relative touch-pan-y select-none',
          isDragging && 'cursor-grabbing',
          innerClassName
        )}
      >
        {children}
      </motion.div>

      {/* Context menu */}
      <AnimatePresence>
        {showContextMenu && longPressActions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -10 }}
            className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 bg-white rounded-lg shadow-xl border border-slate-200 py-1 min-w-[200px]"
          >
            {longPressActions.map((action, index) => (
              <button
                key={index}
                type="button"
                onClick={() => {
                  executeAction(action);
                  setShowContextMenu(false);
                }}
                className={clsx(
                  'w-full px-4 py-2 text-left text-sm font-medium transition-colors flex items-center gap-2',
                  action.variant === 'danger'
                    ? 'text-rose-600 hover:bg-rose-50'
                    : 'text-slate-700 hover:bg-slate-50'
                )}
              >
                {action.icon && <action.icon className="h-4 w-4" />}
                {action.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default SwipeableRow;
