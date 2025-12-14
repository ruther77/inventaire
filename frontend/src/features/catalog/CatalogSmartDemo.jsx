import { useState, useCallback, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Package, Tag, AlertTriangle, TrendingUp, Calendar } from 'lucide-react';
import { SmartTable, SmartDrawer, SmartFilters, DrawerSection, DrawerField, DrawerActions } from '../../components/smart';
import { useProducts } from '../../hooks/useProducts.js';
import { useUpdateProduct } from '../../hooks/useCatalogMutations.js';
import Button from '../../components/ui/Button.jsx';

// ============================================================================
// CATALOG SMART DEMO - Démonstration des composants Phase 3
// ============================================================================

/**
 * CatalogSmartDemo - Page catalogue avec SmartTable, SmartDrawer et SmartFilters
 *
 * Démontre:
 * - Édition inline des prix et stocks
 * - Drawer de détail produit
 * - Filtres intelligents avec suggestions
 */
export default function CatalogSmartDemo({ embedded = false }) {
  const { data: products = [], isLoading } = useProducts();
  const updateMutation = useUpdateProduct();
  const queryClient = useQueryClient();

  // États
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filterValues, setFilterValues] = useState({});
  const [searchValue, setSearchValue] = useState('');

  // Configuration des colonnes SmartTable
  const columns = useMemo(() => [
    {
      key: 'nom',
      header: 'Produit',
      editable: false,
      render: (value, row) => (
        <div>
          <p className="font-medium text-white">{value}</p>
          <p className="text-xs text-slate-500">ID #{row.id}</p>
        </div>
      ),
    },
    {
      key: 'categorie',
      header: 'Catégorie',
      editable: false,
      render: (value) => (
        <span className="px-2 py-1 text-xs rounded-full bg-slate-700 text-slate-300">
          {value || 'Non classé'}
        </span>
      ),
    },
    {
      key: 'prix_achat',
      header: 'P. Achat',
      align: 'right',
      editable: true,
      inputType: 'number',
      render: (value) => (
        <span className="font-mono">{(value || 0).toFixed(2)} €</span>
      ),
    },
    {
      key: 'prix_vente',
      header: 'P. Vente',
      align: 'right',
      editable: true,
      inputType: 'number',
      render: (value) => (
        <span className="font-mono font-semibold text-emerald-400">
          {(value || 0).toFixed(2)} €
        </span>
      ),
    },
    {
      key: 'stock_actuel',
      header: 'Stock',
      align: 'right',
      editable: true,
      inputType: 'number',
      render: (value, row) => {
        const threshold = row.seuil_alerte || 8;
        const stock = value || 0;
        const status = stock === 0 ? 'critical' : stock < threshold ? 'warning' : 'ok';
        const colors = {
          critical: 'text-rose-400 bg-rose-500/20',
          warning: 'text-amber-400 bg-amber-500/20',
          ok: 'text-emerald-400 bg-emerald-500/20',
        };
        return (
          <span className={`px-2 py-1 rounded-full text-sm font-medium ${colors[status]}`}>
            {stock} u
          </span>
        );
      },
    },
    {
      key: 'marge',
      header: 'Marge',
      align: 'right',
      editable: false,
      getValue: (row) => {
        const achat = row.prix_achat || 0;
        const vente = row.prix_vente || 0;
        if (achat === 0) return null;
        return ((vente - achat) / achat * 100).toFixed(1);
      },
      render: (value) => {
        if (value === null) return <span className="text-slate-500">—</span>;
        const num = parseFloat(value);
        const color = num >= 30 ? 'text-emerald-400' : num >= 15 ? 'text-amber-400' : 'text-rose-400';
        return <span className={`font-mono ${color}`}>{value}%</span>;
      },
    },
  ], []);

  // Configuration des filtres
  const filters = useMemo(() => {
    const categories = [...new Set(products.map((p) => p.categorie).filter(Boolean))];
    return [
      {
        key: 'categorie',
        label: 'Catégorie',
        type: 'select',
        icon: Tag,
        options: categories.map((c) => ({ value: c, label: c })),
      },
      {
        key: 'status',
        label: 'Statut stock',
        type: 'select',
        icon: AlertTriangle,
        options: [
          { value: 'critical', label: 'Critique (rupture)' },
          { value: 'warning', label: 'Attention' },
          { value: 'ok', label: 'OK' },
        ],
      },
      {
        key: 'marge',
        label: 'Marge',
        type: 'select',
        icon: TrendingUp,
        options: [
          { value: 'low', label: '< 15%' },
          { value: 'medium', label: '15-30%' },
          { value: 'high', label: '> 30%' },
        ],
      },
    ];
  }, [products]);

  // Suggestions de filtres
  const suggestions = [
    {
      label: 'Ruptures de stock',
      filters: { status: 'critical' },
    },
    {
      label: 'Marges faibles',
      filters: { marge: 'low' },
    },
    {
      label: 'À surveiller',
      filters: { status: 'warning' },
    },
  ];

  // Presets de filtres
  const presets = [
    {
      label: 'Produits critiques',
      description: 'Ruptures et marges faibles',
      filters: { status: 'critical', marge: 'low' },
    },
    {
      label: 'Top performers',
      description: 'Stock OK et bonnes marges',
      filters: { status: 'ok', marge: 'high' },
    },
  ];

  // Filtrage des données
  const filteredProducts = useMemo(() => {
    let result = products;

    // Recherche
    if (searchValue) {
      const search = searchValue.toLowerCase();
      result = result.filter((p) =>
        p.nom?.toLowerCase().includes(search) ||
        p.categorie?.toLowerCase().includes(search)
      );
    }

    // Catégorie
    if (filterValues.categorie) {
      result = result.filter((p) => p.categorie === filterValues.categorie);
    }

    // Status stock
    if (filterValues.status) {
      result = result.filter((p) => {
        const stock = p.stock_actuel || 0;
        const threshold = p.seuil_alerte || 8;
        const status = stock === 0 ? 'critical' : stock < threshold ? 'warning' : 'ok';
        return status === filterValues.status;
      });
    }

    // Marge
    if (filterValues.marge) {
      result = result.filter((p) => {
        const achat = p.prix_achat || 0;
        const vente = p.prix_vente || 0;
        if (achat === 0) return false;
        const marge = ((vente - achat) / achat * 100);
        switch (filterValues.marge) {
          case 'low': return marge < 15;
          case 'medium': return marge >= 15 && marge <= 30;
          case 'high': return marge > 30;
          default: return true;
        }
      });
    }

    return result;
  }, [products, searchValue, filterValues]);

  const aiSuggestions = useMemo(() => {
    const lowStock = filteredProducts
      .filter((p) => (p.stock_actuel || 0) < (p.seuil_alerte || 8))
      .slice(0, 2)
      .map((p) => ({
        type: 'stock',
        title: `${p.nom} bientôt en rupture`,
        action: 'Commander',
      }));

    const priceUnknown = filteredProducts
      .filter((p) => !p.prix_achat)
      .slice(0, 1)
      .map((p) => ({
        type: 'price',
        title: `${p.nom}: prix achat manquant`,
        action: 'Compléter',
      }));

    return [...lowStock, ...priceUnknown];
  }, [filteredProducts]);

  // Handler mise à jour inline
  const handleUpdate = useCallback(async (row, field, value) => {
    const parsedValue = Number.isFinite(parseFloat(value)) ? parseFloat(value) : value;
    const previousStates = queryClient.getQueriesData({ queryKey: ['products'] });

    // Optimistic update : appliquer localement la modification
    previousStates.forEach(([queryKey, oldData]) => {
      if (!oldData) return;
      queryClient.setQueryData(queryKey, (current) => {
        if (!current) return current;
        // Support tableau brut ou objet { items }
        if (Array.isArray(current)) {
          return current.map((product) =>
            product.id === row.id ? { ...product, [field]: parsedValue } : product
          );
        }
        if (Array.isArray(current.items)) {
          return {
            ...current,
            items: current.items.map((product) =>
              product.id === row.id ? { ...product, [field]: parsedValue } : product
            ),
          };
        }
        return current;
      });
    });

    try {
      await updateMutation.mutateAsync({
        productId: row.id,
        payload: { [field]: parsedValue },
      });
    } catch (err) {
      // Rollback
      previousStates.forEach(([queryKey, oldData]) => {
        queryClient.setQueryData(queryKey, oldData);
      });
      toast.error('Mise à jour impossible');
      throw err;
    }
  }, [queryClient, updateMutation]);

  // Handler clic sur ligne
  const handleRowClick = useCallback((row) => {
    setSelectedProduct(row);
    setDrawerOpen(true);
  }, []);

  // Handler actions ligne
  const handleRowAction = useCallback((action, row) => {
    switch (action) {
      case 'view':
        setSelectedProduct(row);
        setDrawerOpen(true);
        break;
      case 'edit':
        setSelectedProduct(row);
        setDrawerOpen(true);
        break;
      case 'delete':
        if (window.confirm(`Supprimer "${row.nom}" ?`)) {
          // deleteMutation.mutate(row.id);
        }
        break;
      default:
        break;
    }
  }, []);

  // Handler changement filtre
  const handleFilterChange = useCallback((key, value) => {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  // Handler reset filtres
  const handleResetFilters = useCallback(() => {
    setFilterValues({});
    setSearchValue('');
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      {!embedded && (
        <div>
          <h1 className="text-2xl font-bold text-white">Catalogue Intelligent</h1>
          <p className="text-sm text-slate-400 mt-1">
            Démonstration Phase 3 - SmartTable avec édition inline
          </p>
        </div>
      )}

      {/* Smart Filters */}
      <SmartFilters
        filters={filters}
        values={filterValues}
        onChange={handleFilterChange}
        onReset={handleResetFilters}
        suggestions={suggestions}
        presets={presets}
        searchable
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        searchPlaceholder="Rechercher un produit..."
      />

      {/* Smart Table */}
      <SmartTable
        data={filteredProducts}
        columns={columns}
        loading={isLoading}
        onUpdate={handleUpdate}
        onRowClick={handleRowClick}
        onRowAction={handleRowAction}
        getRowId={(row) => row.id}
        emptyMessage="Aucun produit trouvé"
        pagination
        pageSize={15}
        sortable
        striped
      />

      {/* Suggestions IA inline */}
      {aiSuggestions.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-sm font-semibold text-white mb-3">Suggestions IA</p>
          <div className="space-y-2">
            {aiSuggestions.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-3 py-2"
              >
                <span className="text-sm text-slate-200">{item.title}</span>
                <Button size="sm" variant="brand">
                  {item.action}
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Smart Drawer */}
      <SmartDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title={selectedProduct?.nom || 'Détail produit'}
        subtitle={selectedProduct?.categorie || 'Sans catégorie'}
        size="lg"
        expandable
        footer={
          <DrawerActions align="between">
            <Button variant="ghost" onClick={() => setDrawerOpen(false)}>
              Fermer
            </Button>
            <div className="flex gap-2">
              <Button variant="outline">Modifier</Button>
              <Button variant="brand">Commander</Button>
            </div>
          </DrawerActions>
        }
      >
        {selectedProduct && (
          <div className="space-y-6">
            <DrawerSection title="Informations générales">
              <div className="grid grid-cols-2 gap-4">
                <DrawerField label="ID" value={`#${selectedProduct.id}`} copyable />
                <DrawerField label="Nom" value={selectedProduct.nom} />
                <DrawerField label="Catégorie" value={selectedProduct.categorie || 'Non classé'} />
                <DrawerField label="Codes-barres" value={selectedProduct.codes?.join(', ') || '—'} copyable />
              </div>
            </DrawerSection>

            <DrawerSection title="Prix & Marges">
              <div className="grid grid-cols-3 gap-4">
                <DrawerField
                  label="Prix d'achat"
                  value={`${(selectedProduct.prix_achat || 0).toFixed(2)} €`}
                  icon={Package}
                />
                <DrawerField
                  label="Prix de vente"
                  value={`${(selectedProduct.prix_vente || 0).toFixed(2)} €`}
                  icon={Tag}
                />
                <DrawerField
                  label="Marge"
                  value={(() => {
                    const achat = selectedProduct.prix_achat || 0;
                    const vente = selectedProduct.prix_vente || 0;
                    if (achat === 0) return '—';
                    return `${((vente - achat) / achat * 100).toFixed(1)}%`;
                  })()}
                  icon={TrendingUp}
                />
              </div>
            </DrawerSection>

            <DrawerSection title="Stock" collapsible>
              <div className="grid grid-cols-2 gap-4">
                <DrawerField label="Stock actuel" value={`${selectedProduct.stock_actuel || 0} unités`} />
                <DrawerField label="Seuil d'alerte" value={`${selectedProduct.seuil_alerte || 0} unités`} />
              </div>
              <div className="mt-4 p-4 rounded-lg bg-white/5 border border-white/10">
                <p className="text-sm text-slate-400">
                  {selectedProduct.stock_actuel === 0
                    ? '🔴 Rupture de stock - Commander immédiatement'
                    : selectedProduct.stock_actuel < (selectedProduct.seuil_alerte || 8)
                      ? '🟡 Stock faible - À surveiller'
                      : '🟢 Stock suffisant'}
                </p>
              </div>
            </DrawerSection>
          </div>
        )}
      </SmartDrawer>
    </div>
  );
}
