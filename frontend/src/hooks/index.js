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
} from './useHotkeys.jsx';

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
} from './usePrefetch.jsx';

// Persisted Filters
export { default as usePersistedFilters } from './usePersistedFilters.js';

// Re-export des hooks existants
export { useProducts } from './useProducts.js';
export { useDashboardMetrics } from './useDashboard.js';

// Accessibility hooks
export {
  useReducedMotion,
  useFocusTrap,
  useAnnounce,
  useKeyboardShortcuts,
  useRovingTabIndex,
  useSkipLinks,
  useHighContrast,
} from './useAccessibility.js';

// Optimistic updates
export {
  useOptimisticMutation,
  useOptimisticList,
  useDebouncedMutation,
} from './useOptimistic.js';

// Virtualisation
export {
  useVirtualList,
  useDynamicVirtualList,
} from './useVirtualization.jsx';

// Extended prefetch
export {
  usePrefetchOnVisible,
  useStandaloneCache,
  cacheUtils,
} from './usePrefetch.jsx';

// Finance - Bank Reconciliation
export {
  useBankReconciliation,
  useReconciliationSummary,
  useUnmatchedTransactions,
  useUnmatchedInvoices,
  useSupplierAliases,
  useRunReconciliation,
  useCreateManualMatch,
  useCreateSupplierAlias,
  useDeleteSupplierAlias,
} from './useBankReconciliation.js';

// Finance - Transactions & Categorization Feedback (Phase 4)
export {
  useFinanceTransactions,
  useUpdateFinanceTransaction,
  useLockFinanceTransaction,
  useFinanceBatchCategorize,
  useFinanceImport,
  useFinanceImportPDF,
  useFinanceAccounts,
  useFinanceAccount,
  useCreateFinanceAccount,
  useUpdateFinanceAccount,
  useDeleteFinanceAccount,
  useDeduplicateTransactions,
  useRefreshFinanceStats,
  // Phase 4: Feedback ML Loop
  useCategoryFeedback,
  useCategoryFeedbackStats,
  useCommonCorrections,
} from './useFinance.js';

// Admin - Audit Trail
export {
  useAuditTrail,
  useAuditSummary,
  useAuditEntries,
  useSearchAuditEntries,
  useEntityHistory,
  useUserActivity,
  useSecurityEvents,
  useRecentChanges,
  useGenerateAuditReport,
  useExportUserDataRGPD,
  useAnonymizeUserDataRGPD,
} from './useAuditTrail.js';

// Intelligence - Inventory
export {
  useInventoryIntelligence,
  useInventoryIntelligenceSummary,
  useReorderPoints,
  useStockoutPredictions,
  useDeadStock,
  useABCXYZClassification,
  useReorderSuggestions,
  useCalculateEOQ,
  useCalculateSafetyStock,
} from './useInventoryIntelligence.js';

// Intelligence - Forecasting
export {
  useForecasting,
  useForecastingSummary,
  useStockDepletionForecast,
  useCashFlowForecast,
  usePriceTrendForecast,
  useForecastSales,
} from './useForecasting.js';

// Intelligence - Anomaly Detection
export {
  useAnomalyDetection,
  useAnomalySummary,
  useTransactionOutliers,
  useDuplicateInvoices,
  useInvoiceSequenceGaps,
  useRoundAmounts,
  useScanAnomalies,
  useResolveAnomaly,
} from './useAnomalyDetection.js';

// Intelligence - Supplier Scoring
export {
  useSupplierScoring,
  useSuppliersRanking,
  useSupplierScore,
  useSupplierScoreHistory,
  useScoringDimensions,
  useCompareSuppliers,
  useRecordDelivery,
  useRecordInvoiceIssue,
} from './useSupplierScoring.js';

// Intelligence - Margins
export {
  useMargins,
  useMarginSummary,
  useProductMargins,
  useCategoryMargins,
  useProductPAMP,
  useDishMargins,
  useMarginAlerts,
  useCalculateMargin,
} from './useMargins.js';

// Cockpit
export {
  useCockpit,
  useCockpitOverview,
  useCockpitLiveKPIs,
  useCockpitAlerts,
  useCockpitHealth,
  useAcknowledgeAlert,
} from './useCockpit.js';

// Portfolio
export {
  usePortfolio,
  useCapitalOverview,
} from './usePortfolio.js';

// Query Config - Retry & Offline
export {
  defaultQueryConfig,
  defaultMutationConfig,
  getErrorType,
  isRetryableError,
  useOnlineStatus,
  useRefetchOnReconnect,
  useManualRetry,
  createQueryOptions,
  errorMessages,
  useErrorMessage,
} from './useQueryConfig.js';

// CommandBar Live Suggestions
export {
  default as useCommandBarLiveSuggestions,
  useContextualSuggestions,
} from './useCommandBarLiveSuggestions.js';

// PDF File Management
export {
  usePDFFile,
  usePDFFileFromUpload,
} from './usePDFFile.js';

// Import Progress Notifications
export {
  useImportProgress,
  useZeroClickJobWithProgress,
} from './useImportProgress.jsx';

// Mobile Navigation
export { default as useMobileNav } from './useMobileNav.js';

// PWA
export { default as usePWA } from './usePWA.js';
export { default as usePushNotifications } from './usePushNotifications.js';

// Offline
export { useOffline } from './useOffline.js';
export {
  useOfflineMutation,
  useOfflineCreate,
  useOfflineUpdate,
  useOfflinePatch,
  useOfflineDelete,
} from './useOfflineMutation.js';

// Barcode Scanner
export { default as useBarcodeScanner } from './useBarcodeScanner.js';

// Gestures
export {
  useGestures,
  useSwipeable,
  useLongPress,
} from './useGestures.js';

// Pull to Refresh
export {
  default as usePullToRefresh,
  usePullToRefreshWithScroll,
  PULL_STATES,
} from './usePullToRefresh.js';
