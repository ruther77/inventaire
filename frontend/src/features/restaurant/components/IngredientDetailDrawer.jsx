import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Leaf,
  Edit3,
  History,
  Link2,
  TrendingUp,
  TrendingDown,
  ChevronRight,
  Utensils,
} from 'lucide-react';
import Button from '@/components/ui/Button.jsx';

// ============================================================================
// INGREDIENTDETAILDRAWER - Drawer latéral pour afficher le détail d'un ingrédient
// Design from mockups/restaurant-ingredients-detail.html
// ============================================================================

export default function IngredientDetailDrawer({
  open,
  onClose,
  ingredient,
  onEdit,
  onHistory,
  onLinkEpicerie,
  onViewPlat,
}) {
  if (!ingredient) return null;

  const {
    id,
    nom,
    categorie,
    unite_base = 'kg',
    cout_unitaire = 0,
    stock_actuel = 0,
    stock_minimum = 5,
    plats_utilisant = [],
    price_history = [],
    produit_epicerie_nom,
    produit_epicerie_id,
    consommation_mensuelle = 0,
  } = ingredient;

  const formatCurrency = (value) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value || 0);

  // Mock des plats utilisant cet ingrédient
  const mockPlats = plats_utilisant.length > 0 ? plats_utilisant : [
    { id: 1, nom: 'Entrecôte grillée', quantite: 250, unite: 'g', icon: '🥩' },
    { id: 2, nom: 'Steak frites', quantite: 200, unite: 'g', icon: '🍟' },
    { id: 3, nom: 'Tartare de boeuf', quantite: 180, unite: 'g', icon: '🥩' },
    { id: 4, nom: 'Carpaccio', quantite: 120, unite: 'g', icon: '🥩' },
  ];

  // Mock historique prix
  const mockPriceHistory = price_history.length > 0 ? price_history : [
    { date: 'Décembre 2025', prix: 22.0, variation: 8 },
    { date: 'Novembre 2025', prix: 20.35, variation: 3 },
    { date: 'Octobre 2025', prix: 19.75, variation: -2 },
    { date: 'Septembre 2025', prix: 20.15, variation: 0 },
  ];

  // Status stock
  const stockStatus = stock_actuel < stock_minimum ? 'low' : 'ok';

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
            <div className="flex items-start justify-between p-6 border-b border-white/10 bg-gradient-to-r from-orange-500/10 to-transparent">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500/20 to-amber-500/20 border border-white/10 flex items-center justify-center text-3xl">
                  🥩
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{nom}</h2>
                  <p className="text-sm text-slate-400">
                    Catégorie: {categorie || 'Non classé'} • Unité: {unite_base} • SKU: ING-{String(id).padStart(3, '0')}
                  </p>
                  <div className="flex gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 rounded-full border font-medium bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                      Actif
                    </span>
                    {mockPriceHistory[0]?.variation > 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full border font-medium bg-amber-500/20 text-amber-400 border-amber-500/30">
                        Prix +{mockPriceHistory[0].variation}% ce mois
                      </span>
                    )}
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
                onClick={() => onEdit?.(ingredient)}
                className="flex-1 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600"
              >
                <Edit3 className="w-4 h-4" />
                Modifier
              </Button>
              <Button variant="ghost" onClick={() => onHistory?.(ingredient)} className="flex-1">
                <History className="w-4 h-4" />
                Historique
              </Button>
              <Button variant="ghost" onClick={() => onLinkEpicerie?.(ingredient)} className="flex-1">
                <Link2 className="w-4 h-4" />
                Lier produit
              </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* KPIs */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-amber-400">{formatCurrency(cout_unitaire)}</p>
                  <p className="text-xs text-slate-500">Prix actuel / {unite_base}</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-white">{mockPlats.length}</p>
                  <p className="text-xs text-slate-500">Plats utilisant</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-white">{consommation_mensuelle || 45} {unite_base}</p>
                  <p className="text-xs text-slate-500">Conso. mensuelle</p>
                </div>
              </div>

              {/* Lien Épicerie */}
              {produit_epicerie_id && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <Link2 className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">Lié à l'épicerie</p>
                      <p className="text-xs text-slate-400">{produit_epicerie_nom || 'Produit épicerie'}</p>
                    </div>
                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400">
                      Prix synchronisé
                    </span>
                  </div>
                </div>
              )}

              {/* Plats utilisant cet ingrédient */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Utensils className="w-4 h-4 text-orange-400" />
                  Utilisé dans ces plats
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {mockPlats.map((plat, idx) => (
                    <div
                      key={idx}
                      onClick={() => onViewPlat?.(plat)}
                      className="flex items-center gap-3 p-3 bg-white/5 rounded-xl hover:bg-white/10 cursor-pointer transition-colors group"
                    >
                      <span className="text-2xl">{plat.icon || '🍽️'}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{plat.nom}</p>
                        <p className="text-xs text-slate-500">{plat.quantite}{plat.unite} / portion</p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                    </div>
                  ))}
                </div>
              </div>

              {/* Historique des prix */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-orange-400" />
                  Historique des prix
                </h3>

                <div className="space-y-2">
                  {mockPriceHistory.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-white/5 rounded-xl"
                    >
                      <span className="text-sm text-slate-400">{item.date}</span>
                      <span className="text-sm font-semibold text-white">
                        {formatCurrency(item.prix)}/{unite_base}
                      </span>
                      <span
                        className={`text-xs font-medium flex items-center gap-1 ${
                          item.variation > 0
                            ? 'text-rose-400'
                            : item.variation < 0
                            ? 'text-emerald-400'
                            : 'text-slate-500'
                        }`}
                      >
                        {item.variation > 0 ? (
                          <>
                            <TrendingUp className="w-3 h-3" />+{item.variation}%
                          </>
                        ) : item.variation < 0 ? (
                          <>
                            <TrendingDown className="w-3 h-3" />{item.variation}%
                          </>
                        ) : (
                          '—'
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Stock */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <span className="text-lg">📦</span>
                  Stock
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Stock actuel</p>
                    <p
                      className={`text-xl font-semibold ${
                        stockStatus === 'low' ? 'text-amber-400' : 'text-white'
                      }`}
                    >
                      {stock_actuel} {unite_base}
                    </p>
                  </div>
                  <div className="p-3 bg-white/5 rounded-xl">
                    <p className="text-xs text-slate-500 mb-1">Stock minimum</p>
                    <p className="text-xl font-semibold text-white">
                      {stock_minimum} {unite_base}
                    </p>
                  </div>
                </div>

                {stockStatus === 'low' && (
                  <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center gap-2">
                    <span className="text-amber-400">⚠️</span>
                    <p className="text-sm text-amber-400">Stock bas - Réapprovisionnement conseillé</p>
                  </div>
                )}
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
