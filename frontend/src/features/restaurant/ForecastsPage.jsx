import { useMemo, useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useRestaurantForecastOverview } from '../../hooks/useRestaurant.js';

const HORIZON_OPTIONS = [
  { value: 7, label: '7 jours' },
  { value: 14, label: '14 jours' },
  { value: 30, label: '30 jours' },
  { value: 60, label: '60 jours' },
  { value: 90, label: '90 jours' },
  { value: 120, label: '120 jours' },
];

const GRANULARITY_OPTIONS = [
  { value: 'daily', label: 'Journalier' },
  { value: 'weekly', label: 'Hebdomadaire' },
  { value: 'monthly', label: 'Mensuel (périodes de 30 j)' },
];

const RISK_COLORS = {
  critique: 'text-rose-600',
  alerte: 'text-amber-600',
  surveillance: 'text-emerald-600',
  ok: 'text-slate-500',
};

const currencyFormatter = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 });

export default function ForecastsPage({ context = 'restaurant' }) {
  const [horizon, setHorizon] = useState(30);
  const [granularity, setGranularity] = useState('weekly');
  const [top, setTop] = useState(8);
  const forecastQuery = useRestaurantForecastOverview({ horizonDays: horizon, granularity, top });
  const data = forecastQuery.data;

  const timelineData = useMemo(() => {
    if (!data?.timeline?.length) return [];
    return data.timeline.map((entry) => ({
      label: entry.period_start === entry.period_end ? entry.period_start : `${entry.period_start} → ${entry.period_end}`,
      units: entry.expected_units,
      value: entry.expected_value,
    }));
  }, [data]);

  const categoriesData = useMemo(() => {
    if (!data?.categories?.length) return [];
    return data.categories.map((entry) => ({
      categorie: entry.categorie || 'Autre',
      value: entry.forecast_value,
      units: entry.forecast_daily,
    }));
  }, [data]);

  const metrics = data?.metrics;
  const topProducts = data?.top_products ?? [];
  const contextLabel = context === 'epicerie' ? 'Épicerie HQ' : 'Restaurant HQ';

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Prévisions</p>
        <h1 className="text-2xl font-semibold text-slate-900">{contextLabel} · Propulsé par ARIMA</h1>
        <p className="text-sm text-slate-500">
          Projection glissante construite sur 6 mois d’historique ventes/stock. Ajuste l’horizon et la granularité pour
          simuler différents scénarios.
        </p>
      </div>

      <Card className="flex flex-wrap items-center gap-4">
        <label className="text-sm font-semibold text-slate-600">
          Horizon
          <select
            className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
            value={horizon}
            onChange={(event) => setHorizon(Number(event.target.value))}
          >
            {HORIZON_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-semibold text-slate-600">
          Granularité
          <select
            className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
            value={granularity}
            onChange={(event) => setGranularity(event.target.value)}
          >
            {GRANULARITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-semibold text-slate-600">
          Top produits
          <select
            className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
            value={top}
            onChange={(event) => setTop(Number(event.target.value))}
          >
            {[5, 8, 12, 20].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <Button size="sm" variant="ghost" onClick={() => forecastQuery.refetch()} disabled={forecastQuery.isFetching}>
          {forecastQuery.isFetching ? 'Actualisation…' : 'Actualiser'}
        </Button>
      </Card>

      <Card className="grid gap-4 md:grid-cols-4">
        <Metric
          label="Volume quotidien"
          value={metrics ? `${numberFormatter.format(metrics.total_daily_units || 0)} u.` : '—'}
          hint="Somme des consommations prévues par jour"
        />
        <Metric
          label="Valeur quotidienne"
          value={metrics ? currencyFormatter.format(metrics.total_daily_value || 0) : '—'}
          hint="Basé sur les prix de vente TTC"
        />
        <Metric
          label="Produits à risque"
          value={metrics ? `${metrics.at_risk_items} réf.` : '—'}
          hint="Couverture < seuil d’alerte"
        />
        <Metric
          label="Couverture médiane"
          value={
            metrics?.median_cover_days !== null && metrics?.median_cover_days !== undefined
              ? `${numberFormatter.format(metrics.median_cover_days)} j`
              : '—'
          }
          hint="Stock / prévision"
        />
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Timeline</p>
            <h3 className="text-lg font-semibold text-slate-900">Projection {granularity === 'daily' ? 'journalisée' : granularity === 'weekly' ? 'hebdo' : 'mensuelle'}</h3>
          </div>
          <p className="text-xs text-slate-500">
            {forecastQuery.isFetching ? 'Actualisation en cours…' : `${timelineData.length} point(s)`} • Horizon {horizon} j
          </p>
        </div>
        {timelineData.length ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip
                  formatter={(value, name) =>
                    name === 'value' ? currencyFormatter.format(value) : `${numberFormatter.format(value)} u.`
                  }
                  labelClassName="text-sm font-semibold"
                />
                <Area type="monotone" dataKey="units" name="Unités" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.1} />
                <Area type="monotone" dataKey="value" name="Valeur" stroke="#6366f1" fill="#6366f1" fillOpacity={0.15} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            {forecastQuery.isLoading ? 'Chargement des prévisions…' : 'Pas encore de données suffisantes pour cette période.'}
          </p>
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <Card className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Top produits</p>
            <h3 className="text-lg font-semibold text-slate-900">Couverture & risque</h3>
          </div>
          {topProducts.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Produit</th>
                    <th className="px-3 py-2">Prévision/j</th>
                    <th className="px-3 py-2">Couverture</th>
                    <th className="px-3 py-2">Risque</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {topProducts.map((product) => (
                    <tr key={product.product_id}>
                      <td className="px-3 py-2">
                        <p className="font-semibold text-slate-900">{product.nom}</p>
                        <p className="text-xs text-slate-500">
                          {product.categorie || '—'} {product.ean ? `· ${product.ean}` : ''}
                        </p>
                      </td>
                      <td className="px-3 py-2">
                        {numberFormatter.format(product.forecast_daily)} u.
                        <div className="text-xs text-slate-500">{currencyFormatter.format(product.forecast_value)}</div>
                      </td>
                      <td className="px-3 py-2">
                        {product.stock_cover_days !== null && product.stock_cover_days !== undefined
                          ? `${numberFormatter.format(product.stock_cover_days)} j`
                          : '∞'}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`text-sm font-semibold ${RISK_COLORS[product.risk_level] || 'text-slate-500'}`}>
                          {product.risk_level.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              {forecastQuery.isLoading ? 'Analyse des produits…' : 'Aucune référence prioritaire pour cet horizon.'}
            </p>
          )}
        </Card>

        <Card className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Catégories</p>
            <h3 className="text-lg font-semibold text-slate-900">Poids des familles</h3>
          </div>
          {categoriesData.length ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={categoriesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" />
                  <YAxis dataKey="categorie" type="category" width={140} />
                  <Tooltip
                    formatter={(value, name) =>
                      name === 'value' ? currencyFormatter.format(value) : `${numberFormatter.format(value)} u./jour`
                    }
                  />
                  <Bar dataKey="value" name="Valeur" fill="#1d4ed8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Pas d’historique suffisant pour ventiler par catégorie.</p>
          )}
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value, hint }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
