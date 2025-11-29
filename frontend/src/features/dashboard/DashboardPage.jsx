import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import AnimatedMetricCard from '../../components/ui/AnimatedMetricCard.jsx';
import FiltersDrawer from '../../components/ui/FiltersDrawer.jsx';
import { useProducts } from '../../hooks/useProducts.js';
import { useDashboardMetrics } from '../../hooks/useDashboard.js';
import { lookupProductByBarcode } from '../../api/client.js';
import FiltersPanel from './components/FiltersPanel.jsx';
import StockCards from './components/StockCards.jsx';
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart,
  Legend,
  CartesianGrid,
} from 'recharts';

const SECTION_DEFINITIONS = [
  {
    id: 'overview',
    label: 'Pilotage',
    groups: [
      {
        title: 'Synthèse',
        items: [
          {
            id: 'overview.core',
            label: 'Cockpit & KPIs',
            description: 'Vue héro, métriques clés et actions rapides.',
          },
          {
            id: 'overview.productFile',
            label: 'Fiches produit',
            description: 'Recherche EAN et visuels produits.',
          },
        ],
      },
    ],
  },
  {
    id: 'inventory',
    label: 'Inventaire',
    groups: [
      {
        title: 'Catalogue',
        items: [
          {
            id: 'inventory.catalog',
            label: 'Focus catalogue',
            description: 'Filtres avancés, cartes stock et top listes.',
          },
        ],
      },
      {
        title: 'Flux & mix',
        items: [
          {
            id: 'inventory.flows',
            label: 'Flux & mix',
            description: 'Entrées/sorties, alertes marge et mix catégories.',
          },
        ],
      },
    ],
  },
];

export default function DashboardPage() {
  const [filters, setFilters] = useState({
    search: '',
    category: 'all',
    status: 'all',
    page: 1,
    per_page: 25,
  });
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [focusToast, setFocusToast] = useState(null);
  const [weeklyWindow, setWeeklyWindow] = useState(8);
  const [eanSearch, setEanSearch] = useState('');
  const [productLookup, setProductLookup] = useState(null);
  const [productLookupError, setProductLookupError] = useState('');
  const [productLookupLoading, setProductLookupLoading] = useState(false);
  const defaultPanel = SECTION_DEFINITIONS[0]?.groups?.[0]?.items?.[0]?.id ?? 'overview.core';
  const [searchParams, setSearchParams] = useSearchParams();
  const sectionParam = searchParams.get('section');
  const [activePanel, setActivePanel] = useState(sectionParam || defaultPanel);
  useEffect(() => {
    if (sectionParam && sectionParam !== activePanel) {
      setActivePanel(sectionParam);
    } else if (!sectionParam && activePanel !== defaultPanel) {
      setActivePanel(defaultPanel);
    }
  }, [sectionParam, activePanel, defaultPanel]);

  const sectionOptions = useMemo(() => {
    const options = [];
    SECTION_DEFINITIONS.forEach((section) => {
      section.groups?.forEach((group) => {
        group.items?.forEach((item) => {
          options.push({
            id: item.id,
            label: `${section.label} · ${item.label}`,
          });
        });
      });
    });
    return options;
  }, []);

  useEffect(() => {
    if (!focusToast) return undefined;
    const timeout = setTimeout(() => setFocusToast(null), 3000);
    return () => clearTimeout(timeout);
  }, [focusToast]);

  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value,
      page: field === 'page' ? Number(value) : 1,
    }));
  };

  const handleFilterReset = () => {
    setFilters({
      search: '',
      category: 'all',
      status: 'all',
      page: 1,
      per_page: 25,
    });
  };

  const triggerFocus = (status, label) => {
    setFilters((prev) => ({
      ...prev,
      status,
      page: 1,
    }));
    setFiltersOpen(true);
    setFocusToast(`${label} en focus`);
  };

  const handlePanelSelect = (panelId) => {
    const params = new URLSearchParams(searchParams);
    if (!panelId || panelId === defaultPanel) {
      params.delete('section');
    } else {
      params.set('section', panelId);
    }
    setSearchParams(params);
  };

  const handleProductLookup = async () => {
    if (!eanSearch.trim()) {
      setProductLookupError('Saisissez un code EAN pour lancer la recherche.');
      setProductLookup(null);
      return;
    }
    setProductLookupLoading(true);
    setProductLookupError('');
    try {
      const data = await lookupProductByBarcode(eanSearch.trim());
      if (!data) {
        setProductLookup(null);
        setProductLookupError('Produit introuvable.');
      } else {
        setProductLookup(data);
      }
    } catch (error) {
      setProductLookup(null);
      setProductLookupError('Produit introuvable.');
    } finally {
      setProductLookupLoading(false);
    }
  };

  const {
    data: productsData,
    isLoading: productsLoading,
    isError: productsError,
  } = useProducts(filters);
  const products = productsData?.items ?? [];
  const productMeta = productsData?.meta;
  const {
    data: dashboardData,
    isLoading: dashboardLoading,
    isError: dashboardError,
  } = useDashboardMetrics();

  const kpis = dashboardData?.kpis ?? {
    total_produits: 0,
    valeur_stock_ht: 0,
    quantite_stock_total: 0,
    alerte_stock_bas: 0,
    stock_epuise: 0,
  };

  const analytics = useMemo(() => {
    if (!products.length) {
      return { active: 0, categories: 0, lowStock: [] };
    }
    const lowStock = [...products]
      .filter((product) => (product.stock_actuel ?? 0) < (product.seuil_alerte ?? 8))
      .sort((a, b) => (a.stock_actuel ?? 0) - (b.stock_actuel ?? 0))
      .slice(0, 5);
    const categories = new Set(products.map((product) => product.categorie ?? 'NC'));
    return {
      active: products.length,
      categories: categories.size,
      lowStock,
    };
  }, [products]);

  const inferredCategories = useMemo(() => {
    return [...new Set(products.map((product) => product.categorie || ''))].filter(Boolean);
  }, [products]);

  const weeklySeries = useMemo(() => {
    const series = dashboardData?.weekly_variation ?? [];
    return series
      .slice(-weeklyWindow)
      .map((entry) => {
        const label = new Date(entry.semaine).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
        const entrees = Number(entry.entrees) || 0;
        const sorties = Number(entry.sorties) || 0;
        return {
          ...entry,
          label,
          entrees,
          sorties,
          net: entrees - sorties,
        };
      });
  }, [dashboardData?.weekly_variation, weeklyWindow]);

  const categoryStockData = useMemo(() => {
    if (!products.length) return [];
    const totals = products.reduce((acc, product) => {
      const key = product.categorie || 'NC';
      acc[key] = (acc[key] || 0) + (Number(product.stock_actuel) || 0);
      return acc;
    }, {});
    return Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([label, qty]) => ({ label, qty }));
  }, [products]);

  const renderPanel = () => {
    switch (activePanel) {
      case 'overview.core':
        return (
          <>
            <Card className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-brand-800 text-white">
              <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.4em] text-brand-100/80">cockpit temps réel</p>
                  <h1 className="font-display text-4xl font-semibold sm:text-5xl">Import, inventaire, cash</h1>
                  <p className="mt-4 max-w-2xl text-base text-slate-100">
                    Concentrez-vous sur les flux critiques : ingestion des factures et relevés, contrôle des mouvements de
                    stock et pilotage consolidé du capital disponibles par tenant.
                  </p>
                  <div className="mt-6 flex flex-wrap gap-3">
                    <Button as="a" href="/import" variant="brand" size="lg">
                      Importer une facture
                      <ArrowUpRight className="h-4 w-4" />
                    </Button>
                    <Button as="a" href="/portfolio" variant="ghost">
                      Consulter le capital global
                    </Button>
                  </div>
                </div>
                <div className="grid gap-4 rounded-3xl border border-white/10 bg-white/10 p-6 text-sm backdrop-blur">
                  <div>
                    <p className="text-xs uppercase tracking-[0.4em] text-brand-100/70">statut plateforme</p>
                    <p className="text-lg font-semibold">Tout est au vert ✅</p>
                  </div>
                  <div className="space-y-2 text-slate-100/90">
                    <p>• Synchronisation catalogue réussie à 06:00</p>
                    <p>• Dernière sauvegarde PostgreSQL : 03:14</p>
                    <p>• 2 alertes critiques à traiter avant 14:00</p>
                  </div>
                </div>
              </div>
              <div className="pointer-events-none absolute inset-0 opacity-30">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.15),_transparent_60%)]" />
              </div>
            </Card>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <AnimatedMetricCard
                label="Références"
                value={
                  dashboardLoading || dashboardError ? '—' : kpis.total_produits.toLocaleString('fr-FR')
                }
                hint="Produits actifs"
              />
              <AnimatedMetricCard
                label="Valeur stock HT"
                value={
                  dashboardLoading || dashboardError
                    ? '—'
                    : `${kpis.valeur_stock_ht.toLocaleString('fr-FR', {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0,
                      })} €`
                }
                hint={`${kpis.quantite_stock_total.toLocaleString('fr-FR')} unités`}
              />
              <AnimatedMetricCard
                label="Alertes stock"
                value={dashboardLoading || dashboardError ? '—' : kpis.alerte_stock_bas}
                hint={`${kpis.stock_epuise} rupture(s)`}
                trend={kpis.alerte_stock_bas ? `+${kpis.alerte_stock_bas}` : '+0'}
              />
              <AnimatedMetricCard
                label="Références actives"
                value={productsLoading || productsError ? '—' : analytics.active}
                hint={`${analytics.categories} familles suivies`}
              />
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="outline" size="sm" onClick={() => setFiltersOpen(true)}>
                Ouvrir les filtres
              </Button>
              <Button variant="ghost" size="sm" onClick={() => triggerFocus('critical', 'Alertes')}>
                Focus alertes
              </Button>
            </div>
          </>
        );
      case 'overview.productFile':
        return (
          <Card className="flex flex-col gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Fiches produit</p>
              <h3 className="text-lg font-semibold text-slate-900">Recherche par code EAN</h3>
              <p className="text-sm text-slate-500">
                Identifiez rapidement un produit et consultez ses informations (prix, stock, photo) depuis le cockpit.
              </p>
            </div>
            <div className="flex flex-col gap-3 md:flex-row">
              <label className="flex-1 text-sm text-slate-600">
                Code EAN
                <input
                  type="text"
                  value={eanSearch}
                  onChange={(event) => setEanSearch(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault();
                      handleProductLookup();
                    }
                  }}
                  className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  placeholder="Ex. 5411188114526"
                />
              </label>
              <Button
                variant="brand"
                className="md:self-end"
                onClick={handleProductLookup}
                disabled={productLookupLoading}
              >
                {productLookupLoading ? 'Recherche…' : 'Afficher la fiche'}
              </Button>
            </div>
            {productLookupError && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">
                {productLookupError}
              </div>
            )}
            {!productLookupLoading && !productLookup && !productLookupError && (
              <p className="text-sm text-slate-500">Saisissez un code EAN pour afficher la fiche produit.</p>
            )}
            {productLookup && (
              <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-1">
                  {productLookup.image_url ? (
                    <img
                      src={productLookup.image_url}
                      alt={`Visuel ${productLookup.nom ?? ''}`}
                      className="w-full rounded-2xl border border-slate-200 object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex h-48 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-400">
                      Image non disponible
                    </div>
                  )}
                </div>
                <div className="md:col-span-2 space-y-3 text-sm text-slate-600">
                  <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Produit</p>
                    <p className="text-lg font-semibold text-slate-900">{productLookup.nom ?? '—'}</p>
                    <p className="text-xs text-slate-500">
                      Catégorie : {productLookup.categorie ?? 'Non renseignée'}
                    </p>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-2xl border border-slate-100 px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Fournisseur</p>
                      <p className="text-sm font-semibold text-slate-900">{productLookup.fournisseur ?? '—'}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-100 px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Stock actuel</p>
                      <p className="text-sm font-semibold text-slate-900">
                        {Number(productLookup.stock_actuel ?? 0).toLocaleString('fr-FR')} u
                      </p>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-100 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Prix d'achat</p>
                    <p className="text-sm font-semibold text-slate-900">
                      {productLookup.prix_achat ? `${productLookup.prix_achat} €` : '—'}
                    </p>
                    <p className="text-xs text-slate-500">Dernière MAJ : {productLookup.updated_at ?? '—'}</p>
                  </div>
                  {Array.isArray(productLookup.codes) && productLookup.codes.length > 0 && (
                    <div className="rounded-2xl border border-slate-100 px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Codes associés</p>
                      <p className="text-sm text-slate-700">{productLookup.codes.join(', ')}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        );
      case 'inventory.catalog':
        return (
          <>
            <div className="grid gap-6 lg:grid-cols-2">
              <FiltersPanel
                categories={dashboardData?.filters?.categories ?? inferredCategories}
                filters={filters}
                meta={productMeta}
                onChange={handleFilterChange}
                onReset={handleFilterReset}
              />
              <StockCards items={products} />
            </div>
            <Card className="grid gap-6 lg:grid-cols-3">
              <DashboardList
                title="Top stock (HT)"
                items={dashboardData?.top_stock_value ?? []}
                valueKey="valeur_stock"
                loading={dashboardLoading}
              />
              <DashboardList
                title="Top ventes"
                items={dashboardData?.top_sales ?? []}
                valueKey="quantite_vendue"
                loading={dashboardLoading}
              />
              <DashboardList
                title="Fournisseurs"
                items={dashboardData?.supplier_breakdown ?? []}
                valueKey="valeur"
                loading={dashboardLoading}
                labelKey="fournisseur"
                suffix=" €"
              />
            </Card>
          </>
        );
      case 'inventory.flows':
        return (
          <>
            <Card className="grid gap-6 lg:grid-cols-2">
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Flux hebdomadaires</p>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span>Fenêtre</span>
                    <select
                      className="rounded-full border border-slate-200 px-2 py-1 text-xs"
                      value={weeklyWindow}
                      onChange={(event) => setWeeklyWindow(Number(event.target.value))}
                    >
                      {[4, 8, 12, 20].map((value) => (
                        <option key={value} value={value}>
                          {value} sem.
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                {dashboardLoading ? (
                  <p className="text-sm text-slate-500">Chargement…</p>
                ) : (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={weeklySeries}>
                        <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Area type="monotone" dataKey="entrees" stackId="flows" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.35} name="Entrées" />
                        <Area type="monotone" dataKey="sorties" stackId="flows" stroke="#f97316" fill="#f97316" fillOpacity={0.35} name="Sorties" />
                        <Area type="monotone" dataKey="net" stroke="#10b981" fill="#10b981" fillOpacity={0.15} name="Net" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
              <DashboardList
                title="Alertes marge"
                items={dashboardData?.margin_alerts ?? []}
                valueKey="marge_pct"
                suffix=" %"
                loading={dashboardLoading}
                labelKey="nom"
              />
            </Card>
            <Card className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Mix catalogue</p>
                  <h3 className="text-lg font-semibold text-slate-900">Stocks par catégorie</h3>
                </div>
              </div>
              {categoryStockData.length ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={categoryStockData} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                      <YAxis />
                      <Tooltip formatter={(value) => Number(value).toLocaleString('fr-FR')} />
                      <Bar dataKey="qty" fill="#6366f1" name="Stock unités" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-sm text-slate-500">Aucune donnée de catalogue disponible.</p>
              )}
            </Card>
          </>
        );
      default:
        return (
          <Card>
            <p className="text-sm text-slate-500">Sélectionnez une section pour afficher son contenu.</p>
          </Card>
        );
    }
  };

  return (
    <div className="relative flex flex-col gap-8">
      {filtersOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-slate-900/70 backdrop-blur" onClick={() => setFiltersOpen(false)} />
          <div className="relative h-full w-full max-w-md">
            <FiltersPanel
              categories={dashboardData?.filters?.categories ?? inferredCategories}
              filters={filters}
              meta={productMeta}
              onChange={handleFilterChange}
              onReset={handleFilterReset}
            />
          </div>
        </div>
      )}
      {focusToast && (
        <div className="fixed bottom-6 right-6 z-50 rounded-2xl border border-white/20 bg-slate-900/90 px-5 py-3 text-sm text-white shadow-lg">
          {focusToast}
        </div>
      )}
      <FiltersDrawer open={filtersOpen} onClose={() => setFiltersOpen(false)} title="Filtres avancés">
        <FiltersPanel
          categories={dashboardData?.filters?.categories ?? inferredCategories}
          filters={filters}
          meta={productMeta}
          onChange={handleFilterChange}
          onReset={handleFilterReset}
        />
      </FiltersDrawer>

      <div className="lg:hidden">
        <label className="text-xs uppercase tracking-[0.3em] text-slate-400" htmlFor="mobile-dashboard-section">
          Section
        </label>
        <select
          id="mobile-dashboard-section"
          value={activePanel}
          onChange={(event) => handlePanelSelect(event.target.value)}
          className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-brand-400 focus:outline-none"
        >
          {sectionOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {renderPanel()}
    </div>
  );
}

function DashboardList({ title, items, valueKey, labelKey = 'nom', loading, suffix = '' }) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{title}</p>
      {loading ? (
        <p className="text-sm text-slate-500">Chargement…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-slate-500">Aucune donnée</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li
              key={`${item[labelKey]}-${index}`}
              className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2 text-sm"
            >
              <span className="font-medium text-slate-900">{item[labelKey]}</span>
              <span className="text-slate-600">
                {Number(item[valueKey] ?? 0).toLocaleString('fr-FR')}
                {suffix}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
