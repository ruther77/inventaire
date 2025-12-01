import { useMemo } from 'react';
import { useRestaurantConsumptions } from '../../hooks/useRestaurant.js';

const currency = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' });
const number = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function formatCurrency(value) {
  return currency.format(value ?? 0);
}

function formatNumber(value) {
  return number.format(value ?? 0);
}

export default function RestaurantConsumptionPage() {
  const { data = [], isLoading } = useRestaurantConsumptions();

  const totals = useMemo(
    () =>
      data.reduce(
        (acc, entry) => {
          acc.cost += entry.cost_spent || 0;
          acc.bottles += entry.bottles_required || 0;
          acc.quantity += entry.quantity_consumed || 0;
          return acc;
        },
        { cost: 0, bottles: 0, quantity: 0 },
      ),
    [data],
  );

  if (isLoading) {
    return <p className="text-sm text-slate-500">Chargement des consommations…</p>;
  }

  if (!data.length) {
    return <p className="text-sm text-slate-500">Aucune consommation restaurant enregistrée pour le moment.</p>;
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-500">Restaurant HQ</p>
        <h1 className="text-2xl font-bold text-slate-900">Consommations découlant des ventes</h1>
        <p className="text-sm text-slate-500">
          Le coût matière est calculé automatiquement via la correspondance plat → produit Épicerie HQ (ratio + prix d&apos;achat).
        </p>
        <dl className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
            <dt className="text-xs uppercase tracking-[0.3em] text-slate-400">Coût total</dt>
            <dd className="text-xl font-semibold text-slate-900">{formatCurrency(totals.cost)}</dd>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
            <dt className="text-xs uppercase tracking-[0.3em] text-slate-400">Bouteilles requises</dt>
            <dd className="text-xl font-semibold text-slate-900">{formatNumber(totals.bottles)}</dd>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
            <dt className="text-xs uppercase tracking-[0.3em] text-slate-400">Quantité totale</dt>
            <dd className="text-xl font-semibold text-slate-900">{formatNumber(totals.quantity)}</dd>
          </div>
        </dl>
      </header>

      <div className="overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Plat</th>
                <th className="px-4 py-3">Produit Épicerie</th>
                <th className="px-4 py-3">Catégorie</th>
                <th className="px-4 py-3 text-right">Qté consommée</th>
                <th className="px-4 py-3 text-right">Bouteilles</th>
                <th className="px-4 py-3 text-right">Coût</th>
                <th className="px-4 py-3 text-right">Stock après ventes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((entry) => (
                <tr key={`${entry.produit_restaurant_id}-${entry.produit_epicerie_id}`}>
                  <td className="px-4 py-3 font-medium text-slate-900">{entry.restaurant_plat ?? '—'}</td>
                  <td className="px-4 py-3">
                    {entry.epicerie_nom}
                    <div className="text-xs text-slate-400">{entry.produit_epicerie_id}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{entry.epicerie_categorie}</td>
                  <td className="px-4 py-3 text-right">{formatNumber(entry.quantity_consumed)}</td>
                  <td className="px-4 py-3 text-right">{formatNumber(entry.bottles_required)}</td>
                  <td className="px-4 py-3 text-right">{formatCurrency(entry.cost_spent)}</td>
                  <td className="px-4 py-3 text-right">{formatNumber(entry.stock_after_sales)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
