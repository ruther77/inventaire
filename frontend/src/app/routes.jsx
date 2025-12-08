import { lazy, Suspense } from 'react';
import {
  LayoutDashboard,
  Boxes,
  ShoppingBag,
  Activity,
  TrendingUp,
  Utensils,
  ReceiptText,
  Download,
  Landmark,
} from 'lucide-react';

// Epicerie pages
import CatalogPage from '../features/catalog/CatalogPage.jsx';
import ImportPage from '../features/invoices/ImportPage.jsx';
import StockMovementsPage from '../features/stock/StockMovementsPage.jsx';
import PricesPage from '../features/prices/PricesPage.jsx';
import DashboardPage from '../features/dashboard/DashboardPage.jsx';

// Restaurant pages
import RestaurantDashboard from '../features/restaurant/RestaurantDashboard.jsx';
import RestaurantChargesPage from '../features/restaurant/RestaurantChargesPage.jsx';
import RestaurantMenuPage from '../features/restaurant/RestaurantMenuPage.jsx';
import RestaurantPriceTrends from '../features/restaurant/RestaurantPriceTrends.jsx';
import RestaurantStockMovementsPage from '../features/restaurant/RestaurantStockMovementsPage.jsx';
import RestaurantConsumptionPage from '../features/restaurant/RestaurantConsumptionPage.jsx';
import RestaurantPriceHistoryComparisonPage from '../features/restaurant/RestaurantPriceHistoryComparisonPage.jsx';
import ForecastsPage from '../features/restaurant/ForecastsPage.jsx';

// Shared
import PortfolioPage from '../features/portfolio/PortfolioPage.jsx';

// Tresorerie pages - Lazy loaded pour performance
const FinanceOverview = lazy(() => import('../features/finance/FinanceOverview.jsx'));
const FinanceTransactionsPage = lazy(() => import('../features/finance/FinanceTransactionsPage.jsx'));
const FinanceAccountsPage = lazy(() => import('../features/finance/FinanceAccountsPage.jsx'));
const FinanceImportsPage = lazy(() => import('../features/finance/FinanceImportsPage.jsx'));
const FinanceRulesPage = lazy(() => import('../features/finance/FinanceRulesPage.jsx'));
const FinanceAnomaliesPage = lazy(() => import('../features/finance/FinanceAnomaliesPage.jsx'));

// Wrapper pour lazy loading avec fallback
const LazyPage = ({ children }) => (
  <Suspense fallback={
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="animate-pulse text-slate-400">Chargement...</div>
    </div>
  }>
    {children}
  </Suspense>
);

export const epicerieRoutes = [
  {
    path: '/',
    label: 'Pilotage',
    description: 'Vue synthétique marges & cash',
    icon: LayoutDashboard,
    element: <DashboardPage />,
  },
  {
    path: '/inventory',
    label: 'Catalogue',
    description: 'Produits & niveaux de stock',
    icon: Boxes,
    element: <CatalogPage />,
  },
  {
    path: '/stock',
    label: 'Mouvements',
    description: 'Entrées / sorties / ajustements',
    icon: Activity,
    element: <StockMovementsPage />,
  },
  {
    path: '/import',
    label: 'Réceptions',
    description: 'Facture → stock',
    icon: ShoppingBag,
    element: <ImportPage />,
  },
  {
    path: '/prices',
    label: 'Suivi prix',
    description: 'Historique fournisseurs & relevés',
    icon: TrendingUp,
    element: <PricesPage />,
  },
  {
    path: '/portfolio',
    label: 'Portefeuille',
    description: 'Consolidé capital & cash',
    icon: TrendingUp,
    element: <PortfolioPage />,
  },
  {
    path: '/charges',
    label: 'Charges',
    description: 'Dépenses & TVA épicerie',
    icon: ReceiptText,
    element: <RestaurantChargesPage context="epicerie" />,
  },
  {
    path: '/forecasts',
    label: 'Prévisions',
    description: 'ARIMA multi-périodes',
    icon: Activity,
    element: <ForecastsPage context="epicerie" />,
  },
];

export const restaurantRoutes = [
  {
    path: '/',
    label: 'Pilotage',
    description: 'Charges & menus',
    icon: LayoutDashboard,
    element: <RestaurantDashboard />,
  },
  {
    path: '/charges',
    label: 'Charges',
    description: 'Dépenses & fournisseurs',
    icon: ReceiptText,
    element: <RestaurantChargesPage />,
  },
  {
    path: '/menu',
    label: 'Menus & recettes',
    description: 'Fiches techniques et coûts matières',
    icon: Utensils,
    element: <RestaurantMenuPage />,
  },
  {
    path: '/stock',
    label: 'Mouvements',
    description: 'Entrées / sorties / ajustements restaurant',
    icon: Activity,
    element: <RestaurantStockMovementsPage />,
  },
  {
    path: '/consumptions',
    label: 'Consommations',
    description: 'Bouteilles sorties & coûts Epicerie',
    icon: Boxes,
    element: <RestaurantConsumptionPage />,
  },
  {
    path: '/price-history',
    label: 'Historique prix',
    description: 'Tarifs plats vs coût Epicerie',
    icon: TrendingUp,
    element: <RestaurantPriceHistoryComparisonPage />,
  },
  {
    path: '/price-trends',
    label: 'Tendances prix',
    description: 'Historique des matières & plats',
    icon: TrendingUp,
    element: <RestaurantPriceTrends />,
  },
  {
    path: '/forecasts',
    label: 'Prévisions',
    description: 'Charges et ventes projetées',
    icon: Activity,
    element: <ForecastsPage context="restaurant" />,
  },
];

export const treasuryRoutes = [
  {
    path: '/',
    label: 'Vue d\'ensemble',
    description: 'Flux de tresorerie consolides',
    icon: LayoutDashboard,
    element: <LazyPage><FinanceOverview /></LazyPage>,
  },
  {
    path: '/transactions',
    label: 'Transactions',
    description: 'Releves bancaires et mouvements',
    icon: Activity,
    element: <LazyPage><FinanceTransactionsPage /></LazyPage>,
  },
  {
    path: '/comptes',
    label: 'Comptes',
    description: 'Soldes et apercu des comptes',
    icon: Landmark,
    element: <LazyPage><FinanceAccountsPage /></LazyPage>,
  },
  {
    path: '/imports',
    label: 'Imports',
    description: 'Importer releves CSV/PDF',
    icon: Download,
    element: <LazyPage><FinanceImportsPage /></LazyPage>,
  },
  {
    path: '/regles',
    label: 'Regles',
    description: 'Categorisation automatique',
    icon: ReceiptText,
    element: <LazyPage><FinanceRulesPage /></LazyPage>,
  },
  {
    path: '/anomalies',
    label: 'Anomalies',
    description: 'Rapprochement et alertes',
    icon: Activity,
    element: <LazyPage><FinanceAnomaliesPage /></LazyPage>,
  },
  {
    path: '/portfolio',
    label: 'Portefeuille',
    description: 'Capital & cash',
    icon: TrendingUp,
    element: <PortfolioPage />,
  },
];
