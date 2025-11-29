import { useQuery } from '@tanstack/react-query';
import { fetchReportsOverview } from '../api/client.js';

export function useReportsOverview() {
  return useQuery({
    queryKey: ['reports-overview'],
    queryFn: fetchReportsOverview,
    staleTime: 60_000,
  });
}
