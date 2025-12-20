/**
 * OperationsPage - Vue Pilotage des opérations
 * Affiche le DashboardPage directement (navigation via sidebar)
 */

import { lazy, Suspense } from 'react';
import { Package } from 'lucide-react';

// Lazy loading du dashboard
const DashboardPage = lazy(() => import('../dashboard/DashboardPage.jsx'));

// Skeleton de chargement
function PageSkeleton() {
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
  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
            <Package className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Pilotage Opérations</h1>
            <p className="text-sm text-slate-400">Vue consolidée des opérations</p>
          </div>
        </div>
      </div>

      {/* Contenu - Dashboard direct */}
      <Suspense fallback={<PageSkeleton />}>
        <DashboardPage />
      </Suspense>
    </div>
  );
}
