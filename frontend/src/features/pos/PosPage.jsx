import { Trash2 } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useProducts } from '../../hooks/useProducts.js';
import { useCheckout } from '../../hooks/useCheckout.js';
import { useState, useMemo, useCallback } from 'react';
import BarcodeScannerPanel from './BarcodeScannerPanel.jsx';

export default function PosPage() {
  const { data: products = [], isLoading } = useProducts();
  const checkout = useCheckout();

  const [selectedId, setSelectedId] = useState('');
  const [qty, setQty] = useState(1);
  const [cart, setCart] = useState([]);
  const [autoAddFromScanner, setAutoAddFromScanner] = useState(true);
  const [paymentMethod, setPaymentMethod] = useState('cb');
  const [discountPercent, setDiscountPercent] = useState(0);
  const [notes, setNotes] = useState('');
  const [lastScannedProduct, setLastScannedProduct] = useState(null);

  const sortedProducts = useMemo(
    () => [...products].sort((a, b) => a.nom.localeCompare(b.nom)),
    [products],
  );

  const selectedProduct = sortedProducts.find((product) => String(product.id) === selectedId);

  const addOrUpdateCart = useCallback((product, quantity) => {
    if (!product || quantity <= 0) return;
    setCart((previous) => {
      const existing = previous.find((line) => line.id === product.id);
      if (existing) {
        return previous.map((line) =>
          line.id === product.id ? { ...line, qty: line.qty + quantity } : line,
        );
      }
      return [
        ...previous,
        {
          id: product.id,
          nom: product.nom,
          prix_vente: product.prix_vente,
          tva: product.tva ?? 0,
          qty: quantity,
          stock: product.stock_actuel ?? null,
        },
      ];
    });
  }, []);

  const cartTotals = cart.reduce(
    (totals, line) => {
      const rate = (line.tva ?? 0) / 100;
      const unitTtc = line.prix_vente || 0;
      const unitHt = rate > -0.99 ? unitTtc / (1 + rate) : unitTtc;
      const lineHt = unitHt * line.qty;
      const lineTtc = unitTtc * line.qty;
      return {
        ht: totals.ht + lineHt,
        ttc: totals.ttc + lineTtc,
      };
    },
    { ht: 0, ttc: 0 },
  );
  const totalHt = cartTotals.ht;
  const grossTotal = cartTotals.ttc;
  const totalTva = Math.max(grossTotal - totalHt, 0);
  const safeDiscountPercent = Math.min(Math.max(discountPercent, 0), 100);
  const discountAmount = (grossTotal * safeDiscountPercent) / 100;
  const totalDue = Math.max(grossTotal - discountAmount, 0);

  const handleAdd = () => {
    if (!selectedProduct || qty <= 0) return;
    addOrUpdateCart(selectedProduct, qty);
    setQty(1);
  };

  const handleProductScanned = useCallback(
    (product, autoAdd) => {
      if (!product) {
        setLastScannedProduct(null);
        return;
      }
      setLastScannedProduct(product);
      setSelectedId(String(product.id));
      if (autoAdd) {
        addOrUpdateCart(product, 1);
      } else {
        setQty(1);
      }
    },
    [addOrUpdateCart],
  );

  const handleCheckout = () => {
    checkout.mutate({
      cart: cart.map((item) => ({
        id: item.id,
        qty: item.qty,
        nom: item.nom,
        prix_vente: item.prix_vente,
        tva: item.tva,
      })),
      username: 'spa-user',
    });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="flex flex-col gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">caisse rapide</p>
          <h2 className="text-2xl font-semibold text-slate-900">Ajouter un article</h2>
        </div>
        <div className="flex flex-col gap-4">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Produit
          </label>
          <select
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-brand-400 focus:outline-none"
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value)}
            disabled={isLoading}
          >
            <option value="">Sélectionner un produit…</option>
            {sortedProducts.map((product) => (
              <option key={product.id} value={product.id}>
                {product.nom} · {product.prix_vente.toFixed(2)} € TTC ·{' '}
                {(product.stock_actuel ?? 0).toLocaleString('fr-FR')} u
              </option>
            ))}
          </select>
          {selectedProduct && (
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-600">
              <p>
                Stock disponible :{' '}
                <span className="font-semibold text-slate-900">
                  {(selectedProduct.stock_actuel ?? 0).toLocaleString('fr-FR')} unités
                </span>
              </p>
              <p>
                Prix vente TTC :{' '}
                <span className="font-semibold text-slate-900">
                  {selectedProduct.prix_vente.toFixed(2)} €
                </span>
              </p>
              <p>
                TVA :{' '}
                <span className="font-semibold text-slate-900">
                  {(selectedProduct.tva ?? 0).toFixed(2)} %
                </span>
              </p>
            </div>
          )}
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Quantité
          </label>
          <input
            type="number"
            min="1"
            className="w-32 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-brand-400 focus:outline-none"
            value={qty}
            onChange={(event) => setQty(Number(event.target.value))}
          />
          <Button
            size="lg"
            variant="brand"
            onClick={handleAdd}
            disabled={!selectedProduct}
          >
            Ajouter au panier
          </Button>
        </div>
      </Card>

      <BarcodeScannerPanel
        autoAddEnabled={autoAddFromScanner}
        onProductDetected={handleProductScanned}
      />
      <Card className="flex flex-wrap items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={autoAddFromScanner}
            onChange={(event) => setAutoAddFromScanner(event.target.checked)}
          />
          Ajouter automatiquement 1 unité par scan
        </label>
        {lastScannedProduct && (
          <p className="text-sm text-slate-500">
            Dernier article :{' '}
            <span className="font-semibold text-slate-900">{lastScannedProduct.nom}</span>
          </p>
        )}
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">panier</p>
            <h3 className="text-xl font-semibold text-slate-900">Vente en cours</h3>
          </div>
          {cart.length > 0 && (
            <Button variant="ghost" onClick={() => setCart([])}>
              Vider
            </Button>
          )}
        </div>

        {cart.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
            Ajoutez vos premiers articles pour lancer l&apos;encaissement.
          </p>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-100">
            <table className="w-full divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-widest text-slate-500">
                <tr>
                  <th className="px-4 py-3">Article</th>
                  <th className="px-4 py-3">Stock</th>
                  <th className="px-4 py-3">Qté</th>
                  <th className="px-4 py-3">Prix TTC</th>
                  <th className="px-4 py-3 text-right">Total</th>
                  <th />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {cart.map((item) => (
                  <tr key={item.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{item.nom}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {item.stock !== null && item.stock !== undefined
                        ? `${item.stock} u`
                        : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <input
                        type="number"
                        min="1"
                        value={item.qty}
                        onChange={(event) =>
                          setCart((previous) =>
                            previous.map((line) =>
                              line.id === item.id
                                ? { ...line, qty: Number(event.target.value) }
                                : line,
                            ),
                          )
                        }
                        className="w-20 rounded-xl border border-slate-200 px-3 py-1.5 text-sm focus:border-brand-400 focus:outline-none"
                      />
                      {item.stock !== null && item.stock !== undefined && item.qty > item.stock && (
                        <p className="text-xs text-rose-600">Au-delà du stock</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {item.prix_vente.toFixed(2)} € TTC
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-slate-900">
                      {(item.prix_vente * item.qty).toFixed(2)} €
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        onClick={() =>
                          setCart((previous) => previous.filter((line) => line.id !== item.id))
                        }
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <div className="flex items-center justify-between text-sm text-slate-600">
            <p>Total HT</p>
            <p className="font-semibold text-slate-900">{totalHt.toFixed(2)} €</p>
          </div>
          <div className="mt-1 flex items-center justify-between text-sm text-slate-600">
            <p>TVA (moy.)</p>
            <p className="font-semibold text-slate-900">{totalTva.toFixed(2)} €</p>
          </div>
          <div className="mt-1 flex items-center justify-between text-sm text-slate-600">
            <p>Remise ({safeDiscountPercent.toFixed(1)} %)</p>
            <p className="font-semibold text-rose-600">- {discountAmount.toFixed(2)} €</p>
          </div>
          <div className="mt-3 flex items-center justify-between text-lg font-semibold text-slate-900">
            <p>Total TTC</p>
            <p>{totalDue.toFixed(2)} €</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-600">
            Mode de paiement
            <select
              value={paymentMethod}
              onChange={(event) => setPaymentMethod(event.target.value)}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            >
              <option value="cb">Carte bancaire</option>
              <option value="cash">Espèces</option>
              <option value="cheque">Chèque</option>
              <option value="transfer">Virement</option>
            </select>
          </label>
          <label className="text-sm text-slate-600">
            Remise %
            <input
              type="number"
              min="0"
              max="100"
              step="0.5"
              value={discountPercent}
              onChange={(event) => setDiscountPercent(Number(event.target.value))}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            />
          </label>
        </div>
        <label className="text-sm text-slate-600">
          Notes de caisse
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={3}
            className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            placeholder="Client régulier, glisser la carte fidélité, etc."
          />
        </label>

        <Button
          size="lg"
          variant="brand"
          disabled={cart.length === 0 || checkout.isLoading}
          onClick={handleCheckout}
        >
          Finaliser la vente
        </Button>
      </Card>
    </div>
  );
}
