import { useState, useCallback, useMemo } from 'react';
import {
  Package,
  Truck,
  FileText,
  Download,
  Mail,
  Printer,
  Loader2,
  Check,
  X,
  Edit3,
  Calendar,
} from 'lucide-react';
import Modal from '@/components/ui/Modal.jsx';
import Button from '@/components/ui/Button.jsx';
import { toast } from 'sonner';

const ORDER_DELIVERY_OPTIONS = [
  { value: 'standard', label: 'Livraison standard', days: '3-5 jours' },
  { value: 'express', label: 'Livraison express', days: '1-2 jours' },
  { value: 'pickup', label: 'Retrait sur place', days: 'Disponible immédiatement' },
];

const numberFormatter = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
});

const quantityFormatter = new Intl.NumberFormat('fr-FR', {
  maximumFractionDigits: 2,
});

export default function CreateOrderModal({
  open,
  onClose,
  supplier,
  items = [],
  onSuccess,
}) {
  const [editableItems, setEditableItems] = useState([]);
  const [delivery, setDelivery] = useState('standard');
  const [notes, setNotes] = useState('');
  const [deliveryDate, setDeliveryDate] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Initialize editable items when modal opens
  useState(() => {
    if (open && items.length > 0) {
      setEditableItems(
        items.map((item) => ({
          ...item,
          quantite_commande: item.quantite_a_commander || item.quantite_auto || 0,
          included: true,
        }))
      );
    }
  }, [open, items]);

  // Sync items when they change
  useMemo(() => {
    if (items.length > 0 && editableItems.length === 0) {
      setEditableItems(
        items.map((item) => ({
          ...item,
          quantite_commande: item.quantite_a_commander || item.quantite_auto || 0,
          included: true,
        }))
      );
    }
  }, [items, editableItems.length]);

  const toggleItem = useCallback((itemId) => {
    setEditableItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, included: !item.included } : item
      )
    );
  }, []);

  const updateQuantity = useCallback((itemId, quantity) => {
    setEditableItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, quantite_commande: Math.max(0, quantity) } : item
      )
    );
  }, []);

  const includedItems = useMemo(
    () => editableItems.filter((item) => item.included && item.quantite_commande > 0),
    [editableItems]
  );

  const totals = useMemo(() => {
    const total = includedItems.reduce(
      (acc, item) => {
        const lineValue = (item.prix_achat || 0) * item.quantite_commande;
        return {
          units: acc.units + item.quantite_commande,
          value: acc.value + lineValue,
          margin: acc.margin + (item.marge_commande || 0),
        };
      },
      { units: 0, value: 0, margin: 0 }
    );
    return total;
  }, [includedItems]);

  const generateOrderPDF = useCallback(async () => {
    setIsGenerating(true);

    // Simulate PDF generation
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Build CSV content as fallback
    const headers = ['Référence', 'Produit', 'Quantité', 'Unité', 'Prix unitaire', 'Total'];
    const rows = includedItems.map((item) => [
      item.code_interne || item.ean || '-',
      item.nom,
      item.quantite_commande,
      item.unite || 'unit',
      (item.prix_achat || 0).toFixed(2),
      ((item.prix_achat || 0) * item.quantite_commande).toFixed(2),
    ]);

    const csvContent = [
      `Bon de commande - ${supplier}`,
      `Date: ${new Date().toLocaleDateString('fr-FR')}`,
      `Livraison souhaitée: ${deliveryDate || 'À convenir'}`,
      '',
      headers.join(';'),
      ...rows.map((row) => row.join(';')),
      '',
      `Total articles: ${includedItems.length}`,
      `Total unités: ${quantityFormatter.format(totals.units)}`,
      `Montant total HT: ${numberFormatter.format(totals.value)}`,
      '',
      notes ? `Notes: ${notes}` : '',
    ].join('\n');

    // Download as CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const slug = supplier.toLowerCase().replace(/\s+/g, '_');
    link.href = url;
    link.download = `commande_${slug}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setIsGenerating(false);
    toast.success('Bon de commande généré');
  }, [includedItems, supplier, deliveryDate, notes, totals]);

  const handleSendEmail = useCallback(() => {
    const subject = encodeURIComponent(`Commande - ${supplier}`);
    const body = encodeURIComponent(
      `Bonjour,\n\nVeuillez trouver ci-joint notre commande.\n\nCordialement`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
    toast.info('Ouverture du client email...');
  }, [supplier]);

  const handleClose = useCallback(() => {
    setEditableItems([]);
    setDelivery('standard');
    setNotes('');
    setDeliveryDate('');
    onClose();
  }, [onClose]);

  const handleConfirm = useCallback(async () => {
    await generateOrderPDF();
    onSuccess?.();
    handleClose();
  }, [generateOrderPDF, onSuccess, handleClose]);

  if (!supplier) return null;

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Créer une commande fournisseur"
      description={`Commande pour ${supplier} - ${includedItems.length} article(s)`}
      size="xl"
    >
      <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
        {/* Supplier header */}
        <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
          <div className="w-14 h-14 rounded-xl bg-blue-500/20 flex items-center justify-center">
            <Truck className="w-7 h-7 text-blue-400" />
          </div>
          <div className="flex-1">
            <p className="text-lg font-semibold text-white">{supplier}</p>
            <p className="text-sm text-slate-400">
              {includedItems.length} article(s) sélectionné(s)
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-white">
              {numberFormatter.format(totals.value)}
            </p>
            <p className="text-sm text-slate-400">HT</p>
          </div>
        </div>

        {/* Items list */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
              <Package className="w-4 h-4" />
              Articles à commander
            </h4>
            <span className="text-xs text-slate-500">
              {includedItems.length} / {editableItems.length} sélectionnés
            </span>
          </div>

          <div className="border border-white/10 rounded-xl overflow-hidden">
            <div className="max-h-64 overflow-y-auto">
              {editableItems.length === 0 ? (
                <div className="p-8 text-center text-slate-500">
                  Aucun article à commander pour ce fournisseur
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-white/5 sticky top-0">
                    <tr className="text-left text-xs uppercase text-slate-500">
                      <th className="px-4 py-3 w-10"></th>
                      <th className="px-4 py-3">Produit</th>
                      <th className="px-4 py-3 w-28 text-right">Quantité</th>
                      <th className="px-4 py-3 w-24 text-right">P.U.</th>
                      <th className="px-4 py-3 w-28 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {editableItems.map((item) => (
                      <tr
                        key={item.id}
                        className={`transition-colors ${
                          item.included ? 'hover:bg-white/5' : 'opacity-50'
                        }`}
                      >
                        <td className="px-4 py-3">
                          <button
                            type="button"
                            onClick={() => toggleItem(item.id)}
                            className={`w-5 h-5 rounded border flex items-center justify-center transition-all ${
                              item.included
                                ? 'bg-blue-500 border-blue-500'
                                : 'border-white/20 hover:border-white/40'
                            }`}
                          >
                            {item.included && <Check className="w-3 h-3 text-white" />}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <p className="font-medium text-white">{item.nom}</p>
                          <p className="text-xs text-slate-500">
                            {item.code_interne || item.ean || 'Sans référence'}
                          </p>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            <input
                              type="number"
                              value={item.quantite_commande}
                              onChange={(e) =>
                                updateQuantity(item.id, parseFloat(e.target.value) || 0)
                              }
                              disabled={!item.included}
                              className="w-20 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-right text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50"
                            />
                            <span className="text-xs text-slate-500 w-8">
                              {item.unite || 'u'}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right text-slate-300">
                          {numberFormatter.format(item.prix_achat || 0)}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-white">
                          {numberFormatter.format((item.prix_achat || 0) * item.quantite_commande)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        {/* Delivery options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">
              Mode de livraison
            </label>
            <div className="space-y-2">
              {ORDER_DELIVERY_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                    delivery === option.value
                      ? 'bg-blue-500/10 border-blue-500/30'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <input
                    type="radio"
                    name="delivery"
                    value={option.value}
                    checked={delivery === option.value}
                    onChange={(e) => setDelivery(e.target.value)}
                    className="sr-only"
                  />
                  <div
                    className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                      delivery === option.value
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-white/30'
                    }`}
                  >
                    {delivery === option.value && (
                      <div className="w-1.5 h-1.5 rounded-full bg-white" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-white">{option.label}</p>
                    <p className="text-xs text-slate-500">{option.days}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="deliveryDate" className="block text-sm font-medium text-slate-300">
                <Calendar className="w-4 h-4 inline mr-1.5" />
                Date de livraison souhaitée
              </label>
              <input
                type="date"
                id="deliveryDate"
                value={deliveryDate}
                onChange={(e) => setDeliveryDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="notes" className="block text-sm font-medium text-slate-300">
                <Edit3 className="w-4 h-4 inline mr-1.5" />
                Notes pour le fournisseur
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Instructions particulières..."
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
              />
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-3 gap-4 p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{includedItems.length}</p>
            <p className="text-xs text-slate-500">Articles</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-white">
              {quantityFormatter.format(totals.units)}
            </p>
            <p className="text-xs text-slate-500">Unités</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-emerald-400">
              {numberFormatter.format(totals.value)}
            </p>
            <p className="text-xs text-slate-500">Total HT</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-white/10 mt-4">
        <div className="flex gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleSendEmail}
            disabled={includedItems.length === 0}
          >
            <Mail className="w-4 h-4" />
            Email
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => window.print()}
            disabled={includedItems.length === 0}
          >
            <Printer className="w-4 h-4" />
            Imprimer
          </Button>
        </div>
        <div className="flex gap-3">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Annuler
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleConfirm}
            disabled={isGenerating || includedItems.length === 0}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Génération...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Télécharger le bon
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
