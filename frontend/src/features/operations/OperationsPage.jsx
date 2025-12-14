/**
 * OperationsPage - Vue unifiée des opérations
 * Design Next-Gen 2025 - Phase 3 Navigation 6 Vues
 *
 * Utilise TabView avec sync URL (?tab=)
 */

import { lazy, Suspense } from 'react';
import {
  LayoutDashboard,
  FileText,
  Boxes,
  Activity,
  TrendingUp,
  Package,
} from 'lucide-react';
import { TabView } from '../../components/ui';

// Lazy loading des sous-pages
const DashboardPage = lazy(() => import('../dashboard/DashboardPage.jsx'));
const ImportPage = lazy(() => import('../invoices/ImportPage.jsx'));
const CatalogPage = lazy(() => import('../catalog/CatalogPage.jsx'));
const StockMovementsPage = lazy(() => import('../stock/StockMovementsPage.jsx'));
const PricesPage = lazy(() => import('../prices/PricesPage.jsx'));

// Skeleton de chargement
function TabSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-20 bg-slate-800/50 rounded-2xl" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-16 bg-slate-800/50 rounded-xl" />
        ))}
      </div>
      <div className="h-96 bg-slate-800/50 rounded-2xl" />
    </div>
  );
}

export default function OperationsPage() {
  const tabs = [
    {
      id: 'pilotage',
      label: 'Pilotage',
      icon: <LayoutDashboard className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <DashboardPage />
        </Suspense>
      ),
    },
    {
      id: 'factures',
      label: 'Factures',
      icon: <FileText className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <ImportPage />
        </Suspense>
      ),
    },
    {
      id: 'catalogue',
      label: 'Catalogue',
      icon: <Boxes className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <CatalogPage />
        </Suspense>
      ),
    },
    {
      id: 'stock',
      label: 'Stock',
      icon: <Activity className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <StockMovementsPage />
        </Suspense>
      ),
    },
    {
      id: 'prix',
      label: 'Prix',
      icon: <TrendingUp className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <PricesPage />
        </Suspense>
      ),
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
            <Package className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Opérations</h1>
            <p className="text-sm text-slate-400">Catalogue, Factures, Stock & Prix</p>
          </div>
        </div>
      </div>

      {/* Onglets avec sync URL */}
      <TabView
        tabs={tabs}
        defaultTab="pilotage"
        paramName="tab"
        variant="default"
        size="md"
      />
    </div>
  );
}
