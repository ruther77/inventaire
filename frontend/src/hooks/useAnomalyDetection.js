import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  scanForAnomalies,
  detectTransactionOutliers,
  detectDuplicateInvoices,
  detectInvoiceSequenceGaps,
  detectRoundAmounts,
  fetchAnomalySummary,
  resolveAnomaly,
} from '../api/client.js';

/**
 * Hook pour le résumé des anomalies.
 */
export function useAnomalySummary() {
  return useQuery({
    queryKey: ['anomaly-detection', 'summary'],
    queryFn: fetchAnomalySummary,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour les outliers de transactions.
 * @param {Object} params - Paramètres (daysBack, threshold)
 */
export function useTransactionOutliers(params = {}) {
  const { daysBack = 90, threshold = 2.5 } = params;
  return useQuery({
    queryKey: ['anomaly-detection', 'outliers', daysBack, threshold],
    queryFn: () => detectTransactionOutliers({ daysBack, threshold }),
    staleTime: 5 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour les factures dupliquées.
 * @param {number} daysBack - Jours à analyser
 */
export function useDuplicateInvoices(daysBack = 90) {
  return useQuery({
    queryKey: ['anomaly-detection', 'duplicates', daysBack],
    queryFn: () => detectDuplicateInvoices(daysBack),
    staleTime: 10 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour les gaps de séquence de factures.
 */
export function useInvoiceSequenceGaps() {
  return useQuery({
    queryKey: ['anomaly-detection', 'sequence-gaps'],
    queryFn: detectInvoiceSequenceGaps,
    staleTime: 30 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour les montants ronds suspects.
 * @param {number} daysBack - Jours à analyser
 */
export function useRoundAmounts(daysBack = 90) {
  return useQuery({
    queryKey: ['anomaly-detection', 'round-amounts', daysBack],
    queryFn: () => detectRoundAmounts(daysBack),
    staleTime: 10 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook mutation pour scanner toutes les anomalies.
 */
export function useScanAnomalies() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params) => scanForAnomalies(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomaly-detection'] });
    },
  });
}

/**
 * Hook mutation pour résoudre une anomalie.
 */
export function useResolveAnomaly() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ anomalyId, resolution }) => resolveAnomaly(anomalyId, resolution),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomaly-detection'] });
    },
  });
}

/**
 * Hook combiné pour la page Anomalies.
 */
export function useAnomalyDetection(options = {}) {
  const { daysBack = 90 } = options;

  const summary = useAnomalySummary();
  const outliers = useTransactionOutliers({ daysBack });
  const duplicates = useDuplicateInvoices(daysBack);
  const sequenceGaps = useInvoiceSequenceGaps();
  const roundAmounts = useRoundAmounts(daysBack);

  const scanMutation = useScanAnomalies();
  const resolveMutation = useResolveAnomaly();

  return {
    // Queries
    summary,
    outliers,
    duplicates,
    sequenceGaps,
    roundAmounts,
    // Computed
    isLoading: summary.isLoading,
    isError: summary.isError,
    totalAnomalies: (outliers.data?.length || 0) +
                    (duplicates.data?.length || 0) +
                    (sequenceGaps.data?.length || 0) +
                    (roundAmounts.data?.length || 0),
    // Mutations
    scan: scanMutation,
    resolve: resolveMutation,
    // Actions
    refetchAll: () => {
      summary.refetch();
      outliers.refetch();
      duplicates.refetch();
      sequenceGaps.refetch();
      roundAmounts.refetch();
    },
  };
}

export default useAnomalyDetection;
