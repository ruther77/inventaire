import { useRestaurantPriceHistoryComparison } from '../../hooks/useRestaurant.js';

const number = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function format(value) {
  return number.format(value ?? 0);
}

export default function RestaurantPriceHistoryComparisonPage() {
  const { data = [], isLoading } = useRestaurantPriceHistoryComparison();

  if (isLoading) {
    return <p className="text-sm text-slate-500">Chargement de l’historique…</p>;
  }

  if (!data.length) {
    return <p className="text-sm text-slate-500">Aucune entrée historique disponible.</p>;
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Comparaison</p>
        <h1 className="text-2xl font-bold text-slate-900">Prix plat vs coût Épicerie</h1>
        <p className="text-sm text-slate-500">
          Le graphe croise chaque variation de prix restaurant avec le dernier coût d’achat Épicerie disponible.
        </p>
      </header>

      <div className="overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Plat</th>
                <th className="px-4 py-3">Date variation</th>
                <th className="px-4 py-3 text-right">Prix vente TTC</th>
                <th className="px-4 py-3">Produit Épicerie</th>
                <th className="px-4 py-3 text-right">Coût achat</th>
                <th className="px-4 py-3 text-right">Date coût</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((entry) => (
                <tr key={`${entry.plat_id}-${entry.plat_changed_at}`}>
                  <td className="px-4 py-3 font-medium text-slate-900">{entry.plat_nom}</td>
                  <td className="px-4 py-3 text-slate-500">{new Date(entry.plat_changed_at).toLocaleString('fr-FR')}</td>
                  <td className="px-4 py-3 text-right">{format(entry.prix_vente_ttc)}</td>
                  <td className="px-4 py-3">
                    {entry.epicerie_nom ?? '—'}
                    <div className="text-xs text-slate-400">{entry.epicerie_id ?? '—'}</div>
                  </td>
                  <td className="px-4 py-3 text-right">{entry.prix_achat != null ? format(entry.prix_achat) : '—'}</td>
                  <td className="px-4 py-3 text-right">
                    {entry.epicerie_changed_at ? new Date(entry.epicerie_changed_at).toLocaleString('fr-FR') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
