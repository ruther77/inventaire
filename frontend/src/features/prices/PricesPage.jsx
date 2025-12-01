/* @refresh reload */
import { useMemo, useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { ResponsiveContainer, LineChart, Line, AreaChart, Area, Tooltip, XAxis, YAxis, CartesianGrid, Legend, BarChart, Bar } from 'recharts';
import { useProducts } from '../../hooks/useProducts.js';
import { usePriceHistory } from '../../hooks/usePriceHistory.js';

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });
const dateFormatter = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' });

const formatCurrency = (value) => `${numberFormatter.format(value || 0)} €`;

const safeDateKey = (value) => {
  if (!value) return null;
  try {
    return new Date(value).toISOString().slice(0, 10);
  } catch {
    return null;
  }
};

const csvEscape = (value) => {
  const text = value === null || value === undefined ? '' : String(value);
  return `"${text.replace(/"/g, '""')}"`;
};

const formatDelta = (value) => {
  if (!value) return '0 €';
  const symbol = value > 0 ? '+' : '';
  return `${symbol}${numberFormatter.format(value)} €`;
};

const formatPercentage = (value) => {
  if (value === null || value === undefined) return '—';
  const symbol = value > 0 ? '+' : '';
  return `${symbol}${numberFormatter.format(value)} %`;
};

const downloadCsv = (rows) => {
  if (!rows.length) return;
  const headers = [
    'Date',
    'Produit',
    'Code',
    'Fournisseur',
    'Prix vente',
    'Prix achat',
    'Delta prix',
    'Delta %',
    'Marge %',
    'Alerte marge',
    'Stock alerte',
    'Ruptures récentes',
    'Quantité',
    'Montant',
    'Contexte',
  ];
  const body = [headers, ...rows.map((row) => [
    row.facture_date,
    row.nom ?? '',
    row.code ?? '',
    row.fournisseur ?? '',
    row.prix_vente ?? '',
    row.prix_achat,
    row.delta_prix ?? '',
    row.delta_pct ?? '',
    row.marge_pct ?? '',
    row.margin_alert ?? '',
    row.stockout_repeated ?? row.stock_alert ?? '',
    row.stockout_events ?? '',
    row.quantite ?? '',
    row.montant ?? '',
    row.source_context ?? '',
  ])]
    .map((line) => line.map(csvEscape).join(','))
    .join('\n');
  const blob = new Blob([body], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'historique_prix.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export default function PricesPage() {
  const { data: products = [] } = useProducts();
  const [filters, setFilters] = useState({
    productId: 'all',
    supplier: '',
    code: '',
    search: '',
    dateStart: '',
    dateEnd: '',
    limit: 200,
  });

  const effectiveFilters = useMemo(
    () => ({
      productId: filters.productId === 'all' ? undefined : Number(filters.productId),
      supplier: filters.supplier || undefined,
      code: filters.code || undefined,
      search: filters.search || undefined,
      dateStart: filters.dateStart || undefined,
      dateEnd: filters.dateEnd || undefined,
      limit: filters.limit,
    }),
    [filters],
  );


  const historyQuery = usePriceHistory(effectiveFilters);
  const items = historyQuery.data ?? [];
  const sortedHistory = useMemo(
    () =>
      [...items].sort((a, b) => {
        const dateA = new Date(a.facture_date || 0).valueOf();
        const dateB = new Date(b.facture_date || 0).valueOf();
        return dateA - dateB;
      }),
    [items],
  );

  const metrics = useMemo(() => {
    if (!sortedHistory.length) {
      return { min: 0, max: 0, last: 0, first: 0, avg: 0 };
    }
    const prices = sortedHistory.map((item) => Number(item.prix_achat ?? 0));
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const last = prices[prices.length - 1];
    const first = prices[0];
    const avg = prices.reduce((sum, price) => sum + price, 0) / prices.length;
    return { min, max, last, first, avg };
  }, [sortedHistory]);

  const priceDelta = metrics.last - metrics.first;
  const deltaPct = metrics.first ? (priceDelta / metrics.first) * 100 : 0;

  const timelineData = useMemo(() => {
    if (!sortedHistory.length) return [];
    const bucket = new Map();
    sortedHistory.forEach((entry) => {
      const key = safeDateKey(entry.facture_date);
      if (!key) return;
      const stored = bucket.get(key) || { date: key, total: 0, count: 0 };
      stored.total += Number(entry.prix_achat ?? 0);
      stored.count += 1;
      bucket.set(key, stored);
    });
    const points = [...bucket.values()].sort((a, b) => new Date(a.date) - new Date(b.date));
    const window = 5;
    return points.map((point, index, arr) => {
      const avg = point.total / (point.count || 1);
      const slice = arr.slice(Math.max(0, index - window + 1), index + 1);
      const moving =
        slice.reduce((sum, entry) => sum + entry.total / (entry.count || 1), 0) / (slice.length || 1);
      return {
        date: point.date,
        average: Number(avg.toFixed(4)),
        moving: Number(moving.toFixed(4)),
      };
    });
  }, [sortedHistory]);

  const supplierBreakdown = useMemo(() => {
    if (!sortedHistory.length) return [];
    const totals = {};
    sortedHistory.forEach((entry) => {
      const supplier = entry.fournisseur || 'Non renseigné';
      totals[supplier] = (totals[supplier] || 0) + Number(entry.montant ?? entry.prix_achat ?? 0);
    });
    return Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([supplier, value]) => ({ supplier, value: Number(value.toFixed(2)) }));
  }, [sortedHistory]);

  const productVariations = useMemo(() => {
    if (!sortedHistory.length) return [];
    const groups = new Map();
    sortedHistory.forEach((entry) => {
      const key = entry.produit_id || entry.code || entry.nom || 'Produit';
      const list = groups.get(key) || [];
      list.push(entry);
      groups.set(key, list);
    });
    return [...groups.entries()]
      .map(([label, list]) => {
        const sorted = [...list].sort((a, b) => new Date(b.facture_date || 0) - new Date(a.facture_date || 0));
        if (sorted.length < 2) return null;
        const latest = sorted[0];
        const previous = sorted[1];
        const lastPrice = Number(latest.prix_achat ?? 0);
        const prevPrice = Number(previous.prix_achat ?? 0);
        const delta = lastPrice - prevPrice;
        const pct = prevPrice ? (delta / prevPrice) * 100 : null;
        return {
          label,
          name: latest.nom || previous.nom || '—',
          code: latest.code || previous.code || '—',
          latest: lastPrice,
          previous: prevPrice,
          delta,
          pct,
          supplier: latest.fournisseur || previous.fournisseur || '—',
        };
      })
      .filter(Boolean);
  }, [sortedHistory]);

  const topIncreases = useMemo(
    () => [...productVariations].filter((entry) => entry.delta > 0).sort((a, b) => b.delta - a.delta).slice(0, 5),
    [productVariations],
  );
  const topDrops = useMemo(
    () => [...productVariations].filter((entry) => entry.delta < 0).sort((a, b) => a.delta - b.delta).slice(0, 5),
    [productVariations],
  );

  const alertItems = useMemo(
    () =>
      items.filter(
        (entry) => entry.margin_alert || entry.stock_alert || entry.stockout_repeated,
      ),
    [items],
  );

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">prix & inflation</p>
            <h2 className="text-2xl font-semibold text-slate-900">Historique fournisseur</h2>
            <p className="text-sm text-slate-500">
              Comparez les évolutions de prix d&apos;achat par produit, fournisseur et période.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="ghost" size="sm" onClick={() => downloadCsv(items)} disabled={!items.length}>
              Export CSV
            </Button>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="text-sm text-slate-600">
            Produit
            <select
              value={filters.productId}
              onChange={(event) => setFilters((prev) => ({ ...prev, productId: event.target.value }))}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            >
              <option value="all">Catalogue complet</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.nom} #{product.id}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm text-slate-600">
            Fournisseur
            <input
              type="text"
              value={filters.supplier}
              onChange={(event) => setFilters((prev) => ({ ...prev, supplier: event.target.value }))}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              placeholder="Metro, Grossiste..."
            />
          </label>
          <label className="text-sm text-slate-600">
            Code/EAN
            <input
              type="text"
              value={filters.code}
              onChange={(event) => setFilters((prev) => ({ ...prev, code: event.target.value }))}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              placeholder="1234567890123"
            />
          </label>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="text-sm text-slate-600">
            Recherche libre
            <input
              type="text"
              value={filters.search}
              onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              placeholder="Nom produit, context..."
            />
          </label>
          <label className="text-sm text-slate-600">
            Début
            <input
              type="date"
              value={filters.dateStart}
              onChange={(event) => setFilters((prev) => ({ ...prev, dateStart: event.target.value }))}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            />
          </label>
          <label className="text-sm text-slate-600">
            Fin
            <input
              type="date"
              value={filters.dateEnd}
              onChange={(event) => setFilters((prev) => ({ ...prev, dateEnd: event.target.value }))}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            />
          </label>
        </div>
      </Card>

      <Card className="grid gap-4 lg:grid-cols-4">
        <Metric
          label="Dernier prix"
          value={formatCurrency(metrics.last)}
          hint={`vs début ${formatDelta(priceDelta)}`}
          accent="text-slate-900"
        />
        <Metric
          label="Variation"
          value={formatDelta(priceDelta)}
          hint={formatPercentage(deltaPct)}
          accent={priceDelta >= 0 ? 'text-rose-600' : 'text-emerald-600'}
        />
        <Metric label="Prix moyen" value={formatCurrency(metrics.avg)} hint="Période filtrée" />
        <Metric
          label="Fourchette"
          value={`${formatCurrency(metrics.min)} → ${formatCurrency(metrics.max)}`}
          hint="Minimum / Maximum observés"
        />
      </Card>

      <Card className="flex flex-col gap-3 border-amber-200 bg-amber-50">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-amber-600">alertes prix/stock</p>
            <h3 className="text-lg font-semibold text-amber-900">
              {alertItems.length} alerte{alertItems.length > 1 ? 's' : ''}
            </h3>
          </div>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-amber-700 shadow-sm">
            Marges <span className="font-bold">{alertItems.filter((a) => a.margin_alert).length}</span> · Ruptures{' '}
            <span className="font-bold">{alertItems.filter((a) => a.stock_alert || a.stockout_repeated).length}</span>
          </span>
        </div>
        {alertItems.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-amber-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-amber-700">
                  <th className="px-3 py-2">Produit</th>
                  <th className="px-3 py-2">Prix achat</th>
                  <th className="px-3 py-2">Marge</th>
                  <th className="px-3 py-2">Rupture</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-amber-100">
                {alertItems.slice(0, 6).map((item) => (
                  <tr key={`${item.id ?? item.code}-${item.facture_date}`}>
                    <td className="px-3 py-2">
                      <p className="font-semibold text-amber-900">{item.nom ?? '—'}</p>
                      <p className="text-xs text-amber-700">{item.code ?? '—'}</p>
                    </td>
                    <td className="px-3 py-2 text-amber-900">{formatCurrency(item.prix_achat)}</td>
                    <td className="px-3 py-2">
                      {item.marge_pct !== null && item.marge_pct !== undefined ? (
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            item.margin_alert
                              ? 'bg-rose-100 text-rose-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {formatPercentage(item.marge_pct)}
                        </span>
                      ) : (
                        <span className="text-xs text-amber-700">N/C</span>
                      )}
                    </td>
                    <td className="px-3 py-2 space-x-2">
                      {item.stock_alert && (
                        <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
                          Stock critique
                        </span>
                      )}
                      {item.stockout_repeated && (
                        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                          Ruptures ({item.stockout_events || 0})
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-amber-800">
            Aucune alerte active sur les marges ou les ruptures répétées pour ces filtres.
          </p>
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <Card className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Courbe de prix</p>
              <h3 className="text-lg font-semibold text-slate-900">Evolution moyenne journalière</h3>
            </div>
            <p className="text-xs text-slate-500">
              {timelineData.length} points • glissante 5 jours
            </p>
          </div>
          {timelineData.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip formatter={(value) => `${numberFormatter.format(value)} €`} />
                  <Legend />
                  <Area type="monotone" dataKey="moving" stroke="#6366f1" fill="#6366f1" fillOpacity={0.1} name="Moyenne mobile" />
                  <Line type="monotone" dataKey="average" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Moyenne quotidienne" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Pas encore d&apos;historique pour ces filtres.</p>
          )}
        </Card>

        <Card className="flex flex-col gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Fournisseurs</p>
            <h3 className="text-lg font-semibold text-slate-900">Top contributeurs</h3>
          </div>
          {supplierBreakdown.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={supplierBreakdown} layout="vertical" margin={{ left: 0, right: 10, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" />
                  <YAxis dataKey="supplier" type="category" width={120} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Bar dataKey="value" fill="#f97316" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Aucun fournisseur identifié.</p>
          )}
        </Card>
      </div>

      <Card className="grid gap-6 lg:grid-cols-2">
        <VariationList title="Top hausses" items={topIncreases} emptyLabel="Aucune hausse détectée." accent="text-rose-600" />
        <VariationList title="Top baisses" items={topDrops} emptyLabel="Aucune détente constatée." accent="text-emerald-600" />
      </Card>

      {!historyQuery.isLoading && items.length === 0 && (
        <Card className="flex flex-col gap-2 border border-amber-200 bg-amber-50 text-sm text-amber-900">
          <p className="font-semibold">Aucune statistique enregistrée</p>
          <p>
            L&apos;historique se remplit lors de l&apos;import de factures (onglet Factures → Commandes)
            ou via l&apos;API `record_price_history`. Réimporte tes factures PDF/CSV pour reconstruire les
            2 dernières années ou utilise le script `price_history_service.record_price_history` pour
            charger un fichier existant.
          </p>
        </Card>
      )}

      <Card className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">Historique des prix</h3>
          <p className="text-sm text-slate-500">{items.length} entrée(s)</p>
        </div>
        {items.length ? (
          <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Produit</th>
                    <th className="px-3 py-2">Code</th>
                    <th className="px-3 py-2">Fournisseur</th>
                    <th className="px-3 py-2">Prix achat</th>
                    <th className="px-3 py-2">Δ prix</th>
                    <th className="px-3 py-2">Marge</th>
                    <th className="px-3 py-2">Quantité</th>
                    <th className="px-3 py-2">Montant</th>
                    <th className="px-3 py-2">Contexte</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {items.map((item) => (
                    <tr key={item.id ?? `${item.code}-${item.facture_date}`}>
                    <td className="px-3 py-2 text-slate-500">
                      {item.facture_date ? dateFormatter.format(new Date(item.facture_date)) : '—'}
                    </td>
                    <td className="px-3 py-2 text-slate-900">{item.nom ?? '—'}</td>
                    <td className="px-3 py-2 text-slate-600">{item.code ?? '—'}</td>
                    <td className="px-3 py-2 text-slate-600">{item.fournisseur ?? '—'}</td>
                    <td className="px-3 py-2">{numberFormatter.format(item.prix_achat ?? 0)} €</td>
                    <td className="px-3 py-2">
                      {item.delta_prix !== null && item.delta_prix !== undefined ? (
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                            item.delta_prix > 0 ? 'bg-rose-50 text-rose-700' : item.delta_prix < 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {formatDelta(item.delta_prix)} ({formatPercentage(item.delta_pct)})
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {item.marge_pct !== null && item.marge_pct !== undefined ? (
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                            item.margin_alert
                              ? 'bg-rose-100 text-rose-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {formatPercentage(item.marge_pct)}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-500">N/C</span>
                      )}
                      {(item.stock_alert || item.stockout_repeated) && (
                        <div className="mt-1 space-x-1">
                          {item.stock_alert && (
                            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
                              Stock critique
                            </span>
                          )}
                          {item.stockout_repeated && (
                            <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                              Ruptures {item.stockout_events ?? 0}
                            </span>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-2">{item.quantite ?? '—'}</td>
                    <td className="px-3 py-2">{item.montant ? `${numberFormatter.format(item.montant)} €` : '—'}</td>
                    <td className="px-3 py-2 text-slate-500">{item.source_context ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            {historyQuery.isLoading ? 'Chargement…' : 'Aucune donnée pour ces filtres.'}
          </p>
        )}
      </Card>
    </div>
  );
}

function Metric({ label, value, hint, accent = 'text-slate-900' }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className={`text-2xl font-semibold ${accent}`}>{value}</p>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

function VariationList({ title, items, emptyLabel, accent }) {
  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400">{title}</p>
        <p className="text-sm text-slate-500">Comparatif entre les deux dernières variations</p>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">{emptyLabel}</p>
      ) : (
        <ul className="divide-y divide-slate-100 text-sm">
          {items.map((entry) => (
            <li key={entry.label} className="flex flex-col gap-1 py-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-900">{entry.name || entry.label}</p>
                  <p className="text-xs text-slate-500">
                    {entry.code && entry.code !== '—' ? `${entry.code} · ` : ''}
                    {entry.supplier}
                  </p>
                </div>
                <span className={`text-sm font-semibold ${accent}`}>{formatDelta(entry.delta)}</span>
              </div>
              <p className="text-xs text-slate-500">
                {formatCurrency(entry.previous)} → {formatCurrency(entry.latest)} ({formatPercentage(entry.pct)})
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
