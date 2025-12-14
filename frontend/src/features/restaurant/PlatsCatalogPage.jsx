import { useState, useMemo } from 'react';
import { Card, Button, Input, Select, DataTable, Badge, SectionHeader } from '@/components/ui';
import { useRestaurantPlats, useUpdateRestaurantPlatPrice } from '@/hooks/useRestaurant.js';
import { PlatDetailModal } from './components';
import { Search, Filter, Eye, TrendingUp, TrendingDown, Utensils } from 'lucide-react';

/**
 * PlatsCatalogPage - Catalogue des plats avec filtres et détails
 */
export default function PlatsCatalogPage() {
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [marginFilter, setMarginFilter] = useState('all'); // 'all' | 'good' | 'medium' | 'low'
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'active' | 'inactive'
  const [selectedPlat, setSelectedPlat] = useState(null);

  // Queries
  const platsQuery = useRestaurantPlats();
  const updatePriceMutation = useUpdateRestaurantPlatPrice();

  const plats = platsQuery.data || [];

  // Catégories uniques
  const categories = useMemo(() => {
    const cats = new Set(plats.map(p => p.categorie).filter(Boolean));
    return Array.from(cats);
  }, [plats]);

  // Filtrage
  const filteredPlats = useMemo(() => {
    return plats.filter(plat => {
      // Recherche
      if (search && !plat.nom.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }

      // Catégorie
      if (categoryFilter && plat.categorie !== categoryFilter) {
        return false;
      }

      // Marge
      if (marginFilter !== 'all') {
        const marge = plat.marge_pct || 0;
        if (marginFilter === 'good' && marge <= 60) return false;
        if (marginFilter === 'medium' && (marge < 40 || marge > 60)) return false;
        if (marginFilter === 'low' && marge >= 40) return false;
      }

      // Statut
      if (statusFilter !== 'all') {
        if (statusFilter === 'active' && !plat.actif) return false;
        if (statusFilter === 'inactive' && plat.actif) return false;
      }

      return true;
    });
  }, [plats, search, categoryFilter, marginFilter, statusFilter]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value) => `${value?.toFixed(1) || 0}%`;

  const getMarginBadge = (marge_pct) => {
    if (marge_pct > 60) {
      return <Badge variant="success">Excellent</Badge>;
    }
    if (marge_pct >= 40) {
      return <Badge variant="warning">Correct</Badge>;
    }
    return <Badge variant="danger">Faible</Badge>;
  };

  const getFoodCostBadge = (food_cost_pct) => {
    if (food_cost_pct < 30) {
      return <Badge variant="success">{formatPercent(food_cost_pct)}</Badge>;
    }
    if (food_cost_pct <= 35) {
      return <Badge variant="warning">{formatPercent(food_cost_pct)}</Badge>;
    }
    return <Badge variant="danger">{formatPercent(food_cost_pct)}</Badge>;
  };

  const columns = [
    {
      key: 'nom',
      label: 'Nom du plat',
      render: (value, row) => (
        <div>
          <p className="font-semibold text-slate-900">{value}</p>
          <p className="text-xs text-slate-500 uppercase tracking-wider">{row.categorie || 'Sans catégorie'}</p>
        </div>
      ),
    },
    {
      key: 'prix_vente_ttc',
      label: 'Prix vente TTC',
      align: 'right',
      render: (value) => (
        <span className="font-semibold text-slate-900">{formatCurrency(value)}</span>
      ),
    },
    {
      key: 'cout_matiere',
      label: 'Coût matière',
      align: 'right',
      render: (value) => (
        <span className="text-slate-700">{formatCurrency(value)}</span>
      ),
    },
    {
      key: 'marge_pct',
      label: 'Marge',
      align: 'right',
      render: (value, row) => (
        <div className="flex flex-col items-end gap-1">
          <span className={`font-semibold ${value > 60 ? 'text-emerald-600' : value >= 40 ? 'text-amber-600' : 'text-rose-600'}`}>
            {formatPercent(value)}
          </span>
          {getMarginBadge(value)}
        </div>
      ),
    },
    {
      key: 'food_cost_pct',
      label: 'Food Cost',
      align: 'right',
      render: (value) => getFoodCostBadge(value),
    },
    {
      key: 'actif',
      label: 'Statut',
      align: 'center',
      render: (value) => (
        <Badge variant={value ? 'success' : 'default'}>
          {value ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      align: 'center',
      render: (_, row) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSelectedPlat(row)}
        >
          <Eye className="w-4 h-4 mr-1" />
          Détails
        </Button>
      ),
    },
  ];

  const handleUpdatePrice = async (platId, newPrice) => {
    await updatePriceMutation.mutateAsync({
      platId,
      payload: { prix_vente_ttc: newPrice },
    });
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <Card className="bg-gradient-to-br from-purple-500 to-pink-400 text-white">
        <div className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-white/70">Catalogue Restaurant</p>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold mb-2">Catalogue des plats</h1>
              <p className="text-sm text-white/90">
                Gérez vos plats, analysez les marges et optimisez les prix de vente.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-right">
                <p className="text-xs text-white/70">Total plats</p>
                <p className="text-2xl font-bold">{plats.length}</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Filtres */}
      <Card>
        <div className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-slate-600" />
            <h3 className="text-lg font-semibold text-slate-900">Filtres</h3>
          </div>

          <div className="grid md:grid-cols-4 gap-4">
            <Input
              placeholder="Rechercher un plat..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              prefix={<Search className="w-4 h-4 text-slate-400" />}
            />

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

          <div className="mt-4 flex items-center gap-2 text-sm text-slate-600">
            <span className="font-medium">{filteredPlats.length}</span>
            <span>plat{filteredPlats.length > 1 ? 's' : ''} trouvé{filteredPlats.length > 1 ? 's' : ''}</span>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <DataTable
          columns={columns}
          data={filteredPlats}
          isLoading={platsQuery.isLoading}
          emptyMessage="Aucun plat trouvé"
        />
      </Card>

      {/* Modal détails */}
      <PlatDetailModal
        plat={selectedPlat}
        isOpen={!!selectedPlat}
        onClose={() => setSelectedPlat(null)}
        onUpdatePrice={handleUpdatePrice}
      />
    </div>
  );
}
