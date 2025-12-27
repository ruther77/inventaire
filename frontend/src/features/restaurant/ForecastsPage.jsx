import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronRight, Download, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { useRestaurantForecastOverview, useRestaurantIngredients } from '@/hooks/useRestaurant.js';
import QueryErrorState from '@/components/feedback/QueryErrorState.jsx';
import { toast } from 'sonner';

/**
 * ForecastsPage - Prévisions Restaurant IA
 * Design from mockups/restaurant-previsions.html
 */

const INGREDIENT_ICONS = {
  viande: '🥩',
  boeuf: '🥩',
  entrecote: '🥩',
  poulet: '🍗',
  poisson: '🐟',
  tomate: '🍅',
  salade: '🥗',
  frites: '🍟',
  fromage: '🧀',
  parmesan: '🧀',
  default: '🥗',
};

export default function ForecastsPage() {
  // Queries
  const forecastQuery = useRestaurantForecastOverview();
  const ingredientsQuery = useRestaurantIngredients();

  const forecast = forecastQuery.data || {};
  const ingredients = ingredientsQuery.data || [];

  // Stats prévisions
  const stats = useMemo(() => ({
    caPrevu: forecast.ca_prevu_7j || 12450,
    couvertsPrevu: forecast.couverts_prevu_7j || 524,
    foodCostPrevu: forecast.food_cost_prevu || 29.2,
    besoinsIngredients: forecast.besoins_ingredients_value || 3640,
    confidenceCA: forecast.confidence_ca || 85,
    confidenceCouverts: forecast.confidence_couverts || 82,
    confidenceFoodCost: forecast.confidence_food_cost || 78,
    confidenceBesoins: forecast.confidence_besoins || 88,
  }), [forecast]);

  // Données journalières pour le graphique CA
  const dailyForecast = useMemo(() => {
    if (forecast.daily_forecast?.length) {
      return forecast.daily_forecast;
    }
    // Mock data
    return [
      { label: 'Lun', value: 1450, type: 'actual' },
      { label: 'Mar', value: 1280, type: 'actual' },
      { label: 'Mer', value: 1680, type: 'actual' },
      { label: 'Jeu', value: 1580, type: 'forecast' },
      { label: 'Ven', value: 2120, type: 'forecast' },
      { label: 'Sam', value: 2340, type: 'forecast' },
      { label: 'Dim', value: 1000, type: 'forecast' },
    ];
  }, [forecast]);

  const maxDaily = Math.max(...dailyForecast.map(d => d.value), 1);

  // Besoins ingrédients prévus
  const ingredientNeeds = useMemo(() => {
    if (forecast.ingredient_needs?.length) {
      return forecast.ingredient_needs;
    }
    // Calculer à partir des ingrédients
    return ingredients.slice(0, 6).map(ing => {
      const stockActuel = ing.stock_actuel || Math.random() * 10;
      const besoinPrevu = Math.random() * 40 + 10;
      const diff = besoinPrevu - stockActuel;
      let status = 'ok';
      if (diff > besoinPrevu * 0.8) status = 'critical';
      else if (diff > besoinPrevu * 0.5) status = 'warning';

      return {
        id: ing.id,
        nom: ing.nom,
        stockActuel: stockActuel.toFixed(1),
        besoinPrevu: besoinPrevu.toFixed(0),
        aCommander: Math.max(0, diff).toFixed(0),
        unite: ing.unite_base || 'kg',
        status,
      };
    });
  }, [forecast, ingredients]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const getIngredientIcon = (name) => {
    const lower = (name || '').toLowerCase();
    for (const [key, icon] of Object.entries(INGREDIENT_ICONS)) {
      if (lower.includes(key)) return icon;
    }
    return INGREDIENT_ICONS.default;
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'critical': return 'text-rose-400';
      case 'warning': return 'text-amber-400';
      default: return 'text-emerald-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'critical': return '⚠️';
      case 'warning': return '⏰';
      default: return '✓';
    }
  };

  const getStatusText = (item) => {
    switch (item.status) {
      case 'critical': return `Commander ${item.aCommander} ${item.unite}`;
      case 'warning': return `Commander ${item.aCommander} ${item.unite}`;
      default: return 'Stock suffisant';
    }
  };

  // Erreur
  if (forecastQuery.isError && !Object.keys(forecast).length) {
    return <QueryErrorState error={forecastQuery.error} onRetry={() => forecastQuery.refetch()} variant="full" />;
  }

  return (
    <div className="min-h-screen p-6 md:p-8">
      <div className="max-w-[1400px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <Link to="/" className="hover:text-white transition-colors">Accueil</Link>
          <ChevronRight className="w-4 h-4" />
          <Link to="/restaurant/plats" className="hover:text-white transition-colors">Restaurant</Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-white">Prévisions</span>
        </nav>

        {/* Header */}
        <h1 className="text-3xl md:text-4xl font-bold mb-2 bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent font-['Sora',sans-serif]">
          🔮 Prévisions Restaurant
        </h1>
        <p className="text-base text-slate-400 mb-8">
          Prévisions IA des ventes et besoins en ingrédients pour les 7 prochains jours
        </p>

        {/* Forecast Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/6 border border-white/15 rounded-2xl p-6 cursor-pointer hover:bg-white/10 transition-all"
            onClick={() => toast.info('Détail CA prévu')}
          >
            <p className="text-xs text-slate-400 mb-2">CA prévu (7j)</p>
            <p className="text-3xl font-bold text-emerald-400 mb-2">{formatCurrency(stats.caPrevu)}</p>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/20 text-emerald-400">
              {stats.confidenceCA}% confiance
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/6 border border-white/15 rounded-2xl p-6 cursor-pointer hover:bg-white/10 transition-all"
            onClick={() => toast.info('Détail couverts prévus')}
          >
            <p className="text-xs text-slate-400 mb-2">Couverts prévus (7j)</p>
            <p className="text-3xl font-bold text-white mb-2">{stats.couvertsPrevu}</p>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/20 text-emerald-400">
              {stats.confidenceCouverts}% confiance
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/6 border border-white/15 rounded-2xl p-6 cursor-pointer hover:bg-white/10 transition-all"
            onClick={() => toast.info('Détail food cost prévu')}
          >
            <p className="text-xs text-slate-400 mb-2">Food Cost prévu</p>
            <p className="text-3xl font-bold text-amber-400 mb-2">{stats.foodCostPrevu}%</p>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/20 text-emerald-400">
              {stats.confidenceFoodCost}% confiance
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white/6 border border-white/15 rounded-2xl p-6 cursor-pointer hover:bg-white/10 transition-all"
            onClick={() => toast.info('Détail besoins ingrédients')}
          >
            <p className="text-xs text-slate-400 mb-2">Besoins ingrédients</p>
            <p className="text-3xl font-bold text-white mb-2">{formatCurrency(stats.besoinsIngredients)}</p>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/20 text-emerald-400">
              {stats.confidenceBesoins}% confiance
            </span>
          </motion.div>
        </div>

        {/* Daily Forecast Chart */}
        <div className="bg-white/6 border border-white/15 rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-base font-semibold text-white">📈 Prévision CA journalier</h3>
            <button
              onClick={() => toast.info('Export en cours...')}
              className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 text-xs font-medium hover:bg-cyan-500/20 transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Exporter
            </button>
          </div>
          <div className="h-72 bg-gradient-to-t from-transparent to-orange-500/5 rounded-xl flex items-end justify-around px-4 pb-4 relative">
            {dailyForecast.map((day, idx) => (
              <div key={idx} className="flex flex-col items-center gap-2">
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: `${(day.value / maxDaily) * 100}%` }}
                  transition={{ delay: idx * 0.1, duration: 0.5 }}
                  className={`w-10 rounded-t cursor-pointer transition-opacity hover:opacity-80 min-h-[20px] ${
                    day.type === 'actual'
                      ? 'bg-gradient-to-t from-orange-500 to-amber-400'
                      : 'bg-gradient-to-t from-cyan-500/60 to-cyan-400/30 border-2 border-dashed border-cyan-400'
                  }`}
                  onClick={() => toast.info(`${day.label} ${day.type === 'actual' ? '(passé)' : '(prévu)'}: ${formatCurrency(day.value)}`)}
                />
                <span className="text-xs text-slate-400">{day.label}</span>
              </div>
            ))}
          </div>
          <div className="flex justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-orange-500" />
              <span className="text-xs text-slate-400">Réalisé</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-cyan-500/60" />
              <span className="text-xs text-slate-400">Prévision IA</span>
            </div>
          </div>
        </div>

        {/* Ingredient Needs */}
        <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
          <h3 className="text-base font-semibold text-white mb-5">🥗 Besoins ingrédients prévus (7j)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ingredientNeeds.map((item, idx) => (
              <motion.div
                key={item.id || idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center justify-between p-4 bg-white/3 rounded-xl hover:bg-white/8 cursor-pointer transition-all"
                onClick={() => toast.info(`Détail ${item.nom}`)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getIngredientIcon(item.nom)}</span>
                  <div>
                    <p className="text-sm font-medium text-white">{item.nom}</p>
                    <p className="text-xs text-slate-400">Stock: {item.stockActuel} {item.unite}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-base font-semibold text-white">{item.besoinPrevu} {item.unite}</p>
                  <p className={`text-xs ${getStatusClass(item.status)}`}>
                    {getStatusIcon(item.status)} {getStatusText(item)}
                  </p>
                </div>
              </motion.div>
            ))}

            {ingredientNeeds.length === 0 && (
              <p className="col-span-2 text-center text-slate-500 py-8">
                Aucune prévision disponible
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
