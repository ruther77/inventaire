/**
 * Page Gestion du Stock.
 *
 * Cette page permet de gérer et surveiller l'état du stock en temps réel.
 * Elle affiche:
 * - Une vue d'ensemble avec la valeur totale du stock et les références actives
 * - Des alertes pour les produits en rupture ou stock bas
 * - Un tableau des produits avec filtrage par onglets (tous, rupture, stock bas, surstock)
 * - Les mouvements de stock récents
 * - Export CSV du stock complet
 *
 * Fonctionnalités principales:
 * - Visualisation des niveaux de stock avec indicateurs colorés
 * - Alertes automatiques pour les seuils critiques
 * - Ajustement rapide du stock via modal
 * - Filtrage intelligent par statut (rupture, bas, surstock)
 * - Export des données pour analyse externe
 *
 * @component
 *
 * @param {boolean} [embedded=false] - Si true, masque le header de la page
 *
 * @example
 * <StockPage />
 * <StockPage embedded={true} />
 */

import { useState, useMemo, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Package,
  Download,
  AlertTriangle,
  RotateCcw,
  ArrowDownCircle,
  ArrowUpCircle,
  RefreshCw,
} from 'lucide-react';
import { useProducts } from '@/hooks/useProducts.js';
import { useRecentMovements } from '@/hooks/useStock.js';
import Button from '@/components/ui/Button.jsx';
import { StockAdjustmentModal } from '@/components/modals/index.js';
import { toast } from 'sonner';

// Helper pour télécharger CSV
const downloadCSV = (data, filename) => {
  const headers = ['ID', 'Produit', 'Stock Actuel', 'Seuil Alerte', 'Stock Max', 'Unite', 'Prix Achat', 'Valeur Stock'];
  const rows = data.map(p => [
    p.id,
    p.nom || '',
    p.stock_actuel || 0,
    p.seuil_alerte || 10,
    p.stock_max || '',
    p.unite || 'u',
    p.prix_achat || 0,
    ((p.stock_actuel || 0) * (p.prix_achat || 0)).toFixed(2),
  ]);

  const csvContent = [
    headers.join(';'),
    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';'))
  ].join('\n');

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// Summary Card Component
function SummaryCard({ value, label, color }) {
  return (
    <div className="bg-white/5 rounded-xl p-4 text-center">
      <p className={`text-2xl font-bold ${color || 'text-white'}`}>{value}</p>
      <p className="text-xs text-slate-400">{label}</p>
    </div>
  );
}

// Stock Level Bar Component
function StockLevelBar({ percentage, status }) {
  const colors = {
    critical: 'bg-rose-500',
    low: 'bg-amber-500',
    ok: 'bg-emerald-500',
  };

  const statusLabels = {
    critical: 'Critique',
    low: 'Bas',
    ok: 'OK',
  };

  const statusColors = {
    critical: 'text-rose-400',
    low: 'text-amber-400',
    ok: 'text-emerald-400',
  };

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${colors[status]}`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
      <span className={`text-sm ${statusColors[status]}`}>{statusLabels[status]}</span>
    </div>
  );
}

// Alert Item Component
function AlertItem({ critical, title, description, onClick }) {
  return (
    <div
      className={`p-4 rounded-xl cursor-pointer transition-all hover:translate-x-1 ${
        critical
          ? 'bg-rose-500/10 border-l-3 border-l-rose-500'
          : 'bg-amber-500/10 border-l-3 border-l-amber-500'
      }`}
      style={{ borderLeftWidth: '3px' }}
      onClick={onClick}
    >
      <p className="text-sm font-medium text-white mb-1">
        {critical ? '⚠️' : '📦'} {title}
      </p>
      <p className="text-xs text-slate-400">{description}</p>
    </div>
  );
}

// Movement Item Component
function MovementItem({ type, title, time, quantity, onClick }) {
  const icons = {
    in: { icon: <ArrowDownCircle className="w-4 h-4" />, bg: 'bg-emerald-500/20', color: 'text-emerald-400' },
    out: { icon: <ArrowUpCircle className="w-4 h-4" />, bg: 'bg-rose-500/20', color: 'text-rose-400' },
    adjust: { icon: <RefreshCw className="w-4 h-4" />, bg: 'bg-amber-500/20', color: 'text-amber-400' },
  };

  const { icon, bg, color } = icons[type] || icons.adjust;

  return (
    <div
      className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 cursor-pointer transition-all"
      onClick={onClick}
    >
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${bg} ${color}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{title}</p>
        <p className="text-xs text-slate-500">{time}</p>
      </div>
      <span className={`text-sm font-semibold ${
        type === 'in' ? 'text-emerald-400' :
        type === 'out' ? 'text-rose-400' : 'text-slate-400'
      }`}>
        {type === 'in' ? '+' : type === 'out' ? '-' : '±'}{quantity}
      </span>
    </div>
  );
}

// Tab Button Component
function TabButton({ active, children, onClick }) {
  return (
    <button
      className={`px-5 py-2.5 rounded-lg text-sm transition-all ${
        active
          ? 'bg-emerald-500/20 text-emerald-400 font-medium'
          : 'text-slate-400 hover:text-white'
      }`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function StockPage({ embedded = false }) {
  const queryClient = useQueryClient();
  const { data: products = [], isLoading } = useProducts();
  const { data: recentMovements = [] } = useRecentMovements({ limit: 10 });

  const [activeTab, setActiveTab] = useState('all');
  const [adjustModalOpen, setAdjustModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Calcul des métriques globales du stock
  // - Valeur totale: somme de (quantité × prix d'achat) pour tous les produits
  // - Références actives: nombre de produits avec stock > 0
  // - Alertes: nombre de produits sous le seuil d'alerte
  const metrics = useMemo(() => {
    const totalValue = products.reduce((sum, p) => {
      return sum + ((p.stock_actuel || 0) * (p.prix_achat || 0));
    }, 0);

    const activeRefs = products.filter(p => (p.stock_actuel || 0) > 0).length;

    const alerts = products.filter(p => {
      const stock = p.stock_actuel || 0;
      const threshold = p.seuil_alerte || 10;
      return stock < threshold;
    });

    return {
      totalValue,
      activeRefs,
      alertCount: alerts.length,
    };
  }, [products]);

  // Filtrage des produits selon l'onglet actif
  // - 'rupture': stock = 0
  // - 'low': 0 < stock < seuil d'alerte
  // - 'overstock': stock > stock max (par défaut seuil × 3)
  // - 'all': tous les produits
  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      const stock = p.stock_actuel || 0;
      const threshold = p.seuil_alerte || 10;
      const maxStock = (p.stock_max || threshold * 3);

      switch (activeTab) {
        case 'rupture':
          return stock === 0;
        case 'low':
          return stock > 0 && stock < threshold;
        case 'overstock':
          return stock > maxStock;
        default:
          return true;
      }
    });
  }, [products, activeTab]);

  // Get stock status
  const getStockStatus = useCallback((product) => {
    const stock = product.stock_actuel || 0;
    const threshold = product.seuil_alerte || 10;

    if (stock === 0) return { status: 'critical', percentage: 0 };
    if (stock < threshold) return { status: 'low', percentage: (stock / threshold) * 50 };
    return { status: 'ok', percentage: Math.min(100, (stock / threshold) * 50 + 50) };
  }, []);

  // Get alerts
  const alerts = useMemo(() => {
    return products
      .filter(p => (p.stock_actuel || 0) < (p.seuil_alerte || 10))
      .slice(0, 5)
      .map(p => ({
        id: p.id,
        critical: (p.stock_actuel || 0) === 0,
        title: (p.stock_actuel || 0) === 0
          ? `Rupture imminente - ${p.nom}`
          : `Stock critique - ${p.nom}`,
        description: `Stock: ${p.stock_actuel || 0}${p.unite || ''} • Seuil min: ${p.seuil_alerte || 10}${p.unite || ''}`,
        product: p,
      }));
  }, [products]);

  // Recent movements - use real data or fallback to mock
  const movements = useMemo(() => {
    if (recentMovements.length > 0) {
      return recentMovements.slice(0, 5).map((m) => ({
        type: m.type_mouvement === 'entree' ? 'in' : m.type_mouvement === 'sortie' ? 'out' : 'adjust',
        title: m.produit_nom || m.source || 'Mouvement',
        time: m.date_mouvement ? new Date(m.date_mouvement).toLocaleDateString('fr-FR') : '—',
        quantity: `${Math.abs(m.quantite || 0)} ${m.unite || 'u'}`,
      }));
    }
    return [
      { type: 'in', title: 'Réception Metro', time: 'Il y a 2h', quantity: '45 articles' },
      { type: 'out', title: 'Sortie production', time: 'Il y a 4h', quantity: '12 articles' },
      { type: 'adjust', title: 'Ajustement inventaire', time: 'Hier', quantity: '3 articles' },
    ];
  }, [recentMovements]);

  const handleOpenAdjust = (product) => {
    setSelectedProduct(product);
    setAdjustModalOpen(true);
  };

  const handleExport = useCallback(() => {
    if (products.length === 0) {
      toast.error('Aucun produit à exporter');
      return;
    }
    const filename = `stock_${new Date().toISOString().slice(0, 10)}.csv`;
    downloadCSV(products, filename);
    toast.success(`${products.length} produits exportés`, {
      description: `Valeur totale: €${metrics.totalValue.toLocaleString('fr-FR')}`,
    });
  }, [products, metrics.totalValue]);

  return (
    <div className="space-y-6">
      {/* Header */}
      {!embedded && (
        <div>
          <h1 className="text-3xl font-bold font-display text-white">Gestion du Stock</h1>
          <p className="text-slate-400 mt-1">Mouvements, alertes et niveaux de stock en temps réel</p>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Overview + Table */}
        <div className="lg:col-span-2 space-y-6">
          {/* Overview Card */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <div className="flex justify-between items-center mb-5">
              <h2 className="text-lg font-semibold text-white">Vue d'ensemble</h2>
              <Button size="sm" variant="ghost" onClick={handleExport}>
                <Download className="w-4 h-4" />
                Exporter
              </Button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <SummaryCard
                value={`€${metrics.totalValue.toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`}
                label="Valeur totale stock"
                color="text-emerald-400"
              />
              <SummaryCard
                value={metrics.activeRefs.toLocaleString()}
                label="Références actives"
              />
              <SummaryCard
                value={metrics.alertCount}
                label="Alertes stock"
                color="text-amber-400"
              />
            </div>

            {/* Tabs */}
            <div className="flex gap-1 p-1 bg-white/5 rounded-xl w-fit mb-6">
              <TabButton active={activeTab === 'all'} onClick={() => setActiveTab('all')}>Tous</TabButton>
              <TabButton active={activeTab === 'rupture'} onClick={() => setActiveTab('rupture')}>Rupture</TabButton>
              <TabButton active={activeTab === 'low'} onClick={() => setActiveTab('low')}>Stock bas</TabButton>
              <TabButton active={activeTab === 'overstock'} onClick={() => setActiveTab('overstock')}>Surstock</TabButton>
            </div>

            {/* Products Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs uppercase text-slate-500 border-b border-white/10">
                    <th className="pb-3 px-4">Produit</th>
                    <th className="pb-3 px-4">Stock actuel</th>
                    <th className="pb-3 px-4">Niveau</th>
                    <th className="pb-3 px-4">Rotation</th>
                    <th className="pb-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-500">Chargement...</td>
                    </tr>
                  ) : filteredProducts.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-500">Aucun produit trouvé</td>
                    </tr>
                  ) : (
                    filteredProducts.slice(0, 10).map(product => {
                      const { status, percentage } = getStockStatus(product);
                      return (
                        <tr
                          key={product.id}
                          className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                          onClick={() => handleOpenAdjust(product)}
                        >
                          <td className="py-3 px-4">
                            <span className="font-medium text-white">{product.nom}</span>
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {product.stock_actuel || 0} {product.unite || 'u'}
                          </td>
                          <td className="py-3 px-4">
                            <StockLevelBar percentage={percentage} status={status} />
                          </td>
                          <td className="py-3 px-4 text-slate-400">
                            {product.rotation || '—'}/jour
                          </td>
                          <td className="py-3 px-4">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleOpenAdjust(product);
                              }}
                            >
                              {status === 'critical' || status === 'low' ? 'Commander' : 'Détails'}
                            </Button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: Alerts + Movements */}
        <div className="space-y-6">
          {/* Alerts */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Alertes Stock</h2>
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-4">Aucune alerte</p>
              ) : (
                alerts.map(alert => (
                  <AlertItem
                    key={alert.id}
                    critical={alert.critical}
                    title={alert.title}
                    description={alert.description}
                    onClick={() => handleOpenAdjust(alert.product)}
                  />
                ))
              )}
            </div>
          </div>

          {/* Recent Movements */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Mouvements récents</h2>
            <div className="space-y-3">
              {movements.map((movement, idx) => (
                <MovementItem
                  key={idx}
                  type={movement.type}
                  title={movement.title}
                  time={movement.time}
                  quantity={movement.quantity}
                  onClick={() => toast.info(`Détail: ${movement.title}`)}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Stock Adjustment Modal */}
      <StockAdjustmentModal
        open={adjustModalOpen}
        onClose={() => {
          setAdjustModalOpen(false);
          setSelectedProduct(null);
        }}
        product={selectedProduct}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['products'] });
        }}
      />
    </div>
  );
}
