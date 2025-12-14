import { useQuery, useMutation } from '@tanstack/react-query';
import {
  calculateEOQ,
  calculateSafetyStock,
  fetchReorderPoints,
  fetchStockoutPredictions,
  fetchDeadStock,
  fetchABCXYZClassification,
  fetchReorderSuggestions,
  fetchInventoryIntelligenceSummary,
} from '../api/client.js';

/**
 * Hook pour le résumé de l'intelligence inventaire.
 */
export function useInventoryIntelligenceSummary() {
  return useQuery({
    queryKey: ['inventory-intelligence', 'summary'],
    queryFn: fetchInventoryIntelligenceSummary,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour les points de réapprovisionnement.
 * @param {Object} filters - Filtres (category, belowThreshold)
 */
export function useReorderPoints(filters = {}) {
  return useQuery({
    queryKey: ['inventory-intelligence', 'reorder-points', filters],
    queryFn: () => fetchReorderPoints(filters),
    staleTime: 5 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour les prédictions de rupture de stock.
 * @param {number} horizonDays - Horizon de prédiction en jours
 */
export function useStockoutPredictions(horizonDays = 30) {
  return useQuery({
    queryKey: ['inventory-intelligence', 'stockout-predictions', horizonDays],
    queryFn: () => fetchStockoutPredictions(horizonDays),
    staleTime: 10 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour le stock dormant.
 * @param {number} rotationThreshold - Seuil de rotation (0-1, default 0.3)
 */
export function useDeadStock(rotationThreshold = 0.3) {
  return useQuery({
    queryKey: ['inventory-intelligence', 'dead-stock', rotationThreshold],
    queryFn: () => fetchDeadStock(rotationThreshold),
    staleTime: 30 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour la classification ABC-XYZ.
 */
export function useABCXYZClassification() {
  return useQuery({
    queryKey: ['inventory-intelligence', 'abc-xyz'],
    queryFn: fetchABCXYZClassification,
    staleTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour les suggestions de réapprovisionnement.
 * @param {number} limit - Nombre max de suggestions
 */
export function useReorderSuggestions(limit = 20) {
  return useQuery({
    queryKey: ['inventory-intelligence', 'reorder-suggestions', limit],
    queryFn: () => fetchReorderSuggestions(limit),
    staleTime: 5 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook mutation pour calculer l'EOQ (Economic Order Quantity).
 */
export function useCalculateEOQ() {
  return useMutation({
    mutationFn: (params) => calculateEOQ(params),
  });
}

/**
 * Hook mutation pour calculer le stock de sécurité.
 */
export function useCalculateSafetyStock() {
  return useMutation({
    mutationFn: (params) => calculateSafetyStock(params),
  });
}

/**
 * Hook combiné pour la page Inventory Intelligence.
 */
export function useInventoryIntelligence(options = {}) {
  const { horizonDays = 30, rotationThreshold = 0.3 } = options;

  const summary = useInventoryIntelligenceSummary();
  const reorderPoints = useReorderPoints({});
  const stockoutPredictions = useStockoutPredictions(horizonDays);
  const deadStock = useDeadStock(rotationThreshold);
  const abcXyz = useABCXYZClassification();
  const suggestions = useReorderSuggestions(20);

  const calculateEOQMutation = useCalculateEOQ();
  const calculateSafetyStockMutation = useCalculateSafetyStock();

  return {
    // Queries
    summary,
    reorderPoints,
    stockoutPredictions,
    deadStock,
    abcXyz,
    suggestions,
    // Computed
    isLoading: summary.isLoading || reorderPoints.isLoading,
    isError: summary.isError || reorderPoints.isError,
    // Mutations
    calculateEOQ: calculateEOQMutation,
    calculateSafetyStock: calculateSafetyStockMutation,
    // Actions
    refetchAll: () => {
      summary.refetch();
      reorderPoints.refetch();
      stockoutPredictions.refetch();
      deadStock.refetch();
      abcXyz.refetch();
      suggestions.refetch();
    },
  };
}

export default useInventoryIntelligence;
