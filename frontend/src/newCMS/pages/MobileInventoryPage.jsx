/**
 * Mobile Inventory Page - Scanner et Ajustement Rapide (Scénario 3.8)
 * Vue mobile optimisée pour inventaire terrain
 */

import { useMemo, useState } from 'react';
import {
  Package,
  Camera,
  Flashlight,
  FileText,
  AlertTriangle,
  Check,
  ChevronRight,
  Minus,
  Plus,
  X,
  RotateCcw,
  Clock,
  Eye,
  Gauge,
  BarChart3,
} from 'lucide-react';
import { useNewCMSQuery } from '../hooks/useNewCMSQuery.js';
import { fetchMobileInventory } from '../../api/newcms.js';

// Mobile Header
function MobileHeader() {
  return (
    <div className="flex items-center justify-between p-4 bg-slate-900/80 backdrop-blur-lg border-b border-white/10">
      <div className="flex items-center gap-2">
        <span className="text-lg">🏪</span>
        <span className="font-medium text-white">Épicerie</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-400">📅 Déc</span>
        <div className="relative">
          <span className="text-sm text-white">🔔</span>
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-[10px] text-white flex items-center justify-center">3</span>
        </div>
      </div>
    </div>
  );
}

// Inventory Progress Card
function InventoryProgress({ scanned = 0, total = 0 }) {
  const percent = total > 0 ? Math.round((scanned / total) * 100) : 0;

  return (
    <div className="p-4 rounded-xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-3">
        <Package className="w-5 h-5 text-blue-400" />
        <span className="font-medium text-white">MODE INVENTAIRE</span>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-slate-400">Produits scannés:</span>
            <span className="text-white font-medium">{scanned}/{total}</span>
          </div>
          <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all"
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="text-right text-xs text-slate-500 mt-1">{percent}%</div>
        </div>

        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-400" />
            <span className="text-slate-400">Temps:</span>
            <span className="text-white">23 min</span>
          </div>
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-slate-400" />
            <span className="text-slate-400">Rythme:</span>
            <span className="text-white">2.0 prod/min</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Scanner Component
function Scanner() {
  return (
    <div className="p-4 rounded-xl bg-slate-800/50 border border-white/10">
      <div className="aspect-[4/3] rounded-xl bg-slate-900 border-2 border-dashed border-slate-600 flex flex-col items-center justify-center mb-4">
        {/* Barcode visualization */}
        <div className="w-48 h-24 rounded-lg bg-slate-800 flex flex-col items-center justify-center mb-4">
          <div className="flex gap-[2px] h-12 mb-2">
            {[...Array(30)].map((_, i) => (
              <div
                key={i}
                className="bg-white"
                style={{ width: i % 3 === 0 ? '3px' : '2px', opacity: 0.7 }}
              />
            ))}
          </div>
          <div className="h-px w-48 bg-red-500/50" />
        </div>

        <div className="flex items-center gap-2 text-slate-400">
          <Camera className="w-5 h-5" />
          <span className="text-sm">Scanner code-barre</span>
        </div>
      </div>

      <div className="flex gap-2">
        <button className="flex-1 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center justify-center gap-2">
          <Flashlight className="w-4 h-4" /> Lampe
        </button>
        <button className="flex-1 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center justify-center gap-2">
          <FileText className="w-4 h-4" /> Manuel
        </button>
      </div>
    </div>
  );
}

// Inventory List
function InventoryList({ items, loading }) {
  const display = items?.length
    ? items
    : [
        { name: 'Tomates 1kg', stock: 12.5, unit: 'kg', alert: false },
        { name: 'Huile Olive 1L', stock: 3, unit: 'u', alert: true },
        { name: 'Mozzarella', stock: 8, unit: 'u', alert: false },
        { name: 'Pain burger', stock: 24, unit: 'u', alert: false },
        { name: 'Steak 180g', stock: 6, unit: 'u', alert: true },
      ];

  return (
    <div className="p-4 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-3">
        <Package className="w-4 h-4 text-blue-400" />
        <span className="font-medium text-white text-sm">INVENTAIRE RAPIDE</span>
      </div>
      {loading && (
        <div className="space-y-2">
          {[...Array(4)].map((_, idx) => (
            <div key={idx} className="h-12 rounded-lg bg-white/5 animate-pulse" />
          ))}
        </div>
      )}
      {!loading && (
        <div className="space-y-2">
          {display.map((item, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border ${
                item.alert ? 'border-amber-500/30 bg-amber-500/10' : 'border-white/10 bg-white/5'
              }`}
            >
              <div className="flex items-center justify-between text-sm">
                <span className="text-white">{item.name}</span>
                <span className="font-semibold text-white">{item.stock} {item.unit}</span>
              </div>
              {item.alert && <p className="text-xs text-amber-300 mt-1">Sous seuil d’alerte</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Last Scanned Product
function LastScannedProduct() {
  const [count, setCount] = useState(23);
  const systemStock = 23;

  return (
    <div className="p-4 rounded-xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-3">
        <BarChart3 className="w-4 h-4 text-blue-400" />
        <span className="font-medium text-white text-sm">DERNIER SCANNÉ</span>
      </div>

      <div className="space-y-3">
        <div>
          <h4 className="font-medium text-white">Riz Basmati 5kg</h4>
          <p className="text-xs text-slate-500 font-mono">Code: 3700123456789</p>
        </div>

        <div className="p-3 rounded-lg bg-slate-700/50">
          <div className="flex justify-between text-sm mb-3">
            <span className="text-slate-400">Stock système:</span>
            <span className="text-white">{systemStock}</span>
          </div>

          <div>
            <span className="text-sm text-slate-400">Stock compté:</span>
            <div className="flex items-center gap-3 mt-2">
              <button
                onClick={() => setCount(c => c - 1)}
                className="w-12 h-12 rounded-xl bg-slate-600 text-white flex items-center justify-center text-xl font-bold hover:bg-slate-500 transition-colors"
              >
                −
              </button>
              <input
                type="text"
                value={count}
                onChange={(e) => setCount(parseInt(e.target.value) || 0)}
                className="flex-1 h-12 rounded-xl bg-slate-800 border border-white/20 text-center text-2xl font-bold text-white"
              />
              <button
                onClick={() => setCount(c => c + 1)}
                className="w-12 h-12 rounded-xl bg-slate-600 text-white flex items-center justify-center text-xl font-bold hover:bg-slate-500 transition-colors"
              >
                +
              </button>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button className="flex-1 py-3 rounded-xl bg-emerald-500 text-white font-medium flex items-center justify-center gap-2">
            <Check className="w-5 h-5" /> Confirmer
          </button>
          <button className="py-3 px-4 rounded-xl bg-white/10 text-slate-300">
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Detected Gaps Card
function DetectedGaps() {
  const gaps = [
    { product: 'Café Moulu', diff: -5 },
    { product: 'Sucre 1kg', diff: +12 },
    { product: 'Huile Olive', diff: -2 },
  ];

  return (
    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span className="font-medium text-white text-sm">ÉCARTS DÉTECTÉS ({gaps.length})</span>
        </div>
      </div>

      <div className="space-y-2 mb-3">
        {gaps.map((gap, idx) => (
          <div key={idx} className="flex items-center justify-between text-sm">
            <span className="text-slate-300">• {gap.product}:</span>
            <span className={gap.diff < 0 ? 'text-rose-400' : 'text-emerald-400'}>
              {gap.diff > 0 ? '+' : ''}{gap.diff} unités
            </span>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <button className="flex-1 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center justify-center gap-2">
          <Eye className="w-4 h-4" /> Voir tous
        </button>
        <button className="flex-1 py-2 rounded-lg bg-amber-500 text-white text-sm flex items-center justify-center gap-2">
          <Check className="w-4 h-4" /> Valider
        </button>
      </div>
    </div>
  );
}

// Gap Adjustment Modal
function GapAdjustmentModal({ onClose }) {
  const [reason, setReason] = useState('error');

  const reasons = [
    { id: 'breakage', label: 'Casse' },
    { id: 'theft', label: 'Vol suspecté' },
    { id: 'error', label: 'Erreur comptage précéd.' },
    { id: 'expired', label: 'Péremption/Retrait' },
    { id: 'other', label: 'Autre' },
  ];

  return (
    <div className="fixed inset-0 bg-black/80 flex items-end z-50">
      <div className="w-full bg-slate-900 rounded-t-3xl p-6 max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Package className="w-5 h-5 text-blue-400" />
            Ajustement Écart
          </h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Product Info */}
        <div className="mb-6">
          <h4 className="font-medium text-white mb-2">Café Moulu 250g</h4>
          <div className="p-3 rounded-xl bg-slate-800/50">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xs text-slate-500 mb-1">Stock système</div>
                <div className="text-lg font-bold text-white">13</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Stock compté</div>
                <div className="text-lg font-bold text-white">8</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Écart</div>
                <div className="text-lg font-bold text-rose-400">-5 ❗</div>
              </div>
            </div>
          </div>
        </div>

        {/* Reason Selection */}
        <div className="mb-6">
          <label className="text-sm text-slate-400 mb-2 block">Motif de l'écart:</label>
          <div className="space-y-2">
            {reasons.map((r) => (
              <label
                key={r.id}
                className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                  reason === r.id
                    ? 'bg-blue-500/20 border border-blue-500/30'
                    : 'bg-slate-800/50 border border-transparent'
                }`}
              >
                <input
                  type="radio"
                  name="reason"
                  value={r.id}
                  checked={reason === r.id}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-4 h-4 text-blue-500"
                />
                <span className="text-white">{r.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Note */}
        <div className="mb-6">
          <label className="text-sm text-slate-400 mb-2 block">Note (optionnel):</label>
          <textarea
            placeholder="Ajouter une note..."
            className="w-full p-3 rounded-xl bg-slate-800/50 border border-white/10 text-white placeholder-slate-500 resize-none h-20"
            defaultValue="Mauvais comptage rayon café le mois dernier"
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 rounded-xl bg-white/10 text-slate-300 font-medium"
          >
            ❌ Annuler
          </button>
          <button className="flex-1 py-3 rounded-xl bg-emerald-500 text-white font-medium flex items-center justify-center gap-2">
            <Check className="w-5 h-5" /> Valider écart
          </button>
        </div>
      </div>
    </div>
  );
}

// Mobile Bottom Nav
function MobileBottomNav() {
  const items = [
    { icon: '🎯', label: 'Cockpit' },
    { icon: '📦', label: 'Ops', active: true },
    { icon: '💰', label: 'Finance' },
    { icon: '🍽️', label: 'Resto' },
    { icon: '🧠', label: 'Intel' },
  ];

  return (
    <div className="flex justify-around p-3 bg-slate-900/90 backdrop-blur-lg border-t border-white/10">
      {items.map((item, idx) => (
        <button
          key={idx}
          className={`flex flex-col items-center gap-1 ${
            item.active ? 'text-blue-400' : 'text-slate-500'
          }`}
        >
          <span className="text-xl">{item.icon}</span>
          <span className="text-[10px]">{item.label}</span>
        </button>
      ))}
    </div>
  );
}

// Main Component
export default function MobileInventoryPage() {
  const [showGapModal, setShowGapModal] = useState(false);
  const inventoryQuery = useNewCMSQuery(['newcms-mobile-inventory'], () =>
    fetchMobileInventory({ page: 1, page_size: 50 })
  );
  const items = useMemo(() => {
    if (!inventoryQuery.data?.items) return null;
    return inventoryQuery.data.items.map((item) => ({
      name: item.nom,
      stock: item.stock_actuel,
      unit: item.categorie || 'u',
      alert: item.stock_actuel < item.seuil_alerte,
    }));
  }, [inventoryQuery.data]);
  const scanned = items?.length ?? 0;
  const total = inventoryQuery.data?.total ?? items?.length ?? 0;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Mobile Header */}
      <MobileHeader />

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 space-y-4 pb-20">
        {inventoryQuery.isError && (
          <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            Impossible de charger l'inventaire mobile (API newCMS). Affichage du fallback démo.
          </div>
        )}
        <InventoryProgress scanned={scanned} total={total} />
        <Scanner />
        <LastScannedProduct />
        <div onClick={() => setShowGapModal(true)}>
          <DetectedGaps />
        </div>
        <InventoryList items={items} loading={inventoryQuery.isLoading && !items} />
      </div>

      {/* Bottom Nav */}
      <MobileBottomNav />

      {/* Gap Modal */}
      {showGapModal && <GapAdjustmentModal onClose={() => setShowGapModal(false)} />}
    </div>
  );
}
