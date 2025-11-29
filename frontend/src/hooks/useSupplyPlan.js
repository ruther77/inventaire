import { useQuery } from '@tanstack/react-query';
import { fetchSupplyPlan } from '../api/client.js';

export function useSupplyPlan(filters) {
  return useQuery({
    queryKey: ['supply-plan', filters],
    queryFn: () => fetchSupplyPlan(filters),
    keepPreviousData: true,
  });
}
