import { useState, useCallback, useEffect } from 'react';
import { Package, Barcode, Euro, AlertTriangle, Loader2, Camera, Truck } from 'lucide-react';
import Modal from '@/components/ui/Modal.jsx';
import Button from '@/components/ui/Button.jsx';
import { useUpdateProduct } from '@/hooks/useCatalogMutations.js';
import { toast } from 'sonner';

const CATEGORIES = [
  'Fruits & Légumes',
  'Viandes',
  'Poissons',
  'Produits laitiers',
  'Épicerie sèche',
  'Boissons',
  'Surgelés',
  'Condiments',
  'Boulangerie',
  'Autres',
];

const UNITS = [
  { value: 'kg', label: 'Kilogramme (kg)' },
  { value: 'L', label: 'Litre (L)' },
  { value: 'unit', label: 'Unité' },
  { value: 'pce', label: 'Pièce' },
  { value: 'g', label: 'Gramme (g)' },
  { value: 'mL', label: 'Millilitre (mL)' },
  { value: 'lot', label: 'Lot' },
];

const SUPPLIERS = [
  'Metro France',
  'Brake France',
  'Pomona',
  'Transgourmet',
  'Sysco',
  'Autre',
];

export default function EditProductModal({ open, onClose, product, onSuccess }) {
  const [form, setForm] = useState({
    nom: '',
    categorie: '',
    prix_achat: '',
    prix_vente: '',
    stock_actuel: '',
    seuil_alerte: '',
    stock_max: '',
    unite: 'kg',
    code_barre: '',
    code_interne: '',
    conditionnement: '',
    fournisseur: '',
    description: '',
  });
  const [errors, setErrors] = useState({});

  const updateProduct = useUpdateProduct();

  // Pré-remplir le formulaire quand le produit change
  useEffect(() => {
    if (product && open) {
      setForm({
        nom: product.nom || '',
        categorie: product.categorie || '',
        prix_achat: product.prix_achat?.toString() || '',
        prix_vente: product.prix_vente?.toString() || '',
        stock_actuel: product.stock_actuel?.toString() || '',
        seuil_alerte: product.seuil_alerte?.toString() || '',
        stock_max: product.stock_max?.toString() || '',
        unite: product.unite || 'kg',
        code_barre: product.code_barre || product.barcode || '',
        code_interne: product.code_interne || product.reference || '',
        conditionnement: product.conditionnement || '',
        fournisseur: product.fournisseur || '',
        description: product.description || '',
      });
      setErrors({});
    }
  }, [product, open]);

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  }, [errors]);

  const validate = useCallback(() => {
    const newErrors = {};

    if (!form.nom.trim()) {
      newErrors.nom = 'Le nom est requis';
    } else if (form.nom.trim().length < 2) {
      newErrors.nom = 'Minimum 2 caractères';
    }

    if (!form.categorie) {
      newErrors.categorie = 'La catégorie est requise';
    }

    if (!form.prix_achat || parseFloat(form.prix_achat) <= 0) {
      newErrors.prix_achat = 'Prix d\'achat invalide';
    }

    if (!form.prix_vente || parseFloat(form.prix_vente) <= 0) {
      newErrors.prix_vente = 'Prix de vente invalide';
    }

    if (parseFloat(form.prix_vente) < parseFloat(form.prix_achat)) {
      newErrors.prix_vente = 'Le prix de vente doit être supérieur au prix d\'achat';
    }

    if (form.stock_actuel && parseFloat(form.stock_actuel) < 0) {
      newErrors.stock_actuel = 'Le stock ne peut pas être négatif';
    }

    if (form.seuil_alerte && parseFloat(form.seuil_alerte) < 0) {
      newErrors.seuil_alerte = 'Le seuil ne peut pas être négatif';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [form]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    if (!validate()) return;

    const payload = {
      nom: form.nom.trim(),
      categorie: form.categorie,
      prix_achat: parseFloat(form.prix_achat),
      prix_vente: parseFloat(form.prix_vente),
      stock_actuel: form.stock_actuel ? parseFloat(form.stock_actuel) : 0,
      seuil_alerte: form.seuil_alerte ? parseFloat(form.seuil_alerte) : 10,
      stock_max: form.stock_max ? parseFloat(form.stock_max) : null,
      unite: form.unite,
      code_barre: form.code_barre.trim() || null,
      code_interne: form.code_interne.trim() || null,
      conditionnement: form.conditionnement.trim() || null,
      fournisseur: form.fournisseur || null,
      description: form.description.trim() || null,
    };

    updateProduct.mutate(
      { productId: product.id, payload },
      {
        onSuccess: () => {
          onSuccess?.();
          onClose();
        },
      }
    );
  }, [form, validate, updateProduct, product, onSuccess, onClose]);

  const handleClose = useCallback(() => {
    setErrors({});
    onClose();
  }, [onClose]);

  if (!product) return null;

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Modifier le produit"
      description={`Édition de "${product.nom}"`}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Section Informations principales */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Package className="w-4 h-4" />
            Informations principales
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Nom */}
            <div className="md:col-span-2">
              <label htmlFor="nom" className="block text-sm font-medium text-slate-300 mb-1.5">
                Nom du produit <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                id="nom"
                name="nom"
                value={form.nom}
                onChange={handleChange}
                placeholder="Ex: Tomates grappe bio"
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.nom ? 'border-rose-500' : 'border-white/10'
                } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all`}
              />
              {errors.nom && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.nom}
                </p>
              )}
            </div>

            {/* Catégorie */}
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
                } text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all appearance-none cursor-pointer`}
              >
                <option value="" className="bg-slate-800">Sélectionner...</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat} className="bg-slate-800">
                    {cat}
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

            {/* Unité */}
            <div>
              <label htmlFor="unite" className="block text-sm font-medium text-slate-300 mb-1.5">
                Unité de mesure
              </label>
              <select
                id="unite"
                name="unite"
                value={form.unite}
                onChange={handleChange}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all appearance-none cursor-pointer"
              >
                {UNITS.map((unit) => (
                  <option key={unit.value} value={unit.value} className="bg-slate-800">
                    {unit.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section Prix */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Euro className="w-4 h-4" />
            Tarification
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Prix d'achat */}
            <div>
              <label htmlFor="prix_achat" className="block text-sm font-medium text-slate-300 mb-1.5">
                Prix d'achat HT <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <input
                  type="number"
                  id="prix_achat"
                  name="prix_achat"
                  value={form.prix_achat}
                  onChange={handleChange}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  className={`w-full px-4 py-3 pr-12 rounded-xl bg-white/5 border ${
                    errors.prix_achat ? 'border-rose-500' : 'border-white/10'
                  } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all`}
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500">€</span>
              </div>
              {errors.prix_achat && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.prix_achat}
                </p>
              )}
            </div>

            {/* Prix de vente */}
            <div>
              <label htmlFor="prix_vente" className="block text-sm font-medium text-slate-300 mb-1.5">
                Prix de vente TTC <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <input
                  type="number"
                  id="prix_vente"
                  name="prix_vente"
                  value={form.prix_vente}
                  onChange={handleChange}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  className={`w-full px-4 py-3 pr-12 rounded-xl bg-white/5 border ${
                    errors.prix_vente ? 'border-rose-500' : 'border-white/10'
                  } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all`}
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500">€</span>
              </div>
              {errors.prix_vente && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.prix_vente}
                </p>
              )}
              {form.prix_achat && form.prix_vente && parseFloat(form.prix_vente) > parseFloat(form.prix_achat) && (
                <p className="mt-1.5 text-sm text-emerald-400">
                  Marge: {((parseFloat(form.prix_vente) - parseFloat(form.prix_achat)) / parseFloat(form.prix_vente) * 100).toFixed(1)}%
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Section Fournisseur */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Truck className="w-4 h-4" />
            Fournisseur & Conditionnement
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Fournisseur */}
            <div>
              <label htmlFor="fournisseur" className="block text-sm font-medium text-slate-300 mb-1.5">
                Fournisseur principal
              </label>
              <select
                id="fournisseur"
                name="fournisseur"
                value={form.fournisseur}
                onChange={handleChange}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all appearance-none cursor-pointer"
              >
                <option value="" className="bg-slate-800">Sélectionner...</option>
                {SUPPLIERS.map((supplier) => (
                  <option key={supplier} value={supplier} className="bg-slate-800">
                    {supplier}
                  </option>
                ))}
              </select>
            </div>

            {/* Conditionnement */}
            <div>
              <label htmlFor="conditionnement" className="block text-sm font-medium text-slate-300 mb-1.5">
                Conditionnement
              </label>
              <input
                type="text"
                id="conditionnement"
                name="conditionnement"
                value={form.conditionnement}
                onChange={handleChange}
                placeholder="Ex: Carton de 12, Palette..."
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>

        {/* Section Stock */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Package className="w-4 h-4" />
            Stock
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Stock actuel */}
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
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.stock_actuel ? 'border-rose-500' : 'border-white/10'
                } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all`}
              />
              {errors.stock_actuel && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.stock_actuel}
                </p>
              )}
            </div>

            {/* Seuil d'alerte */}
            <div>
              <label htmlFor="seuil_alerte" className="block text-sm font-medium text-slate-300 mb-1.5">
                Seuil min
              </label>
              <input
                type="number"
                id="seuil_alerte"
                name="seuil_alerte"
                value={form.seuil_alerte}
                onChange={handleChange}
                placeholder="10"
                step="0.01"
                min="0"
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.seuil_alerte ? 'border-rose-500' : 'border-white/10'
                } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all`}
              />
            </div>

            {/* Stock max */}
            <div>
              <label htmlFor="stock_max" className="block text-sm font-medium text-slate-300 mb-1.5">
                Stock max
              </label>
              <input
                type="number"
                id="stock_max"
                name="stock_max"
                value={form.stock_max}
                onChange={handleChange}
                placeholder="100"
                step="0.01"
                min="0"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>

        {/* Section Codes */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Barcode className="w-4 h-4" />
            Codes & Références
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Code barre */}
            <div>
              <label htmlFor="code_barre" className="block text-sm font-medium text-slate-300 mb-1.5">
                Code barre (EAN/UPC)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  id="code_barre"
                  name="code_barre"
                  value={form.code_barre}
                  onChange={handleChange}
                  placeholder="3700123456789"
                  className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
                />
                <button
                  type="button"
                  onClick={() => toast.info('Scanner non disponible')}
                  className="px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                  title="Scanner le code barre"
                >
                  <Camera className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Code interne */}
            <div>
              <label htmlFor="code_interne" className="block text-sm font-medium text-slate-300 mb-1.5">
                Code interne
              </label>
              <input
                type="text"
                id="code_interne"
                name="code_interne"
                value={form.code_interne}
                onChange={handleChange}
                placeholder="METRO-TOM-001"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
              />
            </div>
          </div>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-slate-300 mb-1.5">
            Description (optionnel)
          </label>
          <textarea
            id="description"
            name="description"
            value={form.description}
            onChange={handleChange}
            rows={3}
            placeholder="Notes ou description du produit..."
            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={updateProduct.isPending}
          >
            {updateProduct.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Mise à jour...
              </>
            ) : (
              'Enregistrer'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
