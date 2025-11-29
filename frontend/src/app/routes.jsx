import {
  LayoutDashboard,
  Boxes,
  ShoppingBag,
  Activity,
  TrendingUp,
  Utensils,
  ReceiptText,
  Download,
} from 'lucide-react';

import DashboardPage from '../features/dashboard/DashboardPage.jsx';
import CatalogPage from '../features/catalog/CatalogPage.jsx';
import ImportPage from '../features/invoices/ImportPage.jsx';
import StockMovementsPage from '../features/stock/StockMovementsPage.jsx';
import PricesPage from '../features/prices/PricesPage.jsx';
import RestaurantDashboard from '../features/restaurant/RestaurantDashboard.jsx';
import RestaurantChargesPage from '../features/restaurant/RestaurantChargesPage.jsx';
import RestaurantMenuPage from '../features/restaurant/RestaurantMenuPage.jsx';
import RestaurantPriceTrends from '../features/restaurant/RestaurantPriceTrends.jsx';
import BankStatementAnalyzer from '../features/restaurant/BankStatementAnalyzer.jsx';
import ForecastsPage from '../features/restaurant/ForecastsPage.jsx';
import PortfolioPage from '../features/portfolio/PortfolioPage.jsx';

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
  {
    path: '/bank-statement',
    label: 'Relevés bancaires',
    description: 'Flux de trésorerie et charges épicerie',
    icon: Download,
    element: <BankStatementAnalyzer defaultAccount="noutam" />,
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
  {
    path: '/bank-statement',
    label: 'Relevés bancaires',
    description: 'Analyse des dépenses et encaissements',
    icon: Download,
    element: <BankStatementAnalyzer defaultAccount="incontournable" />,
  },
];
