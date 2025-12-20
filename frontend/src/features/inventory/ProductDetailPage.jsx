/**
 * ProductDetailPage - Fiche produit detaillee (S2 - Alerte Stock)
 *
 * Affiche:
 * - Informations produit completes
 * - Timeline des evenements (mouvements, prix, commandes)
 * - Graphiques stock et prix
 * - Suggestions EOQ et fournisseurs
 * - Actions rapides (commander, ajuster stock)
 */

import { useState, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Package,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Clock,
  ShoppingCart,
  Edit3,
  BarChart3,
  History,
  Truck,
  FileText,
  DollarSign,
  Calendar,
  Info,
  CheckCircle,
  XCircle,
  ScanBarcode,
} from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Skeleton from '../../components/ui/Skeleton.jsx';
import BarcodeScannerModal from '../../components/ui/BarcodeScannerModal.jsx';
import PurchaseOrderModal from './PurchaseOrderModal.jsx';
import { staggerContainer, staggerItem } from '../../ui/motion.js';
import api from '../../api/client.js';

// ===========================================================================
// API Functions
// ===========================================================================

const fetchProductDetail = async (productId) => {
  const { data } = await api.get(`/catalog/products/${productId}`);
  return data;
};

const fetchProductMovements = async (productId, limit = 20) => {
  const { data } = await api.get(`/stock/movements`, {
    params: { product_id: productId, limit },
  });
  return data;
};

const fetchProductPriceHistory = async (productId) => {
  const { data } = await api.get(`/prices/history/${productId}`);
  return data;
};

const fetchProductEOQ = async (productId) => {
  try {
    const { data } = await api.get(`/inventory-intelligence/eoq/${productId}`);
    return data;
  } catch {
    return null;
  }
};

const fetchProductSuppliers = async (productId) => {
  try {
    const { data } = await api.get(`/catalog/products/${productId}/suppliers`);
    return data;
  } catch {
    return [];
  }
};

// ===========================================================================
// Sub-components
// ===========================================================================

function StockStatusBadge({ stock, threshold }) {
  const status = stock === 0 ? 'critical' : stock < threshold ? 'warning' : 'ok';
  const config = {
    critical: {
      bg: 'bg-rose-500/20',
      text: 'text-rose-400',
      border: 'border-rose-500/30',
      label: 'Rupture',
      icon: XCircle,
    },
    warning: {
      bg: 'bg-amber-500/20',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      label: 'Stock bas',
      icon: AlertTriangle,
    },
    ok: {
      bg: 'bg-emerald-500/20',
      text: 'text-emerald-400',
      border: 'border-emerald-500/30',
      label: 'OK',
      icon: CheckCircle,
    },
  };
  const Icon = config[status].icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${config[status].bg} ${config[status].text} ${config[status].border}`}
    >
      <Icon className="w-4 h-4" />
      {config[status].label}
    </span>
  );
}

function KPICard({ icon: Icon, label, value, subvalue, trend, accent = 'text-white' }) {
  return (
    <motion.div
      className="rounded-2xl border border-white/10 bg-white/5 p-4"
      variants={staggerItem}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider mb-2">
        <Icon className="w-4 h-4" />
        {label}
      </div>
      <p className={`text-2xl font-semibold ${accent}`}>{value}</p>
      {subvalue && <p className="text-xs text-slate-500 mt-1">{subvalue}</p>}
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-sm ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
          {trend >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          {trend >= 0 ? '+' : ''}{trend.toFixed(1)}%
        </div>
      )}
    </motion.div>
  );
}

function TimelineEvent({ event, isLast }) {
  const typeConfig = {
    ENTREE: { icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
    SORTIE: { icon: TrendingDown, color: 'text-rose-400', bg: 'bg-rose-500/20' },
    INVENTAIRE: { icon: BarChart3, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    TRANSFERT: { icon: Truck, color: 'text-amber-400', bg: 'bg-amber-500/20' },
    PRIX: { icon: DollarSign, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    COMMANDE: { icon: ShoppingCart, color: 'text-cyan-400', bg: 'bg-cyan-500/20' },
  };

  const config = typeConfig[event.type] || typeConfig.ENTREE;
  const Icon = config.icon;

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex gap-4">
      {/* Timeline line */}
      <div className="flex flex-col items-center">
        <div className={`w-10 h-10 rounded-full ${config.bg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
        {!isLast && <div className="w-0.5 h-full bg-white/10 my-2" />}
      </div>

      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-medium text-white">{event.type}</p>
            <p className="text-sm text-slate-400">{event.source || 'Systeme'}</p>
          </div>
          <div className="text-right">
            <p className={`font-semibold ${event.quantite > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {event.quantite > 0 ? '+' : ''}{event.quantite} u
            </p>
            <p className="text-xs text-slate-500">{formatDate(event.date_mvt || event.created_at)}</p>
          </div>
        </div>
        {event.ref_doc && (
          <p className="text-xs text-slate-500 mt-1">Ref: {event.ref_doc}</p>
        )}
      </div>
    </div>
  );
}

function EOQSuggestionCard({ eoq, product, onCreateOrder }) {
  if (!eoq) return null;

  return (
    <Card className="border-cyan-500/30 bg-cyan-500/10">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-xl bg-cyan-500/20">
          <ShoppingCart className="w-6 h-6 text-cyan-400" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-white">Recommandation EOQ</h3>
          <p className="text-sm text-slate-400 mt-1">
            Quantite economique optimale calculee
          </p>

          <div className="grid grid-cols-3 gap-4 mt-4">
            <div>
              <p className="text-xs text-slate-500 uppercase">Quantite</p>
              <p className="text-lg font-semibold text-cyan-400">{eoq.optimal_quantity || 50} u</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase">Frequence</p>
              <p className="text-lg font-semibold text-white">{eoq.order_frequency || 'Mensuel'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase">Cout estime</p>
              <p className="text-lg font-semibold text-white">{(eoq.estimated_cost || 150).toFixed(2)} EUR</p>
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button variant="primary" size="sm" onClick={() => onCreateOrder(eoq)}>
              <ShoppingCart className="w-4 h-4" />
              Creer commande
            </Button>
            <Button variant="ghost" size="sm">
              <Info className="w-4 h-4" />
              Details calcul
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

function SupplierCard({ supplier, isRecommended }) {
  return (
    <motion.div
      className={`rounded-xl border p-4 ${
        isRecommended
          ? 'border-emerald-500/30 bg-emerald-500/10'
          : 'border-white/10 bg-white/5'
      }`}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium text-white">{supplier.name}</p>
            {isRecommended && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/20 text-emerald-400">
                Recommande
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Score: <span className="font-semibold text-white">{supplier.score || 8.5}/10</span>
          </p>
        </div>
        <div className="text-right">
          <p className="text-lg font-semibold text-white">{(supplier.price || 12.50).toFixed(2)} EUR</p>
          <p className="text-xs text-slate-500">par unite</p>
        </div>
      </div>

      <div className="flex gap-4 mt-3 text-xs text-slate-500">
        <span>Delai: {supplier.delivery_days || 3}j</span>
        <span>Min: {supplier.min_order || 10} u</span>
      </div>
    </motion.div>
  );
}

// ===========================================================================
// Main Component
// ===========================================================================

export default function ProductDetailPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [showBarcodeScanner, setShowBarcodeScanner] = useState(false);
  const [showPurchaseOrderModal, setShowPurchaseOrderModal] = useState(false);

  // Queries
  const productQuery = useQuery({
    queryKey: ['product', productId],
    queryFn: () => fetchProductDetail(productId),
    enabled: !!productId,
  });

  const movementsQuery = useQuery({
    queryKey: ['product-movements', productId],
    queryFn: () => fetchProductMovements(productId),
    enabled: !!productId,
  });

  const priceHistoryQuery = useQuery({
    queryKey: ['product-price-history', productId],
    queryFn: () => fetchProductPriceHistory(productId),
    enabled: !!productId,
  });

  const eoqQuery = useQuery({
    queryKey: ['product-eoq', productId],
    queryFn: () => fetchProductEOQ(productId),
    enabled: !!productId,
  });

  const suppliersQuery = useQuery({
    queryKey: ['product-suppliers', productId],
    queryFn: () => fetchProductSuppliers(productId),
    enabled: !!productId,
  });

  const product = productQuery.data;
  const movements = movementsQuery.data || [];
  const priceHistory = priceHistoryQuery.data || [];
  const eoq = eoqQuery.data;
  const suppliers = suppliersQuery.data || [];

  const isLoading = productQuery.isLoading;

  // Calculate consumption stats
  const consumptionStats = useMemo(() => {
    if (!movements.length) return { daily: 0, runway: null };

    const exits = movements.filter(m => m.type === 'SORTIE');
    const totalExit = exits.reduce((sum, m) => sum + Math.abs(m.quantite || 0), 0);
    const daily = exits.length > 0 ? totalExit / 30 : 0;
    const runway = product?.stock_actuel && daily > 0
      ? Math.floor(product.stock_actuel / daily)
      : null;

    return { daily, runway };
  }, [movements, product]);

  // Handlers
  const handleCreateOrder = () => {
    setShowPurchaseOrderModal(true);
  };

  const handleEditStock = () => {
    // Navigate to stock adjustment
    navigate(`/operations/stock/adjust/${productId}`);
  };

  const handleBarcodeScanned = async (code, format) => {
    try {
      // Search for product by barcode
      const { data } = await api.get(`/catalog/products/search`, {
        params: { barcode: code },
      });

      if (data && data.id) {
        // Navigate to the scanned product's detail page
        navigate(`/inventory/products/${data.id}`);
      } else {
        console.warn('Product not found for barcode:', code);
        // You could show a toast notification here
      }
    } catch (err) {
      console.error('Error searching product by barcode:', err);
    }
  };

  if (!product && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Package className="w-16 h-16 text-slate-600 mb-4" />
        <h2 className="text-xl font-semibold text-white">Produit non trouve</h2>
        <p className="text-slate-400 mt-2">Le produit demande n'existe pas ou a ete supprime.</p>
        <Button variant="ghost" className="mt-4" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-4 h-4" />
          Retour
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold text-white">{product.nom}</h1>
              <StockStatusBadge stock={product.stock_actuel || 0} threshold={product.seuil_alerte || 10} />
            </div>
            <p className="text-slate-400 mt-1">
              {product.categorie || 'Non classe'} - ID #{product.id}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => setShowBarcodeScanner(true)}>
            <ScanBarcode className="w-4 h-4" />
            Scanner
          </Button>
          <Button variant="ghost" size="sm" onClick={handleEditStock}>
            <Edit3 className="w-4 h-4" />
            Ajuster stock
          </Button>
          <Button variant="primary" size="sm" onClick={() => handleCreateOrder(eoq || {})}>
            <ShoppingCart className="w-4 h-4" />
            Commander
          </Button>
        </div>
      </header>

      {/* Barcode Scanner Modal */}
      <BarcodeScannerModal
        isOpen={showBarcodeScanner}
        onClose={() => setShowBarcodeScanner(false)}
        onConfirm={handleBarcodeScanned}
        title="Scanner un produit"
        subtitle="Scannez le code-barres pour rechercher un produit"
        continuous={false}
        autoConfirm={true}
        autoConfirmDelay={1500}
      />

      {/* Purchase Order Modal */}
      <PurchaseOrderModal
        isOpen={showPurchaseOrderModal}
        onClose={() => setShowPurchaseOrderModal(false)}
        product={product}
        eoqSuggestion={eoq}
        preselectedSupplier={suppliers[0]}
      />

      {/* KPIs */}
      <motion.div
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <KPICard
          icon={Package}
          label="Stock actuel"
          value={`${product.stock_actuel || 0} u`}
          subvalue={`Seuil: ${product.seuil_alerte || 10} u`}
          accent={product.stock_actuel < (product.seuil_alerte || 10) ? 'text-amber-400' : 'text-emerald-400'}
        />
        <KPICard
          icon={TrendingDown}
          label="Conso. moyenne"
          value={`${consumptionStats.daily.toFixed(1)} u/j`}
          subvalue={consumptionStats.runway ? `${consumptionStats.runway} jours restants` : 'N/A'}
        />
        <KPICard
          icon={DollarSign}
          label="Prix d'achat"
          value={`${(product.prix_achat || 0).toFixed(2)} EUR`}
          subvalue={`Vente: ${(product.prix_vente || 0).toFixed(2)} EUR`}
        />
        <KPICard
          icon={BarChart3}
          label="Marge"
          value={product.prix_vente && product.prix_achat
            ? `${(((product.prix_vente - product.prix_achat) / product.prix_vente) * 100).toFixed(1)}%`
            : 'N/A'}
          subvalue="Marge brute"
          accent="text-cyan-400"
        />
      </motion.div>

      {/* Alert si stock critique */}
      {product.stock_actuel < (product.seuil_alerte || 10) && (
        <Card className="border-amber-500/30 bg-amber-500/10">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-amber-500/20">
              <AlertTriangle className="w-6 h-6 text-amber-400" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-amber-400">Stock critique</h3>
              <p className="text-sm text-slate-400">
                {consumptionStats.runway
                  ? `Rupture estimee dans ${consumptionStats.runway} jours au rythme actuel.`
                  : 'Stock sous le seuil d\'alerte. Commande recommandee.'}
              </p>
            </div>
            <Button variant="primary" size="sm" onClick={() => handleCreateOrder(eoq || {})}>
              Commander maintenant
            </Button>
          </div>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex gap-2 bg-white/5 p-1 rounded-xl w-fit">
        {[
          { id: 'overview', label: 'Vue generale', icon: Info },
          { id: 'timeline', label: 'Historique', icon: History },
          { id: 'suppliers', label: 'Fournisseurs', icon: Truck },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="relative px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            {activeTab === tab.id && (
              <motion.span
                layoutId="product-tab"
                className="absolute inset-0 bg-white/10 rounded-lg"
                transition={{ type: 'spring', stiffness: 500, damping: 35 }}
              />
            )}
            <tab.icon className={`relative z-10 w-4 h-4 ${activeTab === tab.id ? 'text-white' : 'text-slate-400'}`} />
            <span className={`relative z-10 ${activeTab === tab.id ? 'text-white' : 'text-slate-400'}`}>
              {tab.label}
            </span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Informations produit */}
            <Card>
              <h3 className="font-semibold text-white mb-4">Informations produit</h3>
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-white/10">
                  <span className="text-slate-400">Code-barres</span>
                  <span className="font-mono text-white">{product.barcode || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/10">
                  <span className="text-slate-400">Categorie</span>
                  <span className="text-white">{product.categorie || 'Non classe'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/10">
                  <span className="text-slate-400">TVA</span>
                  <span className="text-white">{product.tva || 20}%</span>
                </div>
                <div className="flex justify-between py-2 border-b border-white/10">
                  <span className="text-slate-400">Unite</span>
                  <span className="text-white">{product.unite || 'unite'}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-slate-400">Derniere MAJ</span>
                  <span className="text-white">
                    {product.updated_at
                      ? new Date(product.updated_at).toLocaleDateString('fr-FR')
                      : '-'}
                  </span>
                </div>
              </div>
            </Card>

            {/* EOQ Suggestion */}
            <EOQSuggestionCard
              eoq={eoq}
              product={product}
              onCreateOrder={handleCreateOrder}
            />
          </motion.div>
        )}

        {activeTab === 'timeline' && (
          <motion.div
            key="timeline"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card>
              <h3 className="font-semibold text-white mb-6">Historique des mouvements</h3>
              {movements.length > 0 ? (
                <div className="space-y-0">
                  {movements.map((event, idx) => (
                    <TimelineEvent
                      key={event.id || idx}
                      event={event}
                      isLast={idx === movements.length - 1}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun mouvement enregistre</p>
                </div>
              )}
            </Card>
          </motion.div>
        )}

        {activeTab === 'suppliers' && (
          <motion.div
            key="suppliers"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <Card>
              <h3 className="font-semibold text-white mb-4">Fournisseurs disponibles</h3>
              {suppliers.length > 0 ? (
                <div className="space-y-3">
                  {suppliers.map((supplier, idx) => (
                    <SupplierCard
                      key={supplier.id || idx}
                      supplier={supplier}
                      isRecommended={idx === 0}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <Truck className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun fournisseur reference pour ce produit</p>
                  <Button variant="ghost" size="sm" className="mt-4">
                    Ajouter un fournisseur
                  </Button>
                </div>
              )}
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
