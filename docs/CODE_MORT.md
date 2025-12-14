# Inventaire du Code Mort

**Document d'analyse — Version 1.1 — Décembre 2025**

Ce document liste le code non utilisé ou partiellement connecté dans le projet.

---

## Résumé Mis à Jour

| Catégorie | État |
|-----------|------|
| Pages Intelligence | ✅ Toutes connectées (InventoryIntelligence, Margins, Cockpit, etc.) |
| Bank Reconciliation UI | ✅ Page créée et connectée (`BankReconciliationPage.jsx`) |
| Audit Trail UI | ✅ Page créée et connectée (`AuditTrailPage.jsx`) |
| API Client | ⚠️ ~15 fonctions utilisent appels directs au lieu des hooks |
| Rules Engine UI | ⚠️ Partiellement connecté via FinanceRulesPage |
| Hooks TanStack Query | ⚠️ ~50% des pages utilisent les hooks |

---

## 1. Fonctions API Client - État Actuel

### 1.1 Inventory Intelligence (8 fonctions) ✅ CONNECTÉES

**Page** : `features/intelligence/InventoryIntelligencePage.jsx`

```javascript
// ✅ UTILISÉES - Appels directs (à refactoriser vers hooks)
calculateEOQ                      // → POST /inventory-intelligence/eoq
calculateSafetyStock              // → POST /inventory-intelligence/safety-stock
fetchReorderPoints                // → GET /inventory-intelligence/reorder-points
fetchStockoutPredictions          // → GET /inventory-intelligence/stockout-predictions
fetchDeadStock                    // → GET /inventory-intelligence/dead-stock
fetchABCXYZClassification         // → GET /inventory-intelligence/abc-xyz
fetchReorderSuggestions           // → GET /inventory-intelligence/reorder-suggestions
fetchInventoryIntelligenceSummary // → GET /inventory-intelligence/summary
```

**Action** : Créer hook `useInventoryIntelligence.js`

---

### 1.2 Bank Reconciliation (8 fonctions) ✅ CONNECTÉES

**Page** : `features/finance/BankReconciliationPage.jsx`
**Hook** : `hooks/useBankReconciliation.js`

```javascript
// ✅ UTILISÉES via hook useBankReconciliation
runBankReconciliation             // → POST /bank-reconciliation/run
fetchUnmatchedTransactions        // → GET /bank-reconciliation/unmatched/transactions
fetchUnmatchedInvoices            // → GET /bank-reconciliation/unmatched/invoices
createManualMatch                 // → POST /bank-reconciliation/match/manual
fetchSupplierAliases              // → GET /bank-reconciliation/aliases
createSupplierAlias               // → POST /bank-reconciliation/aliases
deleteSupplierAlias               // → DELETE /bank-reconciliation/aliases/{id}
fetchReconciliationSummary        // → GET /bank-reconciliation/summary
```

---

### 1.3 Audit Trail (10 fonctions) ✅ CONNECTÉES

**Page** : `features/admin/AuditTrailPage.jsx`
**Hook** : `hooks/useAuditTrail.js`

```javascript
// ✅ UTILISÉES via hook useAuditTrail
fetchAuditEntries                 // → GET /audit-trail/entries
searchAuditEntries                // → POST /audit-trail/search
fetchEntityHistory                // → GET /audit-trail/entity/{entity}/{id}
fetchUserActivity                 // → GET /audit-trail/user/{id}
generateAuditReport               // → GET /audit-trail/report
fetchSecurityEvents               // → GET /audit-trail/security-events
fetchRecentChanges                // → GET /audit-trail/recent-changes
exportUserDataRGPD                // → GET /audit-trail/rgpd/export/{id}
anonymizeUserDataRGPD             // → DELETE /audit-trail/rgpd/anonymize/{id}
fetchAuditSummary                 // → GET /audit-trail/summary
```

---

### 1.4 Forecasting (5 fonctions) ✅ CONNECTÉES

**Page** : `features/intelligence/ForecastPage.jsx`

```javascript
// ✅ UTILISÉES - Appels directs (à refactoriser vers hooks)
forecastSales                     // → POST /forecasting/sales
fetchStockDepletionForecast       // → GET /forecasting/stock-depletion
fetchCashFlowForecast             // → GET /forecasting/cash-flow
fetchPriceTrendForecast           // → GET /forecasting/price-trend
fetchForecastingSummary           // → GET /forecasting/summary
```

**Action** : Créer hook `useForecasting.js`

---

### 1.5 Anomaly Detection (7 fonctions) ✅ CONNECTÉES

**Page** : `features/intelligence/AnomaliesPage.jsx`

```javascript
// ✅ UTILISÉES - Appels directs (à refactoriser vers hooks)
scanForAnomalies                  // → POST /anomaly-detection/scan
detectTransactionOutliers         // → GET /anomaly-detection/outliers
detectDuplicateInvoices           // → GET /anomaly-detection/duplicates
detectInvoiceSequenceGaps         // → GET /anomaly-detection/sequence-gaps
detectRoundAmounts                // → GET /anomaly-detection/round-amounts
fetchAnomalySummary               // → GET /anomaly-detection/summary
resolveAnomaly                    // → POST /anomaly-detection/resolve
```

**Action** : Créer hook `useAnomalyDetection.js`

---

### 1.6 Supplier Scoring (7 fonctions) ✅ CONNECTÉES

**Page** : `features/intelligence/ScoringPage.jsx`

```javascript
// ✅ UTILISÉES - Appels directs (à refactoriser vers hooks)
fetchSupplierScore                // → GET /supplier-scoring/supplier/{id}
fetchSuppliersRanking             // → GET /supplier-scoring/ranking
compareSuppliers                  // → POST /supplier-scoring/compare
recordSupplierDelivery            // → POST /supplier-scoring/delivery
recordSupplierInvoiceIssue        // → POST /supplier-scoring/invoice-issue
fetchScoringDimensions            // → GET /supplier-scoring/dimensions
fetchSupplierScoreHistory         // → GET /supplier-scoring/history/{id}
```

**Action** : Créer hook `useSupplierScoring.js`

---

### 1.7 Margins (7 fonctions) ✅ CONNECTÉES

**Page** : `features/intelligence/MarginsPage.jsx`

```javascript
// ✅ UTILISÉES - Appels directs (à refactoriser vers hooks)
calculateMargin                   // → POST /margins/calculate
fetchProductMargins               // → GET /margins/products
fetchCategoryMargins              // → GET /margins/categories
fetchProductPAMP                  // → GET /margins/pamp/{product_id}
fetchDishMargins                  // → GET /margins/dishes
fetchMarginAlerts                 // → GET /margins/alerts
fetchMarginSummary                // → GET /margins/summary
```

**Action** : Créer hook `useMargins.js`

---

### 1.8 Rules Engine (8 fonctions) ⚠️ PARTIELLEMENT

**Page** : `features/finance/FinanceRulesPage.jsx` (partiel)

```javascript
// ⚠️ PARTIELLEMENT UTILISÉES
classifyTransaction               // Non utilisé directement
classifyTransactionsBatch         // Non utilisé directement
fetchClassificationRules          // Via FinanceRulesPage
createClassificationRule          // Non utilisé directement
recordClassificationFeedback      // Non utilisé directement
bootstrapDefaultRules             // Non utilisé directement
fetchClassificationStats          // Non utilisé directement
suggestCategory                   // Non utilisé directement
```

**Action** : Intégrer dans FinanceTransactionsPage pour suggestions auto

---

### 1.9 Cockpit (5 fonctions) ✅ CONNECTÉES

**Page** : `features/cockpit/CockpitPage.jsx`

```javascript
// ✅ UTILISÉES - Appels directs (à refactoriser vers hooks)
fetchCockpitOverview              // → GET /cockpit/overview
fetchCockpitLiveKPIs              // → GET /cockpit/kpis/live
fetchCockpitAlerts                // → GET /cockpit/alerts
acknowledgeCockpitAlert           // → POST /cockpit/alerts/{id}/acknowledge
fetchCockpitHealth                // → GET /cockpit/health
```

**Action** : Créer hook `useCockpit.js`

---

## 2. Hooks à Créer (Phase 4)

| Hook | Fonctions API | Page cible |
|------|---------------|------------|
| `useInventoryIntelligence.js` | 8 fonctions | InventoryIntelligencePage |
| `useForecasting.js` | 5 fonctions | ForecastPage |
| `useAnomalyDetection.js` | 7 fonctions | AnomaliesPage |
| `useSupplierScoring.js` | 7 fonctions | ScoringPage |
| `useMargins.js` | 7 fonctions | MarginsPage |
| `useCockpit.js` | 5 fonctions | CockpitPage |

**Total** : 6 hooks à créer, ~39 fonctions à encapsuler

---

## 3. Pages par État de Refactoring

### ✅ Utilisant Hooks TanStack Query

| Page | Hook utilisé |
|------|--------------|
| `BankReconciliationPage.jsx` | `useBankReconciliation` |
| `AuditTrailPage.jsx` | `useAuditTrail` |
| `FinanceTransactionsPage.jsx` | `useFinance` |
| `CatalogPage.jsx` | `useProducts` |
| `DashboardPage.jsx` | `useDashboard` |

### ⚠️ Appels API Directs (à refactoriser)

| Page | Hook à utiliser |
|------|-----------------|
| `InventoryIntelligencePage.jsx` | → `useInventoryIntelligence` |
| `ForecastPage.jsx` | → `useForecasting` |
| `AnomaliesPage.jsx` | → `useAnomalyDetection` |
| `ScoringPage.jsx` | → `useSupplierScoring` |
| `MarginsPage.jsx` | → `useMargins` |
| `CockpitPage.jsx` | → `useCockpit` |

---

## 4. Modules Core - État

| Module | Statut | UI Connectée |
|--------|--------|--------------|
| `event_sourcing.py` | ✅ Actif | Backend only |
| `rules_engine.py` | ✅ Actif | FinanceRulesPage |
| `supplier_scoring.py` | ✅ Actif | ScoringPage |
| `anomaly_detection.py` | ✅ Actif | AnomaliesPage |
| `bank_reconciliation.py` | ✅ Actif | BankReconciliationPage |
| `margin_calculator.py` | ✅ Actif | MarginsPage |
| `forecasting.py` | ✅ Actif | ForecastPage |
| `inventory_intelligence.py` | ✅ Actif | InventoryIntelligencePage |
| `audit_trail.py` | ✅ Actif | AuditTrailPage |
| `analytic_accounting.py` | ⚠️ Dormant | Pas de page dédiée |

---

## 5. Prochaines Étapes Phase 4

1. ✅ ~~Créer BankReconciliationPage~~
2. ✅ ~~Créer AuditTrailPage~~
3. ✅ ~~Créer hooks useBankReconciliation et useAuditTrail~~
4. 🔄 Créer les 6 hooks manquants
5. 🔄 Refactoriser les 6 pages Intelligence/Cockpit
6. 🔄 Unifier la navigation entre tenants
7. ⏳ Migration TypeScript (optionnel)

---

**Dernière mise à jour** : 10 Décembre 2025
