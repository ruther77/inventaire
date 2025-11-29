import { useMemo, useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  useRestaurantCategories,
  useCreateRestaurantCategory,
  useRestaurantCostCenters,
  useCreateRestaurantCostCenter,
  useRestaurantExpenses,
  useCreateRestaurantExpense,
  useRestaurantTvaSummary,
} from '../../hooks/useRestaurant.js';

const euro = (value) => `${Number(value || 0).toFixed(2)} €`;

export default function RestaurantChargesPage({ context = 'restaurant' }) {
  const categories = useRestaurantCategories();
  const costCenters = useRestaurantCostCenters();
  const expenses = useRestaurantExpenses();
  const tvaSummary = useRestaurantTvaSummary();
  const createCategory = useCreateRestaurantCategory();
  const createCostCenter = useCreateRestaurantCostCenter();
  const createExpense = useCreateRestaurantExpense();

  const [categoryName, setCategoryName] = useState('');
  const [costCenterName, setCostCenterName] = useState('');
  const [timelineWindow, setTimelineWindow] = useState('6');
  const [form, setForm] = useState({
    libelle: '',
    montant_ht: '',
    categorie_id: '',
    cost_center_id: '',
    date_operation: new Date().toISOString().slice(0, 10),
  });

  const contextLabel = context === 'epicerie' ? 'Épicerie HQ' : 'Restaurant HQ';
  const chargesTitle = context === 'epicerie' ? 'Charges épicerie' : 'Pilotage des dépenses';
  const chargesSubtitle =
    context === 'epicerie'
      ? 'Analyse consolidée des charges magasins (imports, TVA, centres de coûts).'
      : 'Analyse dynamique basée sur les dépenses importées ou saisies.';

  const expensesList = expenses.data ?? [];

  const extractMonthKey = (value) => {
    if (!value) return 'N/A';
    const dateObj = new Date(value);
    if (Number.isNaN(dateObj.getTime())) return 'N/A';
    return `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
  };

  const monthlyTotals = useMemo(() => {
    const buckets = expensesList.reduce((acc, row) => {
      const key = extractMonthKey(row.date_operation);
      const amount = Number(row.montant_ht) || 0;
      acc[key] = (acc[key] || 0) + amount;
      return acc;
    }, {});
    return Object.entries(buckets)
      .map(([month, total]) => ({ month, total }))
      .sort((a, b) => a.month.localeCompare(b.month));
  }, [expensesList]);

  const filteredMonthly = useMemo(() => {
    if (timelineWindow === 'all') return monthlyTotals;
    const count = Number(timelineWindow) || 6;
    return monthlyTotals.slice(-count);
  }, [monthlyTotals, timelineWindow]);

  const activeMonths = useMemo(() => new Set(filteredMonthly.map((entry) => entry.month)), [filteredMonthly]);

  const scopedExpenses = useMemo(() => {
    if (timelineWindow === 'all') return expensesList;
    return expensesList.filter((expense) => activeMonths.has(extractMonthKey(expense.date_operation)));
  }, [expensesList, activeMonths, timelineWindow]);

  const totalHT = useMemo(
    () => scopedExpenses.reduce((sum, expense) => sum + (Number(expense.montant_ht) || 0), 0),
    [scopedExpenses],
  );
  const avgMonthly = filteredMonthly.length ? totalHT / filteredMonthly.length : 0;

  const groupTotals = (field, fallbackLabel) =>
    scopedExpenses.reduce((acc, expense) => {
      const label = expense[field] || fallbackLabel;
      const amount = Number(expense.montant_ht) || 0;
      acc[label] = (acc[label] || 0) + amount;
      return acc;
    }, {});

  const categoryTotals = useMemo(() => groupTotals('categorie', 'Autres charges'), [scopedExpenses]);
  const costCenterTotals = useMemo(() => groupTotals('cost_center', 'Non affecté'), [scopedExpenses]);

  const topCategories = useMemo(
    () =>
      Object.entries(categoryTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
        .map(([label, amount]) => ({ label, amount })),
    [categoryTotals],
  );

  const topCostCenters = useMemo(
    () =>
      Object.entries(costCenterTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([label, amount]) => ({ label, amount })),
    [costCenterTotals],
  );

  const timelineChartData = useMemo(
    () =>
      filteredMonthly.map((entry) => ({
        label: entry.month,
        total: Number(entry.total.toFixed(2)),
      })),
    [filteredMonthly],
  );

  const tvaEntries = tvaSummary.data ?? [];
  const tvaAggregates = useMemo(() => {
    if (!tvaEntries.length) {
      return {
        totalHt: 0,
        totalTva: 0,
        timeline: [],
        rateBreakdown: [],
      };
    }
    const monthMap = new Map();
    const rateMap = new Map();
    let totalHt = 0;
    let totalTva = 0;
    tvaEntries.forEach((entry) => {
      const month = extractMonthKey(entry.periode);
      const ht = Number(entry.montant_ht) || 0;
      const tva = Number(entry.montant_tva) || 0;
      totalHt += ht;
      totalTva += tva;
      const bucket = monthMap.get(month) || { label: month, ht: 0, tva: 0, ttc: 0 };
      bucket.ht += ht;
      bucket.tva += tva;
      bucket.ttc += Number(entry.montant_ttc) || ht + tva;
      monthMap.set(month, bucket);
      const rateKey = `${entry.taux ?? 0}%`;
      rateMap.set(rateKey, (rateMap.get(rateKey) || 0) + tva);
    });
    return {
      totalHt,
      totalTva,
      timeline: Array.from(monthMap.values()).sort((a, b) => a.label.localeCompare(b.label)),
      rateBreakdown: Array.from(rateMap.entries())
        .map(([label, amount]) => ({ label, amount }))
        .sort((a, b) => b.amount - a.amount),
    };
  }, [tvaEntries]);
  const tvaTableRows = useMemo(
    () =>
      [...tvaEntries].sort((a, b) => {
        const monthDiff = extractMonthKey(a.periode).localeCompare(extractMonthKey(b.periode));
        if (monthDiff !== 0) return monthDiff;
        return (a.taux ?? 0) - (b.taux ?? 0);
      }),
    [tvaEntries],
  );
  const tvaRangeStart = tvaEntries.length ? extractMonthKey(tvaEntries[0].periode) : null;
  const tvaRangeEnd =
    tvaEntries.length > 1 ? extractMonthKey(tvaEntries[tvaEntries.length - 1].periode) : tvaRangeStart;

  const handleExpenseSubmit = (event) => {
    event.preventDefault();
    if (!form.libelle || !form.montant_ht) return;
    createExpense.mutate(
      {
        libelle: form.libelle,
        montant_ht: parseFloat(form.montant_ht),
        categorie_id: form.categorie_id ? Number(form.categorie_id) : undefined,
        cost_center_id: form.cost_center_id ? Number(form.cost_center_id) : undefined,
        date_operation: form.date_operation,
      },
      {
        onSuccess: () => setForm({ ...form, libelle: '', montant_ht: '' }),
      },
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{contextLabel}</p>
          <h2 className="text-2xl font-semibold text-slate-900">{chargesTitle}</h2>
          <p className="text-sm text-slate-500">{chargesSubtitle}</p>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Total HT</p>
            <p className="text-2xl font-semibold text-slate-900">{totalHT.toFixed(2)} €</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Moyenne mensuelle</p>
            <p className="text-2xl font-semibold text-slate-900">{avgMonthly.toFixed(2)} €</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Catégories actives</p>
            <p className="text-2xl font-semibold text-slate-900">{Object.keys(categoryTotals).length}</p>
          </div>
        </div>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-700">Évolution des charges HT</p>
              <p className="text-xs text-slate-500">Fenêtre glissante sur les derniers mois</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span>Fenêtre :</span>
              <select
                className="rounded-full border border-slate-200 px-3 py-1 text-sm"
                value={timelineWindow}
                onChange={(event) => setTimelineWindow(event.target.value)}
              >
                <option value="3">3 mois</option>
                <option value="6">6 mois</option>
                <option value="12">12 mois</option>
                <option value="all">Tout l’historique</option>
              </select>
            </div>
          </div>
          {timelineChartData.length ? (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineChartData} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="chargesGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f97316" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)} €`} />
                  <Area type="monotone" dataKey="total" stroke="#f97316" fill="url(#chargesGradient)" name="Total HT" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Aucune charge à afficher pour la période sélectionnée.</p>
          )}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Répartition</p>
              <h3 className="text-lg font-semibold text-slate-900">Top catégories</h3>
            </div>
          </div>
          {topCategories.length ? (
            <>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topCategories} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(value) => `${Number(value).toFixed(2)} €`} />
                    <Legend />
                    <Bar dataKey="amount" fill="#fb7185" name="Montant HT" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="grid gap-2 text-sm text-slate-600">
                {topCategories.map((entry) => (
                  <div key={entry.label} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                    <span>{entry.label}</span>
                    <span className="font-semibold">{entry.amount.toFixed(2)} €</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">Aucune catégorie renseignée sur cette période.</p>
          )}
        </Card>

        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Analyse</p>
              <h3 className="text-lg font-semibold text-slate-900">Centres de coûts</h3>
            </div>
          </div>
          {topCostCenters.length ? (
            <>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topCostCenters} layout="vertical" margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis dataKey="label" type="category" tick={{ fontSize: 11 }} width={120} />
                    <Tooltip formatter={(value) => `${Number(value).toFixed(2)} €`} />
                    <Bar dataKey="amount" fill="#38bdf8" name="Montant HT" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="grid gap-2 text-sm text-slate-600">
                {topCostCenters.map((entry) => (
                  <div key={entry.label} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                    <span>{entry.label}</span>
                    <span className="font-semibold">{entry.amount.toFixed(2)} €</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">Aucun centre de coût utilisé sur cette période.</p>
          )}
        </Card>
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Déclarations</p>
            <h3 className="text-lg font-semibold text-slate-900">TVA collectée</h3>
          </div>
          <p className="text-xs text-slate-500">
            {tvaSummary.isFetching
              ? 'Calcul en cours…'
              : tvaRangeStart
                ? tvaRangeEnd && tvaRangeEnd !== tvaRangeStart
                  ? `Fenêtre ${tvaRangeStart} → ${tvaRangeEnd}`
                  : `Fenêtre ${tvaRangeStart}`
                : 'Fenêtre vide'}
          </p>
        </div>
        {tvaSummary.isLoading ? (
          <p className="text-sm text-slate-500">Aggregation des montants TVA…</p>
        ) : !tvaEntries.length ? (
          <p className="text-sm text-slate-500">Aucune dépense n’est associée à un taux de TVA pour le moment.</p>
        ) : (
          <>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Total HT</p>
                <p className="text-2xl font-semibold text-slate-900">{euro(tvaAggregates.totalHt)}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">TVA due</p>
                <p className="text-2xl font-semibold text-rose-600">{euro(tvaAggregates.totalTva)}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Taux suivis</p>
                <p className="text-2xl font-semibold text-slate-900">{tvaAggregates.rateBreakdown.length}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Mois couverts</p>
                <p className="text-2xl font-semibold text-slate-900">{tvaAggregates.timeline.length}</p>
              </div>
            </div>
            <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={tvaAggregates.timeline} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(value, name) => `${Number(value).toFixed(2)} €`} />
                    <Legend />
                    <Bar dataKey="ht" name="HT" fill="#0ea5e9" />
                    <Bar dataKey="tva" name="TVA" fill="#f43f5e" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-3">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Taux</p>
                {tvaAggregates.rateBreakdown.map((entry) => (
                  <div
                    key={entry.label}
                    className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2 text-sm text-slate-700"
                  >
                    <span>{entry.label}</span>
                    <span className="font-semibold text-rose-600">{euro(entry.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto rounded-2xl border border-slate-100">
              <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Mois</th>
                    <th className="px-3 py-2">Taux</th>
                    <th className="px-3 py-2">Montant HT</th>
                    <th className="px-3 py-2">TVA</th>
                    <th className="px-3 py-2">TTC</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {tvaTableRows.map((entry) => (
                    <tr key={`${entry.periode}-${entry.taux}`}>
                      <td className="px-3 py-2 text-slate-600">{extractMonthKey(entry.periode)}</td>
                      <td className="px-3 py-2 text-slate-600">{`${entry.taux ?? 0}%`}</td>
                      <td className="px-3 py-2 font-semibold">{euro(entry.montant_ht)}</td>
                      <td className="px-3 py-2 font-semibold text-rose-600">{euro(entry.montant_tva)}</td>
                      <td className="px-3 py-2">{euro(entry.montant_ttc)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Card>

      <Card className="flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">charges</p>
          <h2 className="text-2xl font-semibold text-slate-900">Saisie rapide</h2>
        </div>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleExpenseSubmit}>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Libellé</label>
            <input
              type="text"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={form.libelle}
              onChange={(event) => setForm((prev) => ({ ...prev, libelle: event.target.value }))}
              required
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Montant HT (€)</label>
            <input
              type="number"
              step="0.01"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={form.montant_ht}
              onChange={(event) => setForm((prev) => ({ ...prev, montant_ht: event.target.value }))}
              required
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Catégorie</label>
            <select
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={form.categorie_id}
              onChange={(event) => setForm((prev) => ({ ...prev, categorie_id: event.target.value }))}
            >
              <option value="">Non catégorisée</option>
              {(categories.data ?? []).map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.nom}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Centre de coût</label>
            <select
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={form.cost_center_id}
              onChange={(event) => setForm((prev) => ({ ...prev, cost_center_id: event.target.value }))}
            >
              <option value="">Non affecté</option>
              {(costCenters.data ?? []).map((cc) => (
                <option key={cc.id} value={cc.id}>
                  {cc.nom}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Date</label>
            <input
              type="date"
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={form.date_operation}
              onChange={(event) => setForm((prev) => ({ ...prev, date_operation: event.target.value }))}
            />
          </div>
          <div className="flex items-end">
            <Button type="submit" variant="brand" className="w-full">
              Enregistrer la dépense
            </Button>
          </div>
        </form>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="flex flex-col gap-3">
          <h3 className="text-lg font-semibold text-slate-900">Catégories</h3>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Électricité, Eau…"
              className="flex-1 rounded-2xl border border-slate-200 px-4 py-2 text-sm"
              value={categoryName}
              onChange={(event) => setCategoryName(event.target.value)}
            />
            <Button
              variant="ghost"
              onClick={() =>
                categoryName &&
                createCategory.mutate(categoryName, {
                  onSuccess: () => setCategoryName(''),
                })
              }
            >
              Ajouter
            </Button>
          </div>
          <ul className="divide-y divide-slate-100 text-sm">
            {(categories.data ?? []).map((cat) => (
              <li key={cat.id} className="py-1 text-slate-700">
                {cat.nom}
              </li>
            ))}
          </ul>
        </Card>

        <Card className="flex flex-col gap-3">
          <h3 className="text-lg font-semibold text-slate-900">Centres de coûts</h3>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Cuisine, Bar…"
              className="flex-1 rounded-2xl border border-slate-200 px-4 py-2 text-sm"
              value={costCenterName}
              onChange={(event) => setCostCenterName(event.target.value)}
            />
            <Button
              variant="ghost"
              onClick={() =>
                costCenterName &&
                createCostCenter.mutate(costCenterName, {
                  onSuccess: () => setCostCenterName(''),
                })
              }
            >
              Ajouter
            </Button>
          </div>
          <ul className="divide-y divide-slate-100 text-sm">
            {(costCenters.data ?? []).map((cc) => (
              <li key={cc.id} className="py-1 text-slate-700">
                {cc.nom}
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card className="flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">journal</p>
          <h3 className="text-lg font-semibold text-slate-900">Dépenses récentes</h3>
        </div>
        {scopedExpenses.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Libellé</th>
                  <th className="px-3 py-2">Catégorie</th>
                  <th className="px-3 py-2">Centre</th>
                  <th className="px-3 py-2 text-right">Montant HT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {scopedExpenses.map((expense) => (
                  <tr key={expense.id}>
                    <td className="px-3 py-2 text-slate-500">{expense.date_operation}</td>
                    <td className="px-3 py-2 text-slate-900">{expense.libelle}</td>
                    <td className="px-3 py-2 text-slate-500">{expense.categorie || '—'}</td>
                    <td className="px-3 py-2 text-slate-500">{expense.cost_center || '—'}</td>
                    <td className="px-3 py-2 text-right font-semibold text-slate-900">
                      {(Number(expense.montant_ht) || 0).toFixed(2)} €
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Aucune dépense sur la période sélectionnée.</p>
        )}
      </Card>
    </div>
  );
}
