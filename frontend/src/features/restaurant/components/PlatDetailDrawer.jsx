import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Utensils,
  Edit3,
  History,
  Calculator,
  TrendingUp,
  ChevronRight,
  Plus,
} from 'lucide-react';
import Button from '@/components/ui/Button.jsx';

// ============================================================================
// PLATDETAILDRAWER - Drawer latéral pour afficher le détail d'un plat
// Design from mockups/restaurant-plats-detail.html
// ============================================================================

export default function PlatDetailDrawer({
  open,
  onClose,
  plat,
  onEdit,
  onHistory,
  onSimulate,
  onAddIngredient,
}) {
  if (!plat) return null;

  const {
    id,
    nom,
    categorie,
    prix_vente_ttc = 0,
    cout_matiere = 0,
    marge_pct = 0,
    food_cost_pct = 0,
    actif = true,
    ingredients = [],
  } = plat;

  const formatCurrency = (value) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value || 0);

  const formatPercent = (value) => `${(value || 0).toFixed(1)}%`;

  const getFoodCostColor = (v) => {
    if (v < 30) return 'text-emerald-400';
    if (v <= 35) return 'text-amber-400';
    return 'text-rose-400';
  };

  const getFoodCostBg = (v) => {
    if (v < 30) return 'bg-emerald-500/20 border-emerald-500/30';
    if (v <= 35) return 'bg-amber-500/20 border-amber-500/30';
    return 'bg-rose-500/20 border-rose-500/30';
  };

  // Normaliser les ingrédients
  const normalizedIngredients = (ingredients || []).map((ing) => {
    const unitPrice = ing.unit_price ?? ing.prix_unitaire ?? 0;
    const totalCost = ing.total_cost ?? ing.cout_total ?? unitPrice * (ing.quantite ?? 0);
    return { ...ing, unit_price: unitPrice, total_cost: totalCost };
  });

  const marge = prix_vente_ttc - cout_matiere;

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-slate-900 border-l border-white/10 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-white/10 bg-gradient-to-r from-orange-500/10 to-amber-500/5">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500/20 to-amber-500/20 border border-white/10 flex items-center justify-center text-3xl">
                  🥩
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{nom}</h2>
                  <p className="text-sm text-slate-400">
                    Catégorie: {categorie || 'Non classé'} • Réf: PLT-{String(id).padStart(3, '0')}
                  </p>
                  <div className="flex gap-2 mt-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                        actif
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                          : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                      }`}
                    >
                      {actif ? 'Actif' : 'Inactif'}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getFoodCostBg(
                        food_cost_pct
                      )} ${getFoodCostColor(food_cost_pct)}`}
                    >
                      Food Cost: {formatPercent(food_cost_pct)}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            {/* Actions */}
            <div className="flex gap-3 p-4 border-b border-white/10">
              <Button
                variant="primary"
                onClick={() => onEdit?.(plat)}
                className="flex-1 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600"
              >
                <Edit3 className="w-4 h-4" />
                Modifier
              </Button>
              <Button variant="ghost" onClick={() => onHistory?.(plat)} className="flex-1">
                <History className="w-4 h-4" />
                Historique
              </Button>
              <Button variant="ghost" onClick={() => onSimulate?.(plat)} className="flex-1">
                <Calculator className="w-4 h-4" />
                Simuler
              </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Rentabilité */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <span className="text-lg">💰</span>
                  Rentabilité
                </h3>

                <div className="text-center p-5 bg-gradient-to-br from-orange-500/10 to-amber-500/5 rounded-xl mb-4">
                  <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Prix de vente TTC</p>
                  <p className="text-3xl font-bold text-orange-400">{formatCurrency(prix_vente_ttc)}</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Coût matière</p>
                    <p className="text-lg font-semibold text-white">{formatCurrency(cout_matiere)}</p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Food Cost</p>
                    <p className={`text-lg font-semibold ${getFoodCostColor(food_cost_pct)}`}>
                      {formatPercent(food_cost_pct)}
                    </p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Marge brute</p>
                    <p className="text-lg font-semibold text-emerald-400">{formatCurrency(marge)}</p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Objectif FC</p>
                    <p className="text-lg font-semibold text-white">&lt;30%</p>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-4">
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        food_cost_pct < 30
                          ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                          : food_cost_pct <= 35
                          ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                          : 'bg-gradient-to-r from-rose-500 to-rose-400'
                      }`}
                      style={{ width: `${Math.min(food_cost_pct, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>0%</span>
                    <span>Objectif: 30%</span>
                    <span>50%</span>
                  </div>
                </div>
              </div>

              {/* Composition */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <span className="text-lg">🥗</span>
                    Composition ({normalizedIngredients.length} ingrédients)
                  </h3>
                  <button
                    onClick={() => onAddIngredient?.(plat)}
                    className="text-xs px-3 py-1.5 rounded-lg bg-orange-500/10 border border-orange-500/30 text-orange-400 hover:bg-orange-500/20 transition-colors flex items-center gap-1"
                  >
                    <Plus className="w-3 h-3" />
                    Ajouter
                  </button>
                </div>

                <div className="space-y-2">
                  {normalizedIngredients.length === 0 ? (
                    <p className="text-sm text-slate-500 text-center py-4">Aucun ingrédient renseigné</p>
                  ) : (
                    normalizedIngredients.map((ing, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-white/5 rounded-xl hover:bg-white/10 cursor-pointer transition-colors group"
                      >
                        <div>
                          <p className="text-sm font-medium text-white">{ing.nom || 'Ingrédient'}</p>
                          <p className="text-xs text-slate-500">
                            {ing.quantite} {ing.unite} par portion
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-semibold text-amber-400">
                            {formatCurrency(ing.total_cost)}
                          </span>
                          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Total */}
                {normalizedIngredients.length > 0 && (
                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-white/10">
                    <span className="text-sm font-semibold text-white">Coût total matière</span>
                    <span className="text-lg font-bold text-amber-400">{formatCurrency(cout_matiere)}</span>
                  </div>
                )}
              </div>

              {/* Stats ventes (mockup) */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <span className="text-lg">📊</span>
                  Statistiques ventes
                </h3>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Ventes (30j)</p>
                    <p className="text-lg font-semibold text-white">127</p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">CA généré</p>
                    <p className="text-lg font-semibold text-white">
                      {formatCurrency(127 * prix_vente_ttc)}
                    </p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Tendance</p>
                    <p className="text-lg font-semibold text-emerald-400 flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      +8%
                    </p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Ranking</p>
                    <p className="text-lg font-semibold text-white">#3</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/10">
              <Button variant="ghost" onClick={onClose} className="w-full">
                Fermer
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
