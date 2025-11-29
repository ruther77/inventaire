import { useQuery } from '@tanstack/react-query';
import { fetchInventorySummary } from '../api/client.js';

export function useInventorySummary() {
  return useQuery({
    queryKey: ['inventory-summary'],
    queryFn: fetchInventorySummary,
  });
}
