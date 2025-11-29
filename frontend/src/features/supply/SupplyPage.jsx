import { useMemo, useState, useEffect } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import FiltersDrawer from '../../components/ui/FiltersDrawer.jsx';
import { useSupplyPlan } from '../../hooks/useSupplyPlan.js';

const defaultFilters = {
  targetCoverage: 21,
  alertThreshold: 7,
  minDailySales: 0,
  categories: [],
  search: '',
};

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

const csvEscape = (value) => {
  const text = value === null || value === undefined ? '' : String(value);
  return `"${text.replace(/"/g, '""')}"`;
};

const buildCsv = (items) => {
  const headers = [
    'Produit',
    'Categorie',
    'Classe_ABC',
    'Classe_XYZ',
    'Ventes_jour',
    'Prevision_jour',
    'Stock',
    'Couverture_jours',
    'Ecart_couverture',
    'Priorite',
    'Quantite_commander',
    'Quantite_auto',
    'Valeur_commande',
    'Marge_pct',
    'Marge_commande',
    'Fournisseur',
    'EAN',
  ];

  const rows = items.map((item) => [
    item.nom,
    item.categorie ?? '',
    item.abc_class ?? '',
    item.xyz_class ?? '',
    item.ventes_jour,
    item.ventes_prevision ?? '',
    item.stock_actuel,
    item.couverture_jours ?? '',
    item.ecart_couverture ?? '',
    item.niveau_priorite,
    item.quantite_a_commander,
    item.quantite_auto ?? '',
    item.valeur_commande,
    item.marge_pct ?? '',
    item.marge_commande,
    item.fournisseur ?? '',
    item.ean ?? '',
  ]);

  return [headers, ...rows]
    .map((line) => line.map(csvEscape).join(','))
    .join('\n');
};

const downloadCsv = (filename, items) => {
  if (!items.length) return;
  const blob = new Blob([buildCsv(items)], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const ABC_COLORS = {
  A: 'bg-emerald-100 text-emerald-700',
  B: 'bg-amber-100 text-amber-700',
  C: 'bg-slate-100 text-slate-600',
};
const XYZ_COLORS = {
  X: 'bg-blue-100 text-blue-700',
  Y: 'bg-indigo-100 text-indigo-700',
  Z: 'bg-slate-100 text-slate-600',
};

const ClassificationBadge = ({ abc, xyz }) => {
  const abcClass = ABC_COLORS[abc] || ABC_COLORS.C;
  const xyzClass = XYZ_COLORS[xyz] || XYZ_COLORS.Z;
  return (
    <div className="mt-1 flex gap-1 text-[11px] font-semibold uppercase">
      <span className={`rounded-full px-2 py-0.5 ${abcClass}`}>ABC {abc || 'C'}</span>
      <span className={`rounded-full px-2 py-0.5 ${xyzClass}`}>XYZ {xyz || 'Z'}</span>
    </div>
  );
};

export default function SupplyPage() {
  const [filters, setFilters] = useState(defaultFilters);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [categoriesInitialized, setCategoriesInitialized] = useState(false);
  const { data, isLoading, isFetching, isError } = useSupplyPlan(filters);

  const plan = data ?? {
    summary: { analyzed: 0, recommended_count: 0, units_to_order: 0, value_total: 0, margin_total: 0 },
    items: [],
    supplier_breakdown: [],
    available_categories: [],
  };

  useEffect(() => {
    if (categoriesInitialized || !plan.available_categories.length) {
      return;
    }
    setFilters((prev) => ({ ...prev, categories: plan.available_categories }));
    setCategoriesInitialized(true);
  }, [plan.available_categories, categoriesInitialized]);

  const urgencyList = useMemo(
    () =>
      plan.items
        .filter(
          (item) =>
            item.quantite_a_commander > 0 &&
            (item.niveau_priorite === 'Critique' || item.niveau_priorite === 'Tendue'),
        )
        .slice(0, 6),
    [plan.items],
  );

  const [supplierFocus, setSupplierFocus] = useState(null);

  useEffect(() => {
    if (!plan.supplier_breakdown.length) {
      setSupplierFocus(null);
      return;
    }
    if (!supplierFocus) {
      setSupplierFocus(plan.supplier_breakdown[0].fournisseur);
      return;
    }
    const stillExists = plan.supplier_breakdown.some((supplier) => supplier.fournisseur === supplierFocus);
    if (!stillExists) {
      setSupplierFocus(plan.supplier_breakdown[0].fournisseur);
    }
  }, [plan.supplier_breakdown, supplierFocus]);

  const supplierLines = useMemo(() => {
    if (!supplierFocus) return [];
    return plan.items.filter((item) => item.fournisseur === supplierFocus && item.quantite_a_commander > 0);
  }, [plan.items, supplierFocus]);

  const handleCategoryToggle = (category) => {
    setFilters((prev) => {
      const exists = prev.categories.includes(category);
      if (exists) {
        const remaining = prev.categories.filter((cat) => cat !== category);
        return { ...prev, categories: remaining };
      }
      return { ...prev, categories: [...prev.categories, category] };
    });
  };

  const handleResetFilters = () =>
    setFilters({
      ...defaultFilters,
      categories: plan.available_categories ?? [],
    });

  const handleExportPlan = () => downloadCsv('plan_approvisionnement.csv', plan.items);
  const handleExportSupplier = () => {
    if (!supplierFocus || !supplierLines.length) return;
    const slug = supplierFocus.toLowerCase().replace(/\s+/g, '_');
    downloadCsv(`commande_${slug}.csv`, supplierLines);
  };

  const loadingState = isLoading || isFetching;

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => setDrawerOpen(true)}>
            Ouvrir les filtres avancés
          </Button>
        </div>
      <Card className="flex flex-col gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">approvisionnement</p>
          <h2 className="text-2xl font-semibold text-slate-900">Plan dynamique</h2>
          <p className="text-sm text-slate-500">
            Calcule instantané des réassorts prioritaires en fonction de la couverture cible, des seuils d&apos;alerte
            et de la rotation produit.
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Couverture cible (jours)
            </label>
            <input
              type="range"
              min={7}
              max={60}
              value={filters.targetCoverage}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, targetCoverage: Number(event.target.value) }))
              }
              className="mt-2 w-full"
            />
            <p className="text-sm text-slate-600">{filters.targetCoverage} jours</p>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Seuil d&apos;alerte (jours)
            </label>
            <input
              type="range"
              min={1}
              max={30}
              value={filters.alertThreshold}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  alertThreshold: Math.min(Number(event.target.value), prev.targetCoverage),
                }))
              }
              className="mt-2 w-full"
            />
            <p className="text-sm text-slate-600">{filters.alertThreshold} jours</p>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Filtrer par ventes/jour
            </label>
            <input
              type="number"
              min={0}
              step={0.1}
              value={filters.minDailySales}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, minDailySales: Number(event.target.value) }))
              }
              className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recherche</label>
            <input
              type="search"
              placeholder="Nom, catégorie ou EAN"
              value={filters.search}
              onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
              className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
            />
          </div>
        </div>
        {plan.available_categories.length > 0 && (
          <div className="rounded-2xl border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Catégories</p>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, categories: plan.available_categories ?? [] }))
                  }
                >
                  Tout sélectionner
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFilters((prev) => ({ ...prev, categories: [] }))}
                >
                  Ne rien filtrer
                </Button>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-3">
              {plan.available_categories.map((category) => {
                const checked = filters.categories.includes(category);
                return (
                  <label
                    key={category}
                    className={`cursor-pointer rounded-full border px-4 py-1 text-sm ${
                      checked ? 'border-brand-400 bg-brand-50 text-brand-700' : 'border-slate-200 text-slate-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="mr-2"
                      checked={checked}
                      onChange={() => handleCategoryToggle(category)}
                    />
                    {category}
                  </label>
                );
              })}
            </div>
          </div>
        )}
        <div className="flex flex-wrap gap-3">
          <Button variant="ghost" onClick={handleResetFilters}>
            Réinitialiser
          </Button>
          {plan.items.length > 0 && (
            <Button variant="brand" onClick={handleExportPlan}>
              Exporter le plan (CSV)
            </Button>
          )}
        </div>
      </Card>

      <Card className="flex flex-col gap-4">
        {loadingState && <p className="text-sm text-slate-500">Analyse des stocks…</p>}
        {isError && (
          <p className="text-sm text-rose-500">
            Impossible de calculer le plan d&apos;approvisionnement pour le moment.
          </p>
        )}
        {!loadingState && !isError && (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              <Metric label="Articles analysés" value={plan.summary.analyzed} />
              <Metric label="Réassorts recommandés" value={plan.summary.recommended_count} />
              <Metric label="Unités à commander" value={plan.summary.units_to_order} />
              <Metric label="Valeur estimée" value={`${numberFormatter.format(plan.summary.value_total)} €`} />
              <Metric label="Marge potentielle" value={`${numberFormatter.format(plan.summary.margin_total)} €`} />
            </div>
            {urgencyList.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-slate-400">priorités</p>
                <div className="mt-3 grid gap-3 lg:grid-cols-3">
                  {urgencyList.map((item) => (
                    <div
                      key={item.id}
                      className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-700"
                    >
                      <p className="font-semibold text-slate-900">{item.nom}</p>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                        {item.categorie ?? 'Non classé'}
                      </p>
                      <ClassificationBadge abc={item.abc_class} xyz={item.xyz_class} />
                      <p className="mt-2 text-sm">
                        Stock {item.stock_actuel} u · Couverture{' '}
                        {item.couverture_jours ? `${item.couverture_jours.toFixed(1)} j` : '—'}
                      </p>
                      <p className="text-sm">Prévision : {item.ventes_prevision?.toFixed(2) ?? '-'} u/j</p>
                      <p className="text-sm">
                        Commande plan : {item.quantite_a_commander} u · Auto: {item.quantite_auto ?? 0} u
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      {!loadingState && !isError && (
        <>
          <Card className="p-0">
            {plan.items.length === 0 ? (
              <p className="p-6 text-sm text-slate-500">Aucun article ne correspond aux filtres appliqués.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                      <th className="px-4 py-3">Produit</th>
                      <th className="px-4 py-3">Catégorie</th>
                      <th className="px-4 py-3">Ventes/j</th>
                      <th className="px-4 py-3">Prévision/j</th>
                      <th className="px-4 py-3">Stock</th>
                      <th className="px-4 py-3">Couverture</th>
                      <th className="px-4 py-3">Priorité</th>
                      <th className="px-4 py-3">Qté</th>
                      <th className="px-4 py-3">Auto</th>
                      <th className="px-4 py-3">Valeur</th>
                      <th className="px-4 py-3">Marge</th>
                      <th className="px-4 py-3">Fournisseur</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {plan.items.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-3">
                          <p className="font-medium text-slate-900">{item.nom}</p>
                          <p className="text-xs text-slate-400">EAN {item.ean || '—'}</p>
                          <ClassificationBadge abc={item.abc_class} xyz={item.xyz_class} />
                        </td>
                        <td className="px-4 py-3 text-slate-600">{item.categorie ?? 'Non classé'}</td>
                        <td className="px-4 py-3">{item.ventes_jour.toFixed(2)}</td>
                        <td className="px-4 py-3">{item.ventes_prevision?.toFixed(2) ?? '—'}</td>
                        <td className="px-4 py-3">{item.stock_actuel.toFixed(0)}</td>
                        <td className="px-4 py-3">
                          {item.couverture_jours !== null && item.couverture_jours !== undefined
                            ? `${item.couverture_jours.toFixed(1)} j`
                            : '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold">
                            {item.niveau_priorite}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-semibold text-slate-900">{item.quantite_a_commander}</td>
                        <td className="px-4 py-3">{item.quantite_auto ?? 0}</td>
                        <td className="px-4 py-3">{numberFormatter.format(item.valeur_commande)} €</td>
                        <td className="px-4 py-3">
                          {item.marge_commande ? `${numberFormatter.format(item.marge_commande)} €` : '—'}
                        </td>
                        <td className="px-4 py-3 text-slate-600">{item.fournisseur ?? 'Non renseigné'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {plan.supplier_breakdown.length > 0 && (
            <Card className="flex flex-col gap-4">
              <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] text-slate-400">commandes fournisseurs</p>
                  <h3 className="text-xl font-semibold text-slate-900">Synthèse par fournisseur</h3>
                </div>
                <div className="flex flex-wrap gap-3">
                  <select
                    className="rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                    value={supplierFocus ?? ''}
                    onChange={(event) => setSupplierFocus(event.target.value)}
                  >
                    {plan.supplier_breakdown.map((supplier) => (
                      <option key={supplier.fournisseur} value={supplier.fournisseur}>
                        {supplier.fournisseur}
                      </option>
                    ))}
                  </select>
                  <Button variant="brand" onClick={handleExportSupplier} disabled={!supplierLines.length}>
                    Exporter {supplierFocus || ''}
                  </Button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                      <th className="px-4 py-3">Fournisseur</th>
                      <th className="px-4 py-3">Références</th>
                      <th className="px-4 py-3">Quantité</th>
                      <th className="px-4 py-3">Valeur</th>
                      <th className="px-4 py-3">Marge</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {plan.supplier_breakdown.map((supplier) => (
                      <tr key={supplier.fournisseur}>
                        <td className="px-4 py-3 font-medium text-slate-900">{supplier.fournisseur}</td>
                        <td className="px-4 py-3">{supplier.articles}</td>
                        <td className="px-4 py-3">{supplier.quantite}</td>
                        <td className="px-4 py-3">{numberFormatter.format(supplier.valeur)} €</td>
                        <td className="px-4 py-3">{numberFormatter.format(supplier.marge)} €</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {supplierLines.length === 0 && (
                <p className="text-sm text-slate-500">
                  Sélectionnez un fournisseur avec des lignes de commande pour générer un export dédié.
                </p>
              )}
            </Card>
          )}
        </>
      )}
    </div>
    <FiltersDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} title="Paramètres approvisionnement">
      <div className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Couverture cible</p>
          <p className="text-lg font-semibold text-slate-900">{filters.targetCoverage} jours</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Seuil alerte</p>
          <p className="text-lg font-semibold text-slate-900">{filters.alertThreshold} jours</p>
        </div>
        <p className="text-sm text-slate-500">Modifiez ces valeurs directement depuis la barre supérieure dans quelques instants.</p>
      </div>
    </FiltersDrawer>
    </>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
