import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchCockpitOverview,
  fetchCockpitLiveKPIs,
  fetchCockpitAlerts,
  acknowledgeCockpitAlert,
  fetchCockpitHealth,
} from '../api/client.js';

/**
 * Hook pour la vue d'ensemble du cockpit.
 */
export function useCockpitOverview() {
  return useQuery({
    queryKey: ['cockpit', 'overview'],
    queryFn: fetchCockpitOverview,
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });
}

/**
 * Hook pour les KPIs temps réel.
 * Refetch automatique toutes les 30 secondes.
 */
export function useCockpitLiveKPIs() {
  return useQuery({
    queryKey: ['cockpit', 'kpis', 'live'],
    queryFn: fetchCockpitLiveKPIs,
    staleTime: 30 * 1000, // 30 secondes
    refetchInterval: 30 * 1000, // Auto-refetch toutes les 30s
  });
}

/**
 * Hook pour les alertes du cockpit.
 * @param {Object} filters - Filtres (severity, acknowledged)
 */
export function useCockpitAlerts(filters = {}) {
  const { severity, acknowledged = false } = filters;
  return useQuery({
    queryKey: ['cockpit', 'alerts', severity, acknowledged],
    queryFn: () => fetchCockpitAlerts({ severity, acknowledged }),
    staleTime: 60 * 1000, // 1 minute
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour l'état de santé du système.
 */
export function useCockpitHealth() {
  return useQuery({
    queryKey: ['cockpit', 'health'],
    queryFn: fetchCockpitHealth,
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000, // Auto-refetch toutes les minutes
  });
}

/**
 * Hook mutation pour acquitter une alerte.
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId) => acknowledgeCockpitAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cockpit', 'alerts'] });
    },
  });
}

/**
 * Hook combiné pour la page Cockpit.
 */
export function useCockpit(options = {}) {
  const { alertSeverity } = options;

  const overview = useCockpitOverview();
  const liveKPIs = useCockpitLiveKPIs();
  const alerts = useCockpitAlerts({ severity: alertSeverity });
  const health = useCockpitHealth();

  const acknowledgeMutation = useAcknowledgeAlert();

  return {
    // Queries
    overview,
    liveKPIs,
    alerts,
    health,
    // Computed
    isLoading: overview.isLoading,
    isError: overview.isError,
    criticalAlerts: alerts.data?.filter(a => a.severity === 'critical') || [],
    warningAlerts: alerts.data?.filter(a => a.severity === 'warning') || [],
    systemHealthy: health.data?.status === 'healthy',
    // Mutations
    acknowledgeAlert: acknowledgeMutation,
    // Actions
    refetchAll: () => {
      overview.refetch();
      liveKPIs.refetch();
      alerts.refetch();
      health.refetch();
    },
  };
}

export default useCockpit;
