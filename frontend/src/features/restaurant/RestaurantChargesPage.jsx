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
  useFinanceCategories,
  useCreateFinanceCategory,
  useFinanceCostCenters,
  useCreateFinanceCostCenter,
  useFinanceTimeline,
} from '../../hooks/useFinanceCategories.js';
import { useFinanceTransactions } from '../../hooks/useFinance.js';

// Entity IDs pour le multi-tenant
const ENTITY_IDS = {
  EPICERIE: 1,
  RESTO: 2,
};

const euro = (value) => `${Number(value || 0).toFixed(2)} €`;

export default function RestaurantChargesPage({ context = 'restaurant' }) {
  // Déterminer l'entity_id selon le contexte
  const entityId = context === 'epicerie' ? ENTITY_IDS.EPICERIE : ENTITY_IDS.RESTO;

  // Hooks Finance API avec entity_id
  const categories = useFinanceCategories({ entityId });
  const costCenters = useFinanceCostCenters({ entityId });
  const transactionsQuery = useFinanceTransactions({ entityId, size: 500 });
  const createCategory = useCreateFinanceCategory();
  const createCostCenter = useCreateFinanceCostCenter();

  const [categoryName, setCategoryName] = useState('');
  const [costCenterName, setCostCenterName] = useState('');
  const [timelineWindow, setTimelineWindow] = useState('6');

  const contextLabel = context === 'epicerie' ? 'Épicerie HQ' : 'Restaurant HQ';
  const chargesTitle = context === 'epicerie' ? 'Charges épicerie' : 'Pilotage des dépenses';
  const chargesSubtitle =
    context === 'epicerie'
      ? 'Analyse consolidée des charges magasins (imports, TVA, centres de coûts).'
      : 'Analyse dynamique basée sur les dépenses importées ou saisies.';

  // Flatten transactions from paginated query
  const expensesList = useMemo(() => {
    const items = transactionsQuery.data?.pages?.flatMap((page) => page.items || []) || [];
    // Map finance fields to expected format
    return items.map((tx) => ({
      id: tx.id,
      date_operation: tx.date_operation,
      libelle: tx.label,
      montant_ht: Math.abs(Number(tx.amount) || 0),
      categorie: tx.category_name || tx.category_code || '—',
      categorie_id: tx.category_id,
      cost_center: tx.cost_center_name || '—',
      cost_center_id: tx.cost_center_id,
    }));
  }, [transactionsQuery.data]);

  // Maps pour lookup rapide
  const categoryById = useMemo(() => {
    const map = new Map();
    (categories.data || []).forEach((c) => map.set(c.id, c));
    return map;
  }, [categories.data]);

  const costCenterById = useMemo(() => {
    const map = new Map();
    (costCenters.data || []).forEach((cc) => map.set(cc.id, cc));
    return map;
  }, [costCenters.data]);

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

  const categoryTotals = useMemo(() => {
    return scopedExpenses.reduce((acc, expense) => {
      const label = expense.categorie || 'Autres charges';
      const amount = Number(expense.montant_ht) || 0;
      acc[label] = (acc[label] || 0) + amount;
      return acc;
    }, {});
  }, [scopedExpenses]);

  const costCenterTotals = useMemo(() => {
    return scopedExpenses.reduce((acc, expense) => {
      const label = expense.cost_center || 'Non affecté';
      const amount = Number(expense.montant_ht) || 0;
      acc[label] = (acc[label] || 0) + amount;
      return acc;
    }, {});
  }, [scopedExpenses]);

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
              onClick={() => {
                if (!categoryName) return;
                const code = categoryName.toUpperCase().replace(/\s+/g, '_').slice(0, 20);
                createCategory.mutate(
                  { entity_id: entityId, code, name: categoryName },
                  { onSuccess: () => setCategoryName('') }
                );
              }}
            >
              Ajouter
            </Button>
          </div>
          <ul className="divide-y divide-slate-100 text-sm">
            {(categories.data ?? []).map((cat) => (
              <li key={cat.id} className="py-1 text-slate-700">
                {cat.name}
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
              onClick={() => {
                if (!costCenterName) return;
                const code = costCenterName.toUpperCase().replace(/\s+/g, '_').slice(0, 20);
                createCostCenter.mutate(
                  { entity_id: entityId, code, name: costCenterName },
                  { onSuccess: () => setCostCenterName('') }
                );
              }}
            >
              Ajouter
            </Button>
          </div>
          <ul className="divide-y divide-slate-100 text-sm">
            {(costCenters.data ?? []).map((cc) => (
              <li key={cc.id} className="py-1 text-slate-700">
                {cc.name}
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
