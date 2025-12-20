import { useState, useMemo } from 'react';
import Card from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Input from '@/components/ui/Input.jsx';
import Select from '@/components/ui/Select.jsx';
import SmartTable, { columnHelpers } from '@/components/ui/SmartTable.jsx';
import Modal from '@/components/ui/Modal.jsx';
import { useRestaurantPlats, useUpdateRestaurantPlatPrice, useCreateRestaurantPlat } from '@/hooks/useRestaurant.js';
import { PlatDetailModal } from './components';
import { Search, Filter, Eye, Utensils, TrendingUp, ChefHat, Plus, X } from 'lucide-react';
import { TableSkeleton } from '@/components/ui/Skeleton.jsx';
import QueryErrorState from '@/components/feedback/QueryErrorState.jsx';

/**
 * PlatsCatalogPage - Catalogue des plats avec filtres et détails
 * Dark Theme Design System (2025 Next-Gen)
 */
export default function PlatsCatalogPage() {
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [marginFilter, setMarginFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [selectedPlat, setSelectedPlat] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPlat, setNewPlat] = useState({ nom: '', categorie: '', type: 'cuisine', prix_vente_ttc: '', actif: true });

  // Queries
  const platsQuery = useRestaurantPlats();
  const updatePriceMutation = useUpdateRestaurantPlatPrice();
  const createPlatMutation = useCreateRestaurantPlat();

  const plats = platsQuery.data || [];

  // Catégories uniques
  const categories = useMemo(() => {
    const cats = new Set(plats.map(p => p.categorie).filter(Boolean));
    return Array.from(cats);
  }, [plats]);

  // Filtrage
  const filteredPlats = useMemo(() => {
    return plats.filter(plat => {
      if (search && !plat.nom.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      if (categoryFilter && plat.categorie !== categoryFilter) {
        return false;
      }
      if (typeFilter !== 'all' && plat.type !== typeFilter) {
        return false;
      }
      if (marginFilter !== 'all') {
        const marge = plat.marge_pct || 0;
        if (marginFilter === 'good' && marge <= 60) return false;
        if (marginFilter === 'medium' && (marge < 40 || marge > 60)) return false;
        if (marginFilter === 'low' && marge >= 40) return false;
      }
      if (statusFilter !== 'all') {
        if (statusFilter === 'active' && !plat.actif) return false;
        if (statusFilter === 'inactive' && plat.actif) return false;
      }
      return true;
    });
  }, [plats, search, categoryFilter, typeFilter, marginFilter, statusFilter]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value || 0);
  };

  const formatPercent = (value) => `${value?.toFixed(1) || 0}%`;

  // Stats calculées
  const stats = useMemo(() => {
    if (!filteredPlats.length) return { avgMargin: 0, avgFoodCost: 0, activeCount: 0 };
    const avgMargin = filteredPlats.reduce((acc, p) => acc + (p.marge_pct || 0), 0) / filteredPlats.length;
    const avgFoodCost = filteredPlats.reduce((acc, p) => acc + (p.food_cost_pct || 0), 0) / filteredPlats.length;
    const activeCount = filteredPlats.filter(p => p.actif).length;
    return { avgMargin, avgFoodCost, activeCount };
  }, [filteredPlats]);

  const columns = useMemo(() => [
    {
      key: 'nom',
      header: 'Plat',
      render: (value, row) => (
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl border border-white/10 flex items-center justify-center ${
            row.type === 'bar'
              ? 'bg-gradient-to-br from-amber-500/20 to-orange-500/20'
              : 'bg-gradient-to-br from-violet-500/20 to-pink-500/20'
          }`}>
            <ChefHat className={`w-5 h-5 ${row.type === 'bar' ? 'text-amber-400' : 'text-violet-400'}`} />
          </div>
          <div>
            <p className="font-semibold text-white">{value}</p>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                row.type === 'bar'
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-violet-500/20 text-violet-400'
              }`}>
                {row.type === 'bar' ? 'Bar' : 'Cuisine'}
              </span>
              <span className="text-xs text-slate-500">{row.categorie || ''}</span>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'prix_vente_ttc',
      header: 'Prix TTC',
      align: 'right',
      render: (value) => (
        <span className="font-semibold text-white">{formatCurrency(value)}</span>
      ),
    },
    {
      key: 'cout_matiere',
      header: 'Coût matière',
      align: 'right',
      render: (value) => (
        <span className="text-slate-400">{formatCurrency(value)}</span>
      ),
    },
    {
      key: 'marge_pct',
      header: 'Marge',
      align: 'right',
      render: (value) => {
        const color = value > 60 ? 'text-emerald-400' : value >= 40 ? 'text-amber-400' : 'text-rose-400';
        const bgColor = value > 60 ? 'bg-emerald-500/20 border-emerald-500/30' : value >= 40 ? 'bg-amber-500/20 border-amber-500/30' : 'bg-rose-500/20 border-rose-500/30';
        return (
          <div className="flex flex-col items-end gap-1">
            <span className={`font-bold ${color}`}>{formatPercent(value)}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${bgColor} ${color}`}>
              {value > 60 ? 'Excellent' : value >= 40 ? 'Correct' : 'Faible'}
            </span>
          </div>
        );
      },
    },
    {
      key: 'food_cost_pct',
      header: 'Food Cost',
      align: 'right',
      render: (value) => {
        const color = value < 30 ? 'text-emerald-400' : value <= 35 ? 'text-amber-400' : 'text-rose-400';
        const bgColor = value < 30 ? 'bg-emerald-500/20 border-emerald-500/30' : value <= 35 ? 'bg-amber-500/20 border-amber-500/30' : 'bg-rose-500/20 border-rose-500/30';
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${bgColor} ${color}`}>
            {formatPercent(value)}
          </span>
        );
      },
    },
    {
      key: 'actif',
      header: 'Statut',
      align: 'center',
      render: (value) => (
        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
          value
            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
            : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
        }`}>
          {value ? 'Actif' : 'Inactif'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      sortable: false,
      render: (_, row) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSelectedPlat(row)}
        >
          <Eye className="w-4 h-4" />
          Détails
        </Button>
      ),
    },
  ], []);

  const handleUpdatePrice = async (platId, newPrice) => {
    await updatePriceMutation.mutateAsync({
      platId,
      payload: { prix_vente_ttc: newPrice },
    });
  };

  const handleCreatePlat = async (e) => {
    e.preventDefault();
    if (!newPlat.nom.trim()) return;

    try {
      await createPlatMutation.mutateAsync({
        nom: newPlat.nom,
        categorie: newPlat.categorie || null,
        prix_vente_ttc: parseFloat(newPlat.prix_vente_ttc) || 0,
        actif: newPlat.actif,
      });
      setShowCreateModal(false);
      setNewPlat({ nom: '', categorie: '', prix_vente_ttc: '', actif: true });
    } catch (error) {
      console.error('Error creating plat:', error);
    }
  };

  // Erreur
  if (platsQuery.isError && !plats.length) {
    return <QueryErrorState error={platsQuery.error} onRetry={() => platsQuery.refetch()} variant="full" />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-violet-500/20 via-slate-800/50 to-pink-500/10 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <Utensils className="w-6 h-6 text-violet-400" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-400 mb-1">Restaurant</p>
              <h1 className="text-2xl font-bold text-white">Catalogue des plats</h1>
              <p className="text-sm text-slate-400 mt-1">
                Gérez vos plats, analysez les marges et optimisez les prix de vente.
              </p>
            </div>
          </div>

          {/* Stats rapides + Action */}
          <div className="flex items-center gap-4">
            <div className="text-center px-4 py-2 rounded-xl bg-white/5 border border-white/10">
              <p className="text-xs text-slate-500 uppercase">Plats</p>
              <p className="text-2xl font-bold text-white">{filteredPlats.length}</p>
            </div>
            <div className="text-center px-4 py-2 rounded-xl bg-white/5 border border-white/10">
              <p className="text-xs text-slate-500 uppercase">Marge moy.</p>
              <p className={`text-2xl font-bold ${stats.avgMargin > 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {stats.avgMargin.toFixed(1)}%
              </p>
            </div>
            <div className="text-center px-4 py-2 rounded-xl bg-white/5 border border-white/10">
              <p className="text-xs text-slate-500 uppercase">Actifs</p>
              <p className="text-2xl font-bold text-emerald-400">{stats.activeCount}</p>
            </div>
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 text-white font-medium px-6 py-2.5 rounded-xl flex items-center gap-2 border-0"
            >
              <Plus className="w-4 h-4" />
              Nouveau plat
            </Button>
          </div>
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
                placeholder="Rechercher un plat..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
              />
            </div>

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
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="all">Bar & Cuisine</option>
              <option value="bar">🍺 Bar</option>
              <option value="cuisine">🍳 Cuisine</option>
            </Select>

            <Select
              value={marginFilter}
              onChange={(e) => setMarginFilter(e.target.value)}
            >
              <option value="all">Toutes marges</option>
              <option value="good">Excellente (&gt; 60%)</option>
              <option value="medium">Correcte (40-60%)</option>
              <option value="low">Faible (&lt; 40%)</option>
            </Select>

            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">Tous statuts</option>
              <option value="active">Actifs</option>
              <option value="inactive">Inactifs</option>
            </Select>
          </div>

          <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
            <span className="font-medium text-white">{filteredPlats.length}</span>
            <span>plat{filteredPlats.length > 1 ? 's' : ''} trouvé{filteredPlats.length > 1 ? 's' : ''}</span>
          </div>
        </Card>

      {/* Table */}
        <Card padding="none">
          <SmartTable
            data={filteredPlats}
            columns={columns}
            keyField="id"
            loading={platsQuery.isLoading}
            emptyMessage="Aucun plat trouvé"
            sortable={true}
            filterable={false}
            exportable={true}
            paginated={true}
            pageSize={25}
            striped={true}
          />
        </Card>

      {/* Modal détails */}
      <PlatDetailModal
        plat={selectedPlat}
        isOpen={!!selectedPlat}
        onClose={() => setSelectedPlat(null)}
        onUpdatePrice={handleUpdatePrice}
      />

      {/* Modal création */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} size="md">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-violet-500/20 border border-violet-500/30">
                <Plus className="w-5 h-5 text-violet-400" />
              </div>
              <h2 className="text-xl font-bold text-white">Nouveau plat</h2>
            </div>
            <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          <form onSubmit={handleCreatePlat} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Nom du plat <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                value={newPlat.nom}
                onChange={(e) => setNewPlat(prev => ({ ...prev, nom: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
                placeholder="Ex: Burger classique"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Catégorie
              </label>
              <Select
                value={newPlat.categorie}
                onChange={(e) => setNewPlat(prev => ({ ...prev, categorie: e.target.value }))}
              >
                <option value="">Choisir une catégorie</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Type
              </label>
              <Select
                value={newPlat.type}
                onChange={(e) => setNewPlat(prev => ({ ...prev, type: e.target.value }))}
              >
                <option value="cuisine">🍳 Cuisine</option>
                <option value="bar">🍺 Bar</option>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Prix de vente TTC (€)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={newPlat.prix_vente_ttc}
                onChange={(e) => setNewPlat(prev => ({ ...prev, prix_vente_ttc: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
                placeholder="0.00"
              />
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="plat-actif"
                checked={newPlat.actif}
                onChange={(e) => setNewPlat(prev => ({ ...prev, actif: e.target.checked }))}
                className="w-4 h-4 rounded border-white/20 bg-white/5 text-violet-500 focus:ring-violet-500/20"
              />
              <label htmlFor="plat-actif" className="text-sm text-slate-300">
                Plat actif (disponible à la vente)
              </label>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setShowCreateModal(false)}
              >
                Annuler
              </Button>
              <Button
                type="submit"
                disabled={createPlatMutation.isLoading}
                className="bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 text-white"
              >
                {createPlatMutation.isLoading ? 'Création...' : 'Créer le plat'}
              </Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
}
