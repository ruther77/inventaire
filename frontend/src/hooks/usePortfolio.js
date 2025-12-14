import { useQuery } from '@tanstack/react-query';
import { fetchCapitalOverview } from '../api/client.js';

/**
 * Hook pour récupérer la vue d'ensemble du portefeuille/capital.
 */
export function useCapitalOverview() {
  return useQuery({
    queryKey: ['capital', 'overview'],
    queryFn: fetchCapitalOverview,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

/**
 * Hook combiné pour la page Portfolio.
 */
export function usePortfolio() {
  const overview = useCapitalOverview();

  return {
    // Query
    overview,
    // Data shortcuts
    entities: overview.data?.entities || [],
    globalSummary: overview.data?.global_summary || {
      stock_value: 0,
      bank_balance: 0,
      cash_balance: 0,
      total_assets: 0,
    },
    latestPrices: Array.isArray(overview.data?.latest_prices) ? overview.data.latest_prices : [],
    // Computed
    isLoading: overview.isLoading,
    isError: overview.isError,
    // Actions
    refetch: overview.refetch,
  };
}

export default usePortfolio;
