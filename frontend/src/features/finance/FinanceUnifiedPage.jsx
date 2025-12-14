/**
 * FinanceUnifiedPage - Vue unifiée des finances
 * Design Next-Gen 2025 - Phase 3 Navigation 6 Vues
 *
 * Utilise TabView avec sync URL (?tab=)
 */

import { lazy, Suspense } from 'react';
import {
  Wallet,
  Activity,
  Landmark,
  Link2,
  Download,
  BarChart3,
} from 'lucide-react';
import { TabView } from '../../components/ui';

// Lazy loading des sous-pages
const FinanceOverview = lazy(() => import('./FinanceOverview.jsx'));
const FinanceTransactionsPage = lazy(() => import('./FinanceTransactionsPage.jsx'));
const FinanceAccountsPage = lazy(() => import('./FinanceAccountsPage.jsx'));
const BankReconciliationPage = lazy(() => import('./BankReconciliationPage.jsx'));
const FinanceImportsPage = lazy(() => import('./FinanceImportsPage.jsx'));
const PortfolioPage = lazy(() => import('../portfolio/PortfolioPage.jsx'));

// Skeleton de chargement
function TabSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-slate-800/50 rounded-xl" />
        ))}
      </div>
      <div className="h-96 bg-slate-800/50 rounded-2xl" />
    </div>
  );
}

export default function FinanceUnifiedPage() {
  const tabs = [
    {
      id: 'tresorerie',
      label: 'Trésorerie',
      icon: <Wallet className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <FinanceOverview />
        </Suspense>
      ),
    },
    {
      id: 'transactions',
      label: 'Transactions',
      icon: <Activity className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <FinanceTransactionsPage />
        </Suspense>
      ),
    },
    {
      id: 'comptes',
      label: 'Comptes',
      icon: <Landmark className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <FinanceAccountsPage />
        </Suspense>
      ),
    },
    {
      id: 'rapprochement',
      label: 'Rapprochement',
      icon: <Link2 className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <BankReconciliationPage />
        </Suspense>
      ),
    },
    {
      id: 'portefeuille',
      label: 'Portefeuille',
      icon: <BarChart3 className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <PortfolioPage />
        </Suspense>
      ),
    },
    {
      id: 'imports',
      label: 'Imports',
      icon: <Download className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <FinanceImportsPage />
        </Suspense>
      ),
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
            <Wallet className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Finances</h1>
            <p className="text-sm text-slate-400">Trésorerie, Transactions & Rapprochement</p>
          </div>
        </div>
      </div>

      {/* Onglets avec sync URL */}
      <TabView
        tabs={tabs}
        defaultTab="tresorerie"
        paramName="tab"
        variant="default"
        size="md"
      />
    </div>
  );
}
