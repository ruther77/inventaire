import { useQuery } from '@tanstack/react-query';
import { fetchDashboardMetrics } from '../api/client.js';

export function useDashboardMetrics() {
  return useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchDashboardMetrics,
    staleTime: 60 * 1000, // 1 minute
    refetchOnWindowFocus: false,
  });
}
