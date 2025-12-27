import { lazy, Suspense } from 'react';
import {
  Boxes,
  ShoppingBag,
  Activity,
  TrendingUp,
  Utensils,
  ReceiptText,
  Download,
  Landmark,
  Brain,
  AlertTriangle,
  Calculator,
  LineChart,
  Gauge,
  Link2,
  Settings,
  Wallet,
  FileText,
  BarChart3,
  Package,
  Users,
  Sparkles,
  Shield,
  Zap,
} from 'lucide-react';

// ============================================================================
// LAZY LOADING - Performance optimisée (100% lazy pour réduire bundle initial)
// ============================================================================

// Cockpit
const CockpitPage = lazy(() => import('@/features/cockpit/CockpitUnifiedPage.jsx'));

// Vues unifiées (Phase 2)
const OperationsPage = lazy(() => import('@/features/operations/OperationsPage.jsx'));
const FinanceUnifiedPage = lazy(() => import('@/features/finance/FinanceUnifiedPage.jsx'));
const IntelligenceUnifiedPage = lazy(() => import('@/features/intelligence/IntelligenceUnifiedPage.jsx'));

// Operations (pages individuelles)
const CatalogPage = lazy(() => import('@/features/catalog/CatalogPage.jsx'));
const ImportPage = lazy(() => import('@/features/invoices/ImportPage.jsx'));
const InvoicesListPage = lazy(() => import('@/features/invoices/InvoicesListPage.jsx'));
const PricesPage = lazy(() => import('@/features/prices/PricesPage.jsx'));
const StockPage = lazy(() => import('@/features/stock/StockPage.jsx'));
const StockMovementsPage = lazy(() => import('@/features/stock/StockMovementsPage.jsx'));
const SupplyPage = lazy(() => import('@/features/supply/SupplyPage.jsx'));

// Inventory
const ProductDetailPage = lazy(() => import('@/features/inventory/ProductDetailPage.jsx'));

// Restaurant (toutes les pages en lazy)
const RestaurantChargesPage = lazy(() => import('@/features/restaurant/RestaurantChargesPage.jsx'));
const RestaurantStockMovementsPage = lazy(() => import('@/features/restaurant/RestaurantStockMovementsPage.jsx'));
const RestaurantConsumptionPage = lazy(() => import('@/features/restaurant/RestaurantConsumptionPage.jsx'));
const ForecastsPage = lazy(() => import('@/features/restaurant/ForecastsPage.jsx'));
const PlatsCatalogPage = lazy(() => import('@/features/restaurant/PlatsCatalogPage.jsx'));
const IngredientsPage = lazy(() => import('@/features/restaurant/IngredientsPage.jsx'));
const FoodCostAnalysisPage = lazy(() => import('@/features/restaurant/FoodCostAnalysisPage.jsx'));
const LiensEpiceriePage = lazy(() => import('@/features/restaurant/LiensEpiceriePage.jsx'));

// Finances (pages individuelles)
const PortfolioPage = lazy(() => import('@/features/portfolio/PortfolioPage.jsx'));
const FinanceOverview = lazy(() => import('@/features/finance/FinanceOverview.jsx'));
const FinanceTransactionsPage = lazy(() => import('@/features/finance/FinanceTransactionsPage.jsx'));
const FinanceAccountsPage = lazy(() => import('@/features/finance/FinanceAccountsPage.jsx'));
const FinanceImportsPage = lazy(() => import('@/features/finance/FinanceImportsPage.jsx'));
const FinanceRulesPage = lazy(() => import('@/features/finance/FinanceRulesPage.jsx'));
const FinanceAnomaliesPage = lazy(() => import('@/features/finance/FinanceAnomaliesPage.jsx'));
const BankReconciliationPage = lazy(() => import('@/features/finance/BankReconciliationPage.jsx'));
const FinanceSupplierPortfolioPage = lazy(() => import('@/features/finance/FinanceSupplierPortfolioPage.jsx'));

// Intelligence (pages individuelles)
const SupplierScoringOverviewPage = lazy(() => import('@/features/intelligence/SupplierScoringOverviewPage.jsx'));
const SuppliersListPage = lazy(() => import('@/features/intelligence/SuppliersListPage.jsx'));
const SupplierDetailsPage = lazy(() => import('@/features/intelligence/SupplierDetailsPage.jsx'));
const ScoringCriteriaPage = lazy(() => import('@/features/intelligence/ScoringCriteriaPage.jsx'));
const SupplierAlertsPage = lazy(() => import('@/features/intelligence/SupplierAlertsPage.jsx'));

const IntelligencePage = lazy(() => import('@/features/intelligence/IntelligencePage.jsx'));
const InventoryIntelligencePage = lazy(() => import('@/features/intelligence/InventoryIntelligencePage.jsx'));
const ForecastPage = lazy(() => import('@/features/intelligence/ForecastPage.jsx'));
const AnomaliesPage = lazy(() => import('@/features/intelligence/AnomaliesPage.jsx'));
const MarginsPage = lazy(() => import('@/features/intelligence/MarginsPage.jsx'));

// Admin
const AuditTrailPage = lazy(() => import('@/features/admin/AuditTrailPage.jsx'));

// newCMS Demo
const NewCMSDemo = lazy(() => import('@/newCMS/Demo.jsx'));

// Loader avec animation
const PageLoader = () => (
  <div className="min-h-[60vh] flex items-center justify-center">
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-2 border-blue-500/20 border-t-blue-500 animate-spin" />
        <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-purple-500/20 border-b-purple-500 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
      </div>
      <p className="text-sm text-slate-500 animate-pulse">Chargement...</p>
    </div>
  </div>
);

const LazyPage = ({ children }) => (
  <Suspense fallback={<PageLoader />}>
    {children}
  </Suspense>
);

// ============================================================================
// NAVIGATION STRUCTURE UNIFIÉE 2025 - Phase 2
// ============================================================================

/**
 * Structure de navigation:
 * - COCKPIT : Vue 360° (page d'accueil)
 * - OPÉRATIONS : Vue unifiée avec onglets (Pilotage|Factures|Catalogue|Stock|Prix)
 * - FINANCES : Vue unifiée avec onglets (Trésorerie|Transactions|Comptes|Rapprochement)
 * - RESTAURANT : Menus, Charges, Consommations
 * - INTELLIGENCE : Vue unifiée avec onglets (Dashboard|Stock|Prévisions|Anomalies|Scoring|Marges)
 * - PARAMÈTRES : Audit, Règles
 */

// Section COCKPIT
export const cockpitRoute = {
  path: '/',
  label: 'Cockpit',
  description: 'Vue consolidée 360°',
  icon: Gauge,
  element: <LazyPage><CockpitPage /></LazyPage>,
  gradient: 'from-blue-500 to-purple-600',
};

// Section OPÉRATIONS - Vue unifiée principale
export const operationsUnifiedRoute = {
  path: '/operations',
  label: 'Opérations',
  description: 'Catalogue, Factures, Stock',
  icon: ShoppingBag,
  element: <LazyPage><OperationsPage /></LazyPage>,
  isUnified: true,
};

// Section OPÉRATIONS - Routes individuelles (rétrocompatibilité + liens directs)
export const operationsRoutes = [
  operationsUnifiedRoute,
  {
    path: '/operations/factures',
    label: 'Factures',
    description: 'Liste des factures',
    icon: FileText,
    element: <LazyPage><InvoicesListPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/operations/factures/import',
    label: 'Import Facture',
    description: 'Import → Stock',
    icon: FileText,
    element: <LazyPage><ImportPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/operations/catalogue',
    label: 'Catalogue',
    description: 'Produits & stocks',
    icon: Boxes,
    element: <LazyPage><CatalogPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/operations/stock',
    label: 'Stock',
    description: 'Gestion du stock',
    icon: Activity,
    element: <LazyPage><StockPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/operations/stock/mouvements',
    label: 'Mouvements',
    description: 'Entrées / Sorties',
    icon: Activity,
    element: <LazyPage><StockMovementsPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/operations/prix',
    label: 'Suivi Prix',
    description: 'Historique fournisseurs',
    icon: TrendingUp,
    element: <LazyPage><PricesPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/operations/approvisionnement',
    label: 'Approvisionnement',
    description: 'Plan de commandes',
    icon: Package,
    element: <LazyPage><SupplyPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/inventory/product/:productId',
    label: 'Fiche Produit',
    description: 'Detail produit',
    icon: Package,
    element: <LazyPage><ProductDetailPage /></LazyPage>,
    hidden: true,
  },
];

// Section FINANCES - Vue unifiée principale
export const financesUnifiedRoute = {
  path: '/finances',
  label: 'Finances',
  description: 'Trésorerie & Rapprochement',
  icon: Wallet,
  element: <LazyPage><FinanceUnifiedPage /></LazyPage>,
  isUnified: true,
};

// Section FINANCES - Routes individuelles (rétrocompatibilité + liens directs)
export const financesRoutes = [
  financesUnifiedRoute,
  {
    path: '/finances/tresorerie',
    label: 'Trésorerie',
    description: 'Flux consolidés',
    icon: Wallet,
    element: <LazyPage><FinanceOverview /></LazyPage>,
    hidden: true,
  },
  {
    path: '/finances/transactions',
    label: 'Transactions',
    description: 'Relevés & mouvements',
    icon: Activity,
    element: <LazyPage><FinanceTransactionsPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/finances/comptes',
    label: 'Comptes',
    description: 'Soldes & aperçu',
    icon: Landmark,
    element: <LazyPage><FinanceAccountsPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/finances/rapprochement',
    label: 'Rapprochement',
    description: 'Auto-matching',
    icon: Link2,
    element: <LazyPage><BankReconciliationPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/finances/portefeuille',
    label: 'Portefeuille',
    description: 'Capital & cash',
    icon: BarChart3,
    element: <LazyPage><PortfolioPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/finances/imports',
    label: 'Imports',
    description: 'CSV / PDF',
    icon: Download,
    element: <LazyPage><FinanceImportsPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/finances/fournisseurs',
    label: 'Portefeuille Fournisseurs',
    description: 'Encours & Échéances',
    icon: Users,
    element: <LazyPage><FinanceSupplierPortfolioPage /></LazyPage>,
    hidden: true,
  },
];

// Section RESTAURANT (structure simplifiée - pages essentielles uniquement)
export const restaurantRoutes = [
  {
    path: '/restaurant/food-cost',
    label: 'Food Cost',
    description: 'Analyse & optimisation',
    icon: BarChart3,
    element: <LazyPage><FoodCostAnalysisPage /></LazyPage>,
  },
  {
    path: '/restaurant/plats',
    label: 'Catalogue Plats',
    description: 'Marges & prix',
    icon: Utensils,
    element: <LazyPage><PlatsCatalogPage /></LazyPage>,
  },
  {
    path: '/restaurant/ingredients',
    label: 'Ingrédients',
    description: 'Prix & stocks',
    icon: Package,
    element: <LazyPage><IngredientsPage /></LazyPage>,
  },
  {
    path: '/restaurant/liens',
    label: 'Liens Épicerie',
    description: 'Ingrédients ↔ Produits',
    icon: Link2,
    element: <LazyPage><LiensEpiceriePage /></LazyPage>,
  },
  {
    path: '/restaurant/charges',
    label: 'Charges',
    description: 'Dépenses',
    icon: ReceiptText,
    element: <LazyPage><RestaurantChargesPage /></LazyPage>,
  },
  {
    path: '/restaurant/consommations',
    label: 'Consommations',
    description: 'Sorties & coûts',
    icon: Package,
    element: <LazyPage><RestaurantConsumptionPage /></LazyPage>,
  },
  {
    path: '/restaurant/stock',
    label: 'Stock',
    description: 'Mouvements',
    icon: Activity,
    element: <LazyPage><RestaurantStockMovementsPage /></LazyPage>,
  },
  {
    path: '/restaurant/previsions',
    label: 'Prévisions',
    description: 'Projections',
    icon: Sparkles,
    element: <LazyPage><ForecastsPage context="restaurant" /></LazyPage>,
  },
];

// Section INTELLIGENCE - Vue unifiée principale
export const intelligenceUnifiedRoute = {
  path: '/intelligence',
  label: 'Intelligence',
  description: 'IA & Analytics',
  icon: Brain,
  element: <LazyPage><IntelligenceUnifiedPage /></LazyPage>,
  isUnified: true,
};

// Section INTELLIGENCE - Routes individuelles (rétrocompatibilité + liens directs)
export const intelligenceRoutes = [
  intelligenceUnifiedRoute,
  {
    path: '/intelligence/dashboard',
    label: 'Dashboard IA',
    description: 'Vue consolidée',
    icon: Brain,
    element: <LazyPage><IntelligencePage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/stock',
    label: 'Stock Intelligent',
    description: 'EOQ, ABC-XYZ',
    icon: Zap,
    element: <LazyPage><InventoryIntelligencePage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/previsions',
    label: 'Prévisions',
    description: 'ML predictions',
    icon: LineChart,
    element: <LazyPage><ForecastPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/anomalies',
    label: 'Anomalies',
    description: 'Détection auto',
    icon: AlertTriangle,
    element: <LazyPage><AnomaliesPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/scoring',
    label: 'Scoring',
    description: 'Fournisseurs',
    icon: Users,
    element: <LazyPage><SupplierScoringOverviewPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/scoring/suppliers',
    label: 'Fournisseurs',
    icon: Package,
    element: <LazyPage><SuppliersListPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/scoring/suppliers/:supplierId',
    label: 'Détails fournisseur',
    icon: Users,
    element: <LazyPage><SupplierDetailsPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/scoring/criteria',
    label: 'Critères de scoring',
    icon: Settings,
    element: <LazyPage><ScoringCriteriaPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/scoring/alerts',
    label: 'Alertes fournisseurs',
    icon: AlertTriangle,
    element: <LazyPage><SupplierAlertsPage /></LazyPage>,
    hidden: true,
  },
  {
    path: '/intelligence/marges',
    label: 'Marges',
    description: 'PAMP & calculs',
    icon: Calculator,
    element: <LazyPage><MarginsPage /></LazyPage>,
    hidden: true,
  },
];

// Section PARAMÈTRES
export const settingsRoutes = [
  {
    path: '/parametres/audit',
    label: 'Audit Trail',
    description: 'Historique & sécurité',
    icon: Shield,
    element: <LazyPage><AuditTrailPage /></LazyPage>,
  },
  {
    path: '/parametres/regles',
    label: 'Règles',
    description: 'Catégorisation',
    icon: Settings,
    element: <LazyPage><FinanceRulesPage /></LazyPage>,
  },
  {
    path: '/parametres/anomalies',
    label: 'Alertes Finance',
    description: 'Rapprochement',
    icon: AlertTriangle,
    element: <LazyPage><FinanceAnomaliesPage /></LazyPage>,
  },
];

// ============================================================================
// NAVIGATION SECTIONS POUR SIDEBAR - Version simplifiée (vues unifiées)
// ============================================================================

export const navigationSections = [
  {
    id: 'cockpit',
    label: 'Cockpit',
    description: 'Vue 360°',
    icon: Gauge,
    routes: [cockpitRoute],
    isHome: true,
    directPath: '/',
    gradient: 'from-blue-500 to-cyan-400',
    color: 'blue',
  },
  {
    id: 'operations',
    label: 'Opérations',
    description: 'Stock & Factures',
    icon: ShoppingBag,
    routes: [
      {
        path: '/operations',
        label: 'Pilotage',
        description: 'Vue consolidée',
        icon: Gauge,
      },
      {
        path: '/operations/factures',
        label: 'Factures',
        description: 'Import → Stock',
        icon: FileText,
      },
      {
        path: '/operations/catalogue',
        label: 'Catalogue',
        description: 'Produits & stocks',
        icon: Boxes,
      },
      {
        path: '/operations/stock',
        label: 'Mouvements',
        description: 'Entrées / Sorties',
        icon: Activity,
      },
      {
        path: '/operations/prix',
        label: 'Suivi Prix',
        description: 'Historique fournisseurs',
        icon: TrendingUp,
      },
      {
        path: '/operations/approvisionnement',
        label: 'Approvisionnement',
        description: 'Plan de commandes',
        icon: Package,
      },
      {
        path: '/intelligence/scoring/suppliers',
        label: 'Fournisseurs',
        description: 'Gestion & Scoring',
        icon: Users,
      },
    ],
    gradient: 'from-emerald-500 to-teal-400',
    color: 'emerald',
  },
  {
    id: 'finances',
    label: 'Finances',
    description: 'Trésorerie & Marges',
    icon: Wallet,
    routes: [
      {
        path: '/finances',
        label: 'Trésorerie',
        description: 'Vue consolidée',
        icon: Wallet,
      },
      {
        path: '/finances/transactions',
        label: 'Transactions',
        description: 'Relevés & mouvements',
        icon: Activity,
      },
      {
        path: '/finances/comptes',
        label: 'Comptes',
        description: 'Soldes & aperçu',
        icon: Landmark,
      },
      {
        path: '/finances/rapprochement',
        label: 'Rapprochement',
        description: 'Auto-matching',
        icon: Link2,
      },
      {
        path: '/finances/imports',
        label: 'Imports',
        description: 'CSV / PDF',
        icon: Download,
      },
      {
        path: '/finances/fournisseurs',
        label: 'Fournisseurs',
        description: 'Encours & Échéances',
        icon: Users,
      },
    ],
    gradient: 'from-violet-500 to-purple-400',
    color: 'violet',
  },
  {
    id: 'restaurant',
    label: 'Restaurant',
    description: 'Menus & Charges',
    icon: Utensils,
    routes: restaurantRoutes,
    gradient: 'from-orange-500 to-amber-400',
    color: 'orange',
  },
  {
    id: 'intelligence',
    label: 'Intelligence',
    description: 'IA & Analytics',
    icon: Brain,
    routes: [intelligenceUnifiedRoute],
    isUnified: true,
    directPath: '/intelligence',
    gradient: 'from-pink-500 to-rose-400',
    color: 'pink',
  },
  {
    id: 'parametres',
    label: 'Paramètres',
    description: 'Configuration',
    icon: Settings,
    routes: settingsRoutes,
    gradient: 'from-slate-500 to-slate-400',
    color: 'slate',
  },
];

// Route newCMS Demo
export const newCMSDemoRoute = {
  path: '/newcms-demo',
  label: 'newCMS Demo',
  description: 'Prototype UX 2025',
  icon: Sparkles,
  element: <LazyPage><NewCMSDemo /></LazyPage>,
};

// Toutes les routes à plat (pour le router)
export const allRoutes = [
  cockpitRoute,
  ...operationsRoutes,
  ...financesRoutes,
  ...restaurantRoutes,
  ...intelligenceRoutes,
  ...settingsRoutes,
  // newCMSDemoRoute est géré séparément dans App.jsx (plein écran)
];

// Routes visibles uniquement (pour la sidebar/navigation)
export const visibleRoutes = allRoutes.filter((r) => !r.hidden);
