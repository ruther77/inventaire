import { useState, useCallback } from 'react';
import { X, Mail, Phone, MapPin, Calendar, Package, History, TrendingUp, Truck, CreditCard } from 'lucide-react';
import clsx from 'clsx';
import Button from '../ui/Button.jsx';

/**
 * SupplierModal - Modal fiche fournisseur avec onglets
 * Design basé sur mockup modal-fournisseur.html
 */
export default function SupplierModal({
  open,
  onClose,
  supplier,
  onContact,
  onNewOrder,
}) {
  const [activeTab, setActiveTab] = useState('infos');

  const handleClose = useCallback(() => {
    onClose?.();
  }, [onClose]);

  if (!open || !supplier) return null;

  const tabs = [
    { id: 'infos', label: 'Infos', icon: Package },
    { id: 'products', label: 'Produits', icon: Package },
    { id: 'history', label: 'Historique', icon: History },
  ];

  // Score color based on value
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500 bg-emerald-500/20';
    if (score >= 60) return 'text-amber-400 border-amber-500 bg-amber-500/20';
    return 'text-rose-400 border-rose-500 bg-rose-500/20';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-slate-900/95 border border-white/15 rounded-2xl w-full max-w-[600px] max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10 bg-gradient-to-r from-cyan-500/10 to-transparent">
          <h2 className="text-xl font-semibold text-white font-['Sora',sans-serif]">
            Fiche Fournisseur
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className="w-9 h-9 rounded-xl bg-white/5 border-none text-slate-400 text-lg flex items-center justify-center hover:bg-white/10 hover:text-white transition-colors"
            aria-label="Fermer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Supplier Header */}
          <div className="flex items-center gap-5 mb-6">
            {/* Logo */}
            <div className="w-[72px] h-[72px] rounded-2xl bg-cyan-500/20 flex items-center justify-center text-3xl font-bold text-cyan-400">
              {supplier.name?.charAt(0) || 'S'}
            </div>
            {/* Info */}
            <div className="flex-1">
              <div className="text-xl font-semibold text-white mb-1">
                {supplier.name || 'Fournisseur'}
              </div>
              <div className="text-sm text-slate-400">
                {supplier.type || 'Grossiste'} {supplier.partnerSince && `• Partenaire depuis ${supplier.partnerSince}`}
              </div>
            </div>
            {/* Score */}
            {supplier.score !== undefined && (
              <div className={clsx(
                'w-14 h-14 rounded-full border-[3px] flex items-center justify-center text-lg font-bold',
                getScoreColor(supplier.score)
              )}>
                {supplier.score}
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-white/5 p-1 rounded-xl mb-5">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'flex-1 py-2.5 px-3 text-center rounded-lg text-sm font-medium transition-all',
                  activeTab === tab.id
                    ? 'bg-white/10 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'infos' && (
            <div className="space-y-5">
              {/* Info Grid */}
              <div className="grid grid-cols-2 gap-4">
                <InfoItem
                  icon={Phone}
                  label="Contact principal"
                  value={supplier.contactName || '—'}
                />
                <InfoItem
                  icon={Phone}
                  label="Téléphone"
                  value={supplier.phone || '—'}
                />
                <InfoItem
                  icon={Mail}
                  label="Email"
                  value={supplier.email || '—'}
                />
                <InfoItem
                  icon={CreditCard}
                  label="Délai de paiement"
                  value={supplier.paymentTerms || '30 jours'}
                />
                <div className="col-span-2">
                  <InfoItem
                    icon={MapPin}
                    label="Adresse"
                    value={supplier.address || '—'}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3 mt-5">
                <StatCard
                  value={supplier.totalPurchases ? `€${supplier.totalPurchases.toLocaleString()}` : '€0'}
                  label="Achats (12 mois)"
                  color="text-cyan-400"
                />
                <StatCard
                  value={supplier.orderCount || 0}
                  label="Commandes"
                  color="text-white"
                />
                <StatCard
                  value={supplier.deliveryDelay ? `${supplier.deliveryDelay}j` : '—'}
                  label="Délai livraison"
                  color="text-emerald-400"
                />
              </div>
            </div>
          )}

          {activeTab === 'products' && (
            <div className="space-y-2">
              {supplier.products && supplier.products.length > 0 ? (
                supplier.products.map((product, index) => (
                  <ProductItem key={product.id || index} product={product} />
                ))
              ) : (
                <div className="text-center py-10 text-slate-400">
                  Aucun produit associé
                </div>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <div className="text-center py-10 text-slate-400">
              Historique des commandes à venir...
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center px-6 py-5 border-t border-white/10 bg-slate-900/95">
          <Button
            variant="outline"
            onClick={() => onContact?.(supplier)}
            className="border-cyan-500 text-cyan-400 hover:bg-cyan-500/10"
          >
            <Mail className="w-4 h-4 mr-2" />
            Contacter
          </Button>
          <Button
            variant="primary"
            onClick={() => onNewOrder?.(supplier)}
            className="bg-cyan-500 hover:bg-cyan-600"
          >
            <Package className="w-4 h-4 mr-2" />
            Nouvelle commande
          </Button>
        </div>
      </div>
    </div>
  );
}

// Sub-components
function InfoItem({ icon: Icon, label, value }) {
  return (
    <div className="p-4 bg-white/5 rounded-xl">
      <div className="flex items-center gap-2 text-xs text-slate-400 mb-1.5">
        {Icon && <Icon className="w-3.5 h-3.5" />}
        {label}
      </div>
      <div className="text-sm font-medium text-white">{value}</div>
    </div>
  );
}

function StatCard({ value, label, color = 'text-white' }) {
  return (
    <div className="p-4 bg-white/5 rounded-xl text-center">
      <div className={clsx('text-xl font-bold mb-1', color)}>{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  );
}

function ProductItem({ product }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors">
      <span className="text-xl">{product.icon || '📦'}</span>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white truncate">
          {product.name}
        </div>
        <div className="text-xs text-slate-400">
          {product.reference || 'REF: —'}
        </div>
      </div>
      <span className="text-sm font-semibold text-white">
        {product.price ? `€${product.price}` : '—'}
        {product.unit && `/${product.unit}`}
      </span>
    </div>
  );
}
