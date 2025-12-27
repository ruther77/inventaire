/**
 * Page Opérations Épicerie - Vue unifiée multi-onglets.
 *
 * Cette page centralise toutes les opérations liées à l'épicerie dans une interface à onglets.
 * Elle affiche:
 * - Onglet Pilotage: Dashboard avec KPIs, alertes stock, factures et mouvements récents
 * - Onglet Catalogue: Gestion complète du catalogue produits
 * - Onglet Factures: Liste et import des factures fournisseurs
 * - Onglet Prix: Suivi de l'évolution des prix d'achat
 * - Onglet Stock: Mouvements de stock et inventaire
 *
 * Fonctionnalités principales:
 * - Navigation par onglets avec lazy loading pour performance
 * - KPIs temps réel (valeur stock, produits actifs, alertes, factures)
 * - Actions rapides (importer facture, ajouter produit)
 * - Tableau des alertes stock avec accès rapide aux détails produit
 * - Sidebar avec factures récentes et mouvements de stock
 * - Drawer de détail produit avec historique et actions
 * - Mode embedded pour réutiliser les pages dans les onglets
 *
 * @component
 *
 * @example
 * <OperationsPage />
 */

import { useState, useMemo, useCallback, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShoppingCart,
  Plus,
  Upload,
  Package,
  FileText,
  TrendingUp,
  Activity,
  Truck,
  ChevronRight,
} from 'lucide-react';
import { useProducts } from '@/hooks/useProducts.js';
import { useCategories } from '@/hooks/useCategories.js';
import { useDashboardMetrics } from '@/hooks/useDashboard.js';
import { useRecentMovements } from '@/hooks/useStock.js';
import { useInvoiceHistory } from '@/hooks/useInvoiceImport.js';
import Button from '@/components/ui/Button.jsx';
import { InvoiceImportModal, AddProductModal, EditProductModal, ProductDetailDrawer } from '@/components/modals/index.js';
import { toast } from 'sonner';

// Lazy load des onglets
const CatalogPage = lazy(() => import('@/features/catalog/CatalogPage.jsx'));
const InvoicesListPage = lazy(() => import('@/features/invoices/InvoicesListPage.jsx'));
const PricesPage = lazy(() => import('@/features/prices/PricesPage.jsx'));
const StockPage = lazy(() => import('@/features/stock/StockPage.jsx'));

// Tab skeleton
function TabSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-white/5 rounded-xl" />
        ))}
      </div>
      <div className="h-80 bg-white/5 rounded-2xl" />
    </div>
  );
}

// KPI Card
function KPICard({ label, value, trend, trendType, hint, onClick }) {
  return (
    <div
      className="bg-white/5 border border-white/10 rounded-2xl p-6 cursor-pointer transition-all hover:bg-white/10 hover:-translate-y-0.5"
      onClick={onClick}
    >
      <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">{label}</p>
      <p className="text-3xl font-bold font-display text-white mb-2">{value}</p>
      <div className="flex items-center gap-2">
        {trend && (
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              trendType === 'positive'
                ? 'bg-emerald-500/15 text-emerald-400'
                : trendType === 'negative'
                ? 'bg-rose-500/15 text-rose-400'
                : 'bg-slate-500/15 text-slate-400'
            }`}
          >
            {trend}
          </span>
        )}
        {hint && <span className="text-sm text-slate-400">{hint}</span>}
      </div>
    </div>
  );
}

// Tab Button
function TabButton({ active, icon: Icon, label, count, onClick }) {
  return (
    <button
      className={`flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold transition-all ${
        active
          ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/10 text-white border border-emerald-500/30'
          : 'text-slate-400 hover:text-white hover:bg-white/5'
      }`}
      onClick={onClick}
    >
      <Icon className="w-4 h-4" />
      {label}
      {count !== undefined && (
        <span className={`text-xs px-1.5 py-0.5 rounded-full ${active ? 'bg-white/10' : 'bg-white/5'}`}>
          {count}
        </span>
      )}
    </button>
  );
}

// Sidebar Activity Item
function ActivityItem({ icon, iconBg, title, meta, amount, amountColor, onClick }) {
  return (
    <div
      className="p-4 bg-white/5 rounded-xl hover:bg-white/10 cursor-pointer transition-all hover:translate-x-1"
      onClick={onClick}
    >
      <div className="flex items-center gap-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconBg}`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{title}</p>
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-500">{meta}</span>
            {amount && (
              <span className={`text-sm font-semibold ${amountColor || 'text-emerald-400'}`}>
                {amount}
              </span>
            )}
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-500" />
      </div>
    </div>
  );
}

/**
 * Composant Onglet Pilotage - Vue d'ensemble des opérations.
 *
 * Affiche les KPIs principaux, les alertes stock et l'activité récente.
 */
function PilotageTab({ products, metrics, categoriesCount, movements, invoices, onNavigate, onSelectProduct }) {
  // Calculer les alertes stock: produits sous le seuil d'alerte
  const stockAlerts = useMemo(() => {
    return products.filter((p) => (p.stock_actuel || 0) < (p.seuil_alerte || 10));
  }, [products]);

  // Extraire les KPIs depuis metrics.kpis (structure retournée par le backend)
  // Utilise les valeurs par défaut si les données ne sont pas encore chargées
  const kpis = metrics?.kpis || {};
  const displayCategoriesCount = kpis.categories_count > 0 ? kpis.categories_count : categoriesCount;

  return (
    <>
      {/* KPIs Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        <KPICard
          label="Valeur Stock HT"
          value={`€${(kpis.valeur_stock_ht || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`}
          hint={`${(kpis.quantite_stock_total || 0).toLocaleString('fr-FR')} unités`}
          onClick={() => onNavigate('stock')}
        />
        <KPICard
          label="Produits Actifs"
          value={(kpis.total_produits || products.length).toLocaleString()}
          hint={`${displayCategoriesCount || 0} catégories`}
          onClick={() => onNavigate('catalogue')}
        />
        <KPICard
          label="Alertes Stock"
          value={kpis.alerte_stock_bas || stockAlerts.length}
          trend={`${kpis.stock_epuise || 0} épuisés`}
          trendType={kpis.stock_epuise > 0 ? 'negative' : 'neutral'}
          onClick={() => onNavigate('stock')}
        />
        <KPICard
          label="Factures en attente"
          value={kpis.pending_invoices || 0}
          hint={`€${(kpis.pending_amount || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`}
          onClick={() => onNavigate('factures')}
        />
        <KPICard
          label="Prix Moyen Achat"
          value={`€${(kpis.avg_purchase_price || 0).toFixed(2)}`}
          onClick={() => onNavigate('prix')}
        />
        <KPICard
          label="Rotation Stock"
          value={kpis.avg_rotation > 0 ? `${kpis.avg_rotation.toFixed(1)}j` : '—'}
          hint="Moyenne 90 jours"
          onClick={() => onNavigate('stock')}
        />
      </div>

      {/* Main Grid: Catalogue + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Produits en alerte */}
        <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-white">Produits en alerte</h2>
            <Button size="sm" variant="ghost" onClick={() => onNavigate('stock')}>
              Voir tout
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs uppercase text-slate-500 border-b border-white/10">
                  <th className="pb-3 px-3">Produit</th>
                  <th className="pb-3 px-3">Stock</th>
                  <th className="pb-3 px-3">Seuil</th>
                  <th className="pb-3 px-3">Statut</th>
                  <th className="pb-3 px-3"></th>
                </tr>
              </thead>
              <tbody>
                {stockAlerts.slice(0, 6).map((product) => {
                  const isCritical = (product.stock_actuel || 0) === 0;
                  return (
                    <tr
                      key={product.id}
                      className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                      onClick={() => onSelectProduct?.(product)}
                    >
                      <td className="py-3 px-3 font-medium text-white">{product.nom}</td>
                      <td className="py-3 px-3 text-slate-300">
                        {product.stock_actuel || 0} {product.unite || 'u'}
                      </td>
                      <td className="py-3 px-3 text-slate-400">
                        {product.seuil_alerte || 10} {product.unite || 'u'}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
                            isCritical
                              ? 'bg-rose-500/15 text-rose-400'
                              : 'bg-amber-500/15 text-amber-400'
                          }`}
                        >
                          {isCritical ? '🔴 Épuisé' : '⚠️ Bas'}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <button
                          className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectProduct?.(product);
                          }}
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {stockAlerts.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      Aucune alerte stock
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Sidebar */}
        <div className="space-y-6">
          {/* Factures récentes */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <FileText className="w-4 h-4 text-amber-400" />
              Factures récentes
            </h3>
            <div className="space-y-3">
              {(invoices || []).slice(0, 3).map((inv, idx) => (
                <ActivityItem
                  key={idx}
                  icon={<FileText className="w-4 h-4 text-amber-400" />}
                  iconBg="bg-amber-500/20"
                  title={`Facture ${inv.supplier || inv.numero || '#' + (idx + 1)}`}
                  meta={inv.date || 'Récemment'}
                  amount={`€${(inv.total || 0).toLocaleString()}`}
                  onClick={() => onNavigate('factures')}
                />
              ))}
              {(!invoices || invoices.length === 0) && (
                <p className="text-sm text-slate-500 text-center py-4">Aucune facture récente</p>
              )}
            </div>
          </div>

          {/* Mouvements récents */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-teal-400" />
              Mouvements récents
            </h3>
            <div className="space-y-3">
              {(movements || []).slice(0, 3).map((mov, idx) => {
                const isEntree = mov.type_mouvement === 'entree';
                return (
                  <ActivityItem
                    key={idx}
                    icon={
                      isEntree ? (
                        <Package className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Package className="w-4 h-4 text-rose-400" />
                      )
                    }
                    iconBg={isEntree ? 'bg-emerald-500/20' : 'bg-rose-500/20'}
                    title={`${isEntree ? 'Entrée' : 'Sortie'}: ${mov.produit_nom || 'Produit'}`}
                    meta={mov.source || mov.date_mouvement || '—'}
                    amount={`${isEntree ? '+' : '-'}${Math.abs(mov.quantite || 0)} ${mov.unite || 'u'}`}
                    amountColor={isEntree ? 'text-emerald-400' : 'text-rose-400'}
                    onClick={() => onNavigate('stock')}
                  />
                );
              })}
              {(!movements || movements.length === 0) && (
                <p className="text-sm text-slate-500 text-center py-4">Aucun mouvement récent</p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Actions rapides</h3>
            <div className="space-y-2">
              <Button
                variant="primary"
                className="w-full justify-center bg-emerald-500 hover:bg-emerald-600"
                onClick={() => onNavigate('stock')}
              >
                Commander stock bas
              </Button>
              <Button variant="ghost" className="w-full justify-center" onClick={() => onNavigate('factures')}>
                Valider factures
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function OperationsPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('pilotage');
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [addProductModalOpen, setAddProductModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);

  // Data hooks
  const { data: products = [] } = useProducts();
  const { data: categories = [] } = useCategories();
  const { data: metrics } = useDashboardMetrics();
  const { data: movements = [] } = useRecentMovements({ limit: 5 });
  const { data: invoices = [] } = useInvoiceHistory({ limit: 5 });
  const categoriesCount = categories.length;

  // Handlers pour le drawer produit
  const handleSelectProduct = useCallback((product) => {
    setSelectedProduct(product);
    setDrawerOpen(true);
  }, []);

  const handleOrderProduct = useCallback((product) => {
    toast.info(`Commander ${product.nom}`, {
      description: 'Ouverture du formulaire de commande...',
    });
  }, []);

  const handleViewHistory = useCallback((product) => {
    setDrawerOpen(false);
    setActiveTab('prix');
    toast.info(`Historique de ${product.nom}`, {
      description: 'Navigation vers l\'onglet Prix...',
    });
  }, []);

  const handleEditFromDrawer = useCallback((product) => {
    setDrawerOpen(false);
    setSelectedProduct(product);
    setEditModalOpen(true);
  }, []);

  const tabs = [
    { id: 'pilotage', label: 'Pilotage', icon: ShoppingCart },
    { id: 'catalogue', label: 'Catalogue', icon: Package, count: products.length },
    { id: 'factures', label: 'Factures', icon: FileText },
    { id: 'prix', label: 'Suivi Prix', icon: TrendingUp },
    { id: 'stock', label: 'Mouvements', icon: Activity },
  ];

  const handleNavigate = (tab) => {
    setActiveTab(tab);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-4 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-2xl">
            <ShoppingCart className="w-8 h-8 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold font-display text-white">Épicerie</h1>
            <p className="text-slate-400">Catalogue, Stock, Factures & Prix</p>
          </div>
        </div>

        <div className="flex gap-3">
          <Button variant="primary" onClick={() => setImportModalOpen(true)}>
            <Upload className="w-4 h-4" />
            Importer factures
          </Button>
          <Button variant="ghost" onClick={() => setAddProductModalOpen(true)}>
            <Plus className="w-4 h-4" />
            Nouveau produit
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1.5 bg-white/5 rounded-2xl w-fit">
        {tabs.map((tab) => (
          <TabButton
            key={tab.id}
            active={activeTab === tab.id}
            icon={tab.icon}
            label={tab.label}
            count={tab.count}
            onClick={() => setActiveTab(tab.id)}
          />
        ))}
      </div>

      {/* Tab Content */}
      <Suspense fallback={<TabSkeleton />}>
        {activeTab === 'pilotage' && (
          <PilotageTab
            products={products}
            metrics={metrics}
            categoriesCount={categoriesCount}
            movements={movements}
            invoices={invoices}
            onNavigate={handleNavigate}
            onSelectProduct={handleSelectProduct}
          />
        )}
        {activeTab === 'catalogue' && <CatalogPage embedded />}
        {activeTab === 'factures' && <InvoicesListPage embedded />}
        {activeTab === 'prix' && <PricesPage embedded />}
        {activeTab === 'stock' && <StockPage embedded />}
      </Suspense>

      {/* Modals */}
      <InvoiceImportModal
        open={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onSuccess={() => {
          setImportModalOpen(false);
          setActiveTab('factures');
        }}
      />
      <AddProductModal
        open={addProductModalOpen}
        onClose={() => setAddProductModalOpen(false)}
        onSuccess={() => {
          setAddProductModalOpen(false);
          setActiveTab('catalogue');
        }}
      />
      <EditProductModal
        open={editModalOpen}
        onClose={() => {
          setEditModalOpen(false);
          setSelectedProduct(null);
        }}
        product={selectedProduct}
        onSuccess={() => {
          setEditModalOpen(false);
          setSelectedProduct(null);
        }}
      />
      <ProductDetailDrawer
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedProduct(null);
        }}
        product={selectedProduct}
        movements={movements.filter(m => m.produit_id === selectedProduct?.id).slice(0, 5)}
        onEdit={handleEditFromDrawer}
        onHistory={handleViewHistory}
        onOrder={handleOrderProduct}
      />
    </div>
  );
}
