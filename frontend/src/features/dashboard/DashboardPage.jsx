import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import FiltersDrawer from '../../components/ui/FiltersDrawer.jsx';
import { useProducts } from '../../hooks/useProducts.js';
import { useDashboardMetrics } from '../../hooks/useDashboard.js';
import FiltersPanel from './components/FiltersPanel.jsx';
import StockCards from './components/StockCards.jsx';
import {
  DashboardHero,
  DashboardMetrics,
  DashboardChartsGrid,
  WeeklyFlowsChart,
  CategoryStockChart,
  DashboardListsGrid,
  DashboardList,
  TopStockList,
  TopSalesList,
  SuppliersList,
  MarginAlertsList,
  ProductLookup,
} from './components/index.js';

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
            <DashboardHero
              status={{ level: 'ok', alertCount: kpis.alerte_stock_bas }}
              loading={dashboardLoading}
            />
            <DashboardMetrics
              kpis={kpis}
              analytics={analytics}
              loading={dashboardLoading || dashboardError}
              onMetricClick={(type) => {
                if (type === 'alerts') triggerFocus('critical', 'Alertes');
              }}
            />
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
        return <ProductLookup />;
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
              <WeeklyFlowsChart
                data={weeklySeries}
                loading={dashboardLoading}
                windowSize={weeklyWindow}
                onWindowChange={setWeeklyWindow}
              />
              <MarginAlertsList
                items={dashboardData?.margin_alerts ?? []}
                loading={dashboardLoading}
              />
            </Card>
            <CategoryStockChart
              data={categoryStockData}
              loading={dashboardLoading}
            />
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
