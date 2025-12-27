/**
 * Module de hooks pour le dashboard et les métriques globales.
 *
 * @module hooks/useDashboard
 */
import { useQuery } from '@tanstack/react-query';
import { fetchDashboardMetrics } from '../api/client.js';

/**
 * Hook pour récupérer les métriques et KPIs du dashboard.
 *
 * Retourne un snapshot complet des indicateurs clés de performance:
 * - Valeur totale du stock
 * - Nombre de produits actifs
 * - Alertes de stock bas et ruptures
 * - Variations hebdomadaires (entrées/sorties)
 * - Top produits (ventes, rotations)
 * - Répartition par catégories
 *
 * Les données sont mises en cache 1 minute pour réduire la charge serveur.
 *
 * @returns {Object} Query avec les métriques complètes
 * @property {Object} data.kpis - KPIs principaux (total produits, valeur stock, alertes)
 * @property {Array} data.weekly_variation - Séries temporelles entrées/sorties
 * @property {Array} data.top_products - Produits les plus vendus
 * @property {Array} data.category_breakdown - Répartition stock par catégorie
 *
 * @example
 * const { data: metrics, isLoading } = useDashboardMetrics();
 *
 * if (isLoading) return <Skeleton />;
 *
 * const {
 *   kpis,
 *   weekly_variation,
 *   top_products,
 *   category_breakdown
 * } = metrics;
 *
 * return (
 *   <div>
 *     <MetricCard
 *       label="Valeur stock"
 *       value={kpis.valeur_stock_ht}
 *       format="currency"
 *     />
 *     <WeeklyChart data={weekly_variation} />
 *     <TopProductsTable products={top_products} />
 *   </div>
 * );
 */
export function useDashboardMetrics() {
  return useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchDashboardMetrics,
    staleTime: 60 * 1000, // 1 minute - métriques rafraîchies régulièrement
    refetchOnWindowFocus: false,
  });
}
