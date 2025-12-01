import { useMemo, useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
  CartesianGrid,
} from 'recharts';
import {
  useRestaurantPriceHistoryOverview,
  useRestaurantPlats,
  useRestaurantBankStatementSummary,
} from '../../hooks/useRestaurant.js';

const numberFormatter = new Intl.NumberFormat('fr-FR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatDate(value) {
  if (!value) return '-';
  return new Date(value).toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function RestaurantPriceTrends() {
  const [windowDays, setWindowDays] = useState(90);
  const { data, isLoading } = useRestaurantPriceHistoryOverview(200);
  const platsQuery = useRestaurantPlats();
  const bankSummary = useRestaurantBankStatementSummary(undefined, 6);

  const ingredientChanges = data?.ingredients ?? [];
  const platChanges = data?.plats ?? [];
  const plats = platsQuery.data ?? [];
  const bankTimeline = bankSummary.data?.monthly ?? [];

  const filterByWindow = (entries) => {
    if (windowDays === 'all') return entries;
    const threshold = Date.now() - Number(windowDays) * 24 * 60 * 60 * 1000;
    return entries.filter((entry) => new Date(entry.changed_at).valueOf() >= threshold);
  };

  const filteredIngredientChanges = useMemo(
    () => filterByWindow(ingredientChanges),
    [ingredientChanges, windowDays],
  );
  const filteredPlatChanges = useMemo(() => filterByWindow(platChanges), [platChanges, windowDays]);

  const groupLatestDelta = (entries, keyField, valueField) => {
    const grouped = new Map();
    entries.forEach((entry) => {
      const key = entry[keyField];
      const list = grouped.get(key) || [];
      list.push(entry);
      grouped.set(key, list);
    });
    return [...grouped.values()]
      .map((list) => {
        const sorted = list.sort((a, b) => new Date(b.changed_at) - new Date(a.changed_at));
        if (sorted.length < 2) return null;
        const latest = sorted[0];
        const previous = sorted[1];
        const delta = (latest[valueField] ?? 0) - (previous[valueField] ?? 0);
        return { latest, previous, delta };
      })
      .filter(Boolean);
  };

  const ingredientDeltas = useMemo(
    () => groupLatestDelta(filteredIngredientChanges, 'ingredient_id', 'cout_unitaire'),
    [filteredIngredientChanges],
  );
  const platDeltas = useMemo(
    () => groupLatestDelta(filteredPlatChanges, 'plat_id', 'prix_vente_ttc'),
    [filteredPlatChanges],
  );

  const buildTimeline = (entries, valueField) => {
    const buckets = new Map();
    entries.forEach((entry) => {
      const day = new Date(entry.changed_at).toISOString().slice(0, 10);
      const bucket = buckets.get(day) || { date: day, variations: 0 };
      bucket.variations += Number(entry[valueField] ?? 0);
      buckets.set(day, bucket);
    });
    return [...buckets.values()].sort((a, b) => new Date(a.date) - new Date(b.date));
  };

  const ingredientTimeline = useMemo(
    () => buildTimeline(filteredIngredientChanges, 'cout_unitaire'),
    [filteredIngredientChanges],
  );
  const platTimeline = useMemo(
    () => buildTimeline(filteredPlatChanges, 'prix_vente_ttc'),
    [filteredPlatChanges],
  );

  const topIngredientHikes = useMemo(
    () => [...ingredientDeltas].sort((a, b) => b.delta - a.delta).slice(0, 5),
    [ingredientDeltas],
  );
  const topIngredientDrops = useMemo(
    () => [...ingredientDeltas].sort((a, b) => a.delta - b.delta).slice(0, 5),
    [ingredientDeltas],
  );

  const lowMarginPlats = useMemo(
    () =>
      plats
        .filter((plat) => plat.marge_pct !== undefined)
        .sort((a, b) => (a.marge_pct ?? 0) - (b.marge_pct ?? 0))
        .slice(0, 5),
    [plats],
  );
  const avgMargin =
    plats.length === 0
      ? 0
      : plats.reduce((sum, plat) => sum + (plat.marge_pct ?? 0), 0) / plats.length;

  const bankChartData = useMemo(
    () =>
      bankTimeline.map((entry) => ({
        label: entry.mois,
        entrees: Number(entry.entrees ?? 0),
        sorties: Number(entry.sorties ?? 0),
        net: Number(entry.net ?? (entry.entrees || 0) - (entry.sorties || 0)),
      })),
    [bankTimeline],
  );

  return (
    <div className="flex flex-col gap-6">
      <Card className="space-y-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Restaurant HQ</p>
            <h2 className="text-2xl font-semibold text-slate-900">Tendances des prix des matières</h2>
            <p className="text-sm text-slate-500">
              Visualisez l’évolution des coûts pour anticiper les dérives.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <span>Fenêtre :</span>
            <select
              value={windowDays}
              onChange={(event) => setWindowDays(event.target.value)}
              className="rounded-full border border-slate-200 px-3 py-1 text-sm focus:border-brand-400 focus:outline-none"
            >
              <option value="30">30 jours</option>
              <option value="90">90 jours</option>
              <option value="180">180 jours</option>
              <option value="all">Tout l’historique</option>
            </select>
          </div>
        </div>
        {isLoading ? (
          <p className="text-sm text-slate-500">Chargement des historiques…</p>
        ) : filteredIngredientChanges.length === 0 ? (
          <p className="text-sm text-slate-500">Aucune évolution enregistrée pour l’instant.</p>
        ) : (
          <div className="space-y-6">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ingredientTimeline}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip formatter={(value) => `${numberFormatter.format(value)} €`} />
                  <Legend />
                  <Line type="monotone" dataKey="variations" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="overflow-x-auto rounded-2xl border border-slate-100">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Ingrédient</th>
                    <th className="px-3 py-2">Nouveau coût</th>
                    <th className="px-3 py-2">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredIngredientChanges.map((entry) => (
                    <tr key={`ing-${entry.id}`}>
                      <td className="px-3 py-2 text-slate-900">{entry.ingredient_nom}</td>
                      <td className="px-3 py-2 text-slate-600">{numberFormatter.format(entry.cout_unitaire)} €</td>
                      <td className="px-3 py-2 text-slate-500">{formatDate(entry.changed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      <Card className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Menu & recettes</p>
          <h2 className="text-2xl font-semibold text-slate-900">Prix de vente</h2>
          <p className="text-sm text-slate-500">Suivez les adaptations tarifaires réalisées sur vos plats.</p>
        </div>
        {isLoading ? (
          <p className="text-sm text-slate-500">Chargement des historiques…</p>
        ) : filteredPlatChanges.length === 0 ? (
          <p className="text-sm text-slate-500">Pas de changements enregistrés récemment.</p>
        ) : (
          <div className="space-y-6">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={platTimeline}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip formatter={(value) => `${numberFormatter.format(value)} €`} />
                  <Area type="monotone" dataKey="variations" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="overflow-x-auto rounded-2xl border border-slate-100">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Plat</th>
                    <th className="px-3 py-2">Prix TTC</th>
                    <th className="px-3 py-2">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredPlatChanges.map((entry) => (
                    <tr key={`plat-${entry.id}`}>
                      <td className="px-3 py-2 text-slate-900">{entry.plat_nom}</td>
                      <td className="px-3 py-2 text-slate-600">{numberFormatter.format(entry.prix_vente_ttc)} €</td>
                      <td className="px-3 py-2 text-slate-500">{formatDate(entry.changed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Surveillez vos hausses</p>
            <h3 className="text-lg font-semibold text-slate-900">Top variations positives</h3>
          </div>
          {topIngredientHikes.length ? (
            <ul className="divide-y divide-slate-100 text-sm">
              {topIngredientHikes.map(({ latest, previous, delta }) => (
                <li key={`hike-${latest.ingredient_id}`} className="flex items-center justify-between py-2">
                  <div>
                    <p className="font-semibold text-slate-900">{latest.ingredient_nom}</p>
                    <p className="text-xs text-slate-500">
                      {numberFormatter.format(previous.cout_unitaire)} € → {numberFormatter.format(latest.cout_unitaire)} €
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-rose-600">
                    +{numberFormatter.format(delta)} €
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Aucune hausse notable sur la période.</p>
          )}
        </Card>
        <Card className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Opportunités</p>
            <h3 className="text-lg font-semibold text-slate-900">Top variations négatives</h3>
          </div>
          {topIngredientDrops.length ? (
            <ul className="divide-y divide-slate-100 text-sm">
              {topIngredientDrops.map(({ latest, previous, delta }) => (
                <li key={`drop-${latest.ingredient_id}`} className="flex items-center justify-between py-2">
                  <div>
                    <p className="font-semibold text-slate-900">{latest.ingredient_nom}</p>
                    <p className="text-xs text-slate-500">
                      {numberFormatter.format(previous.cout_unitaire)} € → {numberFormatter.format(latest.cout_unitaire)} €
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-emerald-600">
                    {numberFormatter.format(delta)} €
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Aucune détente de prix constatée.</p>
          )}
        </Card>
      </div>

      <Card className="space-y-4">
        <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Flux bancaires</p>
            <h3 className="text-lg font-semibold text-slate-900">Entrées / sorties récentes</h3>
            <p className="text-sm text-slate-500">Vue synthétique des 6 derniers mois (tenant Restaurant HQ).</p>
          </div>
        </div>
        {bankSummary.isLoading ? (
          <p className="text-sm text-slate-500">Chargement des relevés…</p>
        ) : bankChartData.length === 0 ? (
          <p className="text-sm text-slate-500">Aucun flux bancaires enregistrés pour cette période.</p>
        ) : (
          <div className="grid gap-4 lg:grid-cols-[1.4fr,0.6fr]">
            <div className="h-72 rounded-2xl border border-slate-100 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={bankChartData}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip formatter={(value) => `${numberFormatter.format(value)} €`} />
                  <Legend />
                  <Area type="monotone" dataKey="entrees" name="Entrées" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
                  <Area type="monotone" dataKey="sorties" name="Sorties" stroke="#ef4444" fill="#ef4444" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="net" name="Net" stroke="#6366f1" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="h-72 rounded-2xl border border-slate-100 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={bankChartData}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip formatter={(value) => `${numberFormatter.format(value)} €`} />
                  <Bar dataKey="net" name="Net mensuel" fill="#0ea5e9" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </Card>

      <Card className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Marges critiques</p>
          <h3 className="text-lg font-semibold text-slate-900">Alertes & tendances</h3>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Marge moyenne</p>
            <p className="text-2xl font-semibold text-slate-900">
              {numberFormatter.format(avgMargin)} %
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Plats &lt; 30 %</p>
            <p className="text-2xl font-semibold text-rose-600">{lowMarginPlats.length}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Dernière mise à jour</p>
            <p className="text-sm text-slate-500">
              {filteredPlatChanges[0] ? formatDate(filteredPlatChanges[0].changed_at) : 'Aucune'}
            </p>
          </div>
        </div>
        {lowMarginPlats.length > 0 && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            Les plats listés ci-dessous ont une marge inférieure à 30 %. Pense à réguler leurs coûts ou leur prix de vente.
            <ul className="mt-3 space-y-2">
              {lowMarginPlats.map((plat) => (
                <li key={`alert-${plat.id}`} className="flex items-center justify-between text-slate-900">
                  <span>{plat.nom}</span>
                  <span className="font-semibold">
                    {numberFormatter.format(plat.marge_pct ?? 0)} %
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>
    </div>
  );
}
