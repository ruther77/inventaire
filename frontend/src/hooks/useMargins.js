import { useQuery, useMutation } from '@tanstack/react-query';
import {
  calculateMargin,
  fetchProductMargins,
  fetchCategoryMargins,
  fetchProductPAMP,
  fetchDishMargins,
  fetchMarginAlerts,
  fetchMarginSummary,
} from '../api/client.js';

/**
 * Hook pour le résumé des marges.
 * @param {number} daysBack - Nombre de jours à analyser
 */
export function useMarginSummary(daysBack = 30) {
  return useQuery({
    queryKey: ['margins', 'summary', daysBack],
    queryFn: () => fetchMarginSummary(daysBack),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour les marges par produit.
 * @param {Object} filters - Filtres (category, limit, sortBy, daysBack)
 */
export function useProductMargins(filters = {}) {
  const { category, limit = 100, sortBy = 'gross_margin_pct', daysBack = 30 } = filters;
  // API n'accepte que gross_margin_pct | total_margin | volume_sold
  const allowedSort = ['gross_margin_pct', 'total_margin', 'volume_sold'];
  const sortParam = allowedSort.includes(sortBy) ? sortBy : 'gross_margin_pct';
  return useQuery({
    queryKey: ['margins', 'products', category, limit, sortParam, daysBack],
    queryFn: () => fetchProductMargins({ category, limit, sortBy: sortParam, daysBack }),
    staleTime: 5 * 60 * 1000,
    select: (data) => {
      const items = data?.items || data || [];
      // Normaliser les clés pour l'UI (compatibilité ancienne structure)
      return items.map((item) => ({
        id: item.product_id,
        name: item.product_name,
        category: item.category,
        selling_price: item.selling_price,
        cost_price: item.pamp ?? item.purchase_price,
        margin_amount: item.gross_margin,
        margin_percent: item.gross_margin_pct,
        monthly_revenue: item.total_revenue,
        volume_sold: item.volume_sold,
      }));
    },
  });
}

/**
 * Hook pour les marges par catégorie.
 * @param {number} daysBack - Nombre de jours à analyser
 */
export function useCategoryMargins(daysBack = 30) {
  return useQuery({
    queryKey: ['margins', 'categories', daysBack],
    queryFn: () => fetchCategoryMargins(daysBack),
    staleTime: 10 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour le PAMP d'un produit.
 * @param {number} productId - ID du produit
 */
export function useProductPAMP(productId) {
  return useQuery({
    queryKey: ['margins', 'pamp', productId],
    queryFn: () => fetchProductPAMP(productId),
    enabled: !!productId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook pour les marges des plats (restaurant).
 * @param {number} minMarginPct - Marge minimum (%)
 */
export function useDishMargins(minMarginPct) {
  return useQuery({
    queryKey: ['margins', 'dishes', minMarginPct],
    queryFn: () => fetchDishMargins(minMarginPct),
    staleTime: 10 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour les alertes de marge.
 * @param {number} threshold - Seuil minimum de marge (%)
 */
export function useMarginAlerts(threshold = 20) {
  return useQuery({
    queryKey: ['margins', 'alerts', threshold],
    queryFn: () => fetchMarginAlerts(threshold),
    staleTime: 5 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook mutation pour calculer la marge d'un produit.
 */
export function useCalculateMargin() {
  return useMutation({
    mutationFn: (params) => calculateMargin(params),
  });
}

/**
 * Hook combiné pour la page Marges.
 */
export function useMargins(options = {}) {
  const { category, alertThreshold = 20, daysBack = 30 } = options;

  const summary = useMarginSummary(daysBack);
  const products = useProductMargins({ category, daysBack });
  const categories = useCategoryMargins(daysBack);
  const alerts = useMarginAlerts(alertThreshold);
  const dishes = useDishMargins();

  const calculateMutation = useCalculateMargin();

  return {
    // Queries
    summary,
    products,
    categories,
    alerts,
    dishes,
    // Computed
    isLoading: summary.isLoading || products.isLoading,
    isError: summary.isError || products.isError,
    lowMarginProducts: products.data?.filter(p => (p.margin_pct || 0) < alertThreshold) || [],
    avgMargin: summary.data?.avg_margin_pct || 0,
    // Mutations
    calculate: calculateMutation,
    // Actions
    refetchAll: () => {
      summary.refetch();
      products.refetch();
      categories.refetch();
      alerts.refetch();
      dishes.refetch();
    },
  };
}

export default useMargins;
