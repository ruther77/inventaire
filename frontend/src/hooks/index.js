/**
 * Custom Hooks - Exports centralisés
 */

// Storage
export { default as useLocalStorage, useSessionStorage } from './useLocalStorage.js';

// Debounce & Throttle
export {
  default as useDebounce,
  useDebouncedCallback,
  useThrottle,
  useThrottledCallback,
  useDebouncedState,
} from './useDebounce.js';

// Keyboard
export {
  default as useHotkeys,
  useHotkeysMap,
  KeyboardShortcut,
} from './useHotkeys.js';

// Media Queries
export {
  default as useMediaQuery,
  useBreakpoint,
  useBreakpoints,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  usePrefersDarkMode,
  usePrefersReducedMotion,
  useOrientation,
  breakpoints,
} from './useMediaQuery.js';

// Click Outside
export {
  default as useClickOutside,
  useClickOutsideMultiple,
  useEscapeKey,
  useClickOutsideAndEscape,
} from './useClickOutside.js';

// Prefetch & Optimistic Updates
export {
  default as usePrefetch,
  usePrefetchOnIdle,
  usePrefetchRoute,
  createPrefetchLink,
  useOptimisticUpdate,
  useInfiniteScroll,
} from './usePrefetch.js';

// Persisted Filters
export { default as usePersistedFilters } from './usePersistedFilters.js';

// Re-export des hooks existants
export { useProducts, useProduct, useProductMutation } from './useProducts.js';
export { useDashboardMetrics } from './useDashboard.js';
