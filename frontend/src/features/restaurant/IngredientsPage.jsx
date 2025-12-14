import { useState, useMemo } from 'react';
import { Card, Button, Input, Select, DataTable, Badge } from '@/components/ui';
import { useRestaurantIngredients, useRestaurantIngredientPriceHistory } from '@/hooks/useRestaurant.js';
import { Search, Filter, TrendingUp, TrendingDown, Minus, ChevronRight } from 'lucide-react';
import { Sparkline } from '@/components/ui';

/**
 * IngredientsPage - Liste des ingrédients avec tendances prix
 */
export default function IngredientsPage() {
  const [search, setSearch] = useState('');
  const [supplierFilter, setSupplierFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [trendFilter, setTrendFilter] = useState('all'); // 'all' | 'up' | 'down' | 'stable'

  // Queries
  const ingredientsQuery = useRestaurantIngredients();
  const ingredients = ingredientsQuery.data || [];

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
      // Recherche
      if (search && !ing.nom.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }

      // Fournisseur
      if (supplierFilter && ing.fournisseur !== supplierFilter) {
        return false;
      }

      // Catégorie
      if (categoryFilter && ing.categorie !== categoryFilter) {
        return false;
      }

      // Tendance
      if (trendFilter !== 'all' && ing.price_trend) {
        if (trendFilter === 'up' && ing.price_trend !== 'up') return false;
        if (trendFilter === 'down' && ing.price_trend !== 'down') return false;
        if (trendFilter === 'stable' && ing.price_trend !== 'stable') return false;
      }

      return true;
    });
  }, [ingredients, search, supplierFilter, categoryFilter, trendFilter]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-rose-600" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-emerald-600" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  const getTrendBadge = (trend, evolution) => {
    if (trend === 'up') {
      return <Badge variant="danger">+{evolution?.toFixed(1) || 0}%</Badge>;
    }
    if (trend === 'down') {
      return <Badge variant="success">{evolution?.toFixed(1) || 0}%</Badge>;
    }
    return <Badge variant="default">Stable</Badge>;
  };

  const getStockBadge = (stock, stock_min) => {
    if (!stock_min) return null;
    if (stock <= stock_min) {
      return <Badge variant="danger">Critique</Badge>;
    }
    if (stock <= stock_min * 1.5) {
      return <Badge variant="warning">Bas</Badge>;
    }
    return <Badge variant="success">OK</Badge>;
  };

  const columns = [
    {
      key: 'nom',
      label: 'Ingrédient',
      render: (value, row) => (
        <div>
          <p className="font-semibold text-slate-900">{value}</p>
          <p className="text-xs text-slate-500 uppercase tracking-wider">
            {row.categorie || 'Sans catégorie'} • {row.fournisseur || 'Sans fournisseur'}
          </p>
        </div>
      ),
    },
    {
      key: 'cout_unitaire',
      label: 'Prix unitaire',
      align: 'right',
      render: (value, row) => (
        <div className="text-right">
          <p className="font-semibold text-slate-900">{formatCurrency(value)}</p>
          <p className="text-xs text-slate-500">/ {row.unite_base}</p>
        </div>
      ),
    },
    {
      key: 'stock_actuel',
      label: 'Stock',
      align: 'right',
      render: (value, row) => (
        <div className="text-right">
          <p className="font-semibold text-slate-900">
            {value?.toFixed(2) || 0} {row.unite_base}
          </p>
          {getStockBadge(value, row.stock_min)}
        </div>
      ),
    },
    {
      key: 'price_trend',
      label: 'Tendance',
      align: 'center',
      render: (value, row) => (
        <div className="flex flex-col items-center gap-1">
          {getTrendIcon(value)}
          {getTrendBadge(value, row.price_evolution)}
        </div>
      ),
    },
    {
      key: 'price_history_sparkline',
      label: 'Évolution (30j)',
      align: 'center',
      render: (_, row) => {
        if (!row.price_history || row.price_history.length === 0) {
          return <span className="text-xs text-slate-400">Aucune donnée</span>;
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
      label: '',
      align: 'center',
      render: (_, row) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            // TODO: Ouvrir modal historique prix
            console.log('Historique prix', row);
          }}
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <Card className="bg-gradient-to-br from-teal-500 to-cyan-400 text-white">
        <div className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-white/70">Ingrédients Restaurant</p>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold mb-2">Liste des ingrédients</h1>
              <p className="text-sm text-white/90">
                Suivez les prix, stocks et tendances de vos ingrédients.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-right">
                <p className="text-xs text-white/70">Total ingrédients</p>
                <p className="text-2xl font-bold">{ingredients.length}</p>
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
              placeholder="Rechercher un ingrédient..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              prefix={<Search className="w-4 h-4 text-slate-400" />}
            />

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

          <div className="mt-4 flex items-center gap-2 text-sm text-slate-600">
            <span className="font-medium">{filteredIngredients.length}</span>
            <span>ingrédient{filteredIngredients.length > 1 ? 's' : ''} trouvé{filteredIngredients.length > 1 ? 's' : ''}</span>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <DataTable
          columns={columns}
          data={filteredIngredients}
          isLoading={ingredientsQuery.isLoading}
          emptyMessage="Aucun ingrédient trouvé"
        />
      </Card>
    </div>
  );
}
