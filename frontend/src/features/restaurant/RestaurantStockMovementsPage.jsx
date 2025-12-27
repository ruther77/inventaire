import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronRight, Download, Plus, ClipboardList, AlertTriangle } from 'lucide-react';
import {
  useRestaurantIngredients,
  useRestaurantStockMovements,
  useRestaurantStockSummary,
} from '@/hooks/useRestaurant.js';
import QueryErrorState from '@/components/feedback/QueryErrorState.jsx';
import { toast } from 'sonner';

/**
 * RestaurantStockMovementsPage - Stock Ingrédients Restaurant
 * Design from mockups/restaurant-stock.html
 *
 * Utilise les vraies données de:
 * - /restaurant/ingredients (liste ingrédients)
 * - /restaurant/stock/summary (résumé stock avec statut_stock)
 * - /restaurant/stock/movements (mouvements récents)
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
  creme: '🥛',
  lait: '🥛',
  legume: '🥬',
  biere: '🍺',
  vin: '🍷',
  champagne: '🥂',
  whisky: '🥃',
  rhum: '🥃',
  vodka: '🥃',
  cognac: '🥃',
  eau: '💧',
  coca: '🥤',
  jus: '🧃',
  huile: '🫒',
  riz: '🍚',
  piment: '🌶️',
  default: '📦',
};

const TAB_OPTIONS = [
  { value: 'all', label: 'Tous' },
  { value: 'rupture', label: 'Rupture' },
  { value: 'critique', label: 'Critique' },
  { value: 'ok', label: 'OK' },
];

export default function RestaurantStockMovementsPage() {
  const [activeTab, setActiveTab] = useState('all');

  // Queries - summary contient les vraies données de stock avec statut
  const summaryQuery = useRestaurantStockSummary();
  const movementsQuery = useRestaurantStockMovements({ limit: 100 });

  // Les données du summary sont dans .data (wrapper API)
  const summaryData = summaryQuery.data || [];
  const movements = movementsQuery.data?.items || movementsQuery.data || [];

  // Calcul des stats à partir des vraies données
  const stats = useMemo(() => {
    // Valeur totale du stock (stock * cout_unitaire)
    const totalValue = summaryData.reduce((sum, ing) => {
      const stock = Math.max(0, ing.stock_actuel || 0); // Ignorer stocks négatifs pour la valeur
      const prix = ing.cout_unitaire || 0;
      return sum + (stock * prix);
    }, 0);

    // Ingrédients actifs (stock > 0)
    const activeCount = summaryData.filter(ing => (ing.stock_actuel || 0) > 0).length;

    // Alertes (rupture ou critique)
    const alertCount = summaryData.filter(ing =>
      ing.statut_stock === 'rupture' || ing.statut_stock === 'critique'
    ).length;

    // Rotation moyenne basée sur les mouvements
    const withMovements = summaryData.filter(ing => ing.nb_mouvements > 0);
    const avgRotation = withMovements.length > 0
      ? withMovements.reduce((sum, ing) => sum + (ing.nb_mouvements || 0), 0) / withMovements.length / 30
      : 0;

    return {
      totalValue,
      activeCount: activeCount || summaryData.length,
      alertCount,
      avgRotation: avgRotation > 0 ? avgRotation.toFixed(1) : '—',
      totalIngredients: summaryData.length,
    };
  }, [summaryData]);

  // Enrichir les données du summary avec niveau et statut formaté
  const enrichedIngredients = useMemo(() => {
    return summaryData.map(ing => {
      const stock = ing.stock_actuel || 0;
      const stockMin = ing.stock_min || 5;
      // Calculer le ratio (stock / stock_min * 2 pour avoir 50% = seuil min)
      const ratio = stockMin > 0 ? Math.min(100, Math.max(0, (stock / (stockMin * 2)) * 100)) : 50;

      // Calculer jours restants basé sur la conso moyenne
      const consoMoyenne = ing.nb_mouvements ? ing.nb_mouvements / 30 : 0;
      const joursRestants = consoMoyenne > 0 && stock > 0 ? stock / consoMoyenne : null;

      // Mapper statut_stock à notre système
      let status = 'ok';
      if (ing.statut_stock === 'rupture' || stock <= 0) {
        status = 'rupture';
      } else if (ing.statut_stock === 'critique' || (stockMin > 0 && stock < stockMin)) {
        status = 'critique';
      }

      return {
        ...ing,
        ratio,
        status,
        joursRestants,
      };
    });
  }, [summaryData]);

  // Filtrage par tab
  const filteredIngredients = useMemo(() => {
    if (activeTab === 'all') return enrichedIngredients;
    return enrichedIngredients.filter(ing => ing.status === activeTab);
  }, [enrichedIngredients, activeTab]);

  // Alertes (ingrédients en rupture ou critique) - les plus urgents en premier
  const alerts = useMemo(() => {
    return enrichedIngredients
      .filter(ing => ing.status === 'rupture' || ing.status === 'critique')
      .sort((a, b) => (a.stock_actuel || 0) - (b.stock_actuel || 0))
      .slice(0, 8)
      .map(ing => ({
        id: ing.ingredient_id,
        nom: ing.ingredient_nom,
        type: ing.status,
        stock: ing.stock_actuel || 0,
        seuil: ing.stock_min || 5,
        unite: ing.unite_base || 'kg',
        categorie: ing.categorie,
      }));
  }, [enrichedIngredients]);

  // Mouvements récents formatés
  const recentMovements = useMemo(() => {
    return movements.slice(0, 8).map(m => ({
      id: m.id,
      type: m.type_mouvement?.toLowerCase() === 'entree' ? 'in' : 'out',
      label: m.source || m.commentaire || (m.type_mouvement?.toLowerCase() === 'entree' ? 'Réception' : 'Sortie'),
      ingredient: m.ingredient_nom || 'Inconnu',
      quantite: m.quantite || 0,
      unite: m.unite || '',
      date: m.date_mouvement,
    }));
  }, [movements]);

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
      case 'rupture': return 'bg-rose-500/20 text-rose-400';
      case 'critique': return 'bg-amber-500/20 text-amber-400';
      default: return 'bg-emerald-500/20 text-emerald-400';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'rupture': return 'Rupture';
      case 'critique': return 'Critique';
      default: return 'OK';
    }
  };

  const getLevelColor = (status) => {
    switch (status) {
      case 'rupture': return 'bg-rose-500';
      case 'critique': return 'bg-amber-500';
      default: return 'bg-emerald-500';
    }
  };

  // Compteurs par statut pour les tabs
  const statusCounts = useMemo(() => ({
    all: enrichedIngredients.length,
    rupture: enrichedIngredients.filter(i => i.status === 'rupture').length,
    critique: enrichedIngredients.filter(i => i.status === 'critique').length,
    ok: enrichedIngredients.filter(i => i.status === 'ok').length,
  }), [enrichedIngredients]);

  // Loading et erreur
  const isLoading = summaryQuery.isLoading || movementsQuery.isLoading;

  if (summaryQuery.isError && !summaryData.length) {
    return <QueryErrorState error={summaryQuery.error} onRetry={() => summaryQuery.refetch()} variant="full" />;
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
          <span className="text-white">Stock</span>
        </nav>

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent font-['Sora',sans-serif]">
              📦 Stock Ingrédients
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              {stats.totalIngredients} ingrédients • Dernière mise à jour: temps réel
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => toast.info('Inventaire en cours de développement')}
              className="px-4 py-2.5 bg-white/6 border border-white/15 rounded-xl text-white text-sm font-medium flex items-center gap-2 hover:bg-white/10 transition-colors"
            >
              <ClipboardList className="w-4 h-4" />
              Inventaire
            </button>
            <button
              onClick={() => toast.info('Ajout de mouvement en cours de développement')}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold flex items-center gap-2 transition-all"
            >
              <Plus className="w-4 h-4" />
              Mouvement
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Valeur stock</p>
            <p className="text-2xl font-bold text-white">{formatCurrency(stats.totalValue)}</p>
            <p className="text-xs text-slate-500 mt-1">Stock positif uniquement</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Ingrédients actifs</p>
            <p className="text-2xl font-bold text-white">{stats.activeCount}</p>
            <p className="text-xs text-slate-500 mt-1">sur {stats.totalIngredients} total</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Alertes stock</p>
            <p className="text-2xl font-bold text-amber-400">{stats.alertCount}</p>
            <p className="text-xs text-slate-500 mt-1">rupture ou critique</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Rotation moyenne</p>
            <p className="text-2xl font-bold text-white">{stats.avgRotation} mvt/j</p>
            <p className="text-xs text-slate-500 mt-1">30 derniers jours</p>
          </div>
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
          {/* Stock Table */}
          <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-base font-semibold text-white">Niveaux de stock</h3>
              <button
                onClick={() => toast.info('Export en cours...')}
                className="px-3 py-1.5 bg-orange-500/10 border border-orange-500/30 rounded-lg text-orange-400 text-xs font-medium flex items-center gap-2 hover:bg-orange-500/20 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Exporter
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-white/3 p-1 rounded-lg w-fit mb-4">
              {TAB_OPTIONS.map(tab => (
                <button
                  key={tab.value}
                  onClick={() => setActiveTab(tab.value)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                    activeTab === tab.value
                      ? 'bg-orange-500/20 text-orange-400'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                  <span className="text-xs opacity-70">({statusCounts[tab.value]})</span>
                </button>
              ))}
            </div>

            {/* Table */}
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center py-12 text-slate-400">
                  Chargement des données...
                </div>
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 bg-slate-900/95">
                    <tr className="border-b border-white/10">
                      <th className="text-left py-3 px-3 text-xs uppercase text-slate-400 font-medium">Ingrédient</th>
                      <th className="text-left py-3 px-3 text-xs uppercase text-slate-400 font-medium">Stock</th>
                      <th className="text-left py-3 px-3 text-xs uppercase text-slate-400 font-medium">Niveau</th>
                      <th className="text-left py-3 px-3 text-xs uppercase text-slate-400 font-medium">Statut</th>
                      <th className="text-left py-3 px-3 text-xs uppercase text-slate-400 font-medium">Catégorie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredIngredients.map((ing, idx) => (
                      <motion.tr
                        key={ing.ingredient_id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: Math.min(idx * 0.02, 0.5) }}
                        className="border-b border-white/5 hover:bg-white/3 cursor-pointer transition-colors"
                        onClick={() => toast.info(`Détail ${ing.ingredient_nom}`)}
                      >
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2.5">
                            <span className="text-lg">{getIngredientIcon(ing.ingredient_nom)}</span>
                            <span className="text-sm text-white truncate max-w-[200px]">{ing.ingredient_nom}</span>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-sm text-slate-300">
                          <span className={ing.stock_actuel < 0 ? 'text-rose-400' : ''}>
                            {(ing.stock_actuel || 0).toFixed(1)} {ing.unite_base || ''}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <div className="w-12 h-1.5 bg-white/10 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${ing.ratio}%` }}
                                transition={{ delay: Math.min(idx * 0.02, 0.5), duration: 0.5 }}
                                className={`h-full rounded-full ${getLevelColor(ing.status)}`}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-1 rounded-md text-xs font-semibold ${getStatusClass(ing.status)}`}>
                            {getStatusLabel(ing.status)}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-xs text-slate-400 truncate max-w-[150px]">
                          {ing.categorie || '—'}
                        </td>
                      </motion.tr>
                    ))}

                    {filteredIngredients.length === 0 && (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-500">
                          Aucun ingrédient dans cette catégorie
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Sidebar: Alerts + Movements */}
          <div className="flex flex-col gap-6">
            {/* Alerts */}
            <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Alertes ({alerts.length})
              </h3>
              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {alerts.map((alert, idx) => (
                  <motion.div
                    key={alert.id}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    onClick={() => toast.info(`Commander ${alert.nom}`)}
                    className={`p-3 rounded-xl cursor-pointer transition-all hover:translate-x-1 ${
                      alert.type === 'rupture'
                        ? 'bg-rose-500/10 border-l-[3px] border-rose-500'
                        : 'bg-amber-500/10 border-l-[3px] border-amber-500'
                    }`}
                  >
                    <p className="text-sm font-medium text-white mb-1 truncate">
                      {alert.nom}
                    </p>
                    <p className="text-xs text-slate-400">
                      Stock: {alert.stock.toFixed(1)}{alert.unite} • {alert.type === 'rupture' ? 'Rupture' : 'Critique'}
                    </p>
                  </motion.div>
                ))}

                {alerts.length === 0 && (
                  <p className="text-sm text-slate-500 text-center py-4">Aucune alerte</p>
                )}
              </div>
            </div>

            {/* Recent Movements */}
            <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
              <h3 className="text-base font-semibold text-white mb-4">📦 Mouvements récents</h3>
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {recentMovements.map((m, idx) => (
                  <motion.div
                    key={m.id || idx}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`flex items-center justify-between p-2.5 bg-white/3 rounded-lg ${
                      m.type === 'in'
                        ? 'border-l-[3px] border-emerald-500'
                        : 'border-l-[3px] border-rose-500'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-slate-300 truncate block">{m.label}</span>
                      <span className="text-xs text-slate-500">{m.ingredient}</span>
                    </div>
                    <span className={`text-sm font-medium whitespace-nowrap ${
                      m.type === 'in' ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {m.type === 'in' ? '+' : '-'}{m.quantite} {m.unite}
                    </span>
                  </motion.div>
                ))}

                {recentMovements.length === 0 && (
                  <p className="text-sm text-slate-500 text-center py-4">Aucun mouvement récent</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
