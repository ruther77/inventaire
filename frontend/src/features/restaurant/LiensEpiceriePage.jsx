import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  useRestaurantIngredients,
  useEpicerieProducts,
  useLinkIngredientEpicerie,
  useUnlinkIngredientEpicerie,
} from '@/hooks/useRestaurant.js';
import { Search, Link2, Unlink, Sparkles, ChevronRight, Check, X, Loader2 } from 'lucide-react';
import QueryErrorState from '@/components/feedback/QueryErrorState.jsx';
import { toast } from 'sonner';

/**
 * LiensEpiceriePage - Liaison Ingrédients Restaurant ↔ Produits Épicerie
 * Design from mockups/restaurant-liens-epicerie.html
 */

export default function LiensEpiceriePage() {
  const [ingredientSearch, setIngredientSearch] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Queries
  const ingredientsQuery = useRestaurantIngredients();
  const productsQuery = useEpicerieProducts();
  const linkMutation = useLinkIngredientEpicerie();
  const unlinkMutation = useUnlinkIngredientEpicerie();

  const ingredients = ingredientsQuery.data || [];
  const products = productsQuery.data || [];

  // Stats
  const stats = useMemo(() => {
    const linked = ingredients.filter(i => i.produit_epicerie_id).length;
    const unlinked = ingredients.length - linked;
    return { linked, unlinked, total: ingredients.length };
  }, [ingredients]);

  // Filtrage ingrédients
  const filteredIngredients = useMemo(() => {
    if (!ingredientSearch.trim()) return ingredients;
    const search = ingredientSearch.toLowerCase();
    return ingredients.filter(i => i.nom?.toLowerCase()?.includes(search));
  }, [ingredients, ingredientSearch]);

  // Filtrage produits
  const filteredProducts = useMemo(() => {
    if (!productSearch.trim()) return products;
    const search = productSearch.toLowerCase();
    return products.filter(p => p.nom?.toLowerCase()?.includes(search));
  }, [products, productSearch]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value || 0);
  };

  const handleLink = async () => {
    if (!selectedIngredient || !selectedProduct) {
      toast.error('Sélectionnez un ingrédient et un produit');
      return;
    }

    try {
      await linkMutation.mutateAsync({
        ingredientId: selectedIngredient.id,
        epicerieProductId: selectedProduct.id,
        ratio: 1.0,
      });
      toast.success(`${selectedIngredient.nom} lié à ${selectedProduct.nom}`);
      setSelectedIngredient(null);
      setSelectedProduct(null);
    } catch (error) {
      toast.error(`Erreur: ${error.message}`);
    }
  };

  const handleUnlink = async () => {
    if (!selectedIngredient || !selectedIngredient.produit_epicerie_id) {
      toast.error('Sélectionnez un ingrédient lié');
      return;
    }

    try {
      await unlinkMutation.mutateAsync(selectedIngredient.id);
      toast.success(`${selectedIngredient.nom} délié`);
      setSelectedIngredient(null);
    } catch (error) {
      toast.error(`Erreur: ${error.message}`);
    }
  };

  const handleAutoLink = () => {
    toast.info('Fonctionnalité auto-liaison IA en cours de développement');
  };

  // Erreur
  if (ingredientsQuery.isError && !ingredients.length) {
    return <QueryErrorState error={ingredientsQuery.error} onRetry={() => ingredientsQuery.refetch()} variant="full" />;
  }

  return (
    <div className="min-h-screen p-6 md:p-8">
      <div className="max-w-[1400px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <Link to="/" className="hover:text-white transition-colors">Accueil</Link>
          <ChevronRight className="w-4 h-4" />
          <Link to="/restaurant" className="hover:text-white transition-colors">Restaurant</Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-white">Liens Épicerie</span>
        </nav>

        {/* Header */}
        <h1 className="text-3xl md:text-4xl font-bold mb-2 bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent font-['Sora',sans-serif]">
          🔗 Liens Épicerie-Restaurant
        </h1>
        <p className="text-base text-slate-400 mb-8">
          Associez les ingrédients restaurant aux produits du stock épicerie
        </p>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Ingrédients liés</p>
            <p className="text-2xl font-bold text-emerald-400">{stats.linked}</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Non liés</p>
            <p className="text-2xl font-bold text-amber-400">{stats.unlinked}</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Suggestions IA</p>
            <p className="text-2xl font-bold text-white">{Math.min(stats.unlinked, 8)}</p>
          </div>
        </div>

        {/* Linking Area */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-6">
          {/* Ingrédients Panel */}
          <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-base font-semibold text-white">
                <span className="text-xl">🍴</span>
                Ingrédients Restaurant
              </div>
              <span className="text-xs text-slate-400">{ingredients.length} ingrédients</span>
            </div>

            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Rechercher un ingrédient..."
                value={ingredientSearch}
                onChange={(e) => setIngredientSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white/6 border border-white/10 text-white placeholder-slate-500 text-sm focus:border-orange-500/50 focus:outline-none"
              />
            </div>

            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              {filteredIngredients.map(ingredient => {
                const isLinked = !!ingredient.produit_epicerie_id;
                const isSelected = selectedIngredient?.id === ingredient.id;

                return (
                  <motion.div
                    key={ingredient.id}
                    onClick={() => setSelectedIngredient(ingredient)}
                    className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                      isSelected
                        ? 'border-orange-500 bg-orange-500/10 border'
                        : isLinked
                        ? 'border-emerald-500/50 bg-emerald-500/10 border'
                        : 'border-transparent bg-white/3 hover:bg-white/8 border'
                    }`}
                  >
                    <span className="text-xl">
                      {ingredient.categorie === 'viandes' ? '🥩' :
                       ingredient.categorie === 'legumes' ? '🥬' :
                       ingredient.categorie === 'produits-laitiers' ? '🧀' :
                       ingredient.categorie === 'fruits' ? '🍎' :
                       ingredient.categorie === 'poissons' ? '🐟' :
                       '🍽️'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{ingredient.nom}</p>
                      <p className="text-xs text-slate-400">Unité: {ingredient.unite_base || 'kg'}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-md font-medium ${
                      isLinked
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {isLinked ? '✓ Lié' : 'Non lié'}
                    </span>
                  </motion.div>
                );
              })}

              {filteredIngredients.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-8">Aucun ingrédient trouvé</p>
              )}
            </div>
          </div>

          {/* Connector */}
          <div className="flex flex-row lg:flex-col items-center justify-center gap-4 py-4 lg:py-0">
            <button
              onClick={handleAutoLink}
              className="px-4 py-2 rounded-lg bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 text-sm font-medium hover:bg-cyan-500/30 transition-all flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Auto-lier
            </button>

            <button
              onClick={handleLink}
              disabled={!selectedIngredient || !selectedProduct || linkMutation.isPending}
              className="w-14 h-14 rounded-full bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center text-white text-2xl shadow-lg shadow-orange-500/30 hover:scale-110 transition-transform disabled:opacity-50 disabled:hover:scale-100"
            >
              {linkMutation.isPending ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <Link2 className="w-6 h-6" />
              )}
            </button>

            <button
              onClick={handleUnlink}
              disabled={!selectedIngredient?.produit_epicerie_id || unlinkMutation.isPending}
              className="px-4 py-2 rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-400 text-sm font-medium hover:bg-rose-500/30 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {unlinkMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Unlink className="w-4 h-4" />
              )}
              Délier
            </button>
          </div>

          {/* Produits Panel */}
          <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-base font-semibold text-white">
                <span className="text-xl">🛒</span>
                Produits Épicerie
              </div>
              <span className="text-xs text-slate-400">{products.length} produits</span>
            </div>

            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Rechercher un produit..."
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white/6 border border-white/10 text-white placeholder-slate-500 text-sm focus:border-orange-500/50 focus:outline-none"
              />
            </div>

            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              {filteredProducts.map(product => {
                const isSelected = selectedProduct?.id === product.id;

                return (
                  <motion.div
                    key={product.id}
                    onClick={() => setSelectedProduct(product)}
                    className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                      isSelected
                        ? 'border-orange-500 bg-orange-500/10 border'
                        : 'border-transparent bg-white/3 hover:bg-white/8 border'
                    }`}
                  >
                    <span className="text-xl">
                      {product.categorie?.includes('viande') ? '🥩' :
                       product.categorie?.includes('légume') ? '🥬' :
                       product.categorie?.includes('lait') ? '🧀' :
                       product.categorie?.includes('fruit') ? '🍎' :
                       product.categorie?.includes('poisson') ? '🐟' :
                       '📦'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{product.nom}</p>
                      <p className="text-xs text-slate-400">
                        {formatCurrency(product.prix_achat)}/{product.unite || 'kg'} • Stock: {product.stock_actuel || 0}{product.unite || 'kg'}
                      </p>
                    </div>
                  </motion.div>
                );
              })}

              {filteredProducts.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-8">Aucun produit trouvé</p>
              )}
            </div>
          </div>
        </div>

        {/* Selection Info */}
        <AnimatePresence>
          {(selectedIngredient || selectedProduct) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-slate-800/95 backdrop-blur-md border border-white/20 rounded-2xl p-4 shadow-2xl flex items-center gap-4"
            >
              {selectedIngredient && (
                <div className="flex items-center gap-2 px-3 py-2 bg-orange-500/20 rounded-lg">
                  <span className="text-lg">🍴</span>
                  <span className="text-sm font-medium text-white">{selectedIngredient.nom}</span>
                  <button
                    onClick={() => setSelectedIngredient(null)}
                    className="ml-1 p-1 hover:bg-white/10 rounded"
                  >
                    <X className="w-3 h-3 text-slate-400" />
                  </button>
                </div>
              )}

              {selectedIngredient && selectedProduct && (
                <Link2 className="w-5 h-5 text-orange-400" />
              )}

              {selectedProduct && (
                <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/20 rounded-lg">
                  <span className="text-lg">🛒</span>
                  <span className="text-sm font-medium text-white">{selectedProduct.nom}</span>
                  <button
                    onClick={() => setSelectedProduct(null)}
                    className="ml-1 p-1 hover:bg-white/10 rounded"
                  >
                    <X className="w-3 h-3 text-slate-400" />
                  </button>
                </div>
              )}

              {selectedIngredient && selectedProduct && (
                <button
                  onClick={handleLink}
                  disabled={linkMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 text-white font-semibold text-sm flex items-center gap-2"
                >
                  {linkMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  Lier
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
