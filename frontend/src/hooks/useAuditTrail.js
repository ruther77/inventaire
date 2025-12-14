import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAuditEntries,
  searchAuditEntries,
  fetchEntityHistory,
  fetchUserActivity,
  generateAuditReport,
  fetchSecurityEvents,
  fetchRecentChanges,
  fetchAuditSummary,
  exportUserDataRGPD,
  anonymizeUserDataRGPD,
} from '../api/client.js';

/**
 * Hook pour récupérer le résumé de l'audit.
 */
export function useAuditSummary() {
  return useQuery({
    queryKey: ['audit', 'summary'],
    queryFn: fetchAuditSummary,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer les entrées d'audit avec filtres.
 * @param {Object} filters - Filtres de recherche
 */
export function useAuditEntries(filters = {}) {
  const {
    action,
    entity,
    entityId,
    userId,
    severity,
    search,
    startDate,
    endDate,
    limit = 100,
    offset = 0,
  } = filters;

  return useQuery({
    queryKey: ['audit', 'entries', filters],
    queryFn: () => fetchAuditEntries({
      action,
      entity,
      entityId,
      userId,
      severity,
      search,
      startDate,
      endDate,
      limit,
      offset,
    }),
    staleTime: 2 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour la recherche avancée d'entrées d'audit.
 * @param {Object} criteria - Critères de recherche
 */
export function useSearchAuditEntries(criteria, enabled = true) {
  return useQuery({
    queryKey: ['audit', 'search', criteria],
    queryFn: () => searchAuditEntries(criteria),
    enabled: enabled && !!criteria,
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer l'historique d'une entité spécifique.
 * @param {string} entity - Type d'entité (product, invoice, etc.)
 * @param {number} entityId - ID de l'entité
 * @param {number} limit - Nombre max d'entrées
 */
export function useEntityHistory(entity, entityId, limit = 50) {
  return useQuery({
    queryKey: ['audit', 'entity', entity, entityId, limit],
    queryFn: () => fetchEntityHistory(entity, entityId, limit),
    enabled: !!entity && !!entityId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer l'activité d'un utilisateur.
 * @param {number} userId - ID de l'utilisateur
 * @param {Object} filters - Filtres optionnels
 */
export function useUserActivity(userId, filters = {}) {
  return useQuery({
    queryKey: ['audit', 'user', userId, filters],
    queryFn: () => fetchUserActivity(userId, filters),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer les événements de sécurité récents.
 * @param {number} days - Nombre de jours à analyser (défaut: 7)
 */
export function useSecurityEvents(days = 7) {
  return useQuery({
    queryKey: ['audit', 'security', days],
    queryFn: () => fetchSecurityEvents(days),
    staleTime: 2 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour récupérer les changements récents.
 * @param {Object} filters - Filtres (entity, hours)
 */
export function useRecentChanges(filters = {}) {
  return useQuery({
    queryKey: ['audit', 'recent', filters],
    queryFn: () => fetchRecentChanges(filters),
    staleTime: 60 * 1000, // 1 minute
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook mutation pour générer un rapport d'audit.
 */
export function useGenerateAuditReport() {
  return useMutation({
    mutationFn: ({ startDate, endDate }) => generateAuditReport(startDate, endDate),
  });
}

/**
 * Hook mutation pour exporter les données d'un utilisateur (RGPD).
 */
export function useExportUserDataRGPD() {
  return useMutation({
    mutationFn: (userId) => exportUserDataRGPD(userId),
  });
}

/**
 * Hook mutation pour anonymiser les données d'un utilisateur (RGPD).
 */
export function useAnonymizeUserDataRGPD() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId) => anonymizeUserDataRGPD(userId),
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'user', userId] });
      queryClient.invalidateQueries({ queryKey: ['audit', 'entries'] });
    },
  });
}

/**
 * Hook combiné pour la page Audit Trail.
 */
export function useAuditTrail(filters = {}) {
  const summary = useAuditSummary();
  const entries = useAuditEntries(filters);
  const securityEvents = useSecurityEvents(7);

  const generateReport = useGenerateAuditReport();
  const exportUserData = useExportUserDataRGPD();
  const anonymizeUser = useAnonymizeUserDataRGPD();

  return {
    // Queries
    summary,
    entries,
    securityEvents,
    // Computed
    isLoading: summary.isLoading || entries.isLoading,
    isError: summary.isError || entries.isError,
    // Mutations
    generateReport,
    exportUserData,
    anonymizeUser,
    // Actions
    refetchAll: () => {
      summary.refetch();
      entries.refetch();
      securityEvents.refetch();
    },
  };
}

export default useAuditTrail;
