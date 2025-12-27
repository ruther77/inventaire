# Liste des fichiers à documenter - Frontend

**Total: 420 fichiers JavaScript/JSX**
**Documentés: 9 hooks essentiels**
**Restants: 411 fichiers**

---

## PRIORITÉ 1: Hooks métier (45 restants / 54 total)

### ✅ Hooks documentés (9)

1. ✅ `/frontend/src/hooks/useAuth.js`
2. ✅ `/frontend/src/hooks/useFinance.js`
3. ✅ `/frontend/src/hooks/useInvoiceImport.js`
4. ✅ `/frontend/src/hooks/useStock.js`
5. ✅ `/frontend/src/hooks/useDebounce.js`
6. ✅ `/frontend/src/hooks/useLocalStorage.js`
7. ✅ `/frontend/src/hooks/useClickOutside.js`
8. ✅ `/frontend/src/hooks/useCategories.js`
9. ✅ `/frontend/src/hooks/useProducts.js`
10. ✅ `/frontend/src/hooks/useDashboard.js`
11. ✅ `/frontend/src/hooks/useSuppliers.js`

### ⏳ Hooks à documenter (43)

**Hooks business critiques:**
12. ⏳ `/frontend/src/hooks/useRestaurant.js`
13. ⏳ `/frontend/src/hooks/useCheckout.js`
14. ⏳ `/frontend/src/hooks/useCatalogMutations.js`
15. ⏳ `/frontend/src/hooks/useFinanceCategories.js`
16. ⏳ `/frontend/src/hooks/useFinanceImports.js`
17. ⏳ `/frontend/src/hooks/useBankReconciliation.js`
18. ⏳ `/frontend/src/hooks/useSupplierScoring.js`

**Hooks intelligence/analytics:**
19. ⏳ `/frontend/src/hooks/useAnomalyDetection.js`
20. ⏳ `/frontend/src/hooks/useForecasting.js`
21. ⏳ `/frontend/src/hooks/useMargins.js`
22. ⏳ `/frontend/src/hooks/useInventoryIntelligence.js`
23. ⏳ `/frontend/src/hooks/useCockpit.js`
24. ⏳ `/frontend/src/hooks/usePortfolio.js`
25. ⏳ `/frontend/src/hooks/useReports.js`

**Hooks admin/audit:**
26. ⏳ `/frontend/src/hooks/useAdmin.js`
27. ⏳ `/frontend/src/hooks/useAudit.js`
28. ⏳ `/frontend/src/hooks/useAuditTrail.js`
29. ⏳ `/frontend/src/hooks/useMaintenance.js`

**Hooks UI/UX:**
30. ⏳ `/frontend/src/hooks/useAccessibility.js`
31. ⏳ `/frontend/src/hooks/useMediaQuery.js`
32. ⏳ `/frontend/src/hooks/useMobileNav.js`
33. ⏳ `/frontend/src/hooks/usePersistedFilters.js`
34. ⏳ `/frontend/src/hooks/useQueryConfig.js`
35. ⏳ `/frontend/src/hooks/usePageData.js`

**Hooks techniques:**
36. ⏳ `/frontend/src/hooks/useOffline.js`
37. ⏳ `/frontend/src/hooks/useOfflineMutation.js`
38. ⏳ `/frontend/src/hooks/usePWA.js`
39. ⏳ `/frontend/src/hooks/usePushNotifications.js`
40. ⏳ `/frontend/src/hooks/usePullToRefresh.js`
41. ⏳ `/frontend/src/hooks/useOptimistic.js`

**Hooks spécialisés:**
42. ⏳ `/frontend/src/hooks/useBarcodeScanner.js`
43. ⏳ `/frontend/src/hooks/usePDFFile.js`
44. ⏳ `/frontend/src/hooks/useGestures.js`
45. ⏳ `/frontend/src/hooks/useVirtualization.jsx`
46. ⏳ `/frontend/src/hooks/usePrefetch.jsx`
47. ⏳ `/frontend/src/hooks/useHotkeys.jsx`
48. ⏳ `/frontend/src/hooks/useImportProgress.jsx`
49. ⏳ `/frontend/src/hooks/useCommandBarLiveSuggestions.js`

**Hooks inventory/stock:**
50. ⏳ `/frontend/src/hooks/useInventorySummary.js`
51. ⏳ `/frontend/src/hooks/useSupplyPlan.js`
52. ⏳ `/frontend/src/hooks/usePriceHistory.js`

**Autres hooks:**
53. ⏳ `/frontend/src/hooks/index.js` (fichier barrel export)

---

## PRIORITÉ 2: Pages features (environ 80 fichiers)

### Dashboard
- ⏳ `/frontend/src/features/dashboard/DashboardPage.jsx`
- ⏳ `/frontend/src/features/dashboard/components/DashboardHero.jsx`
- ⏳ `/frontend/src/features/dashboard/components/DashboardMetrics.jsx`
- ⏳ `/frontend/src/features/dashboard/components/DashboardCharts.jsx`
- ⏳ `/frontend/src/features/dashboard/components/DashboardLists.jsx`
- ⏳ `/frontend/src/features/dashboard/components/ProductLookup.jsx`
- ⏳ `/frontend/src/features/dashboard/components/FiltersPanel.jsx`
- ⏳ `/frontend/src/features/dashboard/components/StockCards.jsx`

### Finance/Trésorerie
- ⏳ `/frontend/src/features/finance/FinanceTransactionsPage.jsx`
- ⏳ `/frontend/src/features/finance/FinanceOverview.jsx`
- ⏳ `/frontend/src/features/finance/FinanceUnifiedPage.jsx`
- ⏳ `/frontend/src/features/finance/FinanceAccountsPage.jsx`
- ⏳ `/frontend/src/features/finance/FinanceImportsPage.jsx`
- ⏳ `/frontend/src/features/finance/FinanceRulesPage.jsx`
- ⏳ `/frontend/src/features/finance/FinanceAnomaliesPage.jsx`
- ⏳ `/frontend/src/features/finance/BankReconciliationPage.jsx`
- ⏳ `/frontend/src/features/finance/FinanceSupplierPortfolioPage.jsx`
- ⏳ `/frontend/src/features/finance/components/TransactionFilters.jsx`
- ⏳ `/frontend/src/features/finance/components/BulkCategorizeModal.jsx`
- ⏳ `/frontend/src/features/finance/components/CategoryInlineEdit.jsx`
- ⏳ `/frontend/src/features/finance/components/RecoAnomaliesTable.jsx`
- ⏳ `/frontend/src/features/finance/components/ReconciliationSplitView.jsx`
- ⏳ `/frontend/src/features/finance/components/ImportStepper.jsx`

### Factures (Invoices)
- ⏳ `/frontend/src/features/invoices/ImportPage.jsx`
- ⏳ `/frontend/src/features/invoices/InvoicesListPage.jsx`
- ⏳ `/frontend/src/features/invoices/INTEGRATION_EXAMPLE.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceUploadCard.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceLinesEditor.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceImportActions.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceProcessingCard.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoicePDFWorkspace.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceZeroClickUpload.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceImportWithToast.jsx`
- ⏳ `/frontend/src/features/invoices/components/ProductMatchSuggestions.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceHistoryPanel.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceHistoryTable.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceDocumentSelector.jsx`
- ⏳ `/frontend/src/features/invoices/components/InvoiceList.jsx`
- ⏳ `/frontend/src/features/invoices/components/ImportSessionsView.jsx`

### Catalogue
- ⏳ `/frontend/src/features/catalog/CatalogPage.jsx`
- ⏳ `/frontend/src/features/catalog/CatalogSmartDemo.jsx`

### Stock/Inventory
- ⏳ `/frontend/src/features/stock/StockPage.jsx`
- ⏳ `/frontend/src/features/stock/StockMovementsPage.jsx`
- ⏳ `/frontend/src/features/stock/components/StockScannerPanel.jsx`

### Restaurant
- ⏳ `/frontend/src/features/restaurant/RestaurantDashboard.jsx`
- ⏳ `/frontend/src/features/restaurant/RestaurantOverviewPage.jsx`
- ⏳ `/frontend/src/features/restaurant/RestaurantMenuPage.jsx`
- ⏳ `/frontend/src/features/restaurant/IngredientsPage.jsx`
- ⏳ `/frontend/src/features/restaurant/PlatsCatalogPage.jsx`
- ⏳ `/frontend/src/features/restaurant/FoodCostAnalysisPage.jsx`
- ⏳ `/frontend/src/features/restaurant/RestaurantPriceTrends.jsx`
- ⏳ `/frontend/src/features/restaurant/RestaurantPriceHistoryComparisonPage.jsx`
- ⏳ `/frontend/src/features/restaurant/components/*` (environ 12 composants)

### Intelligence/Analytics
- ⏳ `/frontend/src/features/intelligence/IntelligencePage.jsx`
- ⏳ `/frontend/src/features/intelligence/IntelligenceUnifiedPage.jsx`
- ⏳ `/frontend/src/features/intelligence/AnomaliesPage.jsx`
- ⏳ `/frontend/src/features/intelligence/AnomalyDetectionPage.jsx`
- ⏳ `/frontend/src/features/intelligence/ForecastPage.jsx`
- ⏳ `/frontend/src/features/intelligence/ForecastingPage.jsx`
- ⏳ `/frontend/src/features/intelligence/MarginsPage.jsx`
- ⏳ `/frontend/src/features/intelligence/InventoryIntelligencePage.jsx`
- ⏳ `/frontend/src/features/intelligence/ScoringPage.jsx`
- ⏳ `/frontend/src/features/intelligence/SupplierScoringOverviewPage.jsx`
- ⏳ `/frontend/src/features/intelligence/components/*`

### Treasury
- ⏳ `/frontend/src/features/treasury/BankStatementPage.jsx`
- ⏳ `/frontend/src/features/treasury/components/TreasurySummary.jsx`
- ⏳ `/frontend/src/features/treasury/components/AccountsTab.jsx`
- ⏳ `/frontend/src/features/treasury/components/TransactionsTab.jsx`
- ⏳ `/frontend/src/features/treasury/components/ImportsTab.jsx`
- ⏳ `/frontend/src/features/treasury/components/RulesTab.jsx`

### Autres features
- ⏳ `/frontend/src/features/operations/OperationsPage.jsx`
- ⏳ `/frontend/src/features/operations/OperationsPilotage.jsx`
- ⏳ `/frontend/src/features/prices/PricesPage.jsx`
- ⏳ `/frontend/src/features/supply/SupplyPage.jsx`
- ⏳ `/frontend/src/features/auth/LoginPage.jsx`
- ⏳ `/frontend/src/features/admin/AdminPage.jsx`
- ⏳ `/frontend/src/features/admin/AuditTrailPage.jsx`
- ⏳ `/frontend/src/features/audit/AuditPage.jsx`
- ⏳ `/frontend/src/features/reports/ReportsPage.jsx`
- ⏳ `/frontend/src/features/portfolio/PortfolioPage.jsx`
- ⏳ `/frontend/src/features/cockpit/CockpitPage.jsx`
- ⏳ `/frontend/src/features/cockpit/CockpitUnifiedPage.jsx`
- ⏳ `/frontend/src/features/pos/PosPage.jsx`
- ⏳ `/frontend/src/features/pos/BarcodeScannerPanel.jsx`
- ⏳ `/frontend/src/features/scanner/ScannerPage.jsx`
- ⏳ `/frontend/src/features/legacy/LegacyToolsPage.jsx`
- ⏳ `/frontend/src/features/maintenance/MaintenancePage.jsx`

---

## PRIORITÉ 3: API Client (1 fichier critique)

- ⏳ `/frontend/src/api/client.js` - **CRITIQUE**: toutes les fonctions d'API

---

## PRIORITÉ 4: Composants UI réutilisables (environ 80 fichiers)

### Layout
- ⏳ `/frontend/src/components/layout/PageLayout.jsx`
- ⏳ `/frontend/src/components/layout/PageWrapper.jsx`
- ⏳ `/frontend/src/components/layout/PageHeader.jsx`
- ⏳ `/frontend/src/components/layout/TabNav.jsx`
- ⏳ `/frontend/src/components/layout/CommandBar.jsx`
- ⏳ `/frontend/src/components/layout/BottomNav.jsx`
- ⏳ `/frontend/src/components/layout/MobileBottomNav.jsx`
- ⏳ `/frontend/src/components/layout/MobileMoreMenu.jsx`
- ⏳ `/frontend/src/components/layout/ProgressiveDisclosure.jsx`
- ⏳ `/frontend/src/components/layout/AdaptiveDensity.jsx`

### UI Core
- ⏳ `/frontend/src/components/ui/Button.jsx`
- ⏳ `/frontend/src/components/ui/Card.jsx`
- ⏳ `/frontend/src/components/ui/Input.jsx`
- ⏳ `/frontend/src/components/ui/Select.jsx`
- ⏳ `/frontend/src/components/ui/Modal.jsx`
- ⏳ `/frontend/src/components/ui/Badge.jsx`
- ⏳ `/frontend/src/components/ui/Tooltip.jsx`
- ⏳ `/frontend/src/components/ui/Toast.jsx`
- ⏳ `/frontend/src/components/ui/Skeleton.jsx`
- ⏳ `/frontend/src/components/ui/EmptyState.jsx`
- ⏳ `/frontend/src/components/ui/DataTable.jsx`
- ⏳ `/frontend/src/components/ui/Charts.jsx`
- ⏳ `/frontend/src/components/ui/Grid.jsx`
- ⏳ `/frontend/src/components/ui/SectionHeader.jsx`
- ⏳ `/frontend/src/components/ui/AnimatedMetricCard.jsx`
- ⏳ `/frontend/src/components/ui/MegaSectionNav.jsx`
- ⏳ `/frontend/src/components/ui/GlassCard.jsx`
- (+ environ 50 autres composants UI)

### Feedback
- ⏳ `/frontend/src/components/feedback/LoadingOverlay.jsx`
- ⏳ `/frontend/src/components/feedback/NotificationCenter.jsx`
- ⏳ `/frontend/src/components/feedback/ConfirmDialog.jsx`
- ⏳ `/frontend/src/components/feedback/EmptyState.jsx`
- ⏳ `/frontend/src/components/feedback/ErrorBoundary.jsx`
- ⏳ `/frontend/src/components/feedback/RetryableError.jsx`
- ⏳ `/frontend/src/components/feedback/QueryErrorState.jsx`
- ⏳ `/frontend/src/components/feedback/ActionableEmptyStates.jsx`
- ⏳ `/frontend/src/components/feedback/Toast.jsx`
- ⏳ `/frontend/src/components/feedback/OfflineBanner.jsx`

### Modals
- ⏳ `/frontend/src/components/modals/AddProductModal.jsx`
- ⏳ `/frontend/src/components/modals/EditProductModal.jsx`
- ⏳ `/frontend/src/components/modals/AddSupplierModal.jsx`
- ⏳ `/frontend/src/components/modals/SupplierModal.jsx`
- ⏳ `/frontend/src/components/modals/StockAdjustmentModal.jsx`
- ⏳ `/frontend/src/components/modals/CreateOrderModal.jsx`
- ⏳ `/frontend/src/components/modals/InvoiceImportModal.jsx`
- ⏳ `/frontend/src/components/modals/ProductDetailDrawer.jsx`

### Smart Components
- ⏳ `/frontend/src/components/smart/SmartTable.jsx`
- ⏳ `/frontend/src/components/smart/SmartDrawer.jsx`
- ⏳ `/frontend/src/components/smart/SmartFilters.jsx`

### AI Components
- ⏳ `/frontend/src/components/ai/ConfidenceBadge.jsx`
- ⏳ `/frontend/src/components/ai/QuickAction.jsx`
- ⏳ `/frontend/src/components/ai/AlertCard.jsx`
- ⏳ `/frontend/src/components/ai/SuggestionCard.jsx`
- ⏳ `/frontend/src/components/ai/ImpactPreview.jsx`
- ⏳ `/frontend/src/components/ai/ReconciliationSuggestion.jsx`
- ⏳ `/frontend/src/components/ai/DecisionPanel.jsx`

### Accessibility
- ⏳ `/frontend/src/components/accessibility/SkipLinks.jsx`
- ⏳ `/frontend/src/components/accessibility/AccessibleModal.jsx`

### Animations
- ⏳ `/frontend/src/components/animations/AnimatedComponents.jsx`
- ⏳ `/frontend/src/components/animations/Transitions.jsx`
- ⏳ `/frontend/src/components/animations/PageTransition.jsx`

### PWA
- ⏳ `/frontend/src/components/pwa/InstallPWAButton.jsx`
- ⏳ `/frontend/src/components/pwa/NotificationPermissionButton.jsx`
- ⏳ `/frontend/src/components/pwa/PushNotificationsDemo.jsx`

### PDF
- ⏳ `/frontend/src/components/pdf/PDFViewerWrapper.jsx`

---

## PRIORITÉ 5: Configuration App (environ 10 fichiers)

- ⏳ `/frontend/src/App.jsx`
- ⏳ `/frontend/src/main.jsx`
- ⏳ `/frontend/src/app/AppShell.jsx`
- ⏳ `/frontend/src/app/RestaurantAppShell.jsx`
- ⏳ `/frontend/src/app/routes.jsx`
- ⏳ `/frontend/src/app/SidebarNav.jsx`
- ⏳ `/frontend/src/app/TopBar.jsx`
- ⏳ `/frontend/src/components/SidebarNav.jsx`

---

## PRIORITÉ 6: Contextes (environ 5 fichiers)

- ⏳ `/frontend/src/context/AuthContext.jsx`
- ⏳ `/frontend/src/context/TenantContext.jsx`
- ⏳ `/frontend/src/contexts/FeedbackContext.jsx`
- ⏳ `/frontend/src/contexts/OfflineContext.jsx`
- ⏳ `/frontend/src/contexts/CommandBarContext.jsx`

---

## PRIORITÉ 7: Utilitaires (environ 10 fichiers)

- ⏳ `/frontend/src/utils/banking.js`
- ⏳ `/frontend/src/utils/sessionManager.js`
- ⏳ `/frontend/src/utils/dateUtils.js`
- ⏳ `/frontend/src/services/offlineStorage.js`
- ⏳ `/frontend/src/ui/motion.js`
- ⏳ `/frontend/src/components/ui/design-tokens.js`
- ⏳ `/frontend/src/newCMS/utils/format.js`

---

## PRIORITÉ 8: Modules (environ 40 fichiers)

- ⏳ Tous les fichiers dans `/frontend/src/modules/*`
- ⏳ Tous les fichiers dans `/frontend/src/newCMS/*`

---

## PRIORITÉ 9: Examples et Tests (environ 20 fichiers)

- ⏳ `/frontend/src/examples/*`
- ⏳ Tous les fichiers `*.test.js` et `*.test.jsx`
- ⏳ Tous les fichiers `*.story.jsx` et `*.stories.jsx`
- ⏳ `/frontend/src/test/setup.js`

---

## PRIORITÉ 10: Fichiers index.js (barrels)

- ⏳ Tous les fichiers `index.js` (exports)

---

## Commandes utiles

### Compter les fichiers par dossier

```bash
# Hooks
find frontend/src/hooks -name "*.js" -o -name "*.jsx" | wc -l

# Features
find frontend/src/features -name "*.js" -o -name "*.jsx" | wc -l

# Components
find frontend/src/components -name "*.js" -o -name "*.jsx" | wc -l

# API
find frontend/src/api -name "*.js" | wc -l
```

### Lister les fichiers non documentés

```bash
# Rechercher les fichiers sans en-tête @module
find frontend/src -name "*.js" -o -name "*.jsx" | while read file; do
  if ! grep -q "@module" "$file"; then
    echo "$file"
  fi
done
```

---

## Progression

- ✅ **9 hooks documentés** (useAuth, useFinance, useInvoiceImport, useStock, useDebounce, useLocalStorage, useClickOutside, useCategories, useProducts, useDashboard, useSuppliers)
- ⏳ **411 fichiers restants**
- 📊 **Progression: 2.1%** (9/420)

**Objectif:** 100% des fichiers documentés avec JSDoc exhaustif en français
