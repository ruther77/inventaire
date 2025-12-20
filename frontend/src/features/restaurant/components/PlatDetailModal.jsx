import { useEffect, useMemo, useState, useRef } from 'react';
import { Modal } from '@/components/ui';
import { X, Utensils, Plus, Trash2, Edit3, Check, Search, AlertCircle, Loader2, AlertTriangle } from 'lucide-react';
import CostBreakdownChart from './CostBreakdownChart.jsx';
import PriceSimulatorPanel from './PriceSimulatorPanel.jsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import {
  useAddIngredientToPlat,
  useUpdateIngredientOnPlat,
  useRemoveIngredientFromPlat,
  useRestaurantIngredients,
  useCreateRestaurantIngredient,
  useEpicerieProducts,
  useDeleteRestaurantPlat,
} from '@/hooks/useRestaurant.js';

/**
 * PlatDetailModal - Modal détaillé d'un plat avec fiche technique
 * Permet d'ajouter/modifier/supprimer des ingrédients liés aux produits épicerie
 */
export default function PlatDetailModal({ plat, isOpen, onClose, onUpdatePrice }) {
  const [activeTab, setActiveTab] = useState('fiche');
  const [currentPlat, setCurrentPlat] = useState(plat);
  const [newIngredient, setNewIngredient] = useState({ ingredient_id: '', quantite: '', unite: 'kg' });
  const [ingredientSearch, setIngredientSearch] = useState('');
  const [showIngredientDropdown, setShowIngredientDropdown] = useState(false);
  const [editingIngredient, setEditingIngredient] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [showDeletePlatConfirm, setShowDeletePlatConfirm] = useState(false);
  const [error, setError] = useState(null);
  const dropdownRef = useRef(null);

  // Queries - ingrédients restaurant (liés aux produits épicerie)
  const ingredientsQuery = useRestaurantIngredients();
  const epicerieQuery = useEpicerieProducts();

  const allIngredients = ingredientsQuery.data || [];
  const allEpicerieProducts = epicerieQuery.data || [];

  // Mutations
  const addIngredientMutation = useAddIngredientToPlat();
  const updateIngredientMutation = useUpdateIngredientOnPlat();
  const removeIngredientMutation = useRemoveIngredientFromPlat();
  const createIngredientMutation = useCreateRestaurantIngredient();
  const deletePlatMutation = useDeleteRestaurantPlat();

  useEffect(() => {
    setCurrentPlat(plat);
    setEditingIngredient(null);
    setDeleteConfirm(null);
    setShowDeletePlatConfirm(false);
    setError(null);
  }, [plat]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowIngredientDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Combine ingredients restaurant + produits épicerie pour la recherche
  const searchableItems = useMemo(() => {
    // D'abord les ingrédients restaurant existants
    const items = allIngredients.map(ing => ({
      type: 'ingredient',
      id: ing.id,
      nom: ing.nom,
      prix: ing.produit_epicerie_prix || ing.cout_unitaire || 0,
      unite: ing.unite_base || 'kg',
      produit_epicerie_id: ing.produit_epicerie_id,
      produit_epicerie_nom: ing.produit_epicerie_nom,
    }));

    // Ajouter les produits épicerie qui n'ont pas encore d'ingrédient lié
    const linkedEpicerieIds = new Set(allIngredients.map(i => i.produit_epicerie_id).filter(Boolean));

    allEpicerieProducts.forEach(prod => {
      if (!linkedEpicerieIds.has(prod.id)) {
        items.push({
          type: 'epicerie',
          id: prod.id,
          nom: prod.nom,
          prix: prod.prix_achat || 0,
          unite: 'kg',
          produit_epicerie_id: prod.id,
          categorie: prod.categorie,
        });
      }
    });

    return items;
  }, [allIngredients, allEpicerieProducts]);

  // Filtrer les items disponibles (non déjà dans le plat)
  const usedIngredientIds = useMemo(() => {
    return new Set((currentPlat?.ingredients || []).map(i => i.ingredient_id));
  }, [currentPlat?.ingredients]);

  // Filtrer par recherche
  const filteredItems = useMemo(() => {
    const available = searchableItems.filter(item => {
      if (item.type === 'ingredient') {
        return !usedIngredientIds.has(item.id);
      }
      return true; // Produits épicerie toujours disponibles (on créera l'ingrédient)
    });

    if (!ingredientSearch.trim()) return available.slice(0, 15);
    const search = ingredientSearch.toLowerCase();
    return available
      .filter(item => item.nom?.toLowerCase()?.includes(search))
      .slice(0, 15);
  }, [searchableItems, usedIngredientIds, ingredientSearch]);

  if (!currentPlat) return null;

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
    price_history = [],
  } = currentPlat;

  // Normaliser les ingrédients pour l'affichage
  const normalizedIngredients = (ingredients || []).map((ing) => {
    const unitPrice = ing.unit_price ?? ing.prix_unitaire ?? 0;
    const totalCost = ing.total_cost ?? ing.cout_total ?? unitPrice * (ing.quantite ?? 0);
    return { ...ing, unit_price: unitPrice, total_cost: totalCost };
  });

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value || 0);
  };

  const formatPercent = (value) => `${(value || 0).toFixed(1)}%`;

  const costBreakdownData = normalizedIngredients.map((ing) => ({
    name: ing.nom,
    value: ing.total_cost,
    percentage: cout_matiere > 0 ? (ing.total_cost / cout_matiere) * 100 : 0,
  }));

  const getMarginColor = (v) => (v > 60 ? 'emerald' : v >= 40 ? 'amber' : 'rose');
  const getFoodCostColor = (v) => (v < 30 ? 'emerald' : v <= 35 ? 'amber' : 'rose');

  const handleSelectItem = async (item) => {
    setError(null);

    if (item.type === 'ingredient') {
      // Ingrédient restaurant existant - sélectionner directement
      setNewIngredient({
        ingredient_id: item.id,
        quantite: '',
        unite: item.unite || 'kg',
      });
      setIngredientSearch(item.nom);
    } else {
      // Produit épicerie - créer l'ingrédient restaurant d'abord
      try {
        const created = await createIngredientMutation.mutateAsync({
          nom: item.nom,
          unite_base: item.unite || 'kg',
          cout_unitaire: item.prix || 0,
          produit_epicerie_id: item.id,
          ratio_epicerie: 1.0,
        });
        setNewIngredient({
          ingredient_id: created.id,
          quantite: '',
          unite: item.unite || 'kg',
        });
        setIngredientSearch(item.nom);
      } catch (err) {
        setError(`Erreur création ingrédient: ${err.message}`);
        return;
      }
    }
    setShowIngredientDropdown(false);
  };

  const handleAddIngredient = async () => {
    if (!newIngredient.ingredient_id || !newIngredient.quantite) return;
    setError(null);

    try {
      const payload = {
        ingredient_id: Number(newIngredient.ingredient_id),
        quantite: Number(newIngredient.quantite),
        unite: newIngredient.unite || 'kg',
      };
      const updated = await addIngredientMutation.mutateAsync({ platId: id, payload });
      if (updated?.ingredients) {
        setCurrentPlat(updated);
      }
      setNewIngredient({ ingredient_id: '', quantite: '', unite: 'kg' });
      setIngredientSearch('');
    } catch (err) {
      setError(`Erreur ajout: ${err.message}`);
    }
  };

  const handleStartEdit = (ing) => {
    setEditingIngredient({
      id: ing.ingredient_id,
      quantite: ing.quantite,
      unite: ing.unite,
    });
  };

  const handleSaveEdit = async () => {
    if (!editingIngredient) return;
    setError(null);

    try {
      const payload = { quantite: Number(editingIngredient.quantite), unite: editingIngredient.unite };
      const updated = await updateIngredientMutation.mutateAsync({
        platId: id,
        ingredientId: editingIngredient.id,
        payload,
      });
      if (updated?.ingredients) {
        setCurrentPlat(updated);
      }
      setEditingIngredient(null);
    } catch (err) {
      setError(`Erreur modification: ${err.message}`);
    }
  };

  const handleRemoveIngredient = async (ingredientId) => {
    setError(null);
    try {
      const updated = await removeIngredientMutation.mutateAsync({ platId: id, ingredientId });
      if (updated?.ingredients) {
        setCurrentPlat(updated);
      }
      setDeleteConfirm(null);
    } catch (err) {
      setError(`Erreur suppression: ${err.message}`);
    }
  };

  const handleDeletePlat = async () => {
    setError(null);
    try {
      await deletePlatMutation.mutateAsync(id);
      onClose();
    } catch (err) {
      setError(`Erreur suppression plat: ${err.message}`);
      setShowDeletePlatConfirm(false);
    }
  };

  const isLoading = ingredientsQuery.isLoading || epicerieQuery.isLoading;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <div className="flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-white/10 bg-gradient-to-r from-violet-500/10 to-pink-500/10">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-xl bg-violet-500/20 border border-violet-500/30">
                <Utensils className="w-5 h-5 text-violet-400" />
              </div>
              <h2 className="text-2xl font-bold text-white">{nom}</h2>
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                actif ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
              }`}>
                {actif ? 'Actif' : 'Inactif'}
              </span>
            </div>
            {categorie && <p className="text-xs text-slate-400 uppercase tracking-wider">{categorie}</p>}
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-4 gap-4 p-6 border-b border-white/10 bg-white/5">
          <div className="text-center p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-500 uppercase mb-1">Prix TTC</p>
            <p className="text-xl font-bold text-white">{formatCurrency(prix_vente_ttc)}</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-500 uppercase mb-1">Coût matière</p>
            <p className="text-xl font-bold text-white">{formatCurrency(cout_matiere)}</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-500 uppercase mb-1">Marge</p>
            <p className={`text-xl font-bold text-${getMarginColor(marge_pct)}-400`}>{formatPercent(marge_pct)}</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-500 uppercase mb-1">Food Cost</p>
            <p className={`text-xl font-bold text-${getFoodCostColor(food_cost_pct)}-400`}>{formatPercent(food_cost_pct)}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-4 border-b border-white/10">
          {['fiche', 'history', 'simulator'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab
                  ? 'bg-white/10 text-violet-400 border-t border-x border-white/10'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tab === 'fiche' ? 'Fiche technique' : tab === 'history' ? 'Historique prix' : 'Simulateur'}
            </button>
          ))}
        </div>

        {/* Error banner */}
        {error && (
          <div className="mx-6 mt-4 p-3 bg-rose-500/20 border border-rose-500/30 rounded-xl flex items-center gap-2 text-rose-400">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
            <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'fiche' && (
            <div className="space-y-6">
              {/* Ingrédients */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">
                  Ingrédients
                  {isLoading && <Loader2 className="inline w-4 h-4 ml-2 animate-spin text-slate-400" />}
                </h3>

                {normalizedIngredients.length === 0 ? (
                  <p className="text-sm text-slate-500">Aucun ingrédient renseigné</p>
                ) : (
                  <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                    <table className="min-w-full divide-y divide-white/10">
                      <thead className="bg-white/5">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Ingrédient</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Quantité</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Prix unit.</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Source</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Coût total</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase w-28">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/10">
                        {normalizedIngredients.map((ing, idx) => {
                          const isEditing = editingIngredient?.id === ing.ingredient_id;
                          const isDeleting = deleteConfirm === ing.ingredient_id;

                          // Determine if ingredient is linked to epicerie
                          const linkedIng = allIngredients.find(i => i.id === ing.ingredient_id);
                          const hasEpicerieLink = linkedIng?.produit_epicerie_id;
                          const priceSource = hasEpicerieLink ? 'epicerie' : 'manual';

                          return (
                            <tr key={idx} className="hover:bg-white/5">
                              <td className="px-4 py-3 text-sm text-white font-medium">
                                <div>
                                  <div>{ing.nom || '—'}</div>
                                  {hasEpicerieLink && linkedIng?.produit_epicerie_nom && (
                                    <div className="text-xs text-violet-400 mt-0.5">
                                      {linkedIng.produit_epicerie_nom}
                                    </div>
                                  )}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-sm text-right">
                                {isEditing ? (
                                  <div className="flex items-center justify-end gap-2">
                                    <input
                                      type="number"
                                      step="0.01"
                                      className="w-20 px-2 py-1 rounded-lg bg-white/10 border border-white/20 text-white text-sm text-right"
                                      value={editingIngredient.quantite}
                                      onChange={(e) => setEditingIngredient(prev => ({ ...prev, quantite: e.target.value }))}
                                      autoFocus
                                    />
                                    <input
                                      type="text"
                                      className="w-14 px-2 py-1 rounded-lg bg-white/10 border border-white/20 text-white text-sm"
                                      value={editingIngredient.unite}
                                      onChange={(e) => setEditingIngredient(prev => ({ ...prev, unite: e.target.value }))}
                                    />
                                  </div>
                                ) : (
                                  <span className="text-slate-300">{ing.quantite} {ing.unite}</span>
                                )}
                              </td>
                              <td className="px-4 py-3 text-sm text-slate-300 text-right">{formatCurrency(ing.unit_price)}</td>
                              <td className="px-4 py-3 text-sm text-right">
                                {priceSource === 'epicerie' ? (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400 border border-violet-500/30 text-xs font-medium">
                                    Epicerie
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-500/20 text-slate-400 border border-slate-500/30 text-xs font-medium">
                                    Manuel
                                  </span>
                                )}
                              </td>
                              <td className="px-4 py-3 text-sm font-semibold text-white text-right">{formatCurrency(ing.total_cost)}</td>
                              <td className="px-4 py-3 text-right">
                                {isDeleting ? (
                                  <div className="flex items-center justify-end gap-1">
                                    <button onClick={() => handleRemoveIngredient(ing.ingredient_id)} className="px-2 py-1 text-xs bg-rose-500/20 text-rose-400 rounded-lg">OK</button>
                                    <button onClick={() => setDeleteConfirm(null)} className="px-2 py-1 text-xs bg-white/10 text-slate-300 rounded-lg">Non</button>
                                  </div>
                                ) : isEditing ? (
                                  <div className="flex items-center justify-end gap-1">
                                    <button onClick={handleSaveEdit} className="p-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg"><Check className="w-4 h-4" /></button>
                                    <button onClick={() => setEditingIngredient(null)} className="p-1.5 bg-white/10 text-slate-300 rounded-lg"><X className="w-4 h-4" /></button>
                                  </div>
                                ) : (
                                  <div className="flex items-center justify-end gap-1">
                                    <button onClick={() => handleStartEdit(ing)} className="p-1.5 bg-white/10 text-slate-300 rounded-lg hover:bg-white/20"><Edit3 className="w-4 h-4" /></button>
                                    <button onClick={() => setDeleteConfirm(ing.ingredient_id)} className="p-1.5 bg-white/10 text-slate-300 rounded-lg hover:bg-rose-500/20 hover:text-rose-400"><Trash2 className="w-4 h-4" /></button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                      <tfoot className="bg-white/5">
                        <tr>
                          <td colSpan="4" className="px-4 py-3 text-sm font-semibold text-white">Total coût matière</td>
                          <td className="px-4 py-3 text-sm font-bold text-white text-right">{formatCurrency(cout_matiere)}</td>
                          <td></td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}
              </div>

              {/* Graphique */}
              {normalizedIngredients.length > 0 && (
                <CostBreakdownChart data={costBreakdownData} title="Répartition des coûts" />
              )}

              {/* Ajouter un ingrédient */}
              <div className="mt-6 border-t border-white/10 pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <Plus className="w-5 h-5 text-violet-400" />
                  <h4 className="text-sm font-semibold text-white">Ajouter un ingrédient (produit épicerie)</h4>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                  <div className="relative md:col-span-2" ref={dropdownRef}>
                    <label className="block text-xs uppercase text-slate-500 mb-1">Produit</label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <input
                        type="text"
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-violet-500/50 focus:outline-none"
                        placeholder="Rechercher un produit épicerie..."
                        value={ingredientSearch}
                        onChange={(e) => {
                          setIngredientSearch(e.target.value);
                          setShowIngredientDropdown(true);
                          if (!e.target.value.trim()) {
                            setNewIngredient(prev => ({ ...prev, ingredient_id: '' }));
                          }
                        }}
                        onFocus={() => setShowIngredientDropdown(true)}
                      />

                      {/* Dropdown */}
                      {showIngredientDropdown && (
                        <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-slate-800 border border-white/10 rounded-xl shadow-xl max-h-60 overflow-auto">
                          {isLoading ? (
                            <div className="p-4 text-center text-slate-400">
                              <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                            </div>
                          ) : filteredItems.length > 0 ? (
                            filteredItems.map((item) => (
                              <button
                                key={`${item.type}-${item.id}`}
                                type="button"
                                className="w-full px-4 py-2.5 text-left hover:bg-white/10 transition-colors flex items-center justify-between"
                                onClick={() => handleSelectItem(item)}
                              >
                                <div>
                                  <span className="text-white font-medium">{item.nom}</span>
                                  {item.type === 'epicerie' && (
                                    <span className="ml-2 text-xs px-1.5 py-0.5 bg-violet-500/20 text-violet-400 rounded">épicerie</span>
                                  )}
                                </div>
                                <span className="text-xs text-slate-400">{formatCurrency(item.prix)}/{item.unite}</span>
                              </button>
                            ))
                          ) : (
                            <div className="p-4 text-sm text-slate-400">Aucun produit trouvé</div>
                          )}
                        </div>
                      )}
                    </div>
                    {newIngredient.ingredient_id && (
                      <p className="mt-1 text-xs text-emerald-400">Produit sélectionné</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs uppercase text-slate-500 mb-1">Quantité</label>
                    <input
                      type="number"
                      step="0.01"
                      className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-violet-500/50 focus:outline-none"
                      value={newIngredient.quantite}
                      onChange={(e) => setNewIngredient(prev => ({ ...prev, quantite: e.target.value }))}
                      placeholder="ex: 0.5"
                    />
                  </div>

                  <div>
                    <label className="block text-xs uppercase text-slate-500 mb-1">Unité</label>
                    <input
                      type="text"
                      className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-violet-500/50 focus:outline-none"
                      value={newIngredient.unite}
                      onChange={(e) => setNewIngredient(prev => ({ ...prev, unite: e.target.value }))}
                      placeholder="kg"
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <button
                    onClick={handleAddIngredient}
                    disabled={!newIngredient.ingredient_id || !newIngredient.quantite || addIngredientMutation.isLoading}
                    className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-pink-600 text-white font-medium disabled:opacity-50 hover:from-violet-500 hover:to-pink-500 transition-all flex items-center gap-2"
                  >
                    {addIngredientMutation.isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                    Ajouter l'ingrédient
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Historique */}
          {activeTab === 'history' && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Historique des prix</h3>
              {price_history.length === 0 ? (
                <p className="text-sm text-slate-500">Aucun historique disponible</p>
              ) : (
                <div>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={price_history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="date" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                      <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} tickFormatter={(v) => `${v}€`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                        formatter={(value) => [formatCurrency(value), 'Prix']}
                      />
                      <Line type="monotone" dataKey="prix" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
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
        <div className="flex justify-between items-center gap-2 p-6 border-t border-white/10 bg-white/5">
          <div>
            {showDeletePlatConfirm ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-rose-400">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="text-sm font-medium">Confirmer la suppression ?</span>
                </div>
                <button
                  onClick={handleDeletePlat}
                  disabled={deletePlatMutation.isLoading}
                  className="px-4 py-2 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30 font-medium text-sm disabled:opacity-50"
                >
                  {deletePlatMutation.isLoading ? 'Suppression...' : 'Oui, supprimer'}
                </button>
                <button
                  onClick={() => setShowDeletePlatConfirm(false)}
                  className="px-4 py-2 rounded-xl bg-white/10 border border-white/10 text-white hover:bg-white/20 font-medium text-sm"
                >
                  Annuler
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowDeletePlatConfirm(true)}
                className="px-4 py-2 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30 font-medium text-sm flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Supprimer ce plat
              </button>
            )}
          </div>
          <button onClick={onClose} className="px-6 py-2.5 rounded-xl bg-white/10 border border-white/10 text-white font-medium hover:bg-white/20">
            Fermer
          </button>
        </div>
      </div>
    </Modal>
  );
}
