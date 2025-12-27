/**
 * Page Dashboard - Vue d'ensemble de l'inventaire et du stock.
 *
 * Cette page permet de visualiser en temps réel l'état complet de l'inventaire et du stock.
 * Elle affiche:
 * - Un hero avec le statut de la plateforme et les alertes actives
 * - Les KPIs principaux (produits, valeur stock, alertes)
 * - Un graphique des flux hebdomadaires (entrées/sorties)
 * - Une répartition du stock par catégorie
 * - Les top listes (stock par valeur, ventes, fournisseurs)
 * - Les alertes de stock bas en temps réel
 *
 * @component
 *
 * @example
 * <DashboardPage />
 */

import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Package,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  RefreshCw,
} from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import { useProducts } from '../../hooks/useProducts.js';
import { useDashboardMetrics } from '../../hooks/useDashboard.js';
import {
  DashboardHero,
  DashboardMetrics,
  WeeklyFlowsChart,
  CategoryStockChart,
  DashboardList,
} from './components/index.js';
import { DashboardSkeleton } from '../../components/ui/Skeleton.jsx';
import QueryErrorState from '../../components/feedback/QueryErrorState.jsx';

export default function DashboardPage() {
  const [weeklyWindow, setWeeklyWindow] = useState(8);

  // Données produits
  const {
    data: productsData,
    isLoading: productsLoading,
  } = useProducts({ page: 1, per_page: 100 });
  const products = productsData?.items ?? [];

  // Données dashboard
  const {
    data: dashboardData,
    isLoading: dashboardLoading,
    isError: dashboardError,
    refetch,
  } = useDashboardMetrics();

  // KPIs
  const kpis = dashboardData?.kpis ?? {
    total_produits: 0,
    valeur_stock_ht: 0,
    quantite_stock_total: 0,
    alerte_stock_bas: 0,
    stock_epuise: 0,
  };

  // Analytics calculés
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

  // Série hebdomadaire - Transforme les données brutes en format pour le graphique
  // On limite l'affichage aux X dernières semaines selon weeklyWindow
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
          net: entrees - sorties, // Calcul du flux net
        };
      });
  }, [dashboardData?.weekly_variation, weeklyWindow]);

  // Données par catégorie - Agrégation du stock par catégorie
  // On regroupe tous les produits par catégorie et on somme leurs stocks
  // Affiche uniquement les 6 catégories avec le plus de stock
  const categoryStockData = useMemo(() => {
    if (!products.length) return [];
    const totals = products.reduce((acc, product) => {
      const key = product.categorie || 'NC';
      acc[key] = (acc[key] || 0) + (Number(product.stock_actuel) || 0);
      return acc;
    }, {});
    return Object.entries(totals)
      .sort((a, b) => b[1] - a[1]) // Tri décroissant par quantité
      .slice(0, 6) // Top 6 catégories
      .map(([label, qty]) => ({ label, qty }));
  }, [products]);

  const isLoading = dashboardLoading || productsLoading;

  // Gestion erreur avec QueryErrorState
  if (dashboardError) {
    return (
      <QueryErrorState
        error={dashboardError}
        onRetry={refetch}
        variant="full"
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Hero avec statut */}
      <DashboardHero
        status={{ level: kpis.alerte_stock_bas > 5 ? 'warning' : 'ok', alertCount: kpis.alerte_stock_bas }}
        loading={isLoading}
      />

      {/* KPIs principaux */}
      <DashboardMetrics
        kpis={kpis}
        analytics={analytics}
        loading={isLoading}
      />

      {/* Graphiques */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Flux hebdomadaires */}
        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <h3 className="font-semibold text-white">Flux hebdomadaires</h3>
          </div>
          <WeeklyFlowsChart
            data={weeklySeries}
            loading={isLoading}
            windowSize={weeklyWindow}
            onWindowChange={setWeeklyWindow}
          />
        </div>

        {/* Répartition par catégorie */}
        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-violet-400" />
            <h3 className="font-semibold text-white">Stock par catégorie</h3>
          </div>
          <CategoryStockChart
            data={categoryStockData}
            loading={isLoading}
          />
        </div>
      </div>

      {/* Listes */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-white">Top stock (HT)</h3>
          </div>
          <DashboardList
            items={dashboardData?.top_stock_value ?? []}
            valueKey="valeur_stock"
            loading={isLoading}
          />
        </div>

        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-amber-400" />
            <h3 className="font-semibold text-white">Top ventes</h3>
          </div>
          <DashboardList
            items={dashboardData?.top_sales ?? []}
            valueKey="quantite_vendue"
            loading={isLoading}
          />
        </div>

        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-5 h-5 text-rose-400" />
            <h3 className="font-semibold text-white">Fournisseurs</h3>
          </div>
          <DashboardList
            items={dashboardData?.supplier_breakdown ?? []}
            valueKey="valeur"
            loading={isLoading}
            labelKey="fournisseur"
            suffix=" €"
          />
        </div>
      </div>

      {/* Alertes stock bas */}
      {analytics.lowStock.length > 0 && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-amber-900/20 to-orange-900/20 border border-amber-500/30">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="font-semibold text-white">Alertes stock bas</h3>
            <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400">
              {analytics.lowStock.length} produit(s)
            </span>
          </div>
          <div className="space-y-2">
            {analytics.lowStock.map((product, index) => (
              <motion.div
                key={product.id || index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center justify-between p-3 rounded-xl bg-white/5"
              >
                <div>
                  <p className="font-medium text-white">{product.nom}</p>
                  <p className="text-xs text-slate-400">
                    Seuil : {product.seuil_alerte ?? 8} • Catégorie : {product.categorie || 'NC'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-amber-400">{product.stock_actuel ?? 0}</p>
                  <p className="text-xs text-slate-500">en stock</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
