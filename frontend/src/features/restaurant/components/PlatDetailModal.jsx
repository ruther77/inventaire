import { useState } from 'react';
import { Modal, Button, Badge } from '@/components/ui';
import { X, TrendingUp, Utensils, DollarSign, Percent } from 'lucide-react';
import CostBreakdownChart from './CostBreakdownChart.jsx';
import PriceSimulatorPanel from './PriceSimulatorPanel.jsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

/**
 * PlatDetailModal - Modal détaillé d'un plat avec fiche technique
 *
 * Props:
 * - plat: {
 *     id, nom, categorie, prix_vente_ttc, cout_matiere, marge_brute, marge_pct,
 *     food_cost_pct, actif, ingredients: Array, price_history: Array
 *   }
 * - isOpen: boolean
 * - onClose: () => void
 * - onUpdatePrice: (platId, newPrice) => Promise<void>
 */
export default function PlatDetailModal({ plat, isOpen, onClose, onUpdatePrice }) {
  const [activeTab, setActiveTab] = useState('fiche'); // 'fiche' | 'history' | 'simulator'

  if (!plat) return null;

  const {
    id,
    nom,
    categorie,
    prix_vente_ttc = 0,
    cout_matiere = 0,
    marge_brute = 0,
    marge_pct = 0,
    food_cost_pct = 0,
    actif = true,
    ingredients = [],
    price_history = [],
  } = plat;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value) => `${value?.toFixed(1) || 0}%`;

  // Préparer les données pour le graphique de décomposition
  const costBreakdownData = ingredients.map((ing) => ({
    name: ing.nom,
    value: ing.cout_total,
    percentage: (ing.cout_total / cout_matiere) * 100,
    unite: ing.unite,
  }));

  const getMarginColor = (value) => {
    if (value > 60) return 'emerald';
    if (value >= 40) return 'amber';
    return 'rose';
  };

  const getFoodCostColor = (value) => {
    if (value < 30) return 'emerald';
    if (value <= 35) return 'amber';
    return 'rose';
  };

  const marginColor = getMarginColor(marge_pct);
  const foodCostColor = getFoodCostColor(food_cost_pct);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <div className="flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-slate-200">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <Utensils className="w-6 h-6 text-slate-600" />
              <h2 className="text-2xl font-bold text-slate-900">{nom}</h2>
              <Badge variant={actif ? 'success' : 'default'}>
                {actif ? 'Actif' : 'Inactif'}
              </Badge>
            </div>
            {categorie && (
              <p className="text-sm text-slate-500 uppercase tracking-wider">{categorie}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-600" />
          </button>
        </div>

        {/* KPIs rapides */}
        <div className="grid grid-cols-4 gap-4 p-6 border-b border-slate-200 bg-slate-50">
          <div>
            <p className="text-xs text-slate-500 mb-1">Prix de vente TTC</p>
            <p className="text-xl font-bold text-slate-900">{formatCurrency(prix_vente_ttc)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Coût matière</p>
            <p className="text-xl font-bold text-slate-900">{formatCurrency(cout_matiere)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Marge</p>
            <p className={`text-xl font-bold text-${marginColor}-600`}>{formatPercent(marge_pct)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Food Cost</p>
            <p className={`text-xl font-bold text-${foodCostColor}-600`}>{formatPercent(food_cost_pct)}</p>
          </div>
        </div>

        {/* Onglets */}
        <div className="flex gap-1 px-6 pt-4 border-b border-slate-200">
          <button
            onClick={() => setActiveTab('fiche')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'fiche'
                ? 'bg-white text-blue-600 border-t border-x border-slate-200'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            Fiche technique
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'history'
                ? 'bg-white text-blue-600 border-t border-x border-slate-200'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            Historique prix
          </button>
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'simulator'
                ? 'bg-white text-blue-600 border-t border-x border-slate-200'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            Simulateur
          </button>
        </div>

        {/* Contenu */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Fiche technique */}
          {activeTab === 'fiche' && (
            <div className="space-y-6">
              {/* Ingrédients */}
              <div>
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Ingrédients</h3>
                {ingredients.length === 0 ? (
                  <p className="text-sm text-slate-500">Aucun ingrédient renseigné</p>
                ) : (
                  <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-slate-200">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                            Ingrédient
                          </th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                            Quantité
                          </th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                            Prix unitaire
                          </th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                            Coût total
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-slate-200">
                        {ingredients.map((ing, idx) => (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="px-4 py-3 text-sm font-medium text-slate-900">{ing.nom}</td>
                            <td className="px-4 py-3 text-sm text-slate-600 text-right">
                              {ing.quantite} {ing.unite}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-600 text-right">
                              {formatCurrency(ing.prix_unitaire)}
                            </td>
                            <td className="px-4 py-3 text-sm font-semibold text-slate-900 text-right">
                              {formatCurrency(ing.cout_total)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-slate-50">
                        <tr>
                          <td colSpan="3" className="px-4 py-3 text-sm font-semibold text-slate-900">
                            Total coût matière
                          </td>
                          <td className="px-4 py-3 text-sm font-bold text-slate-900 text-right">
                            {formatCurrency(cout_matiere)}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </div>

              {/* Graphique de décomposition */}
              {ingredients.length > 0 && (
                <CostBreakdownChart
                  data={costBreakdownData}
                  title="Répartition des coûts par ingrédient"
                />
              )}
            </div>
          )}

          {/* Historique des prix */}
          {activeTab === 'history' && (
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Historique des prix</h3>
              {price_history.length === 0 ? (
                <p className="text-sm text-slate-500">Aucun historique disponible</p>
              ) : (
                <div>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={price_history} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: '12px' }} />
                      <YAxis stroke="#64748b" style={{ fontSize: '12px' }} tickFormatter={(v) => `${v}€`} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#fff',
                          border: '1px solid #e2e8f0',
                          borderRadius: '8px',
                        }}
                        formatter={(value) => [`${formatCurrency(value)}`, 'Prix']}
                      />
                      <Line
                        type="monotone"
                        dataKey="prix"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={{ fill: '#3b82f6', r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>

                  <div className="mt-6 bg-white border border-slate-200 rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-slate-200">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase">Prix</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase">Évolution</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-slate-200">
                        {price_history.map((entry, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-3 text-sm text-slate-900">{entry.date}</td>
                            <td className="px-4 py-3 text-sm font-semibold text-slate-900 text-right">
                              {formatCurrency(entry.prix)}
                            </td>
                            <td className="px-4 py-3 text-sm text-right">
                              {entry.evolution !== undefined && (
                                <span className={entry.evolution > 0 ? 'text-emerald-600' : entry.evolution < 0 ? 'text-rose-600' : 'text-slate-600'}>
                                  {entry.evolution > 0 ? '+' : ''}{entry.evolution.toFixed(1)}%
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Simulateur */}
          {activeTab === 'simulator' && (
            <PriceSimulatorPanel
              platData={plat}
              onApply={async (newPrice) => {
                if (onUpdatePrice) {
                  await onUpdatePrice(id, newPrice);
                  onClose();
                }
              }}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-6 border-t border-slate-200 bg-slate-50">
          <Button variant="outline" onClick={onClose}>
            Fermer
          </Button>
        </div>
      </div>
    </Modal>
  );
}
