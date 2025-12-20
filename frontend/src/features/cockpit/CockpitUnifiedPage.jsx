/**
 * Cockpit Unifié - Vue 360° avec onglets
 *
 * Consolide :
 * - Morning Brief (CockpitPage)
 * - Dashboard (DashboardPage)
 * - Portfolio (PortfolioPage)
 * - Alertes
 *
 * Phase 3 - Navigation 6 Vues (UX Next-Gen 2025)
 */

import { lazy, Suspense } from 'react';
import {
  Sun,
  Briefcase,
  AlertTriangle,
  Sparkles,
  LayoutDashboard,
  Gauge,
} from 'lucide-react';
import { TabView } from '../../components/ui';
import { Skeleton } from '../../components/ui/Skeleton.jsx';

// Lazy load des sous-pages
const CockpitContent = lazy(() => import('./CockpitPage.jsx'));
const PortfolioContent = lazy(() => import('../portfolio/PortfolioPage.jsx'));

// Skeleton de chargement
function TabSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-24 bg-slate-800/50 rounded-2xl" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 bg-slate-800/50 rounded-xl" />
        ))}
      </div>
      <div className="h-64 bg-slate-800/50 rounded-2xl" />
    </div>
  );
}

// Contenu des alertes (inline car léger)
function AlertsContent() {
  // @todo: brancher sur /cockpit/alerts + anomalies
  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="w-6 h-6 text-amber-400" />
          <h2 className="text-xl font-semibold text-white">Centre d'alertes</h2>
        </div>
        <p className="text-slate-400 mb-6">
          Toutes vos alertes et notifications en un seul endroit.
        </p>

        {/* Placeholder - à remplacer par vraies alertes */}
        <div className="space-y-3">
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
            <div className="flex items-start gap-3">
              <span className="p-1.5 rounded-lg bg-rose-500/20">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              </span>
              <div>
                <p className="font-medium text-white">Stock critique : Tomates</p>
                <p className="text-sm text-slate-400 mt-1">Seulement 2kg restants - Besoin estimé : 15kg/jour</p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <div className="flex items-start gap-3">
              <span className="p-1.5 rounded-lg bg-amber-500/20">
                <Sparkles className="w-4 h-4 text-amber-400" />
              </span>
              <div>
                <p className="font-medium text-white">3 factures en attente de validation</p>
                <p className="text-sm text-slate-400 mt-1">Metro, Brake, PromoC - Total : 1 247€</p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <div className="flex items-start gap-3">
              <span className="p-1.5 rounded-lg bg-blue-500/20">
                <LayoutDashboard className="w-4 h-4 text-blue-400" />
              </span>
              <div>
                <p className="font-medium text-white">Rapport hebdomadaire disponible</p>
                <p className="text-sm text-slate-400 mt-1">Semaine du 2 au 8 décembre 2025</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CockpitUnifiedPage() {
  // Badge auto sur base des alertes cockpit (si présentes dans le cache)
  const cachedAlerts = []; // placeholder, récupéré via CockpitPage inside
  const tabs = [
    {
      id: 'brief',
      label: 'Morning Brief',
      icon: <Sun className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <CockpitContent />
        </Suspense>
      ),
    },
    {
      id: 'portfolio',
      label: 'Portfolio',
      icon: <Briefcase className="w-4 h-4" />,
      content: (
        <Suspense fallback={<TabSkeleton />}>
          <PortfolioContent />
        </Suspense>
      ),
    },
    {
      id: 'alerts',
      label: 'Alertes',
      icon: <AlertTriangle className="w-4 h-4" />,
      badge: cachedAlerts.length || 3,
      content: <AlertsContent />,
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Header Next-Gen 2025 */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20">
            <Gauge className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Cockpit</h1>
            <p className="text-sm text-slate-400">Vue consolidée 360° - Pilotage & Alertes</p>
          </div>
        </div>
      </div>

      {/* Onglets avec sync URL */}
      <TabView
        tabs={tabs}
        defaultTab="brief"
        paramName="view"
        variant="default"
        size="md"
        className="h-full"
        tabsClassName="mb-6"
      />
    </div>
  );
}
