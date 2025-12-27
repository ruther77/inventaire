import { useState, useCallback, useMemo } from 'react';
import { Package, Minus, Plus, ArrowRight, Loader2, AlertTriangle, Check } from 'lucide-react';
import Modal from '@/components/ui/Modal.jsx';
import Button from '@/components/ui/Button.jsx';
import { useStockAdjustment } from '@/hooks/useStock.js';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const ADJUSTMENT_REASONS = [
  { value: 'inventory', label: 'Inventaire physique' },
  { value: 'loss', label: 'Perte / Casse' },
  { value: 'theft', label: 'Vol / Disparition' },
  { value: 'expiry', label: 'Péremption' },
  { value: 'transfer', label: 'Transfert' },
  { value: 'correction', label: 'Correction d\'erreur' },
  { value: 'other', label: 'Autre' },
];

export default function StockAdjustmentModal({
  open,
  onClose,
  product,
  onSuccess
}) {
  const [mode, setMode] = useState('set'); // 'set', 'add', 'remove'
  const [quantity, setQuantity] = useState('');
  const [reason, setReason] = useState('inventory');
  const [note, setNote] = useState('');
  const [error, setError] = useState('');

  const queryClient = useQueryClient();
  const stockAdjustment = useStockAdjustment();

  const currentStock = product?.stock_actuel ?? 0;
  const unit = product?.unite ?? 'unit';

  const newStock = useMemo(() => {
    const qty = parseFloat(quantity) || 0;
    switch (mode) {
      case 'add':
        return currentStock + qty;
      case 'remove':
        return Math.max(0, currentStock - qty);
      case 'set':
      default:
        return qty;
    }
  }, [mode, quantity, currentStock]);

  const difference = newStock - currentStock;

  const handleQuantityChange = useCallback((value) => {
    const sanitized = value.replace(/[^0-9.]/g, '');
    // Only allow one decimal point
    const parts = sanitized.split('.');
    const cleaned = parts.length > 2 ? parts[0] + '.' + parts.slice(1).join('') : sanitized;
    setQuantity(cleaned);
    setError('');
  }, []);

  const incrementQuantity = useCallback(() => {
    const current = parseFloat(quantity) || 0;
    setQuantity(String(current + 1));
    setError('');
  }, [quantity]);

  const decrementQuantity = useCallback(() => {
    const current = parseFloat(quantity) || 0;
    if (current > 0) {
      setQuantity(String(Math.max(0, current - 1)));
    }
    setError('');
  }, [quantity]);

  const validate = useCallback(() => {
    if (!quantity || parseFloat(quantity) < 0) {
      setError('Quantité invalide');
      return false;
    }

    if (mode === 'remove' && parseFloat(quantity) > currentStock) {
      setError(`Quantité à retirer supérieure au stock actuel (${currentStock} ${unit})`);
      return false;
    }

    if (mode === 'set' && parseFloat(quantity) === currentStock) {
      setError('Le nouveau stock est identique au stock actuel');
      return false;
    }

    return true;
  }, [quantity, mode, currentStock, unit]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    if (!validate()) return;

    stockAdjustment.mutate(
      {
        productId: product.id,
        targetQuantity: newStock,
        username: 'admin', // TODO: Get from auth context
      },
      {
        onSuccess: () => {
          toast.success(
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400" />
              <span>Stock mis à jour: {currentStock} → {newStock} {unit}</span>
            </div>
          );
          queryClient.invalidateQueries({ queryKey: ['products'] });
          queryClient.invalidateQueries({ queryKey: ['stock-timeseries'] });
          queryClient.invalidateQueries({ queryKey: ['stock-recent'] });
          onSuccess?.();
          handleClose();
        },
        onError: (err) => {
          toast.error('Erreur lors de l\'ajustement du stock');
          setError(err.message || 'Une erreur est survenue');
        },
      }
    );
  }, [validate, stockAdjustment, product?.id, newStock, currentStock, unit, queryClient, onSuccess]);

  const handleClose = useCallback(() => {
    setQuantity('');
    setMode('set');
    setReason('inventory');
    setNote('');
    setError('');
    onClose();
  }, [onClose]);

  if (!product) return null;

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Ajustement de stock"
      description={`${product.nom} - Stock actuel: ${currentStock} ${unit}`}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Product info card */}
        <div className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
            <Package className="w-6 h-6 text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-white truncate">{product.nom}</p>
            <p className="text-sm text-slate-400">{product.categorie}</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-white">{currentStock}</p>
            <p className="text-sm text-slate-400">{unit}</p>
          </div>
        </div>

        {/* Mode selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-300">
            Type d'ajustement
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { value: 'set', label: 'Définir', icon: '=' },
              { value: 'add', label: 'Ajouter', icon: '+' },
              { value: 'remove', label: 'Retirer', icon: '-' },
            ].map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => { setMode(option.value); setError(''); }}
                className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border transition-all ${
                  mode === option.value
                    ? 'bg-blue-500/20 border-blue-500/50 text-blue-400'
                    : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
                }`}
              >
                <span className="text-lg font-mono">{option.icon}</span>
                <span className="text-sm font-medium">{option.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Quantity input */}
        <div className="space-y-2">
          <label htmlFor="quantity" className="block text-sm font-medium text-slate-300">
            {mode === 'set' ? 'Nouveau stock' : mode === 'add' ? 'Quantité à ajouter' : 'Quantité à retirer'}
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={decrementQuantity}
              disabled={mode === 'set' && (parseFloat(quantity) || 0) <= 0}
              className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all"
            >
              <Minus className="w-5 h-5" />
            </button>
            <input
              type="text"
              id="quantity"
              inputMode="decimal"
              value={quantity}
              onChange={(e) => handleQuantityChange(e.target.value)}
              placeholder="0"
              className={`flex-1 px-4 py-3 rounded-xl bg-white/5 border ${
                error ? 'border-rose-500' : 'border-white/10'
              } text-white text-center text-xl font-semibold placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all`}
            />
            <button
              type="button"
              onClick={incrementQuantity}
              className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 flex items-center justify-center transition-all"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
          {error && (
            <p className="text-sm text-rose-400 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              {error}
            </p>
          )}
        </div>

        {/* Preview */}
        {quantity && !error && (
          <div className={`flex items-center justify-center gap-4 p-4 rounded-xl border ${
            difference > 0
              ? 'bg-emerald-500/10 border-emerald-500/30'
              : difference < 0
                ? 'bg-rose-500/10 border-rose-500/30'
                : 'bg-white/5 border-white/10'
          }`}>
            <div className="text-center">
              <p className="text-sm text-slate-400">Avant</p>
              <p className="text-xl font-bold text-white">{currentStock}</p>
            </div>
            <ArrowRight className={`w-5 h-5 ${
              difference > 0 ? 'text-emerald-400' : difference < 0 ? 'text-rose-400' : 'text-slate-400'
            }`} />
            <div className="text-center">
              <p className="text-sm text-slate-400">Après</p>
              <p className={`text-xl font-bold ${
                difference > 0 ? 'text-emerald-400' : difference < 0 ? 'text-rose-400' : 'text-white'
              }`}>
                {newStock}
              </p>
            </div>
            <div className="pl-4 border-l border-white/10 text-center">
              <p className="text-sm text-slate-400">Diff</p>
              <p className={`text-xl font-bold ${
                difference > 0 ? 'text-emerald-400' : difference < 0 ? 'text-rose-400' : 'text-slate-400'
              }`}>
                {difference > 0 ? '+' : ''}{difference.toFixed(2)}
              </p>
            </div>
          </div>
        )}

        {/* Reason */}
        <div className="space-y-2">
          <label htmlFor="reason" className="block text-sm font-medium text-slate-300">
            Motif
          </label>
          <select
            id="reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all appearance-none cursor-pointer"
          >
            {ADJUSTMENT_REASONS.map((r) => (
              <option key={r.value} value={r.value} className="bg-slate-800">
                {r.label}
              </option>
            ))}
          </select>
        </div>

        {/* Note */}
        <div className="space-y-2">
          <label htmlFor="note" className="block text-sm font-medium text-slate-300">
            Note (optionnel)
          </label>
          <textarea
            id="note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            placeholder="Ajouter une note..."
            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={stockAdjustment.isPending || !quantity || !!error}
          >
            {stockAdjustment.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Mise à jour...
              </>
            ) : (
              'Confirmer l\'ajustement'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
