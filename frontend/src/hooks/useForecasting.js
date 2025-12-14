import { useQuery, useMutation } from '@tanstack/react-query';
import {
  forecastSales,
  fetchStockDepletionForecast,
  fetchCashFlowForecast,
  fetchPriceTrendForecast,
  fetchForecastingSummary,
} from '../api/client.js';

/**
 * Hook pour le résumé des prévisions.
 */
export function useForecastingSummary() {
  return useQuery({
    queryKey: ['forecasting', 'summary'],
    queryFn: fetchForecastingSummary,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour les prévisions de dépletion de stock.
 * @param {Object} params - Paramètres (productId, horizonDays)
 */
export function useStockDepletionForecast(params = {}) {
  const { productId, horizonDays = 30 } = params;
  return useQuery({
    queryKey: ['forecasting', 'stock-depletion', productId, horizonDays],
    queryFn: () => fetchStockDepletionForecast({ productId, horizonDays }),
    enabled: !!productId,
    staleTime: 10 * 60 * 1000,
  });
}

/**
 * Hook pour les prévisions de cash-flow.
 * @param {number} horizonDays - Horizon de prévision
 */
export function useCashFlowForecast(horizonDays = 90) {
  return useQuery({
    queryKey: ['forecasting', 'cash-flow', horizonDays],
    queryFn: () => fetchCashFlowForecast({ horizonDays }),
    staleTime: 15 * 60 * 1000,
  });
}

/**
 * Hook pour les prévisions de tendance des prix.
 * @param {Object} params - Paramètres (productId, horizonDays)
 */
export function usePriceTrendForecast(params = {}) {
  const { productId, horizonDays = 30 } = params;
  return useQuery({
    queryKey: ['forecasting', 'price-trend', productId, horizonDays],
    queryFn: () => fetchPriceTrendForecast({ productId, horizonDays }),
    enabled: !!productId,
    staleTime: 30 * 60 * 1000,
  });
}

/**
 * Hook mutation pour lancer une prévision de ventes.
 */
export function useForecastSales() {
  return useMutation({
    mutationFn: (params) => forecastSales(params),
  });
}

/**
 * Hook combiné pour la page Forecast.
 */
export function useForecasting(options = {}) {
  const { cashFlowHorizon = 90 } = options;

  const summary = useForecastingSummary();
  const cashFlow = useCashFlowForecast(cashFlowHorizon);

  const forecastSalesMutation = useForecastSales();

  return {
    // Queries
    summary,
    cashFlow,
    // Computed
    isLoading: summary.isLoading || cashFlow.isLoading,
    isError: summary.isError || cashFlow.isError,
    // Mutations
    forecastSales: forecastSalesMutation,
    // Actions
    refetchAll: () => {
      summary.refetch();
      cashFlow.refetch();
    },
  };
}

export default useForecasting;
