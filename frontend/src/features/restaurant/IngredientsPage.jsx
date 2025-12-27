import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Select from '@/components/ui/Select.jsx';
import SmartTable from '@/components/ui/SmartTable.jsx';
import Sparkline from '@/components/ui/Sparkline.jsx';
import Modal, { ConfirmDialog } from '@/components/ui/Modal.jsx';
import { PullToRefresh } from '@/components/ui/PullToRefresh.jsx';
import { SwipeableRowProvider } from '@/components/ui/SwipeableRow.jsx';
import MobileIngredientRow from './components/MobileIngredientRow.jsx';
import { AddIngredientModal, IngredientDetailDrawer } from './components';
import { useRestaurantIngredients, useUpdateRestaurantIngredient, useDeleteRestaurantIngredient, useSyncIngredientPrices, usePriceSyncStatus, useRestaurantIngredientPriceHistory } from '@/hooks/useRestaurant.js';
import { Search, Filter, TrendingUp, TrendingDown, Minus, ChevronRight, Package, AlertTriangle, Link2, Edit3, Trash2, Calendar, DollarSign, Box, Save, X, Plus, RefreshCw, SlidersHorizontal } from 'lucide-react';
import { TableSkeleton } from '@/components/ui/Skeleton.jsx';
import QueryErrorState from '@/components/feedback/QueryErrorState.jsx';

/**
 * IngredientsPage - Liste des ingrédients avec tendances prix
 * Dark Theme Design System (2025 Next-Gen)
 *
 * Mobile/Tablet Kitchen Optimizations:
 * - Pull-to-refresh for quick data updates
 * - Swipeable rows with quick actions (edit, delete, update stock)
 * - Large touch targets (min 48px) for kitchen use
 * - Bold, high-contrast text for ingredient names and stock levels
 * - Visual indicators for low/critical stock (red/amber highlights)
 * - Quick stock update modal with numeric keypad
 * - Responsive: Desktop table view / Mobile swipeable card view
 */
export default function IngredientsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [supplierFilter, setSupplierFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [trendFilter, setTrendFilter] = useState('all');
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [quickStockUpdate, setQuickStockUpdate] = useState(null);
  const [quickStockValue, setQuickStockValue] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [drawerIngredient, setDrawerIngredient] = useState(null);

  // Queries
  const ingredientsQuery = useRestaurantIngredients();
  const ingredients = ingredientsQuery.data || [];
  const priceSyncStatusQuery = usePriceSyncStatus();
  const syncStatus = priceSyncStatusQuery.data || null;
  const ingredientHistoryQuery = useRestaurantIngredientPriceHistory(selectedIngredient?.id);
  const ingredientHistory = ingredientHistoryQuery.data || [];
  const normalizedHistory = useMemo(() => {
    if (!ingredientHistory.length) return [];
    const reversed = [...ingredientHistory].reverse();
    return reversed.map((entry) => ({
      prix: entry.cout_unitaire,
      changed_at: entry.changed_at,
    }));
  }, [ingredientHistory]);

  // Mutations
  const updateMutation = useUpdateRestaurantIngredient();
  const deleteMutation = useDeleteRestaurantIngredient();
  const syncPricesMutation = useSyncIngredientPrices();

  // Handlers
  const handleOpenDetail = (ingredient) => {
    setSelectedIngredient(ingredient);
    setEditForm({
      nom: ingredient.nom,
      unite_base: ingredient.unite_base,
      cout_unitaire: ingredient.cout_unitaire,
      stock_actuel: ingredient.stock_actuel,
      stock_min: ingredient.stock_min || '',
      categorie: ingredient.categorie || '',
      fournisseur: ingredient.fournisseur || '',
    });
    setIsEditing(false);
  };

  const handleCloseModal = () => {
    setSelectedIngredient(null);
    setIsEditing(false);
    setEditForm({});
  };

  const handleSave = async () => {
    if (!selectedIngredient) return;
    try {
      await updateMutation.mutateAsync({
        ingredientId: selectedIngredient.id,
        payload: {
          nom: editForm.nom,
          unite_base: editForm.unite_base,
          cout_unitaire: parseFloat(editForm.cout_unitaire) || 0,
          stock_actuel: parseFloat(editForm.stock_actuel) || 0,
          stock_min: editForm.stock_min ? parseFloat(editForm.stock_min) : null,
          categorie: editForm.categorie || null,
          fournisseur: editForm.fournisseur || null,
        },
      });
      setIsEditing(false);
      handleCloseModal();
    } catch (error) {
      alert(`Erreur: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDelete = async (ingredientId) => {
    try {
      await deleteMutation.mutateAsync(ingredientId || selectedIngredient?.id);
      setShowDeleteConfirm(false);
      if (selectedIngredient) {
        handleCloseModal();
      }
    } catch (error) {
      alert(`Erreur: ${error.response?.data?.detail || error.message}`);
      setShowDeleteConfirm(false);
    }
  };

  const handleQuickStockUpdate = async () => {
    if (!quickStockUpdate) return;
    try {
      await updateMutation.mutateAsync({
        ingredientId: quickStockUpdate.id,
        payload: {
          stock_actuel: parseFloat(quickStockValue) || 0,
        },
      });
      setQuickStockUpdate(null);
      setQuickStockValue('');
    } catch (error) {
      alert(`Erreur: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteWithConfirm = async (ingredient) => {
    if (window.confirm(`Supprimer "${ingredient.nom}" ?`)) {
      await handleDelete(ingredient.id);
    }
  };

  const handleSyncPrices = async (forceUpdate = false) => {
    try {
      const result = await syncPricesMutation.mutateAsync({ forceUpdate });
      const message = forceUpdate
        ? `Synchronisation forcée terminée: ${result.updated_count || 0} prix mis à jour`
        : `Synchronisation terminée: ${result.updated_count || 0} prix mis à jour`;
      alert(message);
    } catch (error) {
      alert(`Erreur lors de la synchronisation: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Fournisseurs et catégories uniques
  const suppliers = useMemo(() => {
    const sups = new Set(ingredients.map(i => i.fournisseur).filter(Boolean));
    return Array.from(sups);
  }, [ingredients]);

  const categories = useMemo(() => {
    const cats = new Set(ingredients.map(i => i.categorie).filter(Boolean));
    return Array.from(cats);
  }, [ingredients]);

  // Filtrage
  const filteredIngredients = useMemo(() => {
    return ingredients.filter(ing => {
      if (search && !ing.nom.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      if (supplierFilter && ing.fournisseur !== supplierFilter) {
        return false;
      }
      if (categoryFilter && ing.categorie !== categoryFilter) {
        return false;
      }
      if (trendFilter !== 'all' && ing.price_trend) {
        if (trendFilter === 'up' && ing.price_trend !== 'up') return false;
        if (trendFilter === 'down' && ing.price_trend !== 'down') return false;
        if (trendFilter === 'stable' && ing.price_trend !== 'stable') return false;
      }
      return true;
    });
  }, [ingredients, search, supplierFilter, categoryFilter, trendFilter]);

  // Stats
  const stats = useMemo(() => {
    const lowStock = ingredients.filter(i => i.stock_actuel && i.stock_min && i.stock_actuel <= i.stock_min).length;
    const priceUp = ingredients.filter(i => i.price_trend === 'up').length;
    const priceDown = ingredients.filter(i => i.price_trend === 'down').length;
    return { lowStock, priceUp, priceDown };
  }, [ingredients]);

  const formatCurrency = useCallback((value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value || 0);
  }, []);

  // Handlers pour le composant mobile
  const handleQuickStockOpen = useCallback((ingredient) => {
    setQuickStockUpdate(ingredient);
    setQuickStockValue(ingredient.stock_actuel?.toString() || '0');
  }, []);

  const columns = useMemo(() => [
    {
      key: 'nom',
      header: 'Ingrédient',
      render: (value, row) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500/20 to-cyan-500/20 border border-white/10 flex items-center justify-center">
            <Package className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <p className="font-semibold text-white">{value}</p>
            <p className="text-xs text-slate-500 uppercase tracking-wider">
              {row.categorie || 'Sans catégorie'} • {row.fournisseur || 'Sans fournisseur'}
            </p>
          </div>
        </div>
      ),
    },
    {
      key: 'cout_unitaire',
      header: 'Prix unitaire',
      align: 'right',
      render: (value, row) => (
        <div className="text-right">
          <p className="font-semibold text-white">{formatCurrency(value)}</p>
          <p className="text-xs text-slate-500">/ {row.unite_base}</p>
        </div>
      ),
    },
    {
      key: 'stock_actuel',
      header: 'Stock',
      align: 'right',
      render: (value, row) => {
        const isCritical = row.stock_min && value <= row.stock_min;
        const isLow = row.stock_min && value <= row.stock_min * 1.5 && !isCritical;
        return (
          <div className="text-right">
            <p className="font-semibold text-white">
              {value?.toFixed(2) || 0} {row.unite_base}
            </p>
            {isCritical && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                Critique
              </span>
            )}
            {isLow && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                Bas
              </span>
            )}
            {!isCritical && !isLow && row.stock_min && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                OK
              </span>
            )}
          </div>
        );
      },
    },
    {
      key: 'price_trend',
      header: 'Tendance',
      align: 'center',
      render: (value, row) => {
        const getTrendIcon = () => {
          if (value === 'up') return <TrendingUp className="w-4 h-4 text-rose-400" />;
          if (value === 'down') return <TrendingDown className="w-4 h-4 text-emerald-400" />;
          return <Minus className="w-4 h-4 text-slate-500" />;
        };
        const getTrendBadge = () => {
          if (value === 'up') {
            return (
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                +{row.price_evolution?.toFixed(1) || 0}%
              </span>
            );
          }
          if (value === 'down') {
            return (
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {row.price_evolution?.toFixed(1) || 0}%
              </span>
            );
          }
          return (
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-500/20 text-slate-400 border border-slate-500/30">
              Stable
            </span>
          );
        };
        return (
          <div className="flex flex-col items-center gap-1">
            {getTrendIcon()}
            {getTrendBadge()}
          </div>
        );
      },
    },
    {
      key: 'price_history_sparkline',
      header: 'Évolution (30j)',
      align: 'center',
      sortable: false,
      render: (_, row) => {
        if (!row.price_history || row.price_history.length === 0) {
          return <span className="text-xs text-slate-500">Aucune donnée</span>;
        }
        const data = row.price_history.map(h => h.prix);
        const trend = row.price_trend === 'up' ? 'up' : row.price_trend === 'down' ? 'down' : 'neutral';
        return (
          <div className="flex justify-center">
            <Sparkline data={data} width={100} height={30} trend={trend} />
          </div>
        );
      },
    },
    {
      key: 'actions',
      header: '',
      sortable: false,
      render: (_, row) => (
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setDrawerIngredient(row);
            }}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            title="Aperçu rapide"
          >
            <SlidersHorizontal className="w-4 h-4 text-slate-400" />
          </button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleOpenDetail(row)}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      ),
    },
  ], [handleOpenDetail]);

  // Erreur
  if (ingredientsQuery.isError && !ingredients.length) {
    return <QueryErrorState error={ingredientsQuery.error} onRetry={() => ingredientsQuery.refetch()} variant="full" />;
  }

  return (
    <PullToRefresh
      onRefresh={async () => {
        await ingredientsQuery.refetch();
      }}
      className="h-full"
    >
      <div className="space-y-6 pb-20">
        {/* Header */}
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-teal-500/20 via-slate-800/50 to-cyan-500/10 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <Package className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-400 mb-1">Restaurant</p>
              <h1 className="text-2xl font-bold text-white">Liste des ingrédients</h1>
              <p className="text-sm text-slate-400 mt-1">
                Suivez les prix, stocks et tendances de vos ingrédients.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant="primary"
              onClick={() => setShowCreateModal(true)}
              className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Nouvel ingrédient
            </Button>
            <Button
              variant="outline"
              onClick={() => handleSyncPrices(false)}
              loading={syncPricesMutation.isPending}
              className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Sync Prix
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/restaurant/liens')}
              className="border-teal-500/50 text-teal-400 hover:bg-teal-500/10"
            >
              <Link2 className="w-4 h-4 mr-2" />
              Liens Epicerie
            </Button>
          </div>
        </div>

        {/* Stats rapides */}
        <div className="flex flex-wrap items-center gap-4 mt-4">
          <div className="text-center px-4 py-2 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-500 uppercase">Total</p>
            <p className="text-2xl font-bold text-white">{ingredients.length}</p>
          </div>
          {stats.lowStock > 0 && (
            <div className="text-center px-4 py-2 rounded-xl bg-rose-500/10 border border-rose-500/30">
              <p className="text-xs text-rose-400 uppercase flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Stock bas
              </p>
              <p className="text-2xl font-bold text-rose-400">{stats.lowStock}</p>
            </div>
          )}
          <div className="text-center px-4 py-2 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-500 uppercase">Prix en hausse</p>
            <p className="text-2xl font-bold text-rose-400">{stats.priceUp}</p>
          </div>
          <div className="text-center px-4 py-2 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-500 uppercase">Prix en baisse</p>
            <p className="text-2xl font-bold text-emerald-400">{stats.priceDown}</p>
          </div>
          {syncStatus && (
            <div className="text-center px-4 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
              <p className="text-xs text-cyan-400 uppercase">Liés épicerie</p>
              <p className="text-2xl font-bold text-cyan-400">{syncStatus.linked_count || 0}</p>
            </div>
          )}
        </div>
      </div>

      {/* Filtres */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-slate-400" />
            <h3 className="text-lg font-semibold text-white">Filtres</h3>
          </div>

          <div className="grid md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Rechercher un ingrédient..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:border-teal-500/50 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              />
            </div>

            <Select
              value={supplierFilter}
              onChange={(e) => setSupplierFilter(e.target.value)}
            >
              <option value="">Tous les fournisseurs</option>
              {suppliers.map(sup => (
                <option key={sup} value={sup}>{sup}</option>
              ))}
            </Select>

            <Select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">Toutes les catégories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </Select>

            <Select
              value={trendFilter}
              onChange={(e) => setTrendFilter(e.target.value)}
            >
              <option value="all">Toutes tendances</option>
              <option value="up">En hausse</option>
              <option value="down">En baisse</option>
              <option value="stable">Stable</option>
            </Select>
          </div>

          <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
            <span className="font-medium text-white">{filteredIngredients.length}</span>
            <span>ingrédient{filteredIngredients.length > 1 ? 's' : ''} trouvé{filteredIngredients.length > 1 ? 's' : ''}</span>
          </div>
        </Card>

      {/* Desktop Table View - Hidden on mobile */}
      <div className="hidden lg:block">
        <Card padding="none">
          <SmartTable
            data={filteredIngredients}
            columns={columns}
            keyField="id"
            loading={ingredientsQuery.isLoading}
            emptyMessage="Aucun ingrédient trouvé"
            sortable={true}
            filterable={false}
            exportable={true}
            paginated={true}
            pageSize={25}
            striped={true}
          />
        </Card>
      </div>

      {/* Mobile/Tablet View - Kitchen optimized */}
      <div className="lg:hidden">
        {/* Loading state - ONLY shown before data loads */}
        {ingredientsQuery.isLoading && (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-teal-500/30 border-t-teal-500 rounded-full animate-spin" />
            <p className="text-slate-400 mt-4">Chargement...</p>
          </div>
        )}

        {/* Empty state - Only shown when not loading and no data */}
        {!ingredientsQuery.isLoading && filteredIngredients.length === 0 && (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">Aucun ingrédient trouvé</p>
          </div>
        )}

        {/* Data view - NO animations once loaded, clean static display */}
        {!ingredientsQuery.isLoading && filteredIngredients.length > 0 && (
          <SwipeableRowProvider>
            <div className="space-y-2">
              {filteredIngredients.map((ingredient) => (
                <MobileIngredientRow
                  key={ingredient.id}
                  ingredient={ingredient}
                  onOpenDetail={handleOpenDetail}
                  onQuickStockUpdate={handleQuickStockOpen}
                  onDelete={handleDeleteWithConfirm}
                  formatCurrency={formatCurrency}
                />
              ))}
            </div>
          </SwipeableRowProvider>
        )}
      </div>

      {/* Modal Détails Ingrédient */}
      <Modal
        open={!!selectedIngredient}
        onClose={handleCloseModal}
        title={isEditing ? `Modifier: ${selectedIngredient?.nom}` : selectedIngredient?.nom || 'Détails ingrédient'}
        size="lg"
      >
        {selectedIngredient && (
          <div className="space-y-6">
            {isEditing ? (
              /* Mode édition */
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-slate-400 uppercase mb-1">Nom</label>
                    <input
                      type="text"
                      value={editForm.nom}
                      onChange={(e) => setEditForm({ ...editForm, nom: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white focus:border-teal-500/50 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 uppercase mb-1">Unité de base</label>
                    <input
                      type="text"
                      value={editForm.unite_base}
                      onChange={(e) => setEditForm({ ...editForm, unite_base: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white focus:border-teal-500/50 focus:outline-none"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-slate-400 uppercase mb-1">Prix unitaire (€)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={editForm.cout_unitaire}
                      onChange={(e) => setEditForm({ ...editForm, cout_unitaire: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white focus:border-teal-500/50 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 uppercase mb-1">Stock actuel</label>
                    <input
                      type="number"
                      step="0.01"
                      value={editForm.stock_actuel}
                      onChange={(e) => setEditForm({ ...editForm, stock_actuel: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white focus:border-teal-500/50 focus:outline-none"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-slate-400 uppercase mb-1">Stock minimum</label>
                    <input
                      type="number"
                      step="0.01"
                      value={editForm.stock_min}
                      onChange={(e) => setEditForm({ ...editForm, stock_min: e.target.value })}
                      placeholder="Optionnel"
                      className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:border-teal-500/50 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 uppercase mb-1">Catégorie</label>
                    <input
                      type="text"
                      value={editForm.categorie}
                      onChange={(e) => setEditForm({ ...editForm, categorie: e.target.value })}
                      placeholder="Ex: Légumes"
                      className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:border-teal-500/50 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 uppercase mb-1">Fournisseur</label>
                    <input
                      type="text"
                      value={editForm.fournisseur}
                      onChange={(e) => setEditForm({ ...editForm, fournisseur: e.target.value })}
                      placeholder="Ex: Metro"
                      className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:border-teal-500/50 focus:outline-none"
                    />
                  </div>
                </div>

                {/* Boutons édition */}
                <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                  <Button
                    variant="ghost"
                    onClick={() => setIsEditing(false)}
                    className="text-slate-400 hover:text-white"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Annuler
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleSave}
                    loading={updateMutation.isPending}
                    className="bg-teal-500 hover:bg-teal-600"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Enregistrer
                  </Button>
                </div>
              </div>
            ) : (
              /* Mode lecture */
              <>
                {/* Infos principales */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase mb-1">
                      <Package className="w-3 h-3" />
                      Catégorie
                    </div>
                    <p className="text-white font-semibold">{selectedIngredient.categorie || 'Non définie'}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase mb-1">
                      <Box className="w-3 h-3" />
                      Fournisseur
                    </div>
                    <p className="text-white font-semibold">{selectedIngredient.fournisseur || 'Non défini'}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase mb-1">
                      <DollarSign className="w-3 h-3" />
                      Prix unitaire
                    </div>
                    <p className="text-white font-semibold">
                      {formatCurrency(selectedIngredient.cout_unitaire)} / {selectedIngredient.unite_base}
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase mb-1">
                      <Box className="w-3 h-3" />
                      Stock actuel
                    </div>
                    <p className="text-white font-semibold">
                      {selectedIngredient.stock_actuel?.toFixed(2) || 0} {selectedIngredient.unite_base}
                    </p>
                    {selectedIngredient.stock_min && (
                      <p className="text-xs text-slate-500 mt-1">
                        Min: {selectedIngredient.stock_min} {selectedIngredient.unite_base}
                      </p>
                    )}
                  </div>
                </div>

                {/* Tendance et évolution prix */}
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-slate-400" />
                      <span className="text-sm font-medium text-white">Évolution du prix (30 derniers jours)</span>
                    </div>
                    {selectedIngredient.price_trend && (
                      <div className="flex items-center gap-2">
                        {selectedIngredient.price_trend === 'up' && (
                          <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            <TrendingUp className="w-3 h-3" />
                            +{selectedIngredient.price_evolution?.toFixed(1) || 0}%
                          </span>
                        )}
                        {selectedIngredient.price_trend === 'down' && (
                          <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            <TrendingDown className="w-3 h-3" />
                            {selectedIngredient.price_evolution?.toFixed(1) || 0}%
                          </span>
                        )}
                        {selectedIngredient.price_trend === 'stable' && (
                          <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-slate-500/20 text-slate-400 border border-slate-500/30">
                            <Minus className="w-3 h-3" />
                            Stable
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  {normalizedHistory.length > 0 ? (
                    <div className="flex justify-center py-4">
                      <Sparkline
                        data={normalizedHistory.map(h => h.prix)}
                        width={400}
                        height={80}
                        trend={selectedIngredient.price_trend === 'up' ? 'up' : selectedIngredient.price_trend === 'down' ? 'down' : 'neutral'}
                      />
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 text-center py-4">Aucun historique de prix disponible</p>
                  )}
                  {normalizedHistory.length > 0 && (
                    <div className="flex justify-between text-xs text-slate-500 mt-2">
                      <span>Il y a 30 jours: {formatCurrency(normalizedHistory[0]?.prix)}</span>
                      <span>Aujourd'hui: {formatCurrency(normalizedHistory[normalizedHistory.length - 1]?.prix)}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                  <Button
                    variant="ghost"
                    onClick={() => setIsEditing(true)}
                    className="text-slate-400 hover:text-white"
                  >
                    <Edit3 className="w-4 h-4 mr-2" />
                    Modifier
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => setShowDeleteConfirm(true)}
                    className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Supprimer
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </Modal>

      {/* Dialogue de confirmation suppression */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Supprimer l'ingrédient"
        description={
          <>
            <p className="mb-3">Êtes-vous sûr de vouloir supprimer "{selectedIngredient?.nom}" ?</p>
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-rose-300">
                  <p className="font-semibold mb-1">Attention</p>
                  <p>Si cet ingrédient est utilisé dans des plats, la suppression échouera. Vous devrez d'abord le retirer de tous les plats concernés.</p>
                </div>
              </div>
            </div>
          </>
        }
        confirmLabel="Supprimer"
        loading={deleteMutation.isPending}
      />

      {/* Quick Stock Update Modal - Kitchen friendly */}
      <Modal
        open={!!quickStockUpdate}
        onClose={() => {
          setQuickStockUpdate(null);
          setQuickStockValue('');
        }}
        title="Mise à jour du stock"
        size="sm"
      >
        {quickStockUpdate && (
          <div className="space-y-6">
            {/* Ingredient info */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-3 mb-2">
                <Package className="w-5 h-5 text-teal-400" />
                <h3 className="text-lg font-bold text-white">{quickStockUpdate.nom}</h3>
              </div>
              <p className="text-sm text-slate-400">
                Stock actuel: <span className="font-semibold text-white">{quickStockUpdate.stock_actuel?.toFixed(1) || 0}</span> {quickStockUpdate.unite_base}
              </p>
            </div>

            {/* Stock input - Large for kitchen use */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Nouveau stock ({quickStockUpdate.unite_base})
              </label>
              <input
                type="number"
                step="0.1"
                value={quickStockValue}
                onChange={(e) => setQuickStockValue(e.target.value)}
                autoFocus
                className="w-full px-4 py-4 text-2xl font-bold text-center rounded-xl border-2 border-teal-500/50 bg-white/5 text-white focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                placeholder="0.0"
              />
            </div>

            {/* Quick buttons */}
            <div className="grid grid-cols-3 gap-2">
              <Button
                variant="outline"
                onClick={() => setQuickStockValue((parseFloat(quickStockValue) || 0) + 1)}
                className="py-3 text-lg font-semibold"
              >
                +1
              </Button>
              <Button
                variant="outline"
                onClick={() => setQuickStockValue((parseFloat(quickStockValue) || 0) + 5)}
                className="py-3 text-lg font-semibold"
              >
                +5
              </Button>
              <Button
                variant="outline"
                onClick={() => setQuickStockValue((parseFloat(quickStockValue) || 0) + 10)}
                className="py-3 text-lg font-semibold"
              >
                +10
              </Button>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 pt-4 border-t border-white/10">
              <Button
                variant="ghost"
                onClick={() => {
                  setQuickStockUpdate(null);
                  setQuickStockValue('');
                }}
                className="flex-1 py-3 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5 mr-2" />
                Annuler
              </Button>
              <Button
                variant="primary"
                onClick={handleQuickStockUpdate}
                loading={updateMutation.isPending}
                className="flex-1 py-3 bg-teal-500 hover:bg-teal-600"
              >
                <Save className="w-5 h-5 mr-2" />
                Enregistrer
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal Création Ingrédient */}
      <AddIngredientModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          ingredientsQuery.refetch();
          setShowCreateModal(false);
        }}
      />

      {/* Drawer aperçu rapide */}
      <IngredientDetailDrawer
        open={!!drawerIngredient}
        onClose={() => setDrawerIngredient(null)}
        ingredient={drawerIngredient}
        onEdit={(ing) => {
          setDrawerIngredient(null);
          handleOpenDetail(ing);
        }}
        onHistory={(ing) => {
          console.log('Historique ingrédient:', ing);
        }}
        onLinkEpicerie={(ing) => {
          navigate('/restaurant/liens');
        }}
        onViewPlat={(plat) => {
          console.log('Voir plat:', plat);
        }}
      />
      </div>
    </PullToRefresh>
  );
}
