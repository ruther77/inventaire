/**
 * newCMS - Next-Gen Content Management System
 *
 * Architecture UX 2025 - 6 Vues Principales :
 * 1. Cockpit - Vue 360° Morning Brief
 * 2. Operations - Catalogue | Factures | Stock | Prix
 * 3. Finance - Transactions | Rapprochement | Comptes
 * 4. Restaurant - Menus | Charges | Stock | Prévisions
 * 5. Intelligence - Dashboard | Stock | Prévisions | Anomalies | Scoring
 * 6. Config - Règles | Audit | Utilisateurs
 *
 * + Centre de Notifications (Alertes Proactives)
 * + Multi-Tenant (Changement de Contexte)
 */

// Pages principales
export { default as CockpitPage } from './pages/CockpitPage.jsx';
export { default as OperationsPage } from './pages/OperationsPage.jsx';
export { default as FinancePage } from './pages/FinancePage.jsx';
export { default as RestaurantPage } from './pages/RestaurantPage.jsx';
export { default as IntelligencePage } from './pages/IntelligencePage.jsx';
export { default as ConfigPage } from './pages/ConfigPage.jsx';

// Centre de notifications
export { default as AlertsCenter } from './pages/AlertsCenter.jsx';

// Composants partagés
export * from './components';

// Layouts
export { default as CMSLayout } from './layouts/CMSLayout.jsx';
export { default as PageLayout } from './layouts/PageLayout.jsx';

// Routes
export { routes, navigationSections } from './routes.jsx';

// Hooks
export * from './hooks';

// Contexts
export { TenantProvider, useTenant } from './contexts/TenantContext.jsx';
export { AlertsProvider, useAlerts } from './contexts/AlertsContext.jsx';
