import { useState, useCallback, useMemo, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Package, Tag, AlertTriangle, TrendingUp, Calendar, Scan, Eye, Package2, Plus } from 'lucide-react';
import { SmartTable, SmartFilters } from '../../components/smart';
import { useProducts } from '../../hooks/useProducts.js';
import { useUpdateProduct, useDeleteProduct } from '../../hooks/useCatalogMutations.js';
import Button from '../../components/ui/Button.jsx';
import { PullToRefresh } from '../../components/ui/PullToRefresh.jsx';
import { SwipeableRow, SwipeableRowProvider } from '../../components/ui/SwipeableRow.jsx';
import { TableSkeleton } from '../../components/ui/Skeleton.jsx';
import QueryErrorState from '../../components/feedback/QueryErrorState.jsx';
import { AddProductModal, EditProductModal, StockAdjustmentModal, ProductDetailDrawer } from '../../components/modals/index.js';
import { ConfirmDialog } from '../../components/ui/Modal.jsx';

// ============================================================================
// CATALOG SMART DEMO - Démonstration des composants Phase 3
// ============================================================================

/**
 * Carte produit pour affichage mobile.
 *
 * Affiche les informations essentielles d'un produit dans un format compact:
 * - Nom et ID du produit
 * - Statut du stock avec indicateur coloré
 * - Catégorie
 * - Prix d'achat, prix de vente et marge calculée
 *
 * @param {Object} product - Données du produit à afficher
 * @param {Function} onViewDetails - Callback pour voir les détails
 * @param {Function} onScanBarcode - Callback pour scanner le code-barres
 * @param {Function} onQuickStock - Callback pour ajuster le stock rapidement
 */
function ProductCard({ product, onViewDetails, onScanBarcode, onQuickStock }) {
  const stock = product.stock_actuel || 0;
  const threshold = product.seuil_alerte || 8;
  const status = stock === 0 ? 'critical' : stock < threshold ? 'warning' : 'ok';

  const statusColors = {
    critical: 'text-rose-400 bg-rose-500/20',
    warning: 'text-amber-400 bg-amber-500/20',
    ok: 'text-emerald-400 bg-emerald-500/20',
  };

  const achat = product.prix_achat || 0;
  const vente = product.prix_vente || 0;
  const marge = achat === 0 ? null : ((vente - achat) / achat * 100).toFixed(1);
  const margeColor = marge === null ? 'text-slate-500' : parseFloat(marge) >= 30 ? 'text-emerald-400' : parseFloat(marge) >= 15 ? 'text-amber-400' : 'text-rose-400';

  return (
    <div
      className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3"
      onClick={() => onViewDetails(product)}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white truncate">{product.nom}</h3>
          <p className="text-xs text-slate-500">ID #{product.id}</p>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status]} shrink-0 ml-2`}>
          {stock} u
        </span>
      </div>

      {/* Category */}
      <div className="flex items-center gap-2">
        <Tag className="h-4 w-4 text-slate-400" />
        <span className="text-sm text-slate-300">{product.categorie || 'Non classé'}</span>
      </div>

      {/* Price & Margin */}
      <div className="grid grid-cols-3 gap-3 pt-2 border-t border-white/10">
        <div>
          <p className="text-xs text-slate-500">Achat</p>
          <p className="text-sm font-mono text-white">{achat.toFixed(2)} €</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Vente</p>
          <p className="text-sm font-mono font-semibold text-emerald-400">{vente.toFixed(2)} €</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Marge</p>
          <p className={`text-sm font-mono font-semibold ${margeColor}`}>
            {marge === null ? '—' : `${marge}%`}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Page Catalogue Intelligent avec édition inline et filtres avancés.
 *
 * Cette page permet de gérer l'ensemble du catalogue produit de manière interactive.
 * Elle affiche:
 * - Un tableau intelligent avec édition inline des prix et stocks
 * - Des filtres avancés par catégorie, statut stock et marge
 * - Un drawer de détails produit avec historique
 * - Des suggestions IA pour optimiser la gestion
 * - Mode mobile avec cartes swipables et actions rapides
 * - Pull-to-refresh sur mobile
 *
 * Fonctionnalités principales:
 * - Édition directe des prix (achat/vente) et quantités en stock
 * - Mise à jour optimiste pour une réactivité immédiate
 * - Filtrage intelligent avec presets et suggestions
 * - Ajout, modification et suppression de produits
 * - Ajustement rapide du stock via modal
 *
 * @component
 *
 * @param {boolean} [embedded=false] - Si true, masque le header de la page
 *
 * @example
 * <CatalogSmartDemo />
 * <CatalogSmartDemo embedded={true} />
 */
export default function CatalogSmartDemo({ embedded = false }) {
  // ==================== TOUS LES HOOKS EN PREMIER (Rules of Hooks) ====================
  const { data: products = [], isLoading, isError, error, refetch } = useProducts();
  const updateMutation = useUpdateProduct();
  const deleteMutation = useDeleteProduct();
  const queryClient = useQueryClient();

  // Modal states
  const [addProductOpen, setAddProductOpen] = useState(false);
  const [editProductOpen, setEditProductOpen] = useState(false);
  const [stockAdjustOpen, setStockAdjustOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [productToAdjust, setProductToAdjust] = useState(null);
  const [productToDelete, setProductToDelete] = useState(null);

  // États UI
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filterValues, setFilterValues] = useState({});
  const [searchValue, setSearchValue] = useState('');
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' ? window.innerWidth < 768 : false);

  // Détection mobile
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

  // Handler mise à jour inline avec optimistic update
  // Applique immédiatement la modification localement avant la réponse du serveur
  // pour une meilleure expérience utilisateur
  const handleUpdate = useCallback(async (row, field, value) => {
    const parsedValue = Number.isFinite(parseFloat(value)) ? parseFloat(value) : value;
    const previousStates = queryClient.getQueriesData({ queryKey: ['products'] });

    // Optimistic update : appliquer localement la modification avant la confirmation serveur
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
      // Rollback en cas d'erreur: restaure les données précédentes
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

  // Handler changement filtre
  const handleFilterChange = useCallback((key, value) => {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  // Handler reset filtres
  const handleResetFilters = useCallback(() => {
    setFilterValues({});
    setSearchValue('');
  }, []);

  // Handler pour le refresh (pull-to-refresh)
  const handleRefresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ['products'] });
  }, [queryClient]);

  // Handler pour le scan de code-barres
  const handleScanBarcode = useCallback((product) => {
    toast.info(`Scanner pour ${product.nom}`, {
      description: 'Fonctionnalité de scan disponible bientôt',
    });
  }, []);

  // Handler pour afficher les détails du produit
  const handleViewDetails = useCallback((product) => {
    setSelectedProduct(product);
    setDrawerOpen(true);
  }, []);

  // Handler pour l'ajustement rapide du stock
  const handleQuickStock = useCallback((product) => {
    setProductToAdjust(product);
    setStockAdjustOpen(true);
  }, []);

  // Handler pour commander un produit
  const handleOrderProduct = useCallback((product) => {
    toast.info(`Commander ${product.nom}`, {
      description: 'Ouverture du formulaire de commande...',
    });
    // TODO: Open order modal
  }, []);

  // Handler pour voir l'historique d'un produit
  const handleViewHistory = useCallback((product) => {
    toast.info(`Historique de ${product.nom}`, {
      description: 'Ouverture de l\'historique...',
    });
    // TODO: Navigate to product history
  }, []);

  // Handler pour éditer un produit depuis le drawer
  const handleEditFromDrawer = useCallback((product) => {
    setDrawerOpen(false);
    setSelectedProduct(product);
    setEditProductOpen(true);
  }, []);

  // Handler pour supprimer un produit
  const handleDeleteProduct = useCallback((product) => {
    setProductToDelete(product);
    setDeleteConfirmOpen(true);
  }, []);

  // Handler actions ligne (doit être après handleQuickStock et handleDeleteProduct)
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
      case 'stock':
        handleQuickStock(row);
        break;
      case 'delete':
        handleDeleteProduct(row);
        break;
      default:
        break;
    }
  }, [handleQuickStock, handleDeleteProduct]);

  // Confirmer la suppression
  const confirmDelete = useCallback(() => {
    if (productToDelete) {
      deleteMutation.mutate(productToDelete.id);
      setDeleteConfirmOpen(false);
      setProductToDelete(null);
    }
  }, [productToDelete, deleteMutation]);

  // Suggestions de filtres (constante, pas besoin de useMemo)
  const suggestions = [
    { label: 'Ruptures de stock', filters: { status: 'critical' } },
    { label: 'Marges faibles', filters: { marge: 'low' } },
    { label: 'À surveiller', filters: { status: 'warning' } },
  ];

  // Presets de filtres (constante, pas besoin de useMemo)
  const presets = [
    { label: 'Produits critiques', description: 'Ruptures et marges faibles', filters: { status: 'critical', marge: 'low' } },
    { label: 'Top performers', description: 'Stock OK et bonnes marges', filters: { status: 'ok', marge: 'high' } },
  ];

  // ==================== FIN DES HOOKS ====================

  // Affichage du skeleton pendant le chargement initial
  if (isLoading && products.length === 0) {
    return (
      <div className="space-y-6">
        {!embedded && (
          <div>
            <h1 className="text-2xl font-bold text-white">Catalogue Intelligent</h1>
            <p className="text-sm text-slate-400 mt-1">Chargement...</p>
          </div>
        )}
        <TableSkeleton rows={8} columns={5} />
      </div>
    );
  }

  // Affichage de l'erreur
  if (isError && products.length === 0) {
    return <QueryErrorState error={error} onRetry={refetch} variant="full" />;
  }

  // ==================== RENDU PRINCIPAL ====================
  return (
    <PullToRefresh onRefresh={handleRefresh}>
      <div className="space-y-6">
        {/* Header */}
        {!embedded && (
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Catalogue Intelligent</h1>
              <p className="text-sm text-slate-400 mt-1">
                {products.length} produits · Édition inline activée
              </p>
            </div>
            <Button variant="primary" onClick={() => setAddProductOpen(true)}>
              <Plus className="w-4 h-4" />
              Ajouter un produit
            </Button>
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

        {/* Mobile View - Cards with Swipe */}
        {isMobile ? (
          <SwipeableRowProvider>
            <div className="space-y-3">
              {isLoading ? (
                <div className="text-center py-8 text-slate-400">Chargement...</div>
              ) : filteredProducts.length === 0 ? (
                <div className="text-center py-8 text-slate-400">Aucun produit trouvé</div>
              ) : (
                filteredProducts.map((product) => (
                  <SwipeableRow
                    key={product.id}
                    id={`product-${product.id}`}
                    leftActions={[
                      {
                        label: 'Scanner',
                        icon: Scan,
                        variant: 'primary',
                        onAction: () => handleScanBarcode(product),
                      },
                    ]}
                    rightActions={[
                      {
                        label: 'Détails',
                        icon: Eye,
                        variant: 'primary',
                        onAction: () => handleViewDetails(product),
                      },
                      {
                        label: 'Stock',
                        icon: Package2,
                        variant: 'success',
                        onAction: () => handleQuickStock(product),
                      },
                    ]}
                  >
                    <ProductCard
                      product={product}
                      onViewDetails={handleViewDetails}
                      onScanBarcode={handleScanBarcode}
                      onQuickStock={handleQuickStock}
                    />
                  </SwipeableRow>
                ))
              )}
            </div>
          </SwipeableRowProvider>
        ) : (
          /* Desktop View - Smart Table */
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
        )}

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

        {/* Product Detail Drawer */}
        <ProductDetailDrawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          product={selectedProduct}
          movements={[]}
          onEdit={handleEditFromDrawer}
          onHistory={handleViewHistory}
          onOrder={handleOrderProduct}
        />

        {/* Add Product Modal */}
        <AddProductModal
          open={addProductOpen}
          onClose={() => setAddProductOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['products'] });
          }}
        />

        {/* Edit Product Modal */}
        <EditProductModal
          open={editProductOpen}
          onClose={() => {
            setEditProductOpen(false);
            setSelectedProduct(null);
          }}
          product={selectedProduct}
          onSuccess={() => {
            setEditProductOpen(false);
            setSelectedProduct(null);
            queryClient.invalidateQueries({ queryKey: ['products'] });
          }}
        />

        {/* Stock Adjustment Modal */}
        <StockAdjustmentModal
          open={stockAdjustOpen}
          onClose={() => {
            setStockAdjustOpen(false);
            setProductToAdjust(null);
          }}
          product={productToAdjust}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['products'] });
          }}
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          open={deleteConfirmOpen}
          onClose={() => {
            setDeleteConfirmOpen(false);
            setProductToDelete(null);
          }}
          onConfirm={confirmDelete}
          title="Supprimer ce produit ?"
          description={`Êtes-vous sûr de vouloir supprimer "${productToDelete?.nom}" ? Cette action est irréversible.`}
          confirmLabel="Supprimer"
          cancelLabel="Annuler"
          variant="destructive"
          loading={deleteMutation.isPending}
        />
      </div>
    </PullToRefresh>
  );
}
