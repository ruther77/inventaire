import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Leaf,
  Search,
  Link2,
  Loader2,
  AlertTriangle,
  Check,
  X,
  Package,
} from 'lucide-react';
import Modal from '@/components/ui/Modal.jsx';
import Button from '@/components/ui/Button.jsx';
import {
  useCreateRestaurantIngredient,
  useEpicerieProducts,
} from '@/hooks/useRestaurant.js';
import { toast } from 'sonner';

// ============================================================================
// ADDINGREDIENTMODAL - Modal de création d'ingrédient avec lien épicerie
// Design from mockups/modal-add-ingredient.html
// ============================================================================

const CATEGORIES = [
  { value: 'legumes', label: 'Légumes' },
  { value: 'fruits', label: 'Fruits' },
  { value: 'viandes', label: 'Viandes' },
  { value: 'poissons', label: 'Poissons' },
  { value: 'produits-laitiers', label: 'Produits laitiers' },
  { value: 'epices', label: 'Épices & Condiments' },
  { value: 'feculents', label: 'Féculents' },
  { value: 'autres', label: 'Autres' },
];

const UNITES = [
  { value: 'kg', label: 'kg' },
  { value: 'g', label: 'g' },
  { value: 'L', label: 'L' },
  { value: 'ml', label: 'ml' },
  { value: 'piece', label: 'pièce' },
];

const ALLERGENES = [
  { value: '', label: 'Aucun' },
  { value: 'gluten', label: 'Gluten' },
  { value: 'lactose', label: 'Lactose' },
  { value: 'oeufs', label: 'Œufs' },
  { value: 'fruits-coque', label: 'Fruits à coque' },
  { value: 'crustaces', label: 'Crustacés' },
  { value: 'arachides', label: 'Arachides' },
  { value: 'soja', label: 'Soja' },
];

const initialFormState = {
  nom: '',
  categorie: '',
  unite_base: 'kg',
  cout_unitaire: '',
  stock_actuel: '',
  stock_minimum: '',
  allergenes: '',
};

export default function AddIngredientModal({ open, onClose, onSuccess }) {
  const [form, setForm] = useState(initialFormState);
  const [errors, setErrors] = useState({});
  const [linkedProduct, setLinkedProduct] = useState(null);
  const [productSearch, setProductSearch] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Queries
  const epicerieQuery = useEpicerieProducts();
  const createIngredientMutation = useCreateRestaurantIngredient();

  const allProducts = epicerieQuery.data || [];

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

  // Filtrer les produits épicerie
  const filteredProducts = useMemo(() => {
    if (!productSearch.trim()) return allProducts.slice(0, 10);
    const search = productSearch.toLowerCase();
    return allProducts.filter((p) => p.nom?.toLowerCase()?.includes(search)).slice(0, 10);
  }, [allProducts, productSearch]);

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

  const handleSelectProduct = (product) => {
    setLinkedProduct(product);
    setProductSearch(product.nom);
    setShowDropdown(false);

    // Auto-fill prix si disponible
    if (product.prix_achat && !form.cout_unitaire) {
      setForm((prev) => ({ ...prev, cout_unitaire: product.prix_achat.toString() }));
    }
  };

  const handleUnlinkProduct = () => {
    setLinkedProduct(null);
    setProductSearch('');
  };

  const validate = useCallback(() => {
    const newErrors = {};

    if (!form.nom.trim()) {
      newErrors.nom = 'Le nom est requis';
    }

    if (!form.categorie) {
      newErrors.categorie = 'La catégorie est requise';
    }

    if (!form.unite_base) {
      newErrors.unite_base = 'L\'unité est requise';
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
        unite_base: form.unite_base,
        cout_unitaire: form.cout_unitaire ? parseFloat(form.cout_unitaire) : 0,
        stock_actuel: form.stock_actuel ? parseFloat(form.stock_actuel) : 0,
        stock_minimum: form.stock_minimum ? parseFloat(form.stock_minimum) : 5,
        allergenes: form.allergenes || null,
        produit_epicerie_id: linkedProduct?.id || null,
        ratio_epicerie: 1.0,
      };

      createIngredientMutation.mutate(payload, {
        onSuccess: () => {
          toast.success('Ingrédient créé avec succès');
          setForm(initialFormState);
          setLinkedProduct(null);
          setProductSearch('');
          setErrors({});
          onSuccess?.();
          // Note: onClose is NOT called here - onSuccess already handles closing via parent
        },
        onError: (err) => {
          toast.error(`Erreur: ${err.message}`);
        },
      });
    },
    [form, linkedProduct, validate, createIngredientMutation, onSuccess, onClose]
  );

  const handleClose = useCallback(() => {
    setForm(initialFormState);
    setLinkedProduct(null);
    setProductSearch('');
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
      title="Nouvel ingrédient"
      icon={<Leaf className="w-5 h-5 text-orange-400" />}
      size="md"
      gradient="from-orange-500/10 to-transparent"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Nom */}
        <div>
          <label htmlFor="nom" className="block text-sm font-medium text-slate-300 mb-1.5">
            Nom de l'ingrédient <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            id="nom"
            name="nom"
            value={form.nom}
            onChange={handleChange}
            placeholder="Ex: Tomates cerises"
            className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
              errors.nom ? 'border-rose-500' : 'border-white/10'
            } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all`}
          />
          {errors.nom && (
            <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              {errors.nom}
            </p>
          )}
        </div>

        {/* Catégorie + Unité */}
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
            <label htmlFor="unite_base" className="block text-sm font-medium text-slate-300 mb-1.5">
              Unité de base <span className="text-rose-400">*</span>
            </label>
            <select
              id="unite_base"
              name="unite_base"
              value={form.unite_base}
              onChange={handleChange}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all appearance-none cursor-pointer"
            >
              {UNITES.map((u) => (
                <option key={u.value} value={u.value} className="bg-slate-800">
                  {u.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Prix + Stock */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="cout_unitaire" className="block text-sm font-medium text-slate-300 mb-1.5">
              Prix au {form.unite_base || 'kg'}
            </label>
            <div className="relative">
              <input
                type="number"
                id="cout_unitaire"
                name="cout_unitaire"
                value={form.cout_unitaire}
                onChange={handleChange}
                placeholder="0.00"
                step="0.01"
                min="0"
                className="w-full px-4 py-3 pr-10 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500">€</span>
            </div>
          </div>

          <div>
            <label htmlFor="stock_actuel" className="block text-sm font-medium text-slate-300 mb-1.5">
              Stock actuel
            </label>
            <input
              type="number"
              id="stock_actuel"
              name="stock_actuel"
              value={form.stock_actuel}
              onChange={handleChange}
              placeholder="0"
              step="0.01"
              min="0"
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all"
            />
          </div>
        </div>

        {/* Stock min + Allergènes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="stock_minimum" className="block text-sm font-medium text-slate-300 mb-1.5">
              Stock minimum
            </label>
            <input
              type="number"
              id="stock_minimum"
              name="stock_minimum"
              value={form.stock_minimum}
              onChange={handleChange}
              placeholder="5"
              step="0.01"
              min="0"
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all"
            />
          </div>

          <div>
            <label htmlFor="allergenes" className="block text-sm font-medium text-slate-300 mb-1.5">
              Allergènes
            </label>
            <select
              id="allergenes"
              name="allergenes"
              value={form.allergenes}
              onChange={handleChange}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all appearance-none cursor-pointer"
            >
              {ALLERGENES.map((a) => (
                <option key={a.value} value={a.value} className="bg-slate-800">
                  {a.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Section Lien Épicerie */}
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
          <div className="text-sm font-semibold text-emerald-400 mb-3 flex items-center gap-2">
            <Link2 className="w-4 h-4" />
            Lier à un produit épicerie
          </div>

          <div className="relative" ref={dropdownRef}>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Rechercher un produit..."
                  value={productSearch}
                  onChange={(e) => {
                    setProductSearch(e.target.value);
                    setShowDropdown(true);
                    if (!e.target.value.trim()) {
                      setLinkedProduct(null);
                    }
                  }}
                  onFocus={() => setShowDropdown(true)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 transition-all"
                />
              </div>
              {linkedProduct && (
                <Button type="button" variant="ghost" onClick={handleUnlinkProduct} className="px-3">
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>

            {/* Dropdown */}
            <AnimatePresence>
              {showDropdown && !linkedProduct && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute z-50 top-full left-0 right-0 mt-2 bg-slate-800 border border-white/10 rounded-xl shadow-xl max-h-60 overflow-auto"
                >
                  {epicerieQuery.isLoading ? (
                    <div className="p-4 text-center text-slate-400">
                      <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                    </div>
                  ) : filteredProducts.length > 0 ? (
                    filteredProducts.map((product) => (
                      <button
                        key={product.id}
                        type="button"
                        onClick={() => handleSelectProduct(product)}
                        className="w-full px-4 py-2.5 text-left hover:bg-white/10 transition-colors flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <Package className="w-4 h-4 text-emerald-400" />
                          <span className="text-white font-medium">{product.nom}</span>
                        </div>
                        <span className="text-xs text-slate-400">
                          {formatCurrency(product.prix_achat)}/{product.unite || 'kg'}
                        </span>
                      </button>
                    ))
                  ) : (
                    <div className="p-4 text-sm text-slate-400 text-center">Aucun produit trouvé</div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Produit lié */}
          <AnimatePresence>
            {linkedProduct && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-3 flex items-center gap-3 p-3 bg-white/5 rounded-xl"
              >
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center text-lg">
                  🍅
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{linkedProduct.nom}</p>
                  <p className="text-xs text-slate-500">
                    REF: {linkedProduct.code_interne || linkedProduct.id} • {formatCurrency(linkedProduct.prix_achat)}/
                    {linkedProduct.unite || 'kg'}
                  </p>
                </div>
                <Check className="w-5 h-5 text-emerald-400" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={createIngredientMutation.isPending}
            className="bg-orange-500 hover:bg-orange-600"
          >
            {createIngredientMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Création...
              </>
            ) : (
              "Créer l'ingrédient"
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
