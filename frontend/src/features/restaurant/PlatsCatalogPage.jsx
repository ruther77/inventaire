import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRestaurantPlats, useUpdateRestaurantPlatPrice, useRestaurantDashboard, useRestaurantPlatPriceHistory } from '@/hooks/useRestaurant.js';
import { PlatDetailModal, AddPlatModal, PlatDetailDrawer, PriceSimulatorPanel } from './components';
import { Plus, TrendingUp, TrendingDown, ChefHat, Search, Filter, HelpCircle, X, History, Calculator } from 'lucide-react';
import QueryErrorState from '@/components/feedback/QueryErrorState.jsx';
import Modal from '@/components/ui/Modal.jsx';
import { toast } from 'sonner';

/**
 * PlatsCatalogPage - Vue unifiée Restaurant
 * Design from mockups/restaurant.html - Dark Theme 2025
 */

const TABS = [
  { id: 'foodcost', label: 'Food Cost & Plats' },
  { id: 'ingredients', label: 'Ingrédients & Prix' },
  { id: 'stock', label: 'Stock & Consommations' },
];

export default function PlatsCatalogPage() {
  const [activeTab, setActiveTab] = useState('foodcost');
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [selectedPlat, setSelectedPlat] = useState(null);
  const [drawerPlat, setDrawerPlat] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [simulatorPlat, setSimulatorPlat] = useState(null);
  const [historyPlat, setHistoryPlat] = useState(null);

  // Queries
  const platsQuery = useRestaurantPlats();
  const dashboardQuery = useRestaurantDashboard();
  const updatePriceMutation = useUpdateRestaurantPlatPrice();
  const historyQuery = useRestaurantPlatPriceHistory(historyPlat?.id);

  const plats = platsQuery.data || [];
  const dashboard = dashboardQuery.data || {};

  // Catégories uniques
  const categories = useMemo(() => {
    const cats = new Set(plats.map(p => p.categorie).filter(Boolean));
    return Array.from(cats);
  }, [plats]);

  // Filtrage
  const filteredPlats = useMemo(() => {
    return plats.filter(plat => {
      if (search && !plat.nom.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      if (categoryFilter && plat.categorie !== categoryFilter) {
        return false;
      }
      return true;
    });
  }, [plats, search, categoryFilter]);

  // Stats calculées
  const stats = useMemo(() => {
    if (!filteredPlats.length) {
      return {
        avgFoodCost: 0,
        avgPrice: 0,
        avgCost: 0,
        avgMargin: 0,
        activeCount: 0,
        bestPlat: null,
      };
    }
    const avgFoodCost = filteredPlats.reduce((acc, p) => acc + (p.food_cost_pct || 0), 0) / filteredPlats.length;
    const avgPrice = filteredPlats.reduce((acc, p) => acc + (p.prix_vente_ttc || 0), 0) / filteredPlats.length;
    const avgCost = filteredPlats.reduce((acc, p) => acc + (p.cout_matiere || 0), 0) / filteredPlats.length;
    const avgMargin = avgPrice - avgCost;
    const activeCount = filteredPlats.filter(p => p.actif).length;

    // Plat le plus rentable (food cost le plus bas)
    const sortedByFC = [...filteredPlats].sort((a, b) => (a.food_cost_pct || 100) - (b.food_cost_pct || 100));
    const bestPlat = sortedByFC[0];

    return { avgFoodCost, avgPrice, avgCost, avgMargin, activeCount, bestPlat };
  }, [filteredPlats]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value || 0);
  };

  const getFoodCostColor = (fc) => {
    if (fc < 30) return 'emerald';
    if (fc <= 35) return 'amber';
    return 'rose';
  };

  const getFoodCostStatus = (fc) => {
    if (fc < 30) return { text: '✓ Objectif atteint (<30%)', color: 'text-emerald-400' };
    if (fc <= 35) return { text: '⚠ Attention (30-35%)', color: 'text-amber-400' };
    return { text: '✗ À optimiser (>35%)', color: 'text-rose-400' };
  };

  const handleUpdatePrice = async (platId, newPrice) => {
    await updatePriceMutation.mutateAsync({
      platId,
      payload: { prix_vente_ttc: newPrice },
    });
  };

  // Erreur
  if (platsQuery.isError && !plats.length) {
    return <QueryErrorState error={platsQuery.error} onRetry={() => platsQuery.refetch()} variant="full" />;
  }

  const fcStatus = getFoodCostStatus(stats.avgFoodCost);
  const fcColor = getFoodCostColor(stats.avgFoodCost);

  return (
    <div className="min-h-screen p-6 md:p-8">
      <div className="max-w-[1600px] mx-auto">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-orange-500/20 to-amber-500/20 border border-white/10">
              <ChefHat className="w-8 h-8 text-orange-400" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-white font-['Sora',sans-serif]">
                Restaurant
              </h1>
              <p className="text-lg text-slate-400 mt-1">
                Gestion des plats, ingrédients & food cost
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <div className={`px-5 py-3 rounded-full font-semibold text-base border ${
              fcColor === 'emerald'
                ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                : fcColor === 'amber'
                ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                : 'bg-rose-500/15 border-rose-500/30 text-rose-400'
            }`}>
              Food Cost: {stats.avgFoodCost.toFixed(0)}%
            </div>
            <div className="px-5 py-3 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 font-semibold text-base">
              {stats.activeCount} plats actifs
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-5 py-3 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold flex items-center gap-2 transition-all"
            >
              <Plus className="w-5 h-5" />
              Nouveau plat
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 p-1.5 bg-white/5 rounded-2xl mb-8 overflow-x-auto">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-xl font-semibold text-sm whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-orange-500/30 to-amber-500/20 text-white'
                  : 'text-slate-400 hover:bg-white/8 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Food Cost Hero */}
        <div className="bg-white/6 backdrop-blur-md border border-white/15 rounded-3xl p-12 text-center mb-8">
          <h2 className="text-xl font-semibold text-slate-400 mb-4">FOOD COST MOYEN</h2>
          <div className={`text-7xl md:text-8xl font-bold font-['Sora',sans-serif] mb-4 ${
            fcColor === 'emerald'
              ? 'bg-gradient-to-r from-emerald-400 to-emerald-300'
              : fcColor === 'amber'
              ? 'bg-gradient-to-r from-amber-400 to-amber-300'
              : 'bg-gradient-to-r from-rose-400 to-rose-300'
          } bg-clip-text text-transparent`}>
            {stats.avgFoodCost.toFixed(0)}%
          </div>
          <p className={`text-lg font-semibold ${fcStatus.color}`}>
            {fcStatus.text}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/6 backdrop-blur-md border border-white/15 rounded-2xl p-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">Prix Moyen Plat</p>
            <p className="text-3xl font-bold text-white font-['Sora',sans-serif]">{formatCurrency(stats.avgPrice)}</p>
            <p className="text-sm text-slate-400 mt-2">Sur {filteredPlats.length} plats</p>
          </div>
          <div className="bg-white/6 backdrop-blur-md border border-white/15 rounded-2xl p-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">Coût Moyen Matière</p>
            <p className="text-3xl font-bold text-white font-['Sora',sans-serif]">{formatCurrency(stats.avgCost)}</p>
            <p className="text-sm text-slate-400 mt-2">Optimisation possible</p>
          </div>
          <div className="bg-white/6 backdrop-blur-md border border-white/15 rounded-2xl p-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">Marge Moyenne</p>
            <p className="text-3xl font-bold text-white font-['Sora',sans-serif]">{formatCurrency(stats.avgMargin)}</p>
            <p className="text-sm text-slate-400 mt-2">{((stats.avgMargin / stats.avgPrice) * 100 || 0).toFixed(0)}% de marge brute</p>
          </div>
          <div className="bg-white/6 backdrop-blur-md border border-white/15 rounded-2xl p-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">Plat le + Rentable</p>
            <p className="text-3xl font-bold text-white font-['Sora',sans-serif]">{stats.bestPlat?.nom || '—'}</p>
            <p className="text-sm text-slate-400 mt-2">
              {stats.bestPlat ? `${stats.bestPlat.food_cost_pct?.toFixed(0)}% food cost` : 'Aucun plat'}
            </p>
          </div>
        </div>

        {/* Filtres */}
        <div className="flex flex-wrap gap-4 mb-8">
          <div className="relative flex-1 min-w-[250px]">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder="Rechercher un plat..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/6 border border-white/10 text-white placeholder-slate-500 focus:border-orange-500/50 focus:outline-none focus:ring-2 focus:ring-orange-500/20"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-3 rounded-xl bg-white/6 border border-white/10 text-white focus:border-orange-500/50 focus:outline-none min-w-[180px] appearance-none cursor-pointer"
          >
            <option value="" className="bg-slate-800">Toutes catégories</option>
            {categories.map(cat => (
              <option key={cat} value={cat} className="bg-slate-800">{cat}</option>
            ))}
          </select>
        </div>

        {/* Plats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredPlats.map((plat, index) => {
              const fc = plat.food_cost_pct || 0;
              const fcCol = getFoodCostColor(fc);
              const marge = (plat.prix_vente_ttc || 0) - (plat.cout_matiere || 0);
              const ingredients = plat.ingredients || [];

              return (
                <motion.div
                  key={plat.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: index * 0.03 }}
                  onClick={() => setDrawerPlat(plat)}
                  className="bg-white/6 backdrop-blur-md border border-white/15 rounded-2xl overflow-hidden cursor-pointer transition-all hover:bg-white/10 hover:border-white/25 hover:-translate-y-1 hover:shadow-2xl hover:shadow-black/40"
                >
                  {/* Image / Emoji */}
                  <div className="h-44 bg-gradient-to-br from-orange-500/20 to-amber-500/10 flex items-center justify-center relative">
                    <span className="text-6xl">{plat.type === 'bar' ? '🍺' : '🍽️'}</span>
                    <div className={`absolute top-3 right-3 px-4 py-2 rounded-full font-bold text-sm text-white backdrop-blur-md ${
                      fcCol === 'emerald' ? 'bg-emerald-500/90'
                      : fcCol === 'amber' ? 'bg-amber-500/90'
                      : 'bg-rose-500/90'
                    }`}>
                      {fc.toFixed(0)}%
                    </div>
                    {!plat.actif && (
                      <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-slate-500/90 text-white text-xs font-medium">
                        Inactif
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-5">
                    <h3 className="text-xl font-bold text-white mb-1">{plat.nom}</h3>
                    <p className="text-xs text-slate-400 uppercase tracking-wider mb-4">
                      {plat.categorie || 'Non classé'} • {plat.type === 'bar' ? 'Bar' : 'Cuisine'}
                    </p>

                    {/* Metrics */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Prix de vente</p>
                        <p className="text-lg font-bold text-white">{formatCurrency(plat.prix_vente_ttc)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Coût matière</p>
                        <p className="text-lg font-bold text-white">{formatCurrency(plat.cout_matiere)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Marge</p>
                        <p className="text-lg font-bold text-emerald-400">{formatCurrency(marge)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Food Cost</p>
                        <p className={`text-lg font-bold ${
                          fcCol === 'emerald' ? 'text-emerald-400'
                          : fcCol === 'amber' ? 'text-amber-400'
                          : 'text-rose-400'
                        }`}>{fc.toFixed(1)}%</p>
                      </div>
                    </div>

                    {/* Ingredients */}
                    {ingredients.length > 0 && (
                      <div className="border-t border-white/10 pt-4 mt-4">
                        <p className="text-xs font-semibold text-slate-400 mb-2">
                          Ingrédients ({ingredients.length})
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {ingredients.slice(0, 5).map((ing, i) => (
                            <span key={i} className="px-2.5 py-1 bg-white/8 rounded-full text-xs text-slate-300">
                              {ing.nom || ing.ingredient_nom}
                            </span>
                          ))}
                          {ingredients.length > 5 && (
                            <span className="px-2.5 py-1 bg-white/8 rounded-full text-xs text-slate-500">
                              +{ingredients.length - 5}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 mt-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedPlat(plat);
                        }}
                        className="flex-1 py-2.5 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400 text-sm font-semibold hover:bg-blue-500/20 transition-all"
                      >
                        Modifier prix
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDrawerPlat(plat);
                        }}
                        className="flex-1 py-2.5 rounded-xl bg-white/5 border border-white/15 text-slate-300 text-sm font-semibold hover:bg-white/10 transition-all"
                      >
                        Détails
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* Empty State */}
        {filteredPlats.length === 0 && !platsQuery.isLoading && (
          <div className="text-center py-16">
            <ChefHat className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Aucun plat trouvé</h3>
            <p className="text-slate-400 mb-6">Modifiez vos filtres ou créez un nouveau plat</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold"
            >
              Créer un plat
            </button>
          </div>
        )}

        {/* Loading */}
        {platsQuery.isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-white/6 border border-white/15 rounded-2xl overflow-hidden animate-pulse">
                <div className="h-44 bg-white/10" />
                <div className="p-5 space-y-3">
                  <div className="h-6 bg-white/10 rounded w-3/4" />
                  <div className="h-4 bg-white/10 rounded w-1/2" />
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="h-12 bg-white/10 rounded" />
                    <div className="h-12 bg-white/10 rounded" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Help Tooltip */}
        <div className="fixed bottom-8 right-8 w-14 h-14 rounded-full bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center cursor-pointer shadow-lg shadow-orange-500/30 hover:scale-110 transition-transform">
          <HelpCircle className="w-6 h-6 text-white" />
        </div>
      </div>

      {/* Modals & Drawers */}
      <PlatDetailModal
        plat={selectedPlat}
        isOpen={!!selectedPlat}
        onClose={() => setSelectedPlat(null)}
        onUpdatePrice={handleUpdatePrice}
      />

      <PlatDetailDrawer
        open={!!drawerPlat}
        onClose={() => setDrawerPlat(null)}
        plat={drawerPlat}
        onEdit={(plat) => {
          setDrawerPlat(null);
          setSelectedPlat(plat);
        }}
        onHistory={(plat) => {
          setDrawerPlat(null);
          setHistoryPlat(plat);
        }}
        onSimulate={(plat) => {
          setDrawerPlat(null);
          setSimulatorPlat(plat);
        }}
        onAddIngredient={(plat) => {
          toast.info('Fonctionnalité d\'ajout d\'ingrédient en cours de développement');
        }}
      />

      <AddPlatModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          platsQuery.refetch();
          setShowCreateModal(false);
        }}
      />

      {/* Modal Historique des prix */}
      <Modal
        open={!!historyPlat}
        onClose={() => setHistoryPlat(null)}
        title={`Historique des prix - ${historyPlat?.nom || ''}`}
        size="lg"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-slate-400 mb-4">
            <History className="w-5 h-5" />
            <span>Évolution des prix de vente</span>
          </div>

          {historyQuery.isLoading ? (
            <div className="py-8 text-center text-slate-400">Chargement...</div>
          ) : historyQuery.data?.length > 0 ? (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {historyQuery.data.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                  <span className="text-sm text-slate-400">
                    {new Date(item.date || item.created_at).toLocaleDateString('fr-FR', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                    })}
                  </span>
                  <span className="text-sm font-semibold text-white">
                    {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: 'EUR',
                    }).format(item.prix || item.prix_vente_ttc || 0)}
                  </span>
                  {item.variation !== undefined && (
                    <span className={`text-xs font-medium ${
                      item.variation > 0 ? 'text-emerald-400' : item.variation < 0 ? 'text-rose-400' : 'text-slate-500'
                    }`}>
                      {item.variation > 0 ? '+' : ''}{item.variation?.toFixed(1)}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500">
              Aucun historique de prix disponible
            </div>
          )}
        </div>
      </Modal>

      {/* Modal Simulateur de prix */}
      <Modal
        open={!!simulatorPlat}
        onClose={() => setSimulatorPlat(null)}
        title={`Simulateur de prix - ${simulatorPlat?.nom || ''}`}
        size="lg"
      >
        {simulatorPlat && (
          <PriceSimulatorPanel
            platData={{
              id: simulatorPlat.id,
              nom: simulatorPlat.nom,
              prix_vente_ttc: simulatorPlat.prix_vente_ttc || 0,
              cout_matiere: simulatorPlat.cout_matiere || 0,
              marge_brute: (simulatorPlat.prix_vente_ttc || 0) - (simulatorPlat.cout_matiere || 0),
              marge_pct: simulatorPlat.marge_pct || 0,
              food_cost_pct: simulatorPlat.food_cost_pct || 0,
            }}
            onApply={async (newPrice) => {
              await handleUpdatePrice(simulatorPlat.id, newPrice);
              toast.success(`Prix mis à jour: ${new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(newPrice)}`);
              setSimulatorPlat(null);
              platsQuery.refetch();
            }}
          />
        )}
      </Modal>
    </div>
  );
}
