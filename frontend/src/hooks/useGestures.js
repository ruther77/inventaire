/**
 * useGestures - Hook pour la gestion des gestes mobiles (swipe, long press)
 *
 * Features:
 * - Détection de swipe (gauche, droite, haut, bas)
 * - Détection de long press
 * - Configuration du seuil de distance et temps
 * - Support des callbacks pour chaque geste
 *
 * @example
 * const gestures = useGestures({
 *   onSwipeLeft: () => console.log('Swipe left'),
 *   onSwipeRight: () => console.log('Swipe right'),
 *   onLongPress: () => console.log('Long press'),
 * });
 *
 * return <div {...gestures}>Content</div>
 */

import { useRef, useCallback } from 'react';

const DEFAULT_SWIPE_THRESHOLD = 50; // pixels
const DEFAULT_LONG_PRESS_DURATION = 500; // milliseconds
const DEFAULT_VELOCITY_THRESHOLD = 0.3; // pixels/ms

export function useGestures({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  onLongPress,
  onLongPressStart,
  onLongPressEnd,
  swipeThreshold = DEFAULT_SWIPE_THRESHOLD,
  longPressDuration = DEFAULT_LONG_PRESS_DURATION,
  velocityThreshold = DEFAULT_VELOCITY_THRESHOLD,
  disabled = false,
} = {}) {
  const touchStartRef = useRef(null);
  const touchEndRef = useRef(null);
  const longPressTimerRef = useRef(null);
  const isLongPressRef = useRef(false);

  const clearLongPressTimer = useCallback(() => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }, []);

  const handleTouchStart = useCallback(
    (e) => {
      if (disabled) return;

      const touch = e.touches[0];
      touchStartRef.current = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
      };
      touchEndRef.current = null;
      isLongPressRef.current = false;

      // Start long press timer
      if (onLongPress || onLongPressStart) {
        longPressTimerRef.current = setTimeout(() => {
          isLongPressRef.current = true;
          onLongPressStart?.(e);
          onLongPress?.(e);
        }, longPressDuration);
      }
    },
    [disabled, onLongPress, onLongPressStart, longPressDuration]
  );

  const handleTouchMove = useCallback(
    (e) => {
      if (disabled || !touchStartRef.current) return;

      // Cancel long press on movement
      clearLongPressTimer();

      const touch = e.touches[0];
      touchEndRef.current = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
      };
    },
    [disabled, clearLongPressTimer]
  );

  const handleTouchEnd = useCallback(
    (e) => {
      if (disabled || !touchStartRef.current) return;

      clearLongPressTimer();

      // If it was a long press, don't process swipe
      if (isLongPressRef.current) {
        onLongPressEnd?.(e);
        touchStartRef.current = null;
        touchEndRef.current = null;
        isLongPressRef.current = false;
        return;
      }

      // Process swipe
      if (touchEndRef.current) {
        const deltaX = touchEndRef.current.x - touchStartRef.current.x;
        const deltaY = touchEndRef.current.y - touchStartRef.current.y;
        const deltaTime = touchEndRef.current.time - touchStartRef.current.time;

        const velocityX = Math.abs(deltaX) / deltaTime;
        const velocityY = Math.abs(deltaY) / deltaTime;

        // Determine swipe direction
        const isHorizontalSwipe = Math.abs(deltaX) > Math.abs(deltaY);
        const isVerticalSwipe = Math.abs(deltaY) > Math.abs(deltaX);

        // Horizontal swipe
        if (isHorizontalSwipe && Math.abs(deltaX) > swipeThreshold && velocityX > velocityThreshold) {
          if (deltaX > 0) {
            onSwipeRight?.(e, { deltaX, deltaY, deltaTime, velocityX });
          } else {
            onSwipeLeft?.(e, { deltaX, deltaY, deltaTime, velocityX });
          }
        }

        // Vertical swipe
        if (isVerticalSwipe && Math.abs(deltaY) > swipeThreshold && velocityY > velocityThreshold) {
          if (deltaY > 0) {
            onSwipeDown?.(e, { deltaX, deltaY, deltaTime, velocityY });
          } else {
            onSwipeUp?.(e, { deltaX, deltaY, deltaTime, velocityY });
          }
        }
      }

      touchStartRef.current = null;
      touchEndRef.current = null;
      isLongPressRef.current = false;
    },
    [
      disabled,
      clearLongPressTimer,
      onSwipeLeft,
      onSwipeRight,
      onSwipeUp,
      onSwipeDown,
      onLongPressEnd,
      swipeThreshold,
      velocityThreshold,
    ]
  );

  const handleTouchCancel = useCallback(() => {
    clearLongPressTimer();
    touchStartRef.current = null;
    touchEndRef.current = null;
    isLongPressRef.current = false;
  }, [clearLongPressTimer]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
    onTouchCancel: handleTouchCancel,
  };
}

/**
 * useSwipeable - Hook simplifié pour la détection de swipe uniquement
 */
export function useSwipeable({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = DEFAULT_SWIPE_THRESHOLD,
  disabled = false,
} = {}) {
  return useGestures({
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    swipeThreshold: threshold,
    disabled,
  });
}

/**
 * useLongPress - Hook simplifié pour la détection de long press uniquement
 */
export function useLongPress({
  onLongPress,
  onLongPressStart,
  onLongPressEnd,
  duration = DEFAULT_LONG_PRESS_DURATION,
  disabled = false,
} = {}) {
  return useGestures({
    onLongPress,
    onLongPressStart,
    onLongPressEnd,
    longPressDuration: duration,
    disabled,
  });
}

export default useGestures;
