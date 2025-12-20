/**
 * usePullToRefresh - Hook for implementing pull-to-refresh gesture
 *
 * Features:
 * - Detects pull-down gesture on scrollable containers
 * - Manages refresh state (idle, pulling, refreshing, done)
 * - Provides pull progress value for animations
 * - Proper iOS/Android feel with natural physics
 * - Prevents pull when content is scrolled
 *
 * @example
 * const {
 *   pullState,
 *   pullProgress,
 *   handlers,
 *   refresh
 * } = usePullToRefresh({
 *   onRefresh: async () => {
 *     await fetchData();
 *   },
 *   threshold: 80,
 * });
 *
 * return (
 *   <div {...handlers}>
 *     <PullIndicator progress={pullProgress} state={pullState} />
 *     <ScrollableContent />
 *   </div>
 * );
 */

import { useState, useRef, useCallback, useEffect } from 'react';

const PULL_THRESHOLD = 80; // pixels to trigger refresh
const MAX_PULL = 120; // maximum pull distance
const RESISTANCE_FACTOR = 0.5; // resistance when pulling (0-1, lower = more resistance)

export const PULL_STATES = {
  IDLE: 'idle',
  PULLING: 'pulling',
  READY: 'ready', // pulled past threshold
  REFRESHING: 'refreshing',
  DONE: 'done',
};

export function usePullToRefresh({
  onRefresh,
  threshold = PULL_THRESHOLD,
  maxPull = MAX_PULL,
  resistance = RESISTANCE_FACTOR,
  disabled = false,
  hapticFeedback = true,
} = {}) {
  const [pullState, setPullState] = useState(PULL_STATES.IDLE);
  const [pullProgress, setPullProgress] = useState(0); // 0 to 1
  const [pullDistance, setPullDistance] = useState(0);

  const touchStartRef = useRef({ y: 0, scrollTop: 0 });
  const containerRef = useRef(null);
  const isRefreshingRef = useRef(false);
  const hapticFiredRef = useRef(false);

  // Calculate pull progress (0 to 1)
  const updatePullProgress = useCallback((distance) => {
    const progress = Math.min(distance / threshold, 1);
    setPullProgress(progress);
    return progress;
  }, [threshold]);

  // Trigger haptic feedback
  const triggerHaptic = useCallback((pattern = 50) => {
    if (hapticFeedback && navigator.vibrate && !hapticFiredRef.current) {
      navigator.vibrate(pattern);
      hapticFiredRef.current = true;
    }
  }, [hapticFeedback]);

  // Reset to idle state
  const reset = useCallback(() => {
    setPullState(PULL_STATES.IDLE);
    setPullProgress(0);
    setPullDistance(0);
    isRefreshingRef.current = false;
    hapticFiredRef.current = false;
  }, []);

  // Execute refresh
  const refresh = useCallback(async () => {
    if (isRefreshingRef.current || !onRefresh) return;

    isRefreshingRef.current = true;
    setPullState(PULL_STATES.REFRESHING);

    try {
      await onRefresh();
      setPullState(PULL_STATES.DONE);

      // Show done state briefly before resetting
      setTimeout(reset, 500);
    } catch (error) {
      console.error('Refresh failed:', error);
      reset();
    }
  }, [onRefresh, reset]);

  // Touch handlers
  const handleTouchStart = useCallback((e) => {
    if (disabled || isRefreshingRef.current) return;

    const container = containerRef.current || e.currentTarget;
    const scrollTop = container.scrollTop || window.scrollY;

    // Only allow pull-to-refresh when at the top
    if (scrollTop > 0) return;

    touchStartRef.current = {
      y: e.touches[0].clientY,
      scrollTop,
    };

    hapticFiredRef.current = false;
  }, [disabled]);

  const handleTouchMove = useCallback((e) => {
    if (disabled || isRefreshingRef.current) return;
    if (!touchStartRef.current.y) return;

    const container = containerRef.current || e.currentTarget;
    const scrollTop = container.scrollTop || window.scrollY;

    // Cancel if user scrolled down
    if (scrollTop > 0) {
      touchStartRef.current = { y: 0, scrollTop: 0 };
      reset();
      return;
    }

    const currentY = e.touches[0].clientY;
    const deltaY = currentY - touchStartRef.current.y;

    // Only respond to downward pulls
    if (deltaY > 0) {
      // Apply resistance to make it feel natural
      const resistedDistance = deltaY * resistance;
      const clampedDistance = Math.min(resistedDistance, maxPull);

      setPullDistance(clampedDistance);
      const progress = updatePullProgress(clampedDistance);

      // Update state based on pull distance
      if (clampedDistance >= threshold) {
        setPullState(PULL_STATES.READY);
        // Haptic feedback when reaching threshold
        if (pullState !== PULL_STATES.READY) {
          triggerHaptic([30, 20, 30]);
        }
      } else if (clampedDistance > 0) {
        setPullState(PULL_STATES.PULLING);
      }

      // Prevent default to avoid scroll bounce on iOS
      if (progress > 0.1) {
        e.preventDefault();
      }
    }
  }, [disabled, threshold, maxPull, resistance, updatePullProgress, reset, triggerHaptic, pullState]);

  const handleTouchEnd = useCallback(() => {
    if (disabled || isRefreshingRef.current) return;

    const shouldRefresh = pullState === PULL_STATES.READY;

    if (shouldRefresh) {
      setPullDistance(threshold); // Snap to threshold position
      refresh();
    } else {
      reset();
    }

    touchStartRef.current = { y: 0, scrollTop: 0 };
  }, [disabled, pullState, threshold, refresh, reset]);

  const handleTouchCancel = useCallback(() => {
    if (disabled) return;
    reset();
    touchStartRef.current = { y: 0, scrollTop: 0 };
  }, [disabled, reset]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      reset();
    };
  }, [reset]);

  return {
    pullState,
    pullProgress, // 0 to 1
    pullDistance, // pixels
    isRefreshing: pullState === PULL_STATES.REFRESHING,
    isPulling: pullState === PULL_STATES.PULLING || pullState === PULL_STATES.READY,
    isReady: pullState === PULL_STATES.READY,
    isDone: pullState === PULL_STATES.DONE,
    handlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
      onTouchCancel: handleTouchCancel,
    },
    containerRef,
    refresh,
    reset,
  };
}

/**
 * usePullToRefreshWithScroll - Variant that works with custom scroll containers
 */
export function usePullToRefreshWithScroll({
  scrollContainerRef,
  ...options
} = {}) {
  const pullToRefresh = usePullToRefresh(options);

  // Use provided container ref
  useEffect(() => {
    if (scrollContainerRef) {
      pullToRefresh.containerRef.current = scrollContainerRef.current;
    }
  }, [scrollContainerRef, pullToRefresh.containerRef]);

  return pullToRefresh;
}

export default usePullToRefresh;
