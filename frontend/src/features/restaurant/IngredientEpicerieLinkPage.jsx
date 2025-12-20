import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import {
  useRestaurantIngredients,
  useLinkIngredientEpicerie,
  useUnlinkIngredientEpicerie,
  useUpdateIngredientRatio,
} from '../../hooks/useRestaurant.js';
import { useQuery } from '@tanstack/react-query';
import api from '../../api/client.js';
import { Search, Link2, Unlink, Package, CheckCircle2, AlertCircle, X, Loader2, Sparkles } from 'lucide-react';

/**
 * RatioInput - Input pour modifier le ratio de conversion
 */
function RatioInput({ ingredientId, initialRatio, onSave, disabled }) {
  const [value, setValue] = useState(initialRatio ?? 1);

  const handleBlur = () => {
    const newRatio = parseFloat(value);
    if (newRatio > 0 && newRatio !== initialRatio) {
      onSave(ingredientId, newRatio);
    }
  };

  return (
    <input
      type="number"
      step="0.01"
      min="0.01"
      className="w-20 rounded-lg border border-white/20 bg-white/5 px-2 py-1.5 text-sm text-right text-white focus:border-teal-400 focus:ring-1 focus:ring-teal-400/50 outline-none"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onBlur={handleBlur}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.target.blur();
        }
      }}
      disabled={disabled}
    />
  );
}

/**
 * ProductSearchCombobox - Recherche asynchrone de produits épicerie
 */
function ProductSearchCombobox({
  ingredientId,
  ingredientName,
  currentProductId,
  currentProductName,
  onSelect,
  onUnlink,
  disabled
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const searchQuery = useQuery({
    queryKey: ['epicerie', 'products', 'search', debouncedSearch, ingredientName],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (debouncedSearch) {
        params.append('q', debouncedSearch);
      } else {
        params.append('suggest_for', ingredientName);
      }
      params.append('limit', '15');
      const res = await api.get(`/restaurant/epicerie/products/search?${params}`);
      return res.data;
    },
    enabled: isOpen,
    staleTime: 30000,
  });

  const products = searchQuery.data || [];

  const handleSelect = (product) => {
    onSelect(ingredientId, product.id);
    setIsOpen(false);
    setSearch('');
  };

  const handleOpen = () => {
    setIsOpen(true);
    setSearch('');
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  if (currentProductId) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 px-3 py-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-sm">
          <span className="text-emerald-300 font-medium">{currentProductName || `Produit #${currentProductId}`}</span>
        </div>
        <button
          onClick={() => onUnlink(ingredientId)}
          disabled={disabled}
          className="p-2 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
          title="Supprimer le lien"
        >
          <Unlink className="w-4 h-4 text-slate-400 hover:text-rose-400" />
        </button>
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {!isOpen ? (
        <button
          onClick={handleOpen}
          disabled={disabled}
          className="w-full px-3 py-2 text-left rounded-lg border border-white/20 bg-white/5 text-sm text-slate-400 hover:border-teal-400/50 hover:bg-white/10 transition-colors disabled:opacity-50"
        >
          <span className="flex items-center gap-2">
            <Search className="w-4 h-4" />
            Rechercher un produit...
          </span>
        </button>
      ) : (
        <div className="absolute z-50 w-80 bg-slate-800 rounded-xl shadow-2xl border border-white/20 overflow-hidden">
          <div className="p-2 border-b border-white/10">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Tapez pour rechercher..."
                className="w-full pl-9 pr-8 py-2 text-sm border border-white/20 bg-white/5 rounded-lg text-white placeholder:text-slate-500 focus:border-teal-400 focus:ring-1 focus:ring-teal-400/50 outline-none"
                autoFocus
              />
              <button
                onClick={() => setIsOpen(false)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-white/10 rounded"
              >
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {searchQuery.isLoading ? (
              <div className="p-4 text-center text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                <span className="text-sm">Recherche...</span>
              </div>
            ) : products.length === 0 ? (
              <div className="p-4 text-center text-slate-500 text-sm">
                Aucun produit trouvé
              </div>
            ) : (
              <>
                {!search && (
                  <div className="px-3 py-1.5 bg-white/5 text-xs text-slate-400 font-medium flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-teal-400" />
                    Suggestions pour "{ingredientName}"
                  </div>
                )}
                {products.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => handleSelect(product)}
                    className="w-full px-3 py-2 text-left hover:bg-white/10 transition-colors border-b border-white/5 last:border-0"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{product.nom}</p>
                        <p className="text-xs text-slate-400 truncate">{product.categorie || 'Sans catégorie'}</p>
                      </div>
                      <div className="text-right shrink-0">
                        {product.prix_achat != null && product.prix_achat > 0 ? (
                          <span className="text-sm font-medium text-emerald-400">
                            {Number(product.prix_achat).toFixed(2)}€
                          </span>
                        ) : (
                          <span className="text-xs text-slate-500">--</span>
                        )}
                        {product.match_score != null && (
                          <p className="text-xs text-slate-500">{product.match_score}% match</p>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * IngredientEpicerieLinkPage - Rapprochement ingrédients restaurant ↔ produits épicerie
 * Style dark mode / glass-morphism avec colonne ratio
 */
export default function IngredientEpicerieLinkPage() {
  const ingredientsQuery = useRestaurantIngredients();
  const ingredients = ingredientsQuery.data || [];

  const [searchIngredient, setSearchIngredient] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Hooks pour les mutations
  const linkIngredient = useLinkIngredientEpicerie();
  const unlinkIngredient = useUnlinkIngredientEpicerie();
  const updateRatio = useUpdateIngredientRatio();

  // Statistiques
  const stats = useMemo(() => {
    const linked = ingredients.filter((i) => i.produit_epicerie_id).length;
    const unlinked = ingredients.length - linked;
    return { total: ingredients.length, linked, unlinked };
  }, [ingredients]);

  // Filtrage
  const filteredIngredients = useMemo(() => {
    return ingredients
      .filter((ing) => {
        if (searchIngredient && !ing.nom.toLowerCase().includes(searchIngredient.toLowerCase())) {
          return false;
        }
        if (statusFilter === 'linked' && !ing.produit_epicerie_id) return false;
        if (statusFilter === 'unlinked' && ing.produit_epicerie_id) return false;
        return true;
      })
      .sort((a, b) => {
        if (!a.produit_epicerie_id && b.produit_epicerie_id) return -1;
        if (a.produit_epicerie_id && !b.produit_epicerie_id) return 1;
        return a.nom.localeCompare(b.nom, 'fr');
      });
  }, [ingredients, searchIngredient, statusFilter]);

  const handleLinkIngredient = useCallback((ingredientId, produitEpicerieId) => {
    linkIngredient.mutate({ ingredientId, epicerieProductId: Number(produitEpicerieId) });
  }, [linkIngredient]);

  const handleUnlinkIngredient = useCallback((ingredientId) => {
    unlinkIngredient.mutate(ingredientId);
  }, [unlinkIngredient]);

  const handleRatioSave = useCallback((ingredientId, ratio) => {
    updateRatio.mutate({ ingredientId, ratio });
  }, [updateRatio]);

  const isLoading = ingredientsQuery.isLoading;
  const isMutating = linkIngredient.isPending || unlinkIngredient.isPending || updateRatio.isPending;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto flex flex-col gap-6">

        {/* Header avec stats */}
        <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-teal-400">liens épicerie</p>
              <h1 className="text-2xl font-semibold text-white">Ingrédients associés</h1>
              <p className="text-sm text-slate-400 mt-1">
                Associez chaque ingrédient à un produit de l'épicerie pour le suivi des coûts et des stocks.
              </p>
            </div>
            <Link2 className="w-10 h-10 text-teal-400" />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-widest text-slate-400">Total ingrédients</p>
              <p className="text-3xl font-bold text-white">{stats.total}</p>
            </div>
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 flex items-center gap-4">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              <div>
                <p className="text-xs uppercase tracking-widest text-emerald-400">Liés</p>
                <p className="text-3xl font-bold text-emerald-300">{stats.linked}</p>
              </div>
            </div>
            <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-center gap-4">
              <AlertCircle className="w-8 h-8 text-amber-400" />
              <div>
                <p className="text-xs uppercase tracking-widest text-amber-400">Non liés</p>
                <p className="text-3xl font-bold text-amber-300">{stats.unlinked}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filtres */}
        <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[250px]">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Filtrer les ingrédients..."
                className="w-full pl-11 pr-4 py-3 rounded-2xl border border-white/20 bg-white/5 text-sm text-white placeholder:text-slate-500 focus:border-teal-400 focus:ring-1 focus:ring-teal-400/50 outline-none"
                value={searchIngredient}
                onChange={(e) => setSearchIngredient(e.target.value)}
              />
            </div>
            <select
              className="rounded-2xl border border-white/20 bg-white/5 px-4 py-3 text-sm text-white focus:border-teal-400 outline-none"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all" className="bg-slate-800">Tous les statuts</option>
              <option value="linked" className="bg-slate-800">Liés uniquement</option>
              <option value="unlinked" className="bg-slate-800">Non liés uniquement</option>
            </select>
          </div>

          <p className="text-sm text-slate-400 mt-4">
            <span className="font-medium text-white">{filteredIngredients.length}</span> ingrédient(s) affiché(s)
            {statusFilter === 'all' && stats.unlinked > 0 && (
              <span className="ml-2 text-amber-400">• {stats.unlinked} à rapprocher</span>
            )}
          </p>
        </div>

        {/* Table */}
        <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-teal-400" />
              <span className="ml-3 text-slate-400">Chargement...</span>
            </div>
          ) : filteredIngredients.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">Aucun ingrédient trouvé.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-white/5 border-b border-white/10">
                  <tr>
                    <th className="px-4 py-4 text-left text-xs uppercase tracking-wider text-slate-400">Ingrédient</th>
                    <th className="px-4 py-4 text-left text-xs uppercase tracking-wider text-slate-400">Produit Épicerie</th>
                    <th className="px-4 py-4 text-right text-xs uppercase tracking-wider text-slate-400">Ratio</th>
                    <th className="px-4 py-4 text-left text-xs uppercase tracking-wider text-slate-400">Catégorie</th>
                    <th className="px-4 py-4 text-right text-xs uppercase tracking-wider text-slate-400">Prix achat</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredIngredients.map((ingredient) => (
                    <tr
                      key={ingredient.id}
                      className={`transition-colors ${ingredient.produit_epicerie_id ? 'bg-emerald-500/5' : 'hover:bg-white/5'}`}
                    >
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${ingredient.produit_epicerie_id ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                          <div>
                            <p className="font-semibold text-white">{ingredient.nom}</p>
                            <p className="text-xs text-slate-500">{ingredient.unite_base}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 min-w-[280px]">
                        <ProductSearchCombobox
                          ingredientId={ingredient.id}
                          ingredientName={ingredient.nom}
                          currentProductId={ingredient.produit_epicerie_id}
                          currentProductName={ingredient.produit_epicerie_nom}
                          onSelect={handleLinkIngredient}
                          onUnlink={handleUnlinkIngredient}
                          disabled={isMutating}
                        />
                      </td>
                      <td className="px-4 py-4 text-right">
                        {ingredient.produit_epicerie_id ? (
                          <RatioInput
                            ingredientId={ingredient.id}
                            initialRatio={ingredient.ratio_epicerie || 1}
                            onSave={handleRatioSave}
                            disabled={isMutating}
                          />
                        ) : (
                          <span className="text-slate-600">--</span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        {ingredient.categorie ? (
                          <span className="px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-medium">
                            {ingredient.categorie}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-600 italic">Non défini</span>
                        )}
                      </td>
                      <td className="px-4 py-4 text-right">
                        {ingredient.cout_unitaire ? (
                          <span className="font-medium text-white">{Number(ingredient.cout_unitaire).toFixed(2)} €</span>
                        ) : (
                          <span className="text-slate-600">--</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
