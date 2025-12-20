/**
 * PurchaseOrderModal - Generation de bon de commande (S2 - Alerte Stock)
 *
 * Modal de creation de commande pre-remplie:
 * - Selection fournisseur avec scoring
 * - Quantite basee sur EOQ
 * - Estimation cout et delai
 * - Validation et envoi
 */

import { useState, useEffect, useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShoppingCart,
  Truck,
  Package,
  Calendar,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Star,
  ChevronDown,
  FileText,
  Send,
  X,
  Plus,
  Minus,
  Info,
} from 'lucide-react';
import Modal from '../../components/ui/Modal.jsx';
import Button from '../../components/ui/Button.jsx';
import Card from '../../components/ui/Card.jsx';
import api from '../../api/client.js';

// ===========================================================================
// API Functions
// ===========================================================================

const fetchSuppliers = async () => {
  const { data } = await api.get('/catalog/vendors');
  return data;
};

const fetchSupplierScore = async (supplierId) => {
  try {
    const { data } = await api.get(`/supplier-scoring/scores/${supplierId}`);
    return data;
  } catch {
    return null;
  }
};

const createPurchaseOrder = async (orderData) => {
  const { data } = await api.post('/supply/orders', orderData);
  return data;
};

// ===========================================================================
// Sub-components
// ===========================================================================

function SupplierOption({ supplier, selected, onSelect, score }) {
  const gradeColors = {
    A: 'text-emerald-400 bg-emerald-500/20',
    B: 'text-blue-400 bg-blue-500/20',
    C: 'text-amber-400 bg-amber-500/20',
    D: 'text-orange-400 bg-orange-500/20',
    F: 'text-rose-400 bg-rose-500/20',
  };

  const grade = score?.grade || 'B';

  return (
    <motion.button
      type="button"
      onClick={() => onSelect(supplier)}
      className={`w-full p-4 rounded-xl border text-left transition-all ${
        selected
          ? 'border-cyan-500 bg-cyan-500/10'
          : 'border-white/10 bg-white/5 hover:border-white/20'
      }`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg ${gradeColors[grade]} flex items-center justify-center font-bold`}>
            {grade}
          </div>
          <div>
            <p className="font-medium text-white">{supplier.name || supplier.nom}</p>
            <p className="text-sm text-slate-400">
              Score: {score?.overall_score?.toFixed(1) || 'N/A'}/10
            </p>
          </div>
        </div>

        {selected && (
          <div className="w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center">
            <CheckCircle className="w-4 h-4 text-white" />
          </div>
        )}
      </div>

      <div className="flex gap-4 mt-3 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <Truck className="w-3 h-3" />
          Delai: {supplier.delivery_days || 3}j
        </span>
        <span className="flex items-center gap-1">
          <Package className="w-3 h-3" />
          Min: {supplier.min_order || 1} u
        </span>
      </div>
    </motion.button>
  );
}

function QuantitySelector({ value, onChange, min = 1, max = 9999, eoqSuggestion }) {
  const presets = useMemo(() => {
    const base = eoqSuggestion || 50;
    return [
      { label: 'Min', value: min },
      { label: 'EOQ', value: base, recommended: true },
      { label: 'x1.5', value: Math.round(base * 1.5) },
      { label: 'x2', value: base * 2 },
    ];
  }, [eoqSuggestion, min]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => onChange(Math.max(min, value - 10))}
          className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition"
        >
          <Minus className="w-4 h-4 text-slate-400" />
        </button>

        <input
          type="number"
          value={value}
          onChange={(e) => onChange(Math.max(min, Math.min(max, parseInt(e.target.value) || min)))}
          className="w-24 text-center text-2xl font-semibold bg-white/5 border border-white/10 rounded-lg py-2 text-white focus:border-cyan-500 focus:outline-none"
        />

        <button
          type="button"
          onClick={() => onChange(Math.min(max, value + 10))}
          className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition"
        >
          <Plus className="w-4 h-4 text-slate-400" />
        </button>

        <span className="text-slate-400">unites</span>
      </div>

      <div className="flex gap-2">
        {presets.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => onChange(preset.value)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              value === preset.value
                ? 'bg-cyan-500 text-white'
                : preset.recommended
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'bg-white/5 text-slate-400 hover:bg-white/10'
            }`}
          >
            {preset.label}
            {preset.recommended && <Star className="w-3 h-3 inline ml-1" />}
          </button>
        ))}
      </div>
    </div>
  );
}

function OrderSummary({ product, supplier, quantity, unitPrice }) {
  const totalHT = quantity * unitPrice;
  const tva = totalHT * ((product?.tva || 20) / 100);
  const totalTTC = totalHT + tva;

  return (
    <Card className="border-white/10 bg-white/5">
      <h4 className="font-medium text-white mb-4">Recapitulatif</h4>

      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Produit</span>
          <span className="text-white">{product?.nom || 'N/A'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Fournisseur</span>
          <span className="text-white">{supplier?.name || supplier?.nom || 'N/A'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Quantite</span>
          <span className="text-white">{quantity} u</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Prix unitaire</span>
          <span className="text-white">{unitPrice.toFixed(2)} EUR</span>
        </div>

        <div className="border-t border-white/10 pt-3 mt-3">
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">Total HT</span>
            <span className="text-white">{totalHT.toFixed(2)} EUR</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">TVA ({product?.tva || 20}%)</span>
            <span className="text-white">{tva.toFixed(2)} EUR</span>
          </div>
          <div className="flex justify-between mt-2 pt-2 border-t border-white/10">
            <span className="font-medium text-white">Total TTC</span>
            <span className="font-bold text-lg text-cyan-400">{totalTTC.toFixed(2)} EUR</span>
          </div>
        </div>

        {supplier && (
          <div className="flex items-center gap-2 mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <Calendar className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-blue-400">
              Livraison estimee: {supplier.delivery_days || 3} jours
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}

// ===========================================================================
// Main Component
// ===========================================================================

export default function PurchaseOrderModal({
  isOpen,
  onClose,
  product,
  eoqSuggestion,
  preselectedSupplier,
}) {
  const queryClient = useQueryClient();

  // State
  const [selectedSupplier, setSelectedSupplier] = useState(preselectedSupplier || null);
  const [quantity, setQuantity] = useState(eoqSuggestion?.optimal_quantity || 50);
  const [notes, setNotes] = useState('');
  const [urgency, setUrgency] = useState('normal');

  // Queries
  const suppliersQuery = useQuery({
    queryKey: ['suppliers'],
    queryFn: fetchSuppliers,
    enabled: isOpen,
  });

  const supplierScoreQuery = useQuery({
    queryKey: ['supplier-score', selectedSupplier?.id],
    queryFn: () => fetchSupplierScore(selectedSupplier?.id),
    enabled: !!selectedSupplier?.id,
  });

  // Mutation
  const createOrderMutation = useMutation({
    mutationFn: createPurchaseOrder,
    onSuccess: () => {
      queryClient.invalidateQueries(['purchase-orders']);
      onClose();
    },
  });

  // Effects
  useEffect(() => {
    if (preselectedSupplier) {
      setSelectedSupplier(preselectedSupplier);
    }
  }, [preselectedSupplier]);

  useEffect(() => {
    if (eoqSuggestion?.optimal_quantity) {
      setQuantity(eoqSuggestion.optimal_quantity);
    }
  }, [eoqSuggestion]);

  // Derived
  const suppliers = suppliersQuery.data || [];
  const unitPrice = product?.prix_achat || selectedSupplier?.price || 10;

  // Handlers
  const handleSubmit = () => {
    if (!selectedSupplier || !product) return;

    createOrderMutation.mutate({
      product_id: product.id,
      supplier_id: selectedSupplier.id,
      quantity,
      unit_price: unitPrice,
      notes,
      urgency,
      status: 'draft',
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Creer un bon de commande"
      size="xl"
    >
      <div className="space-y-6">
        {/* Product info */}
        <div className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center">
            <Package className="w-6 h-6 text-cyan-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-white">{product?.nom || 'Produit'}</h3>
            <p className="text-sm text-slate-400">
              Stock actuel: {product?.stock_actuel || 0} u | Seuil: {product?.seuil_alerte || 10} u
            </p>
          </div>
          {product?.stock_actuel < (product?.seuil_alerte || 10) && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-amber-500/20 text-amber-400 border border-amber-500/30">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              Stock critique
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left column */}
          <div className="space-y-6">
            {/* Supplier selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Fournisseur
              </label>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                {suppliers.map((supplier) => (
                  <SupplierOption
                    key={supplier.id}
                    supplier={supplier}
                    selected={selectedSupplier?.id === supplier.id}
                    onSelect={setSelectedSupplier}
                    score={selectedSupplier?.id === supplier.id ? supplierScoreQuery.data : null}
                  />
                ))}
                {suppliers.length === 0 && (
                  <p className="text-center py-4 text-slate-500">Aucun fournisseur disponible</p>
                )}
              </div>
            </div>

            {/* Quantity */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Quantite a commander
              </label>
              <QuantitySelector
                value={quantity}
                onChange={setQuantity}
                min={selectedSupplier?.min_order || 1}
                eoqSuggestion={eoqSuggestion?.optimal_quantity}
              />
            </div>

            {/* Urgency */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Urgence
              </label>
              <div className="flex gap-2">
                {[
                  { id: 'low', label: 'Basse', color: 'text-slate-400 border-white/10' },
                  { id: 'normal', label: 'Normale', color: 'text-blue-400 border-blue-500/30' },
                  { id: 'high', label: 'Haute', color: 'text-amber-400 border-amber-500/30' },
                  { id: 'critical', label: 'Critique', color: 'text-rose-400 border-rose-500/30' },
                ].map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => setUrgency(option.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium border transition ${
                      urgency === option.id
                        ? `${option.color} bg-white/10`
                        : 'text-slate-500 border-white/10 hover:border-white/20'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Notes (optionnel)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none resize-none"
                placeholder="Instructions particulieres..."
              />
            </div>
          </div>

          {/* Right column - Summary */}
          <div>
            <OrderSummary
              product={product}
              supplier={selectedSupplier}
              quantity={quantity}
              unitPrice={unitPrice}
            />

            {/* EOQ Info */}
            {eoqSuggestion && (
              <div className="mt-4 p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-cyan-400 mt-0.5" />
                  <div>
                    <p className="font-medium text-cyan-400">Recommandation EOQ</p>
                    <p className="text-sm text-slate-400 mt-1">
                      La quantite economique optimale est de {eoqSuggestion.optimal_quantity} unites,
                      ce qui minimise vos couts de stockage et de commande.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              // Save as draft
              handleSubmit();
            }}
            disabled={!selectedSupplier || createOrderMutation.isPending}
          >
            <FileText className="w-4 h-4" />
            Enregistrer brouillon
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={!selectedSupplier || createOrderMutation.isPending}
            loading={createOrderMutation.isPending}
          >
            <Send className="w-4 h-4" />
            Creer la commande
          </Button>
        </div>
      </div>
    </Modal>
  );
}
