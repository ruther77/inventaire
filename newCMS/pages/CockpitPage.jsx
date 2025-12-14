/**
 * Cockpit Page - Morning Brief (Scénario 3.1)
 * Vue 360° consolidée - Mode Matin
 */

import {
  Sun,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Package,
  DollarSign,
  Receipt,
  Calendar,
  ChevronRight,
  Clock,
  Lightbulb,
  ShoppingCart,
  BarChart3,
} from 'lucide-react';

// KPI Card Component
function KPICard({ label, value, trend, trendValue, icon: Icon }) {
  const getTrendColor = () => {
    if (trend === 'up') return 'text-emerald-400';
    if (trend === 'down') return 'text-rose-400';
    return 'text-slate-400';
  };

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  return (
    <div className="p-4 rounded-xl bg-slate-800/50 border border-white/10 hover:border-white/20 transition-all">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-400">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-slate-500" />}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className={`flex items-center gap-1 text-sm ${getTrendColor()}`}>
        <TrendIcon className="w-3 h-3" />
        <span>{trendValue}</span>
      </div>
    </div>
  );
}

// Action Card Component
function ActionCard({ urgency, title, description, suggestion, actions }) {
  const getUrgencyStyles = () => {
    switch (urgency) {
      case 'urgent':
        return 'border-rose-500/30 bg-rose-500/5';
      case 'medium':
        return 'border-amber-500/30 bg-amber-500/5';
      default:
        return 'border-blue-500/30 bg-blue-500/5';
    }
  };

  const getUrgencyBadge = () => {
    switch (urgency) {
      case 'urgent':
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-rose-500/20 text-rose-400">URGENT</span>;
      case 'medium':
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-500/20 text-amber-400">MOYEN</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-400">INFO</span>;
    }
  };

  return (
    <div className={`p-4 rounded-xl border ${getUrgencyStyles()}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          {getUrgencyBadge()}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-white">{title}</h4>
          {description && <p className="text-sm text-slate-400 mt-1">{description}</p>}
          {suggestion && (
            <div className="flex items-start gap-2 mt-2 p-2 rounded-lg bg-white/5">
              <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-slate-300">{suggestion}</span>
            </div>
          )}
          {actions && (
            <div className="flex flex-wrap gap-2 mt-3">
              {actions.map((action, idx) => (
                <button
                  key={idx}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    action.primary
                      ? 'bg-blue-500 text-white hover:bg-blue-600'
                      : 'bg-white/10 text-slate-300 hover:bg-white/20'
                  }`}
                >
                  {action.icon && <span className="mr-1">{action.icon}</span>}
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Week Forecast Component
function WeekForecast() {
  const days = [
    { day: 'Lun', ca: '2.1k', status: 'ok' },
    { day: 'Mar', ca: '2.4k', status: 'ok' },
    { day: 'Mer', ca: '2.2k', status: 'ok' },
    { day: 'Jeu', ca: '2.8k', status: 'warning' },
    { day: 'Ven', ca: '3.5k', status: 'danger' },
    { day: 'Sam', ca: '4.2k', status: 'danger' },
    { day: 'Dim', ca: '1.8k', status: 'ok' },
  ];

  const getStatusEmoji = (status) => {
    switch (status) {
      case 'ok': return '🟢';
      case 'warning': return '🟡';
      case 'danger': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <Calendar className="w-5 h-5 text-blue-400" />
        <h3 className="text-lg font-semibold text-white">Prévisions Semaine</h3>
      </div>

      <div className="grid grid-cols-7 gap-2 mb-4">
        {days.map((d, idx) => (
          <div key={idx} className="text-center p-2 rounded-lg bg-white/5">
            <div className="text-xs text-slate-500 mb-1">{d.day}</div>
            <div className="text-sm font-medium text-white">{d.ca}</div>
            <div className="text-xs mt-1">{getStatusEmoji(d.status)}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
        <AlertTriangle className="w-4 h-4 text-amber-400" />
        <span className="text-sm text-slate-300">
          Vendredi/Samedi: Rupture probable sur 4 produits
        </span>
        <button className="ml-auto text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1">
          Voir détail <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default function CockpitPage() {
  const currentTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  const currentDate = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header avec salutation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500">
            <Sun className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Bonjour Chef !</h1>
            <p className="text-slate-400">Voici votre brief du jour</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-white">{currentTime}</div>
          <div className="text-sm text-slate-400 capitalize">{currentDate}</div>
        </div>
      </div>

      {/* Section KPIs - Hier en bref */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Hier en bref</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            label="CA Jour"
            value="2 847 €"
            trend="up"
            trendValue="+12%"
            icon={DollarSign}
          />
          <KPICard
            label="Marge Brute"
            value="38.2%"
            trend="down"
            trendValue="-2.1%"
            icon={TrendingUp}
          />
          <KPICard
            label="Tickets"
            value="127"
            trend="up"
            trendValue="+8"
            icon={Receipt}
          />
          <KPICard
            label="Panier Moyen"
            value="22.4 €"
            trend="stable"
            trendValue="stable"
            icon={ShoppingCart}
          />
        </div>
      </div>

      {/* Section Actions à traiter */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-white">À traiter aujourd'hui</h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-400">
              3 actions
            </span>
          </div>
          <button className="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition-colors flex items-center gap-2">
            Tout traiter <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-3">
          <ActionCard
            urgency="urgent"
            title="Stock Tomates: 2kg restants (besoin 15kg/jour)"
            suggestion="Commander 50kg chez METRO (livraison demain)"
            actions={[
              { label: '📦 Commander maintenant', primary: true },
              { label: '⏰ Reporter' },
              { label: '❌ Ignorer' },
            ]}
          />

          <ActionCard
            urgency="medium"
            title="3 factures à valider (Metro, Brake, PromoC) - Total: 1 247€"
            suggestion="Catégorisation auto: 94% confiance"
            actions={[
              { label: '✅ Valider tout', primary: true },
              { label: '👁️ Vérifier' },
              { label: '⏰ Plus tard' },
            ]}
          />

          <ActionCard
            urgency="info"
            title="Anomalie prix: Huile olive +23% vs moyenne marché"
            suggestion="Alternative: Fournisseur B à -15% (même qualité)"
            actions={[
              { label: '🔄 Changer fournisseur', primary: true },
              { label: '📊 Voir analyse' },
              { label: '👍 OK prix' },
            ]}
          />
        </div>
      </div>

      {/* Section Prévisions Semaine */}
      <WeekForecast />
    </div>
  );
}
