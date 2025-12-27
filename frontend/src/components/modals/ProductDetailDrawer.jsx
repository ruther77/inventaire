import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Edit3,
  BarChart3,
  ShoppingCart,
  ArrowDownCircle,
  ArrowUpCircle,
  Trash2,
  TrendingUp,
  TrendingDown,
  Package,
  Loader2,
} from 'lucide-react';
import Button from '../ui/Button.jsx';
import { useProductDetail } from '@/hooks/useProducts.js';

// Stat Item Component
function StatItem({ label, value, valueColor, trend, trendType, isLoading }) {
  return (
    <div className="p-3 rounded-lg bg-white/3">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      {isLoading ? (
        <div className="h-7 w-16 bg-white/5 rounded animate-pulse" />
      ) : (
        <p className={`text-lg font-bold ${valueColor || 'text-white'}`}>{value}</p>
      )}
      {trend && !isLoading && (
        <p className={`text-xs mt-1 flex items-center gap-1 ${
          trendType === 'up' ? 'text-emerald-400' : trendType === 'down' ? 'text-rose-400' : 'text-slate-400'
        }`}>
          {trendType === 'up' && <TrendingUp className="w-3 h-3" />}
          {trendType === 'down' && <TrendingDown className="w-3 h-3" />}
          {trend}
        </p>
      )}
    </div>
  );
}

// Price Row Component
function PriceRow({ label, value, valueColor }) {
  return (
    <div className="flex justify-between py-2.5 border-b border-white/5 last:border-0">
      <span className="text-sm text-slate-400">{label}</span>
      <span className={`text-sm font-semibold ${valueColor || 'text-white'}`}>{value}</span>
    </div>
  );
}

// Stock Level Bar Component
function StockLevelBar({ current, min, max }) {
  const percentage = max > 0 ? (current / max) * 100 : 0;
  const minPercentage = max > 0 ? (min / max) * 100 : 20;

  let fillColor = 'bg-emerald-500';
  if (current <= min) fillColor = 'bg-rose-500';
  else if (current <= min * 1.5) fillColor = 'bg-amber-500';

  return (
    <div className="mt-4">
      <div className="flex justify-between text-xs text-slate-500 mb-2">
        <span>0</span>
        <span>Min: {min}</span>
        <span>Max: {Math.round(max)}</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full relative overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${fillColor}`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
        <div
          className="absolute h-full w-0.5 bg-amber-400"
          style={{ left: `${minPercentage}%` }}
        />
      </div>
    </div>
  );
}

// Movement Item Component
function MovementItem({ type, description, date, quantity }) {
  const icons = {
    entree: { icon: ArrowDownCircle, bg: 'bg-emerald-500/20', color: 'text-emerald-400' },
    sortie: { icon: ArrowUpCircle, bg: 'bg-rose-500/20', color: 'text-rose-400' },
    perte: { icon: Trash2, bg: 'bg-slate-500/20', color: 'text-slate-400' },
    in: { icon: ArrowDownCircle, bg: 'bg-emerald-500/20', color: 'text-emerald-400' },
    out: { icon: ArrowUpCircle, bg: 'bg-rose-500/20', color: 'text-rose-400' },
    loss: { icon: Trash2, bg: 'bg-slate-500/20', color: 'text-slate-400' },
  };

  const config = icons[type] || icons.sortie;
  const Icon = config.icon;
  const isEntry = type === 'entree' || type === 'in';

  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-white/5 last:border-0">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${config.bg}`}>
        <Icon className={`w-4 h-4 ${config.color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">{description || 'Mouvement'}</p>
        <p className="text-xs text-slate-500">{date}</p>
      </div>
      <span className={`text-sm font-semibold ${
        isEntry ? 'text-emerald-400' : 'text-rose-400'
      }`}>
        {isEntry ? '+' : '-'}{Math.abs(quantity)}
      </span>
    </div>
  );
}

export default function ProductDetailDrawer({
  open,
  onClose,
  product,
  onEdit,
  onHistory,
  onOrder
}) {
  // Fetch enriched product data from API
  const { data: enrichedProduct, isLoading } = useProductDetail(product?.id);

  // Merge base product data with enriched data
  const productData = useMemo(() => {
    if (!product) return null;
    return {
      ...product,
      ...enrichedProduct,
    };
  }, [product, enrichedProduct]);

  // Calculate derived data
  const stockStatus = useMemo(() => {
    if (!productData) return { status: 'ok', label: 'OK', color: 'text-emerald-400', bg: 'bg-emerald-500/20' };

    const stock = productData.stock_actuel || 0;
    const min = productData.seuil_alerte || 10;

    if (stock === 0) return { status: 'critical', label: 'Rupture', color: 'text-rose-400', bg: 'bg-rose-500/20' };
    if (stock <= min) return { status: 'low', label: 'Stock bas', color: 'text-amber-400', bg: 'bg-amber-500/20' };
    return { status: 'ok', label: 'OK', color: 'text-emerald-400', bg: 'bg-emerald-500/20' };
  }, [productData]);

  const margin = useMemo(() => {
    if (!productData?.prix_vente || !productData?.prix_achat) return null;
    const marginValue = productData.prix_vente - productData.prix_achat;
    const marginPercent = ((marginValue / productData.prix_vente) * 100).toFixed(0);
    return { value: marginValue.toFixed(2), percent: marginPercent };
  }, [productData]);

  // Format movements from API data
  const formattedMovements = useMemo(() => {
    const movements = productData?.mouvements_recents || [];
    if (movements.length === 0) {
      return [];
    }
    return movements.slice(0, 8).map((m) => ({
      type: m.type,
      description: m.source || 'Mouvement stock',
      date: m.date
        ? new Date(m.date).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })
        : '',
      quantity: Math.abs(m.quantite || 0),
    }));
  }, [productData]);

  // Format dernier achat
  const dernierAchatFormatted = useMemo(() => {
    if (!productData?.dernier_achat) return 'N/A';
    const { date, source, quantite } = productData.dernier_achat;
    if (!date) return 'N/A';
    const dateStr = new Date(date).toLocaleDateString('fr-FR');
    return `${dateStr}${source ? ` (${source})` : ''}`;
  }, [productData]);

  // Format rotation display
  const rotationDisplay = useMemo(() => {
    if (!productData) return '—';
    const rotation = productData.rotation || 0;
    if (rotation === 0) return '—';
    return `${rotation.toFixed(1)}x`;
  }, [productData]);

  // Format jours de stock
  const joursStockDisplay = useMemo(() => {
    if (!productData) return '—';
    const jours = productData.jours_de_stock || 0;
    if (jours >= 999) return '∞';
    if (jours === 0) return '0j';
    return `${Math.round(jours)}j`;
  }, [productData]);

  if (!product) return null;

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 w-[450px] h-full bg-[rgba(15,15,25,0.98)] border-l border-white/10 z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-white/10 bg-gradient-to-r from-emerald-500/10 to-transparent">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Package className="w-5 h-5 text-emerald-400" />
                Détail Produit
                {isLoading && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
              </h2>
              <div className="flex gap-2">
                <button
                  className="w-9 h-9 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                  onClick={() => onEdit?.(productData || product)}
                  title="Modifier"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
                <button
                  className="w-9 h-9 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                  onClick={() => onHistory?.(productData || product)}
                  title="Historique"
                >
                  <BarChart3 className="w-4 h-4" />
                </button>
                <button
                  className="w-9 h-9 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                  onClick={onClose}
                  title="Fermer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {/* Product Hero */}
              <div className="flex gap-4">
                <div className="w-24 h-24 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-5xl">
                  {product.emoji || '📦'}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-xl font-semibold text-white truncate">{product.nom}</h3>
                  <p className="text-sm text-slate-500 mt-1">
                    REF: {product.reference || product.id}
                    {productData?.codes?.[0] && ` • EAN: ${productData.codes[0]}`}
                  </p>
                  <div className="flex gap-2 mt-3">
                    {product.categorie && (
                      <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-blue-500/20 text-blue-400">
                        {product.categorie}
                      </span>
                    )}
                    <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${stockStatus.bg} ${stockStatus.color}`}>
                      {stockStatus.label}
                    </span>
                  </div>
                </div>
              </div>

              {/* KPIs Section */}
              <div className="rounded-xl bg-white/3 p-4">
                <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-slate-400" />
                  KPIs
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <StatItem
                    label="Stock actuel"
                    value={`${productData?.stock_actuel || 0} ${product.unite || 'u'}`}
                    valueColor={stockStatus.color}
                    trend={productData?.trend_stock_pct !== undefined
                      ? `${productData.trend_stock_pct >= 0 ? '+' : ''}${productData.trend_stock_pct}% vs semaine`
                      : null}
                    trendType={productData?.trend_stock_pct >= 0 ? 'up' : 'down'}
                    isLoading={isLoading}
                  />
                  <StatItem
                    label="Couverture"
                    value={joursStockDisplay}
                    trend={rotationDisplay !== '—' ? `Rotation: ${rotationDisplay}` : null}
                    trendType={productData?.rotation > 1 ? 'up' : 'neutral'}
                    isLoading={isLoading}
                  />
                  <StatItem
                    label="Ventes (30j)"
                    value={productData?.ventes_30j !== undefined ? `${Math.round(productData.ventes_30j)} ${product.unite || 'u'}` : '—'}
                    trend={productData?.trend_ventes_pct !== undefined
                      ? `${productData.trend_ventes_pct >= 0 ? '+' : ''}${productData.trend_ventes_pct}% vs sem. préc.`
                      : null}
                    trendType={productData?.trend_ventes_pct >= 0 ? 'up' : 'down'}
                    isLoading={isLoading}
                  />
                  <StatItem
                    label="Marge"
                    value={margin ? `${margin.percent}%` : 'N/A'}
                    valueColor={margin && parseInt(margin.percent) < 30 ? 'text-amber-400' : 'text-white'}
                    trend={margin && parseInt(margin.percent) < 30 ? 'Sous objectif' : margin ? 'OK' : null}
                    trendType={margin && parseInt(margin.percent) >= 30 ? 'up' : 'down'}
                  />
                </div>
              </div>

              {/* Prix Section */}
              <div className="rounded-xl bg-white/3 p-4">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <span className="text-base">💰</span>
                  Prix
                  {productData?.trend_prix_pct !== undefined && productData.trend_prix_pct !== 0 && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ml-auto ${
                      productData.trend_prix_pct > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {productData.trend_prix_pct > 0 ? '+' : ''}{productData.trend_prix_pct}%
                    </span>
                  )}
                </h4>
                <PriceRow
                  label="Prix d'achat HT"
                  value={`€${(productData?.prix_achat || 0).toFixed(2)}/${product.unite || 'u'}`}
                />
                <PriceRow
                  label="Prix de vente TTC"
                  value={`€${(productData?.prix_vente || 0).toFixed(2)}/${product.unite || 'u'}`}
                />
                {margin && (
                  <PriceRow
                    label="Marge brute"
                    value={`€${margin.value}/${product.unite || 'u'} (${margin.percent}%)`}
                    valueColor="text-amber-400"
                  />
                )}
                <PriceRow
                  label="Dernier achat"
                  value={dernierAchatFormatted}
                />
              </div>

              {/* Stock Level Section */}
              <div className="rounded-xl bg-white/3 p-4">
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Package className="w-4 h-4 text-slate-400" />
                  Niveau de stock
                </h4>
                <StockLevelBar
                  current={productData?.stock_actuel || 0}
                  min={productData?.seuil_alerte || 20}
                  max={productData?.stock_max || 100}
                />
              </div>

              {/* Mouvements récents */}
              <div className="rounded-xl bg-white/3 p-4">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <span className="text-base">📋</span>
                  Mouvements récents
                </h4>
                <div className="max-h-52 overflow-y-auto">
                  {isLoading ? (
                    <div className="space-y-3">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-12 bg-white/5 rounded animate-pulse" />
                      ))}
                    </div>
                  ) : formattedMovements.length > 0 ? (
                    formattedMovements.map((movement, idx) => (
                      <MovementItem
                        key={idx}
                        type={movement.type}
                        description={movement.description}
                        date={movement.date}
                        quantity={movement.quantity}
                      />
                    ))
                  ) : (
                    <p className="text-sm text-slate-500 text-center py-4">
                      Aucun mouvement récent
                    </p>
                  )}
                </div>
              </div>

              {/* Historique des prix (si disponible) */}
              {productData?.historique_prix?.length > 1 && (
                <div className="rounded-xl bg-white/3 p-4">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <span className="text-base">📈</span>
                    Historique des prix
                  </h4>
                  <div className="space-y-1">
                    {productData.historique_prix.slice(0, 5).map((entry, idx) => (
                      <div key={idx} className="flex justify-between py-1.5 text-sm">
                        <span className="text-slate-400">
                          {entry.date ? new Date(entry.date).toLocaleDateString('fr-FR') : '—'}
                          {entry.fournisseur && ` • ${entry.fournisseur}`}
                        </span>
                        <span className="font-medium text-white">€{entry.prix?.toFixed(2) || '—'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Consommations par ventes de plats */}
              {productData?.plats_utilisant?.length > 0 && (
                <div className="rounded-xl bg-white/3 p-4">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <span className="text-base">🍽️</span>
                    Utilisé dans les plats
                    {productData.conso_plats_30j > 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400 ml-auto">
                        -{productData.conso_plats_30j.toFixed(2)} sur 30j
                      </span>
                    )}
                  </h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {productData.plats_utilisant.slice(0, 6).map((plat, idx) => (
                      <div key={idx} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-white truncate">{plat.plat_nom}</p>
                          <p className="text-xs text-slate-500">
                            via {plat.ingredient_nom} • {plat.qte_par_plat.toFixed(3)}/plat
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-violet-400">
                            -{plat.consomme_30j.toFixed(2)}
                          </p>
                          <p className="text-xs text-slate-500">{plat.ventes_30j} ventes</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Consommations récentes par plats */}
              {productData?.consommations_recentes?.length > 0 && (
                <div className="rounded-xl bg-white/3 p-4">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <span className="text-base">📊</span>
                    Sorties récentes (ventes plats)
                  </h4>
                  <div className="max-h-40 overflow-y-auto space-y-1">
                    {productData.consommations_recentes.slice(0, 8).map((conso, idx) => (
                      <div key={idx} className="flex items-center justify-between py-1.5 text-sm">
                        <div className="min-w-0 flex-1">
                          <span className="text-slate-400">
                            {conso.date ? new Date(conso.date).toLocaleDateString('fr-FR', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            }) : '—'}
                          </span>
                          <span className="text-white ml-2 truncate">{conso.plat_nom}</span>
                        </div>
                        <span className="text-rose-400 font-medium">
                          -{conso.quantite_consommee.toFixed(3)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-5 border-t border-white/10">
              <Button
                variant="ghost"
                className="flex-1"
                onClick={() => onHistory?.(productData || product)}
              >
                <BarChart3 className="w-4 h-4" />
                Historique
              </Button>
              <Button
                variant="brand"
                className="flex-1"
                onClick={() => onOrder?.(productData || product)}
              >
                <ShoppingCart className="w-4 h-4" />
                Commander
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
