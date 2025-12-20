/**
 * Intelligence Module - Exports
 *
 * Plan de restructuration 2025-12 - Pages et composants du module Intelligence
 */

// Main Pages
export { default as IntelligencePage } from './IntelligencePage.jsx';
export { default as ForecastPage } from './ForecastPage.jsx';
export { default as AnomaliesPage } from './AnomaliesPage.jsx';
export { default as ScoringPage } from './ScoringPage.jsx';

// Supplier Scoring Pages (SUPPLIER_SCORING_FRONTEND_INTEGRATION.md)
export { default as SupplierScoringOverviewPage } from './SupplierScoringOverviewPage.jsx';
export { default as SuppliersListPage } from './SuppliersListPage.jsx';
export { default as SupplierDetailsPage } from './SupplierDetailsPage.jsx';
export { default as ScoringCriteriaPage } from './ScoringCriteriaPage.jsx';
export { default as SupplierAlertsPage } from './SupplierAlertsPage.jsx';

// Additional pages
export { default as InventoryIntelligencePage } from './InventoryIntelligencePage.jsx';
export { default as MarginsPage } from './MarginsPage.jsx';
export { default as ForecastingPage } from './ForecastingPage.jsx';
export { default as AnomalyDetectionPage } from './AnomalyDetectionPage.jsx';
export { default as IntelligenceUnifiedPage } from './IntelligenceUnifiedPage.jsx';

// Components
export * from './components/index.js';
