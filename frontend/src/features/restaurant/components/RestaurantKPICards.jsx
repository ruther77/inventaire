import { TrendingUp, TrendingDown, DollarSign, Utensils, AlertTriangle, Percent } from 'lucide-react';
import { MetricCard, MetricCardGroup } from '@/components/ui';

/**
 * RestaurantKPICards - Cartes KPI pour le dashboard restaurant
 *
 * Props:
 * - data: objet contenant les métriques (chiffre_affaire, food_cost_pct, marge_moyenne, plats_actifs)
 * - isLoading: boolean pour l'état de chargement
 */
export default function RestaurantKPICards({ data = {}, isLoading = false }) {
  const {
    chiffre_affaire = 0,
    food_cost_pct = 0,
    marge_moyenne = 0,
    plats_actifs = 0,
    ca_evolution = 0,
    food_cost_evolution = 0,
  } = data;

  // Colorisation du Food Cost (vert <30%, jaune 30-35%, rouge >35%)
  const getFoodCostColor = (value) => {
    if (value < 30) return 'text-emerald-600';
    if (value <= 35) return 'text-amber-600';
    return 'text-rose-600';
  };

  // Colorisation de la marge (vert >60%, jaune 40-60%, rouge <40%)
  const getMarginColor = (value) => {
    if (value > 60) return 'text-emerald-600';
    if (value >= 40) return 'text-amber-600';
    return 'text-rose-600';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value) => `${value.toFixed(1)} %`;

  const getTrendIcon = (evolution) => {
    if (evolution > 0) return <TrendingUp className="w-4 h-4" />;
    if (evolution < 0) return <TrendingDown className="w-4 h-4" />;
    return null;
  };

  const getTrendColor = (evolution) => {
    if (evolution > 0) return 'text-emerald-600';
    if (evolution < 0) return 'text-rose-600';
    return 'text-slate-400';
  };

  if (isLoading) {
    return (
      <MetricCardGroup>
        <MetricCard label="Chargement..." value="..." />
        <MetricCard label="Chargement..." value="..." />
        <MetricCard label="Chargement..." value="..." />
        <MetricCard label="Chargement..." value="..." />
      </MetricCardGroup>
    );
  }

  return (
    <MetricCardGroup>
      <MetricCard
        label="Chiffre d'affaires"
        value={formatCurrency(chiffre_affaire)}
        icon={<DollarSign className="w-5 h-5 text-blue-500" />}
        trend={ca_evolution !== 0 && (
          <div className={`flex items-center gap-1 text-sm ${getTrendColor(ca_evolution)}`}>
            {getTrendIcon(ca_evolution)}
            <span>{Math.abs(ca_evolution).toFixed(1)}%</span>
          </div>
        )}
        hint="Période en cours"
      />

      <MetricCard
        label="Food Cost"
        value={formatPercent(food_cost_pct)}
        icon={<Percent className={`w-5 h-5 ${getFoodCostColor(food_cost_pct)}`} />}
        trend={food_cost_evolution !== 0 && (
          <div className={`flex items-center gap-1 text-sm ${getTrendColor(-food_cost_evolution)}`}>
            {getTrendIcon(-food_cost_evolution)}
            <span>{Math.abs(food_cost_evolution).toFixed(1)}%</span>
          </div>
        )}
        hint={food_cost_pct < 30 ? 'Excellent' : food_cost_pct <= 35 ? 'Acceptable' : 'À surveiller'}
        className={food_cost_pct > 35 ? 'border-rose-200 bg-rose-50/50' : ''}
      />

      <MetricCard
        label="Marge moyenne"
        value={formatPercent(marge_moyenne)}
        icon={<TrendingUp className={`w-5 h-5 ${getMarginColor(marge_moyenne)}`} />}
        hint={marge_moyenne > 60 ? 'Très bon' : marge_moyenne >= 40 ? 'Correct' : 'Faible'}
        className={marge_moyenne < 40 ? 'border-rose-200 bg-rose-50/50' : ''}
      />

      <MetricCard
        label="Plats actifs"
        value={plats_actifs}
        icon={<Utensils className="w-5 h-5 text-purple-500" />}
        hint="Sur la carte"
      />
    </MetricCardGroup>
  );
}
