import { useQuery } from '@tanstack/react-query';
import { fetchProducts } from '../api/client.js';

export function useProducts(filters = { page: 1, per_page: 50 }) {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => fetchProducts(filters),
    keepPreviousData: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
}
