import { ArrowUpRight, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import { Skeleton } from '../../../components/ui/Skeleton.jsx';

/**
 * DashboardHero - Section héro du dashboard avec status et actions rapides
 * Pattern: Progressive disclosure avec animations
 */
export default function DashboardHero({ status, loading = false }) {
  if (loading) {
    return <DashboardHeroSkeleton />;
  }

  const statusConfig = {
    ok: {
      icon: CheckCircle2,
      label: 'Tout est au vert',
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/20',
    },
    warning: {
      icon: AlertTriangle,
      label: 'Attention requise',
      color: 'text-amber-400',
      bg: 'bg-amber-500/20',
    },
    error: {
      icon: AlertTriangle,
      label: 'Action urgente',
      color: 'text-rose-400',
      bg: 'bg-rose-500/20',
    },
  };

  const currentStatus = statusConfig[status?.level || 'ok'];
  const StatusIcon = currentStatus.icon;

  return (
    <Card className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-brand-800 text-white">
      <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        {/* Contenu principal */}
        <div className="flex-1">
          <p className="text-sm uppercase tracking-[0.4em] text-brand-100/80">
            cockpit temps réel
          </p>
          <h1 className="font-display text-3xl font-semibold sm:text-4xl lg:text-5xl mt-2">
            Import, inventaire, cash
          </h1>
          <p className="mt-4 max-w-2xl text-base text-slate-100/90">
            Concentrez-vous sur les flux critiques : ingestion des factures et relevés,
            contrôle des mouvements de stock et pilotage consolidé du capital.
          </p>

          {/* Actions rapides */}
          <div className="mt-6 flex flex-wrap gap-3">
            <Button as="a" href="/import" variant="brand" size="lg">
              Importer une facture
              <ArrowUpRight className="h-4 w-4" />
            </Button>
            <Button as="a" href="/portfolio" variant="ghost" className="text-white hover:bg-white/10">
              Consulter le capital
            </Button>
          </div>
        </div>

        {/* Panel de statut */}
        <div className="flex-shrink-0 w-full lg:w-80">
          <div className="rounded-3xl border border-white/10 bg-white/10 p-5 backdrop-blur">
            {/* Statut principal */}
            <div className="flex items-center gap-3 mb-4">
              <div className={`rounded-full p-2 ${currentStatus.bg}`}>
                <StatusIcon className={`h-5 w-5 ${currentStatus.color}`} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-white/60">
                  statut plateforme
                </p>
                <p className="text-lg font-semibold">{currentStatus.label}</p>
              </div>
            </div>

            {/* Liste des événements */}
            <div className="space-y-2 text-sm text-slate-100/80">
              {status?.events?.map((event, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className="text-white/40">•</span>
                  <span>{event}</span>
                </div>
              )) || (
                <>
                  <div className="flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-white/40" />
                    <span>Synchronisation catalogue réussie à 06:00</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-white/40" />
                    <span>Dernière sauvegarde PostgreSQL : 03:14</span>
                  </div>
                </>
              )}
            </div>

            {/* Alertes */}
            {status?.alertCount > 0 && (
              <div className="mt-4 pt-4 border-t border-white/10">
                <Button
                  as="a"
                  href="/alerts"
                  variant="ghost"
                  size="sm"
                  className="w-full justify-between text-amber-300 hover:bg-amber-500/20"
                >
                  <span>{status.alertCount} alerte(s) à traiter</span>
                  <ArrowUpRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Background gradient effect */}
      <div className="pointer-events-none absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.15),_transparent_60%)]" />
      </div>
    </Card>
  );
}

function DashboardHeroSkeleton() {
  return (
    <Card className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-brand-800 p-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex-1 space-y-4">
          <Skeleton className="h-4 w-32 bg-white/20" />
          <Skeleton className="h-12 w-80 bg-white/20" />
          <Skeleton className="h-4 w-full max-w-xl bg-white/20" />
          <Skeleton className="h-4 w-3/4 max-w-xl bg-white/20" />
          <div className="flex gap-3 mt-6">
            <Skeleton className="h-12 w-44 rounded-2xl bg-white/20" />
            <Skeleton className="h-12 w-40 rounded-2xl bg-white/20" />
          </div>
        </div>
        <Skeleton className="h-48 w-full lg:w-80 rounded-3xl bg-white/10" />
      </div>
    </Card>
  );
}
