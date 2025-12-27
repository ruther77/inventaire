/**
 * Page Menus et Coûts Restaurant.
 *
 * Cette page permet de gérer les fiches techniques des plats et d'analyser leur rentabilité.
 * Elle affiche:
 * - Les métriques globales (marge moyenne, food cost moyen, nombre de plats)
 * - Une liste complète des plats avec leurs coûts et marges
 * - Les alertes sur les ingrédients manquants ou problématiques
 * - Un modal de détail par plat avec décomposition des coûts
 * - Un simulateur d'impact prix pour optimiser les marges
 *
 * Fonctionnalités principales:
 * - Affichage du food cost et de la marge par plat
 * - Décomposition détaillée des coûts par ingrédient
 * - Simulation de hausse de prix (+5%, +10%) avec impact sur marge et food cost
 * - Recalcul automatique des coûts après mise à jour des prix d'achat
 * - Détection des ingrédients avec coût élevé ou données manquantes
 * - Badges visuels pour identifier rapidement les plats problématiques
 *
 * @component
 *
 * @example
 * <RestaurantMenusCostsPage />
 */

import { useState } from 'react';
import { Card, Button, SectionHeader, Badge } from '@/components/ui';
import { useRestaurantMenusOverview, useRestaurantPlatDetails, useSimulatePlatPrice } from '@/hooks/useRestaurant.js';
import api from '@/api/client.js';
import { AlertTriangle, Utensils, Percent, TrendingUp, Info, Play } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

function Metric({ label, value, icon: Icon, accent }) {
  return (
    <div className="p-4 rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center gap-2 text-sm text-slate-500">
        {Icon && <Icon className={`w-4 h-4 ${accent || 'text-slate-400'}`} />}
        <span>{label}</span>
      </div>
      <p className="text-2xl font-semibold text-slate-900 mt-1">{value}</p>
    </div>
  );
}

/**
 * Modal de détail d'un plat avec simulateur de prix.
 *
 * Affiche la fiche technique complète d'un plat et permet de simuler
 * l'impact d'une hausse de prix sur la marge et le food cost.
 */
function PlatDetailModal({ plat, onClose }) {
  const simulateMutation = useSimulatePlatPrice();
  const [simulation, setSimulation] = useState(null);

  // Simuler une hausse de prix et calculer les nouveaux indicateurs
  const simulate = (deltaPct) => {
    if (!plat?.id) return;
    const newPrice = plat.selling_price * (1 + deltaPct / 100);
    simulateMutation.mutate(
      { platId: plat.id, payload: { new_price: Number(newPrice.toFixed(2)) } },
      {
        onSuccess: (data) => setSimulation(data),
      }
    );
  };

  if (!plat) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60 px-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Fiche technique</p>
            <h3 className="text-xl font-semibold text-slate-900">{plat.nom}</h3>
          </div>
          <Button size="sm" variant="ghost" onClick={onClose}>Fermer</Button>
        </div>

        <div className="grid md:grid-cols-2 gap-4 px-6 py-4">
          <Card>
            <div className="p-4">
              <p className="text-sm font-semibold text-slate-800 mb-2">Coûts & marges</p>
              <div className="space-y-2 text-sm text-slate-600">
                <div className="flex justify-between"><span>Prix de vente</span><span>{plat.selling_price.toFixed(2)} €</span></div>
                <div className="flex justify-between"><span>Coût matière</span><span>{plat.cost.toFixed(2)} €</span></div>
                <div className="flex justify-between"><span>Marge</span><span>{plat.margin_pct.toFixed(1)}%</span></div>
                <div className="flex justify-between"><span>Food cost</span><span>{plat.food_cost_pct.toFixed(1)}%</span></div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <p className="text-sm font-semibold text-slate-800 mb-3">Ingrédients</p>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {plat.ingredients.map((ing) => (
                  <div key={ing.ingredient_id} className="flex justify-between text-sm">
                    <div>
                      <p className="font-semibold text-slate-900">{ing.nom}</p>
                      <p className="text-xs text-slate-500">{ing.quantite} {ing.unite}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-slate-900">{ing.total_cost.toFixed(2)} €</p>
                      <p className="text-xs text-slate-500">{ing.cost_percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>

        <div className="px-6 pb-6">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm font-semibold text-slate-800">Actions rapides</p>
                <p className="text-xs text-slate-500">Simuler une hausse de prix pour voir l’impact marge/FC</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => simulate(5)} loading={simulateMutation.isLoading}>
                  <Play className="w-4 h-4 mr-2" /> +5%
                </Button>
                <Button size="sm" variant="secondary" onClick={() => simulate(10)} loading={simulateMutation.isLoading}>
                  <Play className="w-4 h-4 mr-2" /> +10%
                </Button>
              </div>
            </div>

            {simulation && (
              <div className="grid md:grid-cols-3 gap-3 text-sm">
                <div className="p-3 rounded-lg bg-white border border-slate-200">
                  <p className="text-slate-500">Prix simulé</p>
                  <p className="text-lg font-semibold text-slate-900">{simulation.simulated.selling_price.toFixed(2)} €</p>
                </div>
                <div className="p-3 rounded-lg bg-white border border-slate-200">
                  <p className="text-slate-500">Marge simulée</p>
                  <p className="text-lg font-semibold text-emerald-700">{simulation.simulated.margin_pct.toFixed(1)}%</p>
                </div>
                <div className="p-3 rounded-lg bg-white border border-slate-200">
                  <p className="text-slate-500">Food cost simulé</p>
                  <p className="text-lg font-semibold text-slate-900">{simulation.simulated.food_cost_pct.toFixed(1)}%</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RestaurantMenusCostsPage() {
  const overviewQuery = useRestaurantMenusOverview();
  const [selectedPlatId, setSelectedPlatId] = useState(null);
  const platDetailQuery = useRestaurantPlatDetails(selectedPlatId);
  const queryClient = useQueryClient();

  const recomputeCosts = useMutation({
    mutationFn: (threshold = 35) => api.post('/restaurant/plats/recompute-costs', threshold),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'menus', 'overview'] });
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'plat', 'details'] });
    },
  });

  const overview = overviewQuery.data || {};
  const platCosts = overview.plat_costs || [];
  const metrics = overview.metrics || {};
  const alerts = overview.ingredient_alerts || [];

  const formatPct = (v = 0) => `${(v || 0).toFixed(1)}%`;

  return (
    <div className="flex flex-col gap-6">
      <SectionHeader
        title="Menus & Coûts"
        subtitle="Gestion des fiches techniques, marges et food cost"
        icon={Utensils}
      />

      <div className="flex justify-end gap-2">
        <Button size="sm" variant="secondary" onClick={() => recomputeCosts.mutate(35)} loading={recomputeCosts.isLoading}>
          Recalculer les coûts
        </Button>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        <Metric label="Plats actifs" value={metrics.total_plats ?? '—'} icon={Utensils} accent="text-orange-500" />
        <Metric label="Food Cost moyen" value={formatPct(metrics.avg_food_cost_pct)} icon={Percent} accent="text-emerald-500" />
        <Metric label="Alertes ingrédients" value={metrics.alerts_count ?? 0} icon={AlertTriangle} accent="text-amber-500" />
        <Metric label="Top marge" value={metrics.top_plats?.[0]?.nom ?? '—'} icon={TrendingUp} accent="text-blue-500" />
      </div>

      <Card>
        <div className="p-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">Fiches techniques</h3>
          {overviewQuery.isFetching && <span className="text-xs text-slate-500">Rafraîchissement...</span>}
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500">Plat</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Prix</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Coût</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Food cost</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Marge</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {overviewQuery.isLoading ? (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-500">Chargement...</td></tr>
              ) : platCosts.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-500">Aucun plat trouvé</td></tr>
              ) : (
                platCosts.map((plat) => (
                  <tr key={plat.plat_id} className="hover:bg-slate-50 cursor-pointer" onClick={() => setSelectedPlatId(plat.plat_id)}>
                    <td className="px-4 py-3 text-sm font-semibold text-slate-900">{plat.nom}</td>
                    <td className="px-4 py-3 text-right text-sm text-slate-700">{plat.prix_vente_ttc.toFixed(2)} €</td>
                    <td className="px-4 py-3 text-right text-sm text-slate-700">{plat.cout_matiere.toFixed(2)} €</td>
                    <td className="px-4 py-3 text-right text-sm text-slate-700">{formatPct(plat.food_cost_pct)}</td>
                    <td className="px-4 py-3 text-right text-sm font-semibold text-slate-900">{formatPct(plat.marge_pct)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <h3 className="text-lg font-semibold text-slate-900">Alertes ingrédients</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {alerts.length === 0 ? (
            <div className="p-4 text-sm text-slate-500 flex items-center gap-2">
              <Info className="w-4 h-4" /> Aucun stock critique détecté.
            </div>
          ) : alerts.map((alert) => (
            <div key={alert.ingredient_id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-semibold text-slate-900">{alert.nom}</p>
                <p className="text-xs text-slate-500">Stock: {alert.stock_actuel}</p>
              </div>
              <Badge variant={alert.status === 'rupture' ? 'danger' : 'warning'}>
                {alert.status}
              </Badge>
            </div>
          ))}
        </div>
      </Card>

      {selectedPlatId && (
        <PlatDetailModal
          plat={platDetailQuery.data}
          onClose={() => setSelectedPlatId(null)}
        />
      )}
    </div>
  );
}
