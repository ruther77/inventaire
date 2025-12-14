/**
 * IntelligenceUnifiedPage - Vue unifiée de l'Intelligence IA
 * Design Next-Gen 2025 - Phase 3 Navigation 6 Vues
 *
 * Utilise TabView avec sync URL (?tab=)
 */

import { lazy, Suspense } from 'react';
import {
  Brain,
  Zap,
  LineChart,
  AlertTriangle,
  Users,
  Calculator,
  Sparkles,
} from 'lucide-react';
import { TabView } from '../../components/ui';

// Lazy loading des sous-pages
const IntelligencePage = lazy(() => import('./IntelligencePage.jsx'));
const InventoryIntelligencePage = lazy(() => import('./InventoryIntelligencePage.jsx'));
const ForecastPage = lazy(() => import('./ForecastPage.jsx'));
const AnomaliesPage = lazy(() => import('./AnomaliesPage.jsx'));
const ScoringPage = lazy(() => import('./ScoringPage.jsx'));
const MarginsPage = lazy(() => import('./MarginsPage.jsx'));

// Skeleton avec effet IA
function TabSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 border-2 border-pink-500/20 rounded-full" />
            <div className="absolute inset-0 w-12 h-12 border-2 border-transparent border-t-pink-500 rounded-full animate-spin" />
            <Sparkles className="absolute inset-0 m-auto w-5 h-5 text-pink-400 animate-pulse" />
          </div>
          <span className="text-sm text-slate-400">Analyse en cours...</span>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-slate-800/50 rounded-xl" />
        ))}
      </div>
      <div className="h-64 bg-slate-800/50 rounded-2xl" />
    </div>
  );
}

export default function IntelligenceUnifiedPage() {
  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <Brain className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <IntelligencePage />
        </Suspense>
      ),
    },
    {
      id: 'stock',
      label: 'Stock Intel',
      icon: <Zap className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <InventoryIntelligencePage />
        </Suspense>
      ),
    },
    {
      id: 'previsions',
      label: 'Prévisions',
      icon: <LineChart className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <ForecastPage />
        </Suspense>
      ),
    },
    {
      id: 'anomalies',
      label: 'Anomalies',
      icon: <AlertTriangle className="w-4 h-4" />,
      badge: 3,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <AnomaliesPage />
        </Suspense>
      ),
    },
    {
      id: 'scoring',
      label: 'Scoring',
      icon: <Users className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <ScoringPage />
        </Suspense>
      ),
    },
    {
      id: 'marges',
      label: 'Marges',
      icon: <Calculator className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <MarginsPage />
        </Suspense>
      ),
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-gradient-to-br from-pink-500/20 to-violet-500/20">
            <Brain className="w-6 h-6 text-pink-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Intelligence</h1>
            <p className="text-sm text-slate-400">Analyses IA, Prévisions & Scoring</p>
          </div>
          <span className="ml-auto px-3 py-1 text-xs font-medium rounded-full bg-pink-500/20 text-pink-400 border border-pink-500/30">
            IA active
          </span>
        </div>
      </div>

      {/* Onglets avec sync URL */}
      <TabView
        tabs={tabs}
        defaultTab="dashboard"
        paramName="tab"
        variant="default"
        size="md"
      />
    </div>
  );
}
