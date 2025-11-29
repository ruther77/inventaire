import { useQuery } from '@tanstack/react-query';
import { fetchPriceHistory } from '../api/client.js';

export function usePriceHistory(filters) {
  return useQuery({
    queryKey: ['price-history', filters],
    queryFn: () => fetchPriceHistory(filters),
    keepPreviousData: true,
  });
}
