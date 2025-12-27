import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Utensils,
  Plus,
  X,
  Search,
  Loader2,
  AlertTriangle,
  Trash2,
  TrendingUp,
  TrendingDown,
  Check,
} from 'lucide-react';
import Modal from '@/components/ui/Modal.jsx';
import Button from '@/components/ui/Button.jsx';
import {
  useCreateRestaurantPlat,
  useRestaurantIngredients,
  useEpicerieProducts,
  useCreateRestaurantIngredient,
} from '@/hooks/useRestaurant.js';
import { toast } from 'sonner';

// ============================================================================
// ADDPLATMODAL - Modal de création de plat avec composition ingrédients
// Design from mockups/modal-add-plat.html
// ============================================================================

const CATEGORIES = [
  { value: 'entrees', label: 'Entrées' },
  { value: 'plats', label: 'Plats' },
  { value: 'desserts', label: 'Desserts' },
  { value: 'boissons', label: 'Boissons' },
  { value: 'accompagnements', label: 'Accompagnements' },
];

const initialFormState = {
  nom: '',
  categorie: '',
  prix_vente_ttc: '',
  portions: 1,
  objectif_food_cost: 30,
};

export default function AddPlatModal({ open, onClose, onSuccess }) {
  const [form, setForm] = useState(initialFormState);
  const [errors, setErrors] = useState({});
  const [ingredients, setIngredients] = useState([]);
  const [ingredientSearch, setIngredientSearch] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Queries
  const ingredientsQuery = useRestaurantIngredients();
  const epicerieQuery = useEpicerieProducts();
  const createPlatMutation = useCreateRestaurantPlat();
  const createIngredientMutation = useCreateRestaurantIngredient();

  const allIngredients = ingredientsQuery.data || [];
  const allEpicerieProducts = epicerieQuery.data || [];

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Combine ingredients + produits épicerie pour la recherche
  const searchableItems = useMemo(() => {
    const items = allIngredients.map((ing) => ({
      type: 'ingredient',
      id: ing.id,
      nom: ing.nom,
      prix: ing.produit_epicerie_prix || ing.cout_unitaire || 0,
      unite: ing.unite_base || 'kg',
    }));

    // Ajouter produits épicerie non liés
    const linkedIds = new Set(allIngredients.map((i) => i.produit_epicerie_id).filter(Boolean));
    allEpicerieProducts.forEach((prod) => {
      if (!linkedIds.has(prod.id)) {
        items.push({
          type: 'epicerie',
          id: prod.id,
          nom: prod.nom,
          prix: prod.prix_achat || 0,
          unite: 'kg',
        });
      }
    });

    return items;
  }, [allIngredients, allEpicerieProducts]);

  // Filtrer par recherche et exclure déjà sélectionnés
  const filteredItems = useMemo(() => {
    const usedIds = new Set(ingredients.map((i) => i.ingredient_id));
    const available = searchableItems.filter((item) => {
      if (item.type === 'ingredient') return !usedIds.has(item.id);
      return true;
    });

    if (!ingredientSearch.trim()) return available.slice(0, 10);
    const search = ingredientSearch.toLowerCase();
    return available.filter((item) => item.nom?.toLowerCase()?.includes(search)).slice(0, 10);
  }, [searchableItems, ingredients, ingredientSearch]);

  // Calcul du coût matière total
  const coutMatiereTotal = useMemo(() => {
    return ingredients.reduce((sum, ing) => sum + (ing.cout_total || 0), 0);
  }, [ingredients]);

  // Calcul du food cost
  const foodCostPct = useMemo(() => {
    const prixVente = parseFloat(form.prix_vente_ttc) || 0;
    if (prixVente <= 0) return 0;
    return (coutMatiereTotal / prixVente) * 100;
  }, [coutMatiereTotal, form.prix_vente_ttc]);

  // Status du food cost
  const foodCostStatus = useMemo(() => {
    const objectif = form.objectif_food_cost || 30;
    if (foodCostPct <= objectif) return 'good';
    if (foodCostPct <= objectif + 5) return 'warning';
    return 'danger';
  }, [foodCostPct, form.objectif_food_cost]);

  const handleChange = useCallback(
    (e) => {
      const { name, value } = e.target;
      setForm((prev) => ({ ...prev, [name]: value }));
      if (errors[name]) {
        setErrors((prev) => ({ ...prev, [name]: null }));
      }
    },
    [errors]
  );

  const handleSelectItem = async (item) => {
    let ingredientId = item.id;
    let prix = item.prix;

    // Si c'est un produit épicerie, créer l'ingrédient d'abord
    if (item.type === 'epicerie') {
      try {
        const created = await createIngredientMutation.mutateAsync({
          nom: item.nom,
          unite_base: item.unite || 'kg',
          cout_unitaire: item.prix || 0,
          produit_epicerie_id: item.id,
          ratio_epicerie: 1.0,
        });
        ingredientId = created.id;
        prix = item.prix;
      } catch (err) {
        toast.error(`Erreur création ingrédient: ${err.message}`);
        return;
      }
    }

    // Ajouter à la liste
    setIngredients((prev) => [
      ...prev,
      {
        ingredient_id: ingredientId,
        nom: item.nom,
        quantite: 0,
        unite: item.unite || 'kg',
        prix_unitaire: prix,
        cout_total: 0,
      },
    ]);

    setIngredientSearch('');
    setShowDropdown(false);
  };

  const handleIngredientChange = (index, field, value) => {
    setIngredients((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };

      // Recalculer le coût total
      if (field === 'quantite') {
        const qty = parseFloat(value) || 0;
        const prixUnit = updated[index].prix_unitaire || 0;
        // Conversion: si l'unité est en g et le prix en kg, diviser par 1000
        const unite = updated[index].unite || 'kg';
        let coutTotal = qty * prixUnit;
        if (unite === 'g') {
          coutTotal = (qty / 1000) * prixUnit;
        } else if (unite === 'ml') {
          coutTotal = (qty / 1000) * prixUnit;
        }
        updated[index].cout_total = coutTotal;
      }

      return updated;
    });
  };

  const handleRemoveIngredient = (index) => {
    setIngredients((prev) => prev.filter((_, i) => i !== index));
  };

  const validate = useCallback(() => {
    const newErrors = {};

    if (!form.nom.trim()) {
      newErrors.nom = 'Le nom est requis';
    }

    if (!form.categorie) {
      newErrors.categorie = 'La catégorie est requise';
    }

    if (!form.prix_vente_ttc || parseFloat(form.prix_vente_ttc) <= 0) {
      newErrors.prix_vente_ttc = 'Prix de vente invalide';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [form]);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();

      if (!validate()) return;

      const payload = {
        nom: form.nom.trim(),
        categorie: form.categorie,
        prix_vente_ttc: parseFloat(form.prix_vente_ttc),
        portions: parseInt(form.portions) || 1,
        objectif_food_cost: parseFloat(form.objectif_food_cost) || 30,
        actif: true,
        ingredients: ingredients.map((ing) => ({
          ingredient_id: ing.ingredient_id,
          quantite: parseFloat(ing.quantite) || 0,
          unite: ing.unite,
        })),
      };

      createPlatMutation.mutate(payload, {
        onSuccess: () => {
          toast.success('Plat créé avec succès');
          setForm(initialFormState);
          setIngredients([]);
          setErrors({});
          onSuccess?.();
          onClose();
        },
        onError: (err) => {
          toast.error(`Erreur: ${err.message}`);
        },
      });
    },
    [form, ingredients, validate, createPlatMutation, onSuccess, onClose]
  );

  const handleClose = useCallback(() => {
    setForm(initialFormState);
    setIngredients([]);
    setErrors({});
    onClose();
  }, [onClose]);

  const formatCurrency = (value) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value || 0);

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Nouveau plat"
      icon={<Utensils className="w-5 h-5 text-orange-400" />}
      size="lg"
      gradient="from-orange-500/10 to-amber-500/5"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Informations de base */}
        <div className="space-y-4">
          {/* Nom */}
          <div>
            <label htmlFor="nom" className="block text-sm font-medium text-slate-300 mb-1.5">
              Nom du plat <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              id="nom"
              name="nom"
              value={form.nom}
              onChange={handleChange}
              placeholder="Ex: Entrecôte grillée sauce béarnaise"
              className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                errors.nom ? 'border-rose-500' : 'border-white/10'
              } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-transparent transition-all`}
            />
            {errors.nom && (
              <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                {errors.nom}
              </p>
            )}
          </div>

          {/* Catégorie + Prix */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="categorie" className="block text-sm font-medium text-slate-300 mb-1.5">
                Catégorie <span className="text-rose-400">*</span>
              </label>
              <select
                id="categorie"
                name="categorie"
                value={form.categorie}
                onChange={handleChange}
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.categorie ? 'border-rose-500' : 'border-white/10'
                } text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all appearance-none cursor-pointer`}
              >
                <option value="" className="bg-slate-800">
                  Sélectionner...
                </option>
                {CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value} className="bg-slate-800">
                    {cat.label}
                  </option>
                ))}
              </select>
              {errors.categorie && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.categorie}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="prix_vente_ttc" className="block text-sm font-medium text-slate-300 mb-1.5">
                Prix de vente TTC <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <input
                  type="number"
                  id="prix_vente_ttc"
                  name="prix_vente_ttc"
                  value={form.prix_vente_ttc}
                  onChange={handleChange}
                  placeholder="24.90"
                  step="0.10"
                  min="0"
                  className={`w-full px-4 py-3 pr-10 rounded-xl bg-white/5 border ${
                    errors.prix_vente_ttc ? 'border-rose-500' : 'border-white/10'
                  } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all`}
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500">€</span>
              </div>
              {errors.prix_vente_ttc && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.prix_vente_ttc}
                </p>
              )}
            </div>
          </div>

          {/* Portions + Objectif Food Cost */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="portions" className="block text-sm font-medium text-slate-300 mb-1.5">
                Nombre de portions
              </label>
              <input
                type="number"
                id="portions"
                name="portions"
                value={form.portions}
                onChange={handleChange}
                min="1"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all"
              />
            </div>

            <div>
              <label htmlFor="objectif_food_cost" className="block text-sm font-medium text-slate-300 mb-1.5">
                Objectif Food Cost (%)
              </label>
              <input
                type="number"
                id="objectif_food_cost"
                name="objectif_food_cost"
                value={form.objectif_food_cost}
                onChange={handleChange}
                min="0"
                max="100"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all"
              />
            </div>
          </div>
        </div>

        {/* Section Composition */}
        <div>
          <h3 className="text-base font-semibold text-white mb-4 pb-2 border-b border-white/10 flex items-center gap-2">
            <span className="text-lg">🥗</span>
            Composition du plat
          </h3>

          {/* Liste des ingrédients */}
          <div className="bg-white/5 rounded-xl p-4 mb-4">
            {/* Header */}
            <div className="grid grid-cols-12 gap-3 text-xs text-slate-500 uppercase tracking-wider pb-2 border-b border-white/10 mb-2">
              <div className="col-span-5">Ingrédient</div>
              <div className="col-span-2 text-right">Quantité</div>
              <div className="col-span-2 text-center">Unité</div>
              <div className="col-span-2 text-right">Coût</div>
              <div className="col-span-1"></div>
            </div>

            {/* Ingrédients */}
            <AnimatePresence mode="popLayout">
              {ingredients.length === 0 ? (
                <p className="text-sm text-slate-500 py-4 text-center">Aucun ingrédient ajouté</p>
              ) : (
                ingredients.map((ing, index) => (
                  <motion.div
                    key={ing.ingredient_id}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="grid grid-cols-12 gap-3 items-center py-2 border-b border-white/5 last:border-0"
                  >
                    <div className="col-span-5 text-sm text-white font-medium truncate">{ing.nom}</div>
                    <div className="col-span-2">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={ing.quantite}
                        onChange={(e) => handleIngredientChange(index, 'quantite', e.target.value)}
                        className="w-full px-2 py-1.5 rounded-lg bg-white/10 border border-white/10 text-white text-sm text-right focus:outline-none focus:border-orange-500/50"
                      />
                    </div>
                    <div className="col-span-2 text-center text-sm text-slate-400">{ing.unite}</div>
                    <div className="col-span-2 text-right text-sm font-semibold text-amber-400">
                      {formatCurrency(ing.cout_total)}
                    </div>
                    <div className="col-span-1 flex justify-end">
                      <button
                        type="button"
                        onClick={() => handleRemoveIngredient(index)}
                        className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>

            {/* Ajouter ingrédient */}
            <div className="relative mt-3" ref={dropdownRef}>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Rechercher un ingrédient..."
                  value={ingredientSearch}
                  onChange={(e) => {
                    setIngredientSearch(e.target.value);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-orange-500/10 border border-dashed border-orange-500/30 text-white placeholder-orange-300/50 focus:outline-none focus:border-orange-500/50 transition-all"
                />
              </div>

              {/* Dropdown */}
              <AnimatePresence>
                {showDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute z-50 top-full left-0 right-0 mt-2 bg-slate-800 border border-white/10 rounded-xl shadow-xl max-h-60 overflow-auto"
                  >
                    {ingredientsQuery.isLoading || epicerieQuery.isLoading ? (
                      <div className="p-4 text-center text-slate-400">
                        <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                      </div>
                    ) : filteredItems.length > 0 ? (
                      filteredItems.map((item) => (
                        <button
                          key={`${item.type}-${item.id}`}
                          type="button"
                          onClick={() => handleSelectItem(item)}
                          className="w-full px-4 py-2.5 text-left hover:bg-white/10 transition-colors flex items-center justify-between"
                        >
                          <div>
                            <span className="text-white font-medium">{item.nom}</span>
                            {item.type === 'epicerie' && (
                              <span className="ml-2 text-xs px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">
                                épicerie
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-slate-400">
                            {formatCurrency(item.prix)}/{item.unite}
                          </span>
                        </button>
                      ))
                    ) : (
                      <div className="p-4 text-sm text-slate-400 text-center">Aucun ingrédient trouvé</div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Aperçu Food Cost */}
        {(ingredients.length > 0 || parseFloat(form.prix_vente_ttc) > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-xl p-5 border ${
              foodCostStatus === 'good'
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : foodCostStatus === 'warning'
                ? 'bg-amber-500/10 border-amber-500/30'
                : 'bg-rose-500/10 border-rose-500/30'
            }`}
          >
            <div className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <span>📊</span>
              Aperçu Food Cost
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400 text-sm">Coût matière total</span>
                <span className="text-white font-semibold">{formatCurrency(coutMatiereTotal)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 text-sm">Prix de vente</span>
                <span className="text-white font-semibold">{formatCurrency(parseFloat(form.prix_vente_ttc) || 0)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-white/10">
                <span className="text-slate-400 text-sm">Food Cost</span>
                <span
                  className={`font-bold text-lg ${
                    foodCostStatus === 'good'
                      ? 'text-emerald-400'
                      : foodCostStatus === 'warning'
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }`}
                >
                  {foodCostPct.toFixed(1)}%
                  {foodCostStatus === 'good' && ' ✓'}
                  {foodCostStatus === 'danger' && ' ⚠'}
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={createPlatMutation.isPending}
            className="bg-orange-500 hover:bg-orange-600"
          >
            {createPlatMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Création...
              </>
            ) : (
              'Créer le plat'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
