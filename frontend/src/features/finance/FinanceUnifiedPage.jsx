/**
 * FinanceUnifiedPage - Vue Trésorerie des finances
 * Affiche FinanceOverview directement (navigation via sidebar)
 */

import { lazy, Suspense } from 'react';
import { Wallet } from 'lucide-react';

// Lazy loading de la vue trésorerie
const FinanceOverview = lazy(() => import('./FinanceOverview.jsx'));

// Skeleton de chargement
function PageSkeleton() {
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
  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
            <Wallet className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Trésorerie</h1>
            <p className="text-sm text-slate-400">Vue consolidée des finances</p>
          </div>
        </div>
      </div>

      {/* Contenu - FinanceOverview direct */}
      <Suspense fallback={<PageSkeleton />}>
        <FinanceOverview />
      </Suspense>
    </div>
  );
}
