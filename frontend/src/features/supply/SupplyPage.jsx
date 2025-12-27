/**
 * Page Plan d'Approvisionnement.
 *
 * Cette page permet de générer et gérer un plan d'approvisionnement optimisé basé sur les prévisions de ventes.
 * Elle affiche:
 * - Les KPIs du plan (articles analysés, réassorts, unités à commander, valeur, marge)
 * - Des filtres de couverture cible, seuil d'alerte, ventes minimales
 * - Une liste des produits prioritaires nécessitant une commande urgente
 * - Un tableau complet avec classification ABC-XYZ et priorités
 * - Une ventilation par fournisseur pour créer des commandes groupées
 *
 * Fonctionnalités principales:
 * - Calcul automatique des besoins basé sur la couverture cible
 * - Classification ABC (valeur) et XYZ (régularité) des produits
 * - Priorisation automatique (Critique, Tendue, Confortable, Excédentaire)
 * - Filtrage multi-critères (catégories, recherche, seuils)
 * - Génération de commandes par fournisseur
 * - Export CSV du plan complet
 * - Badges visuels pour identification rapide des priorités
 *
 * @component
 *
 * @example
 * <SupplyPage />
 */

import { useMemo, useState, useEffect, useCallback } from 'react';
import {
  Package,
  TrendingUp,
  AlertTriangle,
  Download,
  Filter,
  Search,
  Truck,
  ShoppingCart,
  BarChart3,
  ChevronUp,
  ChevronDown,
  Loader2,
} from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import FiltersDrawer from '../../components/ui/FiltersDrawer.jsx';
import { CreateOrderModal } from '../../components/modals/index.js';
import { useSupplyPlan } from '../../hooks/useSupplyPlan.js';

const defaultFilters = {
  targetCoverage: 21,
  alertThreshold: 7,
  minDailySales: 0,
  categories: [],
  search: '',
};

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });
const currencyFormatter = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' });

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
  A: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  B: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  C: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const XYZ_COLORS = {
  X: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  Y: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  Z: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const PRIORITY_COLORS = {
  Critique: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  Tendue: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  Confortable: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  Excédentaire: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

const ClassificationBadge = ({ abc, xyz }) => {
  const abcClass = ABC_COLORS[abc] || ABC_COLORS.C;
  const xyzClass = XYZ_COLORS[xyz] || XYZ_COLORS.Z;
  return (
    <div className="flex gap-1.5 text-[10px] font-semibold uppercase">
      <span className={`rounded-full px-2 py-0.5 border ${abcClass}`}>{abc || 'C'}</span>
      <span className={`rounded-full px-2 py-0.5 border ${xyzClass}`}>{xyz || 'Z'}</span>
    </div>
  );
};

const PriorityBadge = ({ priority }) => {
  const colorClass = PRIORITY_COLORS[priority] || PRIORITY_COLORS.Confortable;
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold border ${colorClass}`}>
      {priority}
    </span>
  );
};

export default function SupplyPage() {
  const [filters, setFilters] = useState(defaultFilters);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [categoriesInitialized, setCategoriesInitialized] = useState(false);
  const [orderModalOpen, setOrderModalOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);

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

  // Liste des produits urgents à commander en priorité
  // Filtre uniquement les items Critiques ou Tendus avec quantité à commander > 0
  const urgencyList = useMemo(
    () =>
      plan.items
        .filter(
          (item) =>
            item.quantite_a_commander > 0 &&
            (item.niveau_priorite === 'Critique' || item.niveau_priorite === 'Tendue'),
        )
        .slice(0, 6), // Top 6 urgences
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

  const handleCategoryToggle = useCallback((category) => {
    setFilters((prev) => {
      const exists = prev.categories.includes(category);
      if (exists) {
        const remaining = prev.categories.filter((cat) => cat !== category);
        return { ...prev, categories: remaining };
      }
      return { ...prev, categories: [...prev.categories, category] };
    });
  }, []);

  const handleResetFilters = useCallback(() =>
    setFilters({
      ...defaultFilters,
      categories: plan.available_categories ?? [],
    }), [plan.available_categories]);

  const handleExportPlan = useCallback(() => downloadCsv('plan_approvisionnement.csv', plan.items), [plan.items]);

  const handleCreateOrder = useCallback((supplier) => {
    setSelectedSupplier(supplier);
    setOrderModalOpen(true);
  }, []);

  const loadingState = isLoading || isFetching;

  return (
    <>
      <div className="flex flex-col gap-6 p-6">
        {/* Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20">
                <Package className="w-6 h-6 text-blue-400" />
              </div>
              Plan d'approvisionnement
            </h1>
            <p className="text-slate-400 mt-1">
              Optimisation des commandes basée sur la couverture cible et les prévisions
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="subtle" size="sm" onClick={() => setDrawerOpen(true)}>
              <Filter className="w-4 h-4" />
              Filtres avancés
            </Button>
            {plan.items.length > 0 && (
              <Button variant="primary" size="sm" onClick={handleExportPlan}>
                <Download className="w-4 h-4" />
                Exporter CSV
              </Button>
            )}
          </div>
        </div>

        {/* Summary KPIs */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <MetricCard
            icon={<BarChart3 className="w-5 h-5" />}
            label="Articles analysés"
            value={plan.summary.analyzed}
            color="blue"
          />
          <MetricCard
            icon={<AlertTriangle className="w-5 h-5" />}
            label="Réassorts recommandés"
            value={plan.summary.recommended_count}
            color="amber"
          />
          <MetricCard
            icon={<Package className="w-5 h-5" />}
            label="Unités à commander"
            value={numberFormatter.format(plan.summary.units_to_order)}
            color="purple"
          />
          <MetricCard
            icon={<ShoppingCart className="w-5 h-5" />}
            label="Valeur estimée"
            value={currencyFormatter.format(plan.summary.value_total)}
            color="emerald"
          />
          <MetricCard
            icon={<TrendingUp className="w-5 h-5" />}
            label="Marge potentielle"
            value={currencyFormatter.format(plan.summary.margin_total)}
            color="teal"
          />
        </div>

        {/* Filters card */}
        <Card className="glass-panel p-6">
          <div className="grid gap-6 lg:grid-cols-4">
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
                className="mt-2 w-full accent-blue-500"
              />
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">7</span>
                <span className="text-white font-semibold">{filters.targetCoverage} jours</span>
                <span className="text-slate-500">60</span>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Seuil d'alerte (jours)
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
                className="mt-2 w-full accent-amber-500"
              />
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">1</span>
                <span className="text-white font-semibold">{filters.alertThreshold} jours</span>
                <span className="text-slate-500">30</span>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Ventes min/jour
              </label>
              <input
                type="number"
                min={0}
                step={0.1}
                value={filters.minDailySales}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, minDailySales: Number(event.target.value) }))
                }
                className="mt-2 w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recherche</label>
              <div className="relative mt-2">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="search"
                  placeholder="Nom, catégorie ou EAN"
                  value={filters.search}
                  onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
                  className="w-full rounded-xl bg-white/5 border border-white/10 pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>
            </div>
          </div>

          {/* Categories */}
          {plan.available_categories.length > 0 && (
            <div className="mt-6 pt-6 border-t border-white/10">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Catégories</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setFilters((prev) => ({ ...prev, categories: plan.available_categories ?? [] }))}
                    className="text-xs text-blue-400 hover:text-blue-300"
                  >
                    Tout sélectionner
                  </button>
                  <span className="text-slate-600">|</span>
                  <button
                    onClick={() => setFilters((prev) => ({ ...prev, categories: [] }))}
                    className="text-xs text-slate-400 hover:text-slate-300"
                  >
                    Aucun
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {plan.available_categories.map((category) => {
                  const checked = filters.categories.includes(category);
                  return (
                    <button
                      key={category}
                      onClick={() => handleCategoryToggle(category)}
                      className={`rounded-full px-4 py-1.5 text-sm transition-all ${
                        checked
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10'
                      }`}
                    >
                      {category}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className="mt-4 flex justify-end">
            <Button variant="ghost" size="sm" onClick={handleResetFilters}>
              Réinitialiser les filtres
            </Button>
          </div>
        </Card>

        {/* Loading / Error states */}
        {loadingState && (
          <div className="flex items-center justify-center gap-3 py-12">
            <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
            <span className="text-slate-400">Analyse des stocks en cours...</span>
          </div>
        )}

        {isError && (
          <Card className="glass-panel p-6 border-rose-500/30">
            <div className="flex items-center gap-3 text-rose-400">
              <AlertTriangle className="w-5 h-5" />
              <span>Impossible de calculer le plan d'approvisionnement pour le moment.</span>
            </div>
          </Card>
        )}

        {/* Priority items */}
        {!loadingState && !isError && urgencyList.length > 0 && (
          <Card className="glass-panel p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h3 className="text-lg font-semibold text-white">Priorités immédiates</h3>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {urgencyList.map((item) => (
                <div
                  key={item.id}
                  className="rounded-xl bg-white/5 border border-white/10 p-4 hover:bg-white/[0.07] transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white truncate">{item.nom}</p>
                      <p className="text-xs text-slate-500 uppercase tracking-wide">
                        {item.categorie ?? 'Non classé'}
                      </p>
                    </div>
                    <PriorityBadge priority={item.niveau_priorite} />
                  </div>
                  <ClassificationBadge abc={item.abc_class} xyz={item.xyz_class} />
                  <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-slate-500">Stock:</span>{' '}
                      <span className="text-white">{item.stock_actuel} u</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Couverture:</span>{' '}
                      <span className="text-white">
                        {item.couverture_jours ? `${item.couverture_jours.toFixed(1)} j` : '—'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Prévision:</span>{' '}
                      <span className="text-white">{item.ventes_prevision?.toFixed(2) ?? '-'} u/j</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Commande:</span>{' '}
                      <span className="text-emerald-400 font-semibold">{item.quantite_a_commander} u</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Main table */}
        {!loadingState && !isError && (
          <Card className="glass-panel overflow-hidden">
            {plan.items.length === 0 ? (
              <div className="p-12 text-center">
                <Package className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">Aucun article ne correspond aux filtres appliqués.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-widest text-slate-500 border-b border-white/10">
                      <th className="px-4 py-4">Produit</th>
                      <th className="px-4 py-4">Catégorie</th>
                      <th className="px-4 py-4 text-right">Ventes/j</th>
                      <th className="px-4 py-4 text-right">Stock</th>
                      <th className="px-4 py-4 text-right">Couverture</th>
                      <th className="px-4 py-4">Priorité</th>
                      <th className="px-4 py-4 text-right">Qté</th>
                      <th className="px-4 py-4 text-right">Valeur</th>
                      <th className="px-4 py-4">Fournisseur</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {plan.items.map((item) => (
                      <tr key={item.id} className="hover:bg-white/[0.03] transition-colors">
                        <td className="px-4 py-4">
                          <p className="font-medium text-white">{item.nom}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-slate-500">{item.ean || '—'}</span>
                            <ClassificationBadge abc={item.abc_class} xyz={item.xyz_class} />
                          </div>
                        </td>
                        <td className="px-4 py-4 text-slate-400">{item.categorie ?? 'Non classé'}</td>
                        <td className="px-4 py-4 text-right text-white">{item.ventes_jour.toFixed(2)}</td>
                        <td className="px-4 py-4 text-right text-white">{item.stock_actuel.toFixed(0)}</td>
                        <td className="px-4 py-4 text-right">
                          <span className={item.couverture_jours < filters.alertThreshold ? 'text-rose-400' : 'text-white'}>
                            {item.couverture_jours !== null && item.couverture_jours !== undefined
                              ? `${item.couverture_jours.toFixed(1)} j`
                              : '—'}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <PriorityBadge priority={item.niveau_priorite} />
                        </td>
                        <td className="px-4 py-4 text-right font-semibold text-emerald-400">
                          {item.quantite_a_commander > 0 ? `+${item.quantite_a_commander}` : '—'}
                        </td>
                        <td className="px-4 py-4 text-right text-white">
                          {currencyFormatter.format(item.valeur_commande)}
                        </td>
                        <td className="px-4 py-4 text-slate-400">{item.fournisseur ?? 'Non renseigné'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}

        {/* Supplier breakdown */}
        {!loadingState && !isError && plan.supplier_breakdown.length > 0 && (
          <Card className="glass-panel p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
                  <Truck className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Commandes par fournisseur</h3>
                  <p className="text-sm text-slate-400">Générez des bons de commande par fournisseur</p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <select
                  className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-blue-500 focus:outline-none appearance-none cursor-pointer min-w-[200px]"
                  value={supplierFocus ?? ''}
                  onChange={(event) => setSupplierFocus(event.target.value)}
                >
                  {plan.supplier_breakdown.map((supplier) => (
                    <option key={supplier.fournisseur} value={supplier.fournisseur} className="bg-slate-800">
                      {supplier.fournisseur} ({supplier.articles} articles)
                    </option>
                  ))}
                </select>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleCreateOrder(supplierFocus)}
                  disabled={!supplierLines.length}
                >
                  <ShoppingCart className="w-4 h-4" />
                  Créer commande
                </Button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500 border-b border-white/10">
                    <th className="px-4 py-3">Fournisseur</th>
                    <th className="px-4 py-3 text-right">Références</th>
                    <th className="px-4 py-3 text-right">Quantité</th>
                    <th className="px-4 py-3 text-right">Valeur</th>
                    <th className="px-4 py-3 text-right">Marge</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {plan.supplier_breakdown.map((supplier) => (
                    <tr
                      key={supplier.fournisseur}
                      className={`transition-colors cursor-pointer ${
                        supplierFocus === supplier.fournisseur
                          ? 'bg-blue-500/10'
                          : 'hover:bg-white/[0.03]'
                      }`}
                      onClick={() => setSupplierFocus(supplier.fournisseur)}
                    >
                      <td className="px-4 py-4">
                        <span className="font-medium text-white">{supplier.fournisseur}</span>
                      </td>
                      <td className="px-4 py-4 text-right text-white">{supplier.articles}</td>
                      <td className="px-4 py-4 text-right text-white">{numberFormatter.format(supplier.quantite)}</td>
                      <td className="px-4 py-4 text-right text-white">{currencyFormatter.format(supplier.valeur)}</td>
                      <td className="px-4 py-4 text-right text-emerald-400">
                        {currencyFormatter.format(supplier.marge)}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <Button
                          variant="subtle"
                          size="xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreateOrder(supplier.fournisseur);
                          }}
                        >
                          Commander
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      {/* Filters drawer - Nouveau design */}
      <FiltersDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="Filtres avancés"
        filters={[
          {
            id: 'categories',
            label: 'Catégories',
            type: 'checkbox',
            options: plan.available_categories.map(cat => ({
              value: cat,
              label: cat,
              count: plan.items.filter(i => i.categorie === cat).length,
            })),
          },
          {
            id: 'priority',
            label: 'Priorité',
            type: 'checkbox',
            options: [
              { value: 'Critique', label: 'Critique', count: plan.items.filter(i => i.niveau_priorite === 'Critique').length },
              { value: 'Tendue', label: 'Tendue', count: plan.items.filter(i => i.niveau_priorite === 'Tendue').length },
              { value: 'Confortable', label: 'Confortable', count: plan.items.filter(i => i.niveau_priorite === 'Confortable').length },
              { value: 'Excédentaire', label: 'Excédentaire', count: plan.items.filter(i => i.niveau_priorite === 'Excédentaire').length },
            ],
          },
          {
            id: 'price',
            label: 'Fourchette de prix',
            type: 'range',
            min: 0,
            max: Math.max(...plan.items.map(i => i.valeur_commande || 0), 100),
          },
        ]}
        activeFilters={{
          categories: filters.categories,
        }}
        onApply={(newFilters) => {
          if (newFilters.categories) {
            setFilters(prev => ({ ...prev, categories: newFilters.categories }));
          }
        }}
        onReset={handleResetFilters}
        resultCount={plan.items.length}
      />

      {/* Order modal */}
      <CreateOrderModal
        open={orderModalOpen}
        onClose={() => setOrderModalOpen(false)}
        supplier={selectedSupplier}
        items={plan.items.filter((item) => item.fournisseur === selectedSupplier && item.quantite_a_commander > 0)}
        onSuccess={() => {
          setOrderModalOpen(false);
        }}
      />
    </>
  );
}

function MetricCard({ icon, label, value, color = 'blue' }) {
  const colors = {
    blue: 'from-blue-500/20 to-blue-600/20 border-blue-500/20',
    amber: 'from-amber-500/20 to-orange-500/20 border-amber-500/20',
    purple: 'from-purple-500/20 to-pink-500/20 border-purple-500/20',
    emerald: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/20',
    teal: 'from-teal-500/20 to-cyan-500/20 border-teal-500/20',
  };

  const iconColors = {
    blue: 'text-blue-400',
    amber: 'text-amber-400',
    purple: 'text-purple-400',
    emerald: 'text-emerald-400',
    teal: 'text-teal-400',
  };

  return (
    <div className={`rounded-2xl bg-gradient-to-br ${colors[color]} border p-5`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={iconColors[color]}>{icon}</div>
        <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
