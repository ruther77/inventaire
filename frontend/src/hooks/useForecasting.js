/**
 * Module de hooks pour les prévisions et analyses prédictives (ventes, stock, trésorerie).
 * @module hooks/useForecasting
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import {
  forecastSales,
  fetchStockDepletionForecast,
  fetchCashFlowForecast,
  fetchPriceTrendForecast,
  fetchForecastingSummary,
} from '../api/client.js';

/**
 * Hook pour récupérer le résumé des prévisions.
 *
 * Fournit une vue d'ensemble des prédictions actives : ventes attendues,
 * risques de rupture, tendances de trésorerie, etc.
 *
 * @returns {Object} Query TanStack avec le résumé des prévisions
 * @property {Object} data - Résumé des différentes prévisions
 * @property {boolean} isLoading - État de chargement
 *
 * @example
 * const { data: summary } = useForecastingSummary();
 * console.log(summary.salesForecast, summary.stockAlerts);
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
 * Hook pour les prévisions de dépletion (épuisement) du stock.
 *
 * Estime la date à laquelle un produit sera en rupture de stock
 * en fonction de la consommation actuelle et des tendances historiques.
 *
 * @param {Object} params - Paramètres de prévision
 * @param {number} params.productId - ID du produit à analyser
 * @param {number} [params.horizonDays=30] - Horizon de prévision en jours
 *
 * @returns {Object} Query TanStack avec la prévision de dépletion
 * @property {Object} data - Date estimée de rupture et recommandations
 *
 * @example
 * const { data: forecast } = useStockDepletionForecast({
 *   productId: 42,
 *   horizonDays: 60
 * });
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
 * Hook pour les prévisions de trésorerie (cash-flow).
 *
 * Prédit l'évolution de la trésorerie en tenant compte des encaissements
 * et décaissements attendus (ventes, achats, charges fixes).
 *
 * @param {number} [horizonDays=90] - Horizon de prévision en jours
 *
 * @returns {Object} Query TanStack avec la prévision de cash-flow
 * @property {Array} data - Évolution journalière/hebdomadaire de la trésorerie
 *
 * @example
 * const { data: cashFlow } = useCashFlowForecast(120);
 * // Prévision sur 4 mois
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
