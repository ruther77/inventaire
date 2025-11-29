import { useMemo } from 'react';
import Card from '../../components/ui/Card.jsx';
import MetricCard from '../../components/ui/MetricCard.jsx';
import { useRestaurantDashboard, useRestaurantTvaSummary } from '../../hooks/useRestaurant.js';

const currency = (value) => `${value.toFixed(2)} €`;

export default function RestaurantDashboard() {
  const dashboardQuery = useRestaurantDashboard();
  const tvaQuery = useRestaurantTvaSummary();

  const data = dashboardQuery.data ?? {};
  const metrics = data.metrics ?? {
    current_month_charges: 0,
    avg_margin_pct: 0,
    active_menu_items: 0,
    margin_alerts: 0,
  };
  const monthly = data.charges_monthly ?? [];
  const byCenter = data.charges_by_center ?? [];
  const menuCosts = data.menu_costs ?? [];
  const lowStock = data.low_stock_ingredients ?? [];
  const tvaEntries = tvaQuery.data ?? [];
  const tvaDue = useMemo(() => {
    if (!tvaEntries.length) return 0;
    return tvaEntries.reduce((sum, entry) => sum + (Number(entry.montant_tva) || 0), 0);
  }, [tvaEntries]);

  const worstMargins = [...menuCosts].sort((a, b) => a.marge_pct - b.marge_pct).slice(0, 3);
  const bestMargins = [...menuCosts].sort((a, b) => b.marge_pct - a.marge_pct).slice(0, 3);
  const totalCenter = byCenter.reduce((sum, entry) => sum + entry.total_ht, 0);

  if (dashboardQuery.isLoading) {
    return (
      <div className="restaurant-panel">
        <p className="text-sm text-slate-500">Chargement des indicateurs…</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Card className="bg-gradient-to-br from-rose-600 to-orange-400 text-white">
        <div className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-white/70">restaurant hq</p>
          <h1 className="text-3xl font-semibold">Pilotage cuisine & charges</h1>
          <p className="text-sm text-white/90">
            Suivez vos charges fixes, identifiez les plats à faible marge et surveillez les matières critiques depuis
            un cockpit unifié.
          </p>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Charges du mois" value={currency(metrics.current_month_charges)} hint="Montant HT" />
        <MetricCard label="Marge moyenne" value={`${metrics.avg_margin_pct.toFixed(1)} %`} hint="Brute menu" />
        <MetricCard label="Plats actifs" value={metrics.active_menu_items} hint="Carte publiée" />
        <MetricCard label="Alertes marge" value={metrics.margin_alerts} hint="< 30 % de marge" />
        <MetricCard label="TVA à décaisser" value={currency(tvaDue)} hint="Période TVA (6 mois)" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">charges mensuelles</p>
            <h3 className="text-lg font-semibold text-slate-900">Historique des coûts fixes</h3>
          </div>
          {monthly.length === 0 ? (
            <p className="text-sm text-slate-500">Aucune dépense saisie pour l’instant.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Mois</th>
                    <th className="px-3 py-2">Total HT</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {monthly.map((row) => (
                    <tr key={row.label}>
                      <td className="px-3 py-2 text-slate-700">{row.label}</td>
                      <td className="px-3 py-2 font-semibold text-slate-900">{currency(row.total_ht)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card className="flex flex-col gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">répartition</p>
            <h3 className="text-lg font-semibold text-slate-900">Centres de coûts</h3>
          </div>
          {byCenter.length === 0 ? (
            <p className="text-sm text-slate-500">Aucun centre de coûts alimenté.</p>
          ) : (
            <div className="space-y-3">
              {byCenter.map((entry) => {
                const ratio = totalCenter ? Math.round((entry.total_ht / totalCenter) * 100) : 0;
                return (
                  <div key={entry.label} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-sm font-medium text-slate-700">
                      <span>{entry.label}</span>
                      <span>{currency(entry.total_ht)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-rose-500 to-orange-400"
                        style={{ width: `${ratio}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="flex flex-col gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">marges</p>
            <h3 className="text-lg font-semibold text-slate-900">Plats sous surveillance</h3>
          </div>
          {worstMargins.length === 0 ? (
            <p className="text-sm text-slate-500">Ajoutez des plats et leurs ingrédients pour suivre les marges.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Plat</th>
                    <th className="px-3 py-2">Coût matière</th>
                    <th className="px-3 py-2">Marge</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {worstMargins.map((plat) => (
                    <tr key={plat.id}>
                      <td className="px-3 py-2 font-semibold text-slate-900">
                        {plat.nom}
                        <span className="block text-xs font-normal uppercase tracking-[0.3em] text-slate-400">
                          {plat.categorie ?? 'NC'}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-slate-600">{currency(plat.cout_matiere)}</td>
                      <td className="px-3 py-2 font-semibold text-rose-600">
                        {currency(plat.marge_brute)} ({plat.marge_pct.toFixed(1)} %)
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card className="flex flex-col gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">succès cartes</p>
            <h3 className="text-lg font-semibold text-slate-900">Top marges</h3>
          </div>
          {bestMargins.length === 0 ? (
            <p className="text-sm text-slate-500">Aucun plat rentable pour le moment.</p>
          ) : (
            <div className="space-y-3">
              {bestMargins.map((plat) => (
                <div key={plat.id} className="rounded-2xl border border-slate-100 p-3 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{plat.nom}</p>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{plat.categorie ?? 'NC'}</p>
                    </div>
                    <span className="text-sm font-semibold text-emerald-600">{plat.marge_pct.toFixed(1)} %</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Coût matière : <span className="font-semibold text-slate-700">{currency(plat.cout_matiere)}</span>
                  </p>
                  <p className="text-xs text-slate-500">
                    Prix carte : <span className="font-semibold text-slate-700">{currency(plat.prix_vente_ttc)}</span>
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card className="flex flex-col gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">stocks cuisine</p>
          <h3 className="text-lg font-semibold text-slate-900">Ingrédients à réapprovisionner</h3>
        </div>
        {lowStock.length === 0 ? (
          <p className="text-sm text-slate-500">Aucune alerte de stock critique.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                  <th className="px-3 py-2">Ingrédient</th>
                  <th className="px-3 py-2">Stock</th>
                  <th className="px-3 py-2">Coût</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lowStock.map((ing) => (
                  <tr key={ing.id}>
                    <td className="px-3 py-2 font-medium text-slate-900">{ing.nom}</td>
                    <td className="px-3 py-2 text-slate-600">
                      {ing.stock_actuel.toFixed(2)} {ing.unite_base}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{currency(ing.cout_unitaire)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
