import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import Card from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import {
  useRestaurantIngredients,
  useRestaurantStockMovements,
  useRestaurantStockSummary,
  useRestaurantStockDailyByCategory,
  useRestaurantStockDailyByPlat,
  useCreateRestaurantStockMovement,
} from '@/hooks/useRestaurant.js';
import { Package, TrendingUp, TrendingDown, ArrowDownToLine, ArrowUpFromLine, RefreshCw } from 'lucide-react';
import clsx from 'clsx';

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

// Palette de couleurs pour les catégories restaurant
const CATEGORY_COLORS = {
  'Bières': '#f59e0b',
  'Vins rouges': '#991b1b',
  'Vins blancs': '#fef3c7',
  'Vins rosés': '#fda4af',
  'Spiritueux': '#7c3aed',
  'Softs / Énergisants': '#06b6d4',
  'Eaux': '#67e8f9',
  'Viandes': '#dc2626',
  'Viandes & Charcuterie': '#b91c1c',
  'Viandes / Poisson / Charcut': '#ef4444',
  'Poissons': '#0ea5e9',
  'Poissons / Fruits de mer': '#0284c7',
  'Fruits de mer': '#38bdf8',
  'Mer / Viandes base': '#0369a1',
  'Fruits & Légumes frais': '#22c55e',
  'Surgelés': '#a5b4fc',
  'Surgelés légumes': '#93c5fd',
  'Conserves': '#a3a3a3',
  'Conserves / Tomates': '#f97316',
  'Huiles & Vinaigres': '#eab308',
  'Huiles / Condiments': '#facc15',
  'Épices & Bouillons': '#f472b6',
  'Épices / Herbes / Bouillons': '#ec4899',
  'Épicerie sucrée': '#c084fc',
  'Pâtes, Riz & Céréales': '#fcd34d',
  'Pâtes / Riz / Semoule / Farine': '#fbbf24',
  'Farines & Semoules': '#d4a373',
  'Fruits secs & Graines': '#a16207',
  'Laits / Crèmes': '#fef9c3',
  'Produits du monde': '#fb923c',
  'Emballages / Jetables': '#9ca3af',
  'Apéritifs / Fortifiés': '#8b5cf6',
  'Effervescents / Champagne': '#fcd34d',
  'Non classé': '#6b7280',
};

const getColorForCategory = (category) => CATEGORY_COLORS[category] || '#6b7280';

// Palette de couleurs pour les plats (plus vive et variée)
const PLAT_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
  '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
  '#ec4899', '#f43f5e',
];

const getColorForPlat = (index) => PLAT_COLORS[index % PLAT_COLORS.length];

const currencyFormatter = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' });

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

export default function RestaurantStockMovementsPage() {
  const { data: ingredients = [] } = useRestaurantIngredients();
  const [selectedIngredient, setSelectedIngredient] = useState('all');
  const [windowDays, setWindowDays] = useState(30);
  const [recentLimit, setRecentLimit] = useState(500);
  const [targetQuantity, setTargetQuantity] = useState('');
  const [adjustIngredientId, setAdjustIngredientId] = useState(null);
  const [adjustType, setAdjustType] = useState('ENTREE');
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

  const createMovement = useCreateRestaurantStockMovement();

  const ingredientOptions = useMemo(
    () =>
      [{ label: 'Tous les ingrédients', value: 'all', stock: '—' }].concat(
        ingredients.map((ing) => ({
          label: `${ing.nom} (#${ing.id})`,
          value: String(ing.id),
          stock: ing.stock_actuel ?? 0,
          unite: ing.unite_base || 'u',
        })),
      ),
    [ingredients],
  );

  const currentIngredient = ingredientOptions.find((option) => option.value === selectedIngredient);
  const ingredientId = selectedIngredient === 'all' ? null : Number(selectedIngredient);

  const summaryQuery = useRestaurantStockSummary();
  const summaryData = summaryQuery.data || [];

  // Calculer la date de début basée sur windowDays
  const dateFrom = useMemo(() => {
    if (windowDays === 0) return undefined; // 0 = toutes les données
    const date = new Date();
    date.setDate(date.getDate() - windowDays);
    return date.toISOString().split('T')[0];
  }, [windowDays]);

  // Données agrégées pour le graphique (optimisé côté backend)
  const dailyByCategoryQuery = useRestaurantStockDailyByCategory({
    dateFrom,
    typeMouvement: 'sortie',
  });
  const dailyCategoryData = dailyByCategoryQuery.data || { series: [], categories: [] };

  // Données agrégées par plat pour le graphique
  const dailyByPlatQuery = useRestaurantStockDailyByPlat({
    dateFrom,
  });
  const dailyPlatData = dailyByPlatQuery.data || { series: [], plats: [] };

  const movementsQuery = useRestaurantStockMovements({
    ingredientId: ingredientId || undefined,
    dateFrom,
    limit: recentLimit,
  });
  const movements = movementsQuery.data?.items || movementsQuery.data || [];

  const metrics = useMemo(() => {
    const entries = movements.filter((m) => m.type_mouvement?.toLowerCase() === 'entree').reduce((sum, m) => sum + (m.quantite || 0), 0);
    const outputs = movements.filter((m) => m.type_mouvement?.toLowerCase() === 'sortie').reduce((sum, m) => sum + (m.quantite || 0), 0);
    return {
      entries,
      outputs,
      net: entries - outputs,
    };
  }, [movements]);

  const dailySeries = useMemo(() => {
    const buckets = new Map();
    movements.forEach((m) => {
      const key = m.date_mouvement?.split('T')[0] || 'unknown';
      const entry = buckets.get(key) || { jour: key, entrees: 0, sorties: 0 };
      const typeLower = m.type_mouvement?.toLowerCase();
      if (typeLower === 'entree') {
        entry.entrees += m.quantite || 0;
      } else if (typeLower === 'sortie') {
        entry.sorties += m.quantite || 0;
      }
      buckets.set(key, entry);
    });
    return [...buckets.values()]
      .sort((a, b) => new Date(a.jour) - new Date(b.jour))
      .map((entry) => ({
        ...entry,
        net: entry.entrees - entry.sorties,
      }));
  }, [movements]);

  const cumulative = useMemo(() => {
    let total = 0;
    return dailySeries.map((point) => {
      total += point.net;
      return { ...point, cumul: total };
    });
  }, [dailySeries]);

  const topMovements = useMemo(() => {
    const aggregate = (targetType) => {
      const totals = {};
      movements.forEach((m) => {
        if (m.type_mouvement?.toLowerCase() !== targetType) return;
        const label = m.ingredient_nom || `#${m.ingredient_id ?? '?'}`;
        totals[label] = (totals[label] || 0) + (Number(m.quantite) || 0);
      });
      return Object.entries(totals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([label, qty]) => ({ label, qty }));
    };
    return {
      incoming: aggregate('entree'),
      outgoing: aggregate('sortie'),
    };
  }, [movements]);

  const handleAdjustment = () => {
    const ingId = adjustIngredientId ?? ingredientId;
    if (!ingId) return;
    const qty = Number(targetQuantity);
    if (Number.isNaN(qty) || qty <= 0) return;

    createMovement.mutate({
      ingredientId: ingId,
      typeMouvement: adjustType,
      quantite: qty,
      source: 'inventaire_manuel',
      commentaire: `Ajustement manuel - ${adjustType === 'ENTREE' ? 'entrée' : adjustType === 'SORTIE' ? 'sortie' : 'ajustement'}`,
    });
    setTargetQuantity('');
  };

  const handleRefresh = () => {
    movementsQuery.refetch();
    summaryQuery.refetch();
    dailyByCategoryQuery.refetch();
    dailyByPlatQuery.refetch();
  };

  const isLoading = movementsQuery.isLoading || summaryQuery.isLoading || dailyByCategoryQuery.isLoading || dailyByPlatQuery.isLoading;

  const renderPanel = () => {
    switch (activePanel) {
      case 'overview.core':
        return (
          <>
            <Card>
              <div className="flex flex-col gap-6 p-6">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-400 mb-1">Stock Restaurant</p>
                    <h2 className="text-2xl font-bold text-white">Flux & inventaires</h2>
                    <p className="text-sm text-slate-400 mt-1">
                      Visualisez les entrées/sorties et ajustez rapidement les stocks ingrédients.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleRefresh}
                      disabled={isLoading}
                    >
                      <RefreshCw className={clsx('h-4 w-4 mr-1', isLoading && 'animate-spin')} />
                      Actualiser
                    </Button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <select
                    value={selectedIngredient}
                    onChange={(event) => setSelectedIngredient(event.target.value)}
                    className="rounded-lg border border-white/10 bg-slate-800 px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >
                    {ingredientOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select
                    value={windowDays}
                    onChange={(event) => setWindowDays(Number(event.target.value))}
                    className="rounded-lg border border-white/10 bg-slate-800 px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value={7}>7 jours</option>
                    <option value={30}>30 jours</option>
                    <option value={90}>3 mois</option>
                    <option value={180}>6 mois</option>
                    <option value={365}>1 an</option>
                    <option value={730}>2 ans</option>
                    <option value={0}>Tout l'historique</option>
                  </select>
                  <select
                    value={recentLimit}
                    onChange={(event) => setRecentLimit(Number(event.target.value))}
                    className="rounded-lg border border-white/10 bg-slate-800 px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value={50}>50 lignes</option>
                    <option value={100}>100 lignes</option>
                    <option value={200}>200 lignes</option>
                    <option value={500}>500 lignes</option>
                    <option value={1000}>1000 lignes</option>
                    <option value={5000}>5000 lignes</option>
                  </select>
                </div>

                {selectedIngredient !== 'all' && (
                  <div className="rounded-lg border border-white/10 bg-slate-800/50 px-4 py-3 text-sm text-slate-300">
                    Stock actuel pour <span className="font-semibold text-white">{currentIngredient?.label}</span> :
                    <span className="ml-2 text-lg font-bold text-white">
                      {numberFormatter.format(currentIngredient?.stock ?? 0)} {currentIngredient?.unite || 'u'}
                    </span>
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-3">
                  <MetricCard
                    label="Entrées"
                    value={`+${numberFormatter.format(metrics.entries)}`}
                    icon={ArrowDownToLine}
                    color="emerald"
                  />
                  <MetricCard
                    label="Sorties"
                    value={`-${numberFormatter.format(metrics.outputs)}`}
                    icon={ArrowUpFromLine}
                    color="rose"
                  />
                  <MetricCard
                    label="Variation nette"
                    value={numberFormatter.format(metrics.net)}
                    icon={metrics.net >= 0 ? TrendingUp : TrendingDown}
                    color={metrics.net >= 0 ? 'emerald' : 'rose'}
                  />
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-slate-400">Sorties par jour (par catégorie)</h3>
                  <span className="text-xs text-slate-500">
                    {dailyCategoryData.series.length} jours · {dailyCategoryData.categories.length} catégories
                  </span>
                </div>
                <div className="h-80">
                  {dailyByCategoryQuery.isLoading ? (
                    <div className="flex items-center justify-center h-full text-slate-400">
                      Chargement des données...
                    </div>
                  ) : dailyCategoryData.series.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-slate-500">
                      Aucune donnée pour cette période
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={dailyCategoryData.series}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="jour" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={(v) => v?.slice(5)} />
                        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                          labelStyle={{ color: '#fff' }}
                          formatter={(value, name) => [numberFormatter.format(value), name]}
                        />
                        <Legend
                          wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                          formatter={(value) => <span style={{ color: '#94a3b8' }}>{value}</span>}
                        />
                        {dailyCategoryData.categories.map((category) => (
                          <Bar
                            key={category}
                            dataKey={category}
                            stackId="sorties"
                            fill={getColorForCategory(category)}
                            name={category}
                          />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-slate-400">Ventes par jour (par plat)</h3>
                  <span className="text-xs text-slate-500">
                    {dailyPlatData.series.length} jours · {dailyPlatData.plats.length} plats
                  </span>
                </div>
                <div className="h-80">
                  {dailyByPlatQuery.isLoading ? (
                    <div className="flex items-center justify-center h-full text-slate-400">
                      Chargement des données...
                    </div>
                  ) : dailyPlatData.series.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-slate-500">
                      Aucune donnée de ventes pour cette période
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={dailyPlatData.series}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="jour" tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={(v) => v?.slice(5)} />
                        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={(v) => `${v.toFixed(0)}€`} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                          labelStyle={{ color: '#fff' }}
                          formatter={(value, name) => [currencyFormatter.format(value), name]}
                        />
                        <Legend
                          wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }}
                          formatter={(value) => <span style={{ color: '#94a3b8' }}>{value.length > 20 ? value.slice(0, 20) + '...' : value}</span>}
                        />
                        {dailyPlatData.plats.map((plat, index) => (
                          <Bar
                            key={plat}
                            dataKey={plat}
                            stackId="plats"
                            fill={getColorForPlat(index)}
                            name={plat}
                          />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </Card>
          </>
        );

      case 'analytics.history':
        return (
          <>
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <div className="p-6">
                  <p className="text-xs uppercase tracking-widest text-slate-400 mb-1">Top ingrédients</p>
                  <h3 className="text-lg font-bold text-white mb-4">Entrées récentes</h3>
                  {topMovements.incoming.length ? (
                    <ul className="divide-y divide-white/5 text-sm">
                      {topMovements.incoming.map((item) => (
                        <li key={item.label} className="flex items-center justify-between py-3">
                          <span className="text-slate-300">{item.label}</span>
                          <span className="font-semibold text-emerald-400">
                            +{numberFormatter.format(item.qty)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-500">Aucune entrée détectée.</p>
                  )}
                </div>
              </Card>
              <Card>
                <div className="p-6">
                  <p className="text-xs uppercase tracking-widest text-slate-400 mb-1">Top ingrédients</p>
                  <h3 className="text-lg font-bold text-white mb-4">Sorties récentes</h3>
                  {topMovements.outgoing.length ? (
                    <ul className="divide-y divide-white/5 text-sm">
                      {topMovements.outgoing.map((item) => (
                        <li key={item.label} className="flex items-center justify-between py-3">
                          <span className="text-slate-300">{item.label}</span>
                          <span className="font-semibold text-rose-400">
                            -{numberFormatter.format(item.qty)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-500">Aucune sortie détectée.</p>
                  )}
                </div>
              </Card>
            </div>

            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Mouvements récents</h3>
                  <p className="text-sm text-slate-400">
                    {movements.length ?? 0} lignes — limite {recentLimit}
                  </p>
                </div>
                {movements.length ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="text-left text-xs uppercase tracking-widest text-slate-500 border-b border-white/10">
                          <th className="px-3 py-3">Date</th>
                          <th className="px-3 py-3">Ingrédient</th>
                          <th className="px-3 py-3">Type</th>
                          <th className="px-3 py-3 text-right">Quantité</th>
                          <th className="px-3 py-3">Source</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {movements.map((movement) => {
                          const dateValue = movement.date_mouvement || movement.created_at || null;
                          const displayDate = dateValue ? new Date(dateValue).toLocaleString('fr-FR') : '—';
                          const typeLower = movement.type_mouvement?.toLowerCase();
                          const typeColor = typeLower === 'entree' ? 'text-emerald-400' :
                            typeLower === 'sortie' ? 'text-rose-400' : 'text-amber-400';
                          return (
                            <tr key={movement.id} className="hover:bg-white/5">
                              <td className="px-3 py-3 text-slate-400">{displayDate}</td>
                              <td className="px-3 py-3 text-white font-medium">{movement.ingredient_nom || '—'}</td>
                              <td className={clsx('px-3 py-3 font-medium', typeColor)}>{movement.type_mouvement}</td>
                              <td className="px-3 py-3 text-right text-white">{movement.quantite} {movement.unite || ''}</td>
                              <td className="px-3 py-3 text-slate-500">{movement.source || '—'}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Package className="h-12 w-12 mx-auto text-slate-600 mb-3" />
                    <p className="text-slate-400">
                      {movementsQuery.isLoading ? 'Chargement…' : 'Aucun mouvement à afficher.'}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </>
        );

      case 'operations.adjust':
        return (
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-bold text-white mb-2">Ajustement / Inventaire</h3>
              <p className="text-sm text-slate-400 mb-6">
                Enregistrez une entrée, sortie ou ajustement de stock pour un ingrédient.
              </p>
              <div className="grid gap-4 md:grid-cols-4">
                <label className="text-sm text-slate-400">
                  Ingrédient
                  <select
                    value={String(adjustIngredientId ?? selectedIngredient)}
                    onChange={(event) =>
                      setAdjustIngredientId(event.target.value === 'all' ? null : Number(event.target.value))
                    }
                    className="mt-2 w-full rounded-lg border border-white/10 bg-slate-800 px-4 py-2.5 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >
                    {ingredientOptions.filter(o => o.value !== 'all').map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm text-slate-400">
                  Type de mouvement
                  <select
                    value={adjustType}
                    onChange={(event) => setAdjustType(event.target.value)}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-slate-800 px-4 py-2.5 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value="ENTREE">Entrée (+)</option>
                    <option value="SORTIE">Sortie (-)</option>
                    <option value="AJUSTEMENT">Ajustement</option>
                  </select>
                </label>
                <label className="text-sm text-slate-400">
                  Quantité
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    value={targetQuantity}
                    onChange={(event) => setTargetQuantity(event.target.value)}
                    placeholder="Ex: 5"
                    className="mt-2 w-full rounded-lg border border-white/10 bg-slate-800 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                  />
                </label>
                <label className="text-sm text-slate-400">
                  Stock actuel
                  <input
                    type="text"
                    readOnly
                    value={
                      (() => {
                        const id = adjustIngredientId ?? (ingredientId ?? 'all');
                        const opt = ingredientOptions.find((o) => o.value === String(id));
                        return opt && opt.value !== 'all' ? `${opt.stock ?? '—'} ${opt.unite || 'u'}` : '—';
                      })()
                    }
                    className="mt-2 w-full rounded-lg border border-white/10 bg-slate-700/50 px-4 py-2.5 text-sm text-slate-300"
                  />
                </label>
              </div>
              <div className="mt-6">
                <Button
                  variant="brand"
                  onClick={handleAdjustment}
                  disabled={createMovement.isPending || !adjustIngredientId || !targetQuantity}
                >
                  {createMovement.isPending ? 'Enregistrement...' : 'Enregistrer le mouvement'}
                </Button>
              </div>
              {createMovement.isSuccess && (
                <p className="mt-4 text-sm text-emerald-400">
                  Mouvement enregistré avec succès !
                </p>
              )}
              {createMovement.isError && (
                <p className="mt-4 text-sm text-rose-400">
                  Erreur : {createMovement.error?.message || 'Échec de l\'enregistrement'}
                </p>
              )}
            </div>
          </Card>
        );

      default:
        return (
          <Card>
            <div className="p-6">
              <p className="text-sm text-slate-400">Sélectionnez un panneau pour afficher son contenu.</p>
            </div>
          </Card>
        );
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Mobile section selector */}
      <div className="lg:hidden">
        <label className="text-xs uppercase tracking-widest text-slate-400" htmlFor="mobile-stock-section">
          Section
        </label>
        <select
          id="mobile-stock-section"
          value={activePanel}
          onChange={(event) => handlePanelSelect(event.target.value)}
          className="mt-2 w-full rounded-lg border border-white/10 bg-slate-800 px-4 py-2.5 text-sm text-white focus:border-blue-500 focus:outline-none"
        >
          {sectionOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Desktop tabs */}
      <div className="hidden lg:flex gap-2 border-b border-white/10 pb-2">
        {sectionOptions.map((option) => (
          <button
            key={option.id}
            onClick={() => handlePanelSelect(option.id)}
            className={clsx(
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              activePanel === option.id
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {renderPanel()}
    </div>
  );
}

function MetricCard({ label, value, icon: Icon, color = 'blue' }) {
  const colorClasses = {
    blue: 'bg-blue-500/20 text-blue-400',
    emerald: 'bg-emerald-500/20 text-emerald-400',
    rose: 'bg-rose-500/20 text-rose-400',
    amber: 'bg-amber-500/20 text-amber-400',
  };

  return (
    <div className="rounded-xl border border-white/10 bg-slate-800/50 p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-400">{label}</p>
          <p className="mt-2 text-2xl font-bold text-white">{value}</p>
        </div>
        {Icon && (
          <div className={clsx('p-2 rounded-lg', colorClasses[color])}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  );
}
