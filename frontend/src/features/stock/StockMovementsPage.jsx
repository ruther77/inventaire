import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useProducts } from '../../hooks/useProducts.js';
import { useStockTimeseries, useRecentMovements, useStockAdjustment } from '../../hooks/useStock.js';

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

const SECTION_DEFINITIONS = [
  {
    id: 'overview',
    label: 'Pilotage',
    groups: [
      {
        title: 'Flux',
        items: [
          {
            id: 'overview.core',
            label: 'Vue globale',
            description: 'Filtres, KPIs et visualisations cumulées.',
          },
        ],
      },
    ],
  },
  {
    id: 'analytics',
    label: 'Analyses',
    groups: [
      {
        title: 'Classements & historique',
        items: [
          {
            id: 'analytics.history',
            label: 'Top & journal',
            description: 'Top entrées/sorties et journal détaillé.',
          },
        ],
      },
    ],
  },
  {
    id: 'operations',
    label: 'Opérations',
    groups: [
      {
        title: 'Inventaire',
        items: [
          {
            id: 'operations.adjust',
            label: 'Ajustements',
            description: 'Inventaire et corrections rapides.',
          },
        ],
      },
    ],
  },
];

export default function StockMovementsPage() {
  const { data: products = [] } = useProducts();
  const [selectedProduct, setSelectedProduct] = useState('all');
  const [windowDays, setWindowDays] = useState(30);
  const [recentLimit, setRecentLimit] = useState(50);
  const [targetQuantity, setTargetQuantity] = useState('');
  const [adjustProductId, setAdjustProductId] = useState(null);
  const defaultPanel =
    SECTION_DEFINITIONS[0]?.groups?.[0]?.items?.[0]?.id ?? 'overview.core';
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
  const handlePanelSelect = (panelId) => {
    const params = new URLSearchParams(searchParams);
    if (!panelId || panelId === defaultPanel) {
      params.delete('section');
    } else {
      params.set('section', panelId);
    }
    setSearchParams(params);
  };
  const adjustment = useStockAdjustment();

  const productOptions = useMemo(
    () =>
      [{ label: 'Catalogue complet', value: 'all', stock: '—' }].concat(
        products.map((product) => ({
          label: `${product.nom} (#${product.id})`,
          value: String(product.id),
          stock: product.stock_actuel ?? 0,
        })),
      ),
    [products],
  );

  const currentProduct = productOptions.find((option) => option.value === selectedProduct);
  const productId = selectedProduct === 'all' ? null : Number(selectedProduct);

  const timeseriesQuery = useStockTimeseries({ windowDays, productId });
  const recentQuery = useRecentMovements({ limit: recentLimit, productId });

  const metrics = useMemo(() => {
    const dataset = timeseriesQuery.data ?? [];
    const entries = dataset.filter((item) => item.type === 'ENTREE').reduce((sum, item) => sum + item.quantite, 0);
    const outputs = dataset.filter((item) => item.type === 'SORTIE').reduce((sum, item) => sum + item.quantite, 0);
    return {
      entries,
      outputs,
      net: entries - outputs,
    };
  }, [timeseriesQuery.data]);

  const dailySeries = useMemo(() => {
    const items = timeseriesQuery.data ?? [];
    const buckets = new Map();
    items.forEach((point) => {
      const key = point.jour;
      const entry = buckets.get(key) || { jour: key, entrees: 0, sorties: 0 };
      if (point.type === 'ENTREE') {
        entry.entrees += point.quantite;
      } else {
        entry.sorties += point.quantite;
      }
      buckets.set(key, entry);
    });
    return [...buckets.values()]
      .sort((a, b) => new Date(a.jour) - new Date(b.jour))
      .map((entry) => ({
        ...entry,
        net: entry.entrees - entry.sorties,
      }));
  }, [timeseriesQuery.data]);

  const cumulative = useMemo(() => {
    let total = 0;
    return dailySeries.map((point) => {
      total += point.net;
      return { ...point, cumul: total };
    });
  }, [dailySeries]);

  const topMovements = useMemo(() => {
    const list = recentQuery.data ?? [];
    const aggregate = (targetType) => {
      const totals = {};
      list.forEach((movement) => {
        if (!movement?.type) return;
        const type = movement.type.toUpperCase();
        if (type !== targetType) return;
        const label = movement.produit || `#${movement.produit_id ?? '?'}`;
        totals[label] = (totals[label] || 0) + (Number(movement.quantite) || 0);
      });
      return Object.entries(totals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([label, qty]) => ({ label, qty }));
    };
    return {
      incoming: aggregate('ENTREE'),
      outgoing: aggregate('SORTIE'),
    };
  }, [recentQuery.data]);

  const handleAdjustment = () => {
    const pid = adjustProductId ?? productId;
    if (!pid) return;
    const qty = Number(targetQuantity);
    if (Number.isNaN(qty)) return;
    adjustment.mutate({ productId: pid, targetQuantity: qty, username: 'api' });
  };

  const renderPanel = () => {
    switch (activePanel) {
      case 'overview.core':
        return (
          <>
            <Card className="flex flex-col gap-6">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] text-slate-400">pilotage stock</p>
                  <h2 className="text-2xl font-semibold text-slate-900">Flux & inventaires</h2>
                  <p className="text-sm text-slate-500">
                    Visualisez les entrées/sorties et ajustez rapidement les stocks.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <select
                    value={selectedProduct}
                    onChange={(event) => setSelectedProduct(event.target.value)}
                    className="rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  >
                    {productOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select
                    value={windowDays}
                    onChange={(event) => setWindowDays(Number(event.target.value))}
                    className="rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  >
                    {[7, 30, 90, 180].map((days) => (
                      <option key={days} value={days}>
                        Fenêtre {days} j
                      </option>
                    ))}
                  </select>
                  <select
                    value={recentLimit}
                    onChange={(event) => setRecentLimit(Number(event.target.value))}
                    className="rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  >
                    {[25, 50, 100, 200].map((limit) => (
                      <option key={limit} value={limit}>
                        {limit} lignes
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {selectedProduct !== 'all' && (
                <div className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3 text-sm text-slate-600">
                  Stock actuel pour <span className="font-semibold text-slate-900">{currentProduct?.label}</span> :
                  <span className="ml-2 text-lg font-semibold text-slate-900">
                    {numberFormatter.format(currentProduct?.stock ?? 0)}
                  </span>
                </div>
              )}
              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="Entrées" value={`+${numberFormatter.format(metrics.entries)}`} />
                <Metric label="Sorties" value={`-${numberFormatter.format(metrics.outputs)}`} />
                <Metric label="Variation nette" value={numberFormatter.format(metrics.net)} />
              </div>
            </Card>
            <Card className="flex flex-col gap-4">
              <div className="grid gap-6 lg:grid-cols-2">
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dailySeries}>
                      <XAxis dataKey="jour" tick={{ fontSize: 12 }} />
                      <YAxis />
                      <Tooltip formatter={(value) => numberFormatter.format(value)} />
                      <Bar dataKey="entrees" fill="#0ea5e9" name="Entrées" />
                      <Bar dataKey="sorties" fill="#fb7185" name="Sorties" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={cumulative}>
                      <XAxis dataKey="jour" tick={{ fontSize: 12 }} />
                      <YAxis />
                      <Tooltip formatter={(value) => numberFormatter.format(value)} />
                      <Line type="monotone" dataKey="cumul" stroke="#10b981" strokeWidth={2} dot />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </Card>
          </>
        );
      case 'analytics.history':
        return (
          <>
            <div className="grid gap-4 lg:grid-cols-2">
              <Card className="flex flex-col gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Top articles</p>
                  <h3 className="text-lg font-semibold text-slate-900">Entrées récentes</h3>
                </div>
                {topMovements.incoming.length ? (
                  <ul className="divide-y divide-slate-100 text-sm">
                    {topMovements.incoming.map((item) => (
                      <li key={item.label} className="flex items-center justify-between py-2">
                        <span className="text-slate-600">{item.label}</span>
                        <span className="font-semibold text-emerald-600">
                          +{numberFormatter.format(item.qty)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Aucune entrée détectée.</p>
                )}
              </Card>
              <Card className="flex flex-col gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Top articles</p>
                  <h3 className="text-lg font-semibold text-slate-900">Sorties récentes</h3>
                </div>
                {topMovements.outgoing.length ? (
                  <ul className="divide-y divide-slate-100 text-sm">
                    {topMovements.outgoing.map((item) => (
                      <li key={item.label} className="flex items-center justify-between py-2">
                        <span className="text-slate-600">{item.label}</span>
                        <span className="font-semibold text-rose-600">
                          -{numberFormatter.format(item.qty)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Aucune sortie détectée.</p>
                )}
              </Card>
            </div>
            <Card className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Mouvements récents</h3>
                <p className="text-sm text-slate-500">
                  {recentQuery.data?.length ?? 0} lignes — limite {recentLimit}
                </p>
              </div>
              {recentQuery.data?.length ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-100 text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                        <th className="px-3 py-2">Date</th>
                        <th className="px-3 py-2">Produit</th>
                        <th className="px-3 py-2">Type</th>
                        <th className="px-3 py-2">Quantité</th>
                        <th className="px-3 py-2">Source</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {recentQuery.data.map((movement) => {
                        const dateValue = movement.date_mvt || movement.created_at || movement.updated_at || null;
                        const displayDate = dateValue ? new Date(dateValue).toLocaleString('fr-FR') : '—';
                        return (
                          <tr key={movement.id}>
                            <td className="px-3 py-2 text-slate-600">{displayDate}</td>
                            <td className="px-3 py-2 text-slate-900">{movement.produit}</td>
                            <td className="px-3 py-2">{movement.type}</td>
                            <td className="px-3 py-2">{movement.quantite}</td>
                            <td className="px-3 py-2 text-slate-500">{movement.source || '—'}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-slate-500">
                  {timeseriesQuery.isLoading || recentQuery.isLoading ? 'Chargement…' : 'Aucun mouvement à afficher.'}
                </p>
              )}
            </Card>
          </>
        );
      case 'operations.adjust':
        return (
          <Card className="flex flex-col gap-4">
            <h3 className="text-lg font-semibold text-slate-900">Ajustement / Inventaire</h3>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="text-sm text-slate-600">
                Produit
                <select
                  value={String(adjustProductId ?? selectedProduct)}
                  onChange={(event) =>
                    setAdjustProductId(event.target.value === 'all' ? null : Number(event.target.value))
                  }
                  className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                >
                  {productOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm text-slate-600">
                Stock cible
                <input
                  type="number"
                  min={0}
                  value={targetQuantity}
                  onChange={(event) => setTargetQuantity(event.target.value)}
                  className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                />
              </label>
              <label className="text-sm text-slate-600">
                Stock actuel
                <input
                  type="text"
                  readOnly
                  value={
                    productOptions.find(
                      (option) => option.value === String(adjustProductId ?? (productId ?? 'all')),
                    )?.stock ?? '—'
                  }
                  className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm bg-slate-50"
                />
              </label>
            </div>
            <Button variant="brand" onClick={handleAdjustment} disabled={adjustment.isLoading}>
              Enregistrer l&apos;ajustement
            </Button>
            {adjustment.data && (
              <p className="text-sm text-emerald-600">
                Stock de {adjustment.data.product_name} ajusté à {adjustment.data.new_stock} u.
              </p>
            )}
          </Card>
        );
      default:
        return (
          <Card>
            <p className="text-sm text-slate-500">Sélectionnez un panneau pour afficher son contenu.</p>
          </Card>
        );
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="lg:hidden">
        <label className="text-xs uppercase tracking-[0.3em] text-slate-400" htmlFor="mobile-stock-section">
          Section
        </label>
        <select
          id="mobile-stock-section"
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

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
