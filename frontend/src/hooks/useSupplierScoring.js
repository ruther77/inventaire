import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  // Legacy endpoints
  fetchSupplierScore,
  fetchSuppliersRanking,
  compareSuppliers,
  recordSupplierDelivery,
  recordSupplierInvoiceIssue,
  fetchScoringDimensions,
  fetchSupplierScoreHistory,
  // Nouveaux endpoints
  fetchSupplierScoringOverview,
  fetchSuppliersList,
  fetchSupplierDetails,
  fetchSupplierHistoryById,
  fetchScoringCriteria,
  updateScoringCriteria,
  fetchSupplierAlerts,
  acknowledgeSupplierAlert,
  recalculateSupplierScores,
} from '../api/client.js';

// ============================================================================
// NOUVEAUX HOOKS POUR SUPPLIER SCORING DETAILS
// ============================================================================

/**
 * Hook pour récupérer la vue d'ensemble du scoring fournisseurs.
 */
export function useSupplierScoringOverview() {
  return useQuery({
    queryKey: ['supplier-scoring', 'overview'],
    queryFn: fetchSupplierScoringOverview,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer la liste paginée des fournisseurs avec leurs scores.
 * @param {Object} filters - Filtres et pagination
 */
export function useSuppliersPaginated(filters = {}) {
  const { page = 1, perPage = 20, minScore, maxScore, trend, search, sortBy, sortOrder } = filters;

  return useQuery({
    queryKey: ['supplier-scoring', 'suppliers', { page, perPage, minScore, maxScore, trend, search, sortBy, sortOrder }],
    queryFn: () => fetchSuppliersList({ page, perPage, minScore, maxScore, trend, search, sortBy, sortOrder }),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    keepPreviousData: true,
  });
}

/**
 * Hook pour récupérer les détails d'un fournisseur par ID.
 * @param {number|string} supplierId - ID du fournisseur
 */
export function useSupplierDetails(supplierId) {
  return useQuery({
    queryKey: ['supplier-scoring', 'supplier-details', supplierId],
    queryFn: () => fetchSupplierDetails(supplierId),
    enabled: !!supplierId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer l'historique des scores par ID fournisseur.
 * @param {number|string} supplierId - ID du fournisseur
 * @param {Object} options - Options (limit, periodDays)
 */
export function useSupplierHistoryById(supplierId, options = {}) {
  const { limit = 12, periodDays = 365 } = options;

  return useQuery({
    queryKey: ['supplier-scoring', 'history-by-id', supplierId, { limit, periodDays }],
    queryFn: () => fetchSupplierHistoryById(supplierId, { limit, periodDays }),
    enabled: !!supplierId,
    staleTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer les critères de scoring configurables.
 */
export function useScoringCriteria() {
  return useQuery({
    queryKey: ['supplier-scoring', 'criteria'],
    queryFn: fetchScoringCriteria,
    staleTime: 60 * 60 * 1000, // 1 heure
  });
}

/**
 * Hook mutation pour mettre à jour les critères de scoring.
 */
export function useUpdateScoringCriteria() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (criteria) => updateScoringCriteria(criteria),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'criteria'] });
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'suppliers'] });
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'overview'] });
    },
  });
}

/**
 * Hook pour récupérer les alertes sur les scores fournisseurs.
 * @param {Object} filters - Filtres (severity, acknowledged, limit)
 */
export function useSupplierAlerts(filters = {}) {
  const { severity, acknowledged, limit = 50 } = filters;

  return useQuery({
    queryKey: ['supplier-scoring', 'alerts', { severity, acknowledged, limit }],
    queryFn: () => fetchSupplierAlerts({ severity, acknowledged, limit }),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refresh toutes les 5 minutes
  });
}

/**
 * Hook mutation pour acquitter une alerte fournisseur.
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId) => acknowledgeSupplierAlert(alertId),
    onSuccess: () => {
      // Invalider les queries d'alertes pour rafraîchir la liste
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'alerts'] });
    },
  });
}

/**
 * Hook mutation pour recalculer les scores des fournisseurs.
 */
export function useRecalculateScores() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ supplierIds, forceRecalculate } = {}) =>
      recalculateSupplierScores({ supplierIds, forceRecalculate }),
    onSuccess: () => {
      // Invalider toutes les queries de scoring
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring'] });
    },
  });
}

// ============================================================================
// HOOKS LEGACY (conservés pour rétrocompatibilité)
// ============================================================================

/**
 * Hook pour récupérer le classement des fournisseurs (legacy).
 * @param {Object} filters - Filtres (limit, category)
 */
export function useSuppliersRanking(filters = {}) {
  const { limit = 50, category } = filters;
  return useQuery({
    queryKey: ['supplier-scoring', 'ranking', limit, category],
    queryFn: () => fetchSuppliersRanking({ limit, category }),
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    select: (data) => data?.items || data || [],
  });
}

/**
 * Hook pour récupérer le score d'un fournisseur par nom (legacy).
 * @param {string} supplierName - Nom du fournisseur
 * @param {number} periodDays - Période en jours
 */
export function useSupplierScore(supplierName, periodDays = 90) {
  return useQuery({
    queryKey: ['supplier-scoring', 'supplier', supplierName, periodDays],
    queryFn: () => fetchSupplierScore(supplierName, periodDays),
    enabled: !!supplierName,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer l'historique de score d'un fournisseur par nom (legacy).
 * @param {string} supplierName - Nom du fournisseur
 * @param {number} limit - Nombre d'entrées
 */
export function useSupplierScoreHistory(supplierName, limit = 12) {
  return useQuery({
    queryKey: ['supplier-scoring', 'history', supplierName, limit],
    queryFn: () => fetchSupplierScoreHistory(supplierName, limit),
    enabled: !!supplierName,
    staleTime: 30 * 60 * 1000,
  });
}

/**
 * Hook pour récupérer les dimensions de scoring (legacy).
 */
export function useScoringDimensions() {
  return useQuery({
    queryKey: ['supplier-scoring', 'dimensions'],
    queryFn: fetchScoringDimensions,
    staleTime: 60 * 60 * 1000, // 1 heure
  });
}

/**
 * Hook mutation pour comparer des fournisseurs (legacy).
 */
export function useCompareSuppliers() {
  return useMutation({
    mutationFn: (supplierIds) => compareSuppliers(supplierIds),
  });
}

/**
 * Hook mutation pour enregistrer une livraison (legacy).
 */
export function useRecordDelivery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (deliveryData) => recordSupplierDelivery(deliveryData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'supplier', variables.supplierId] });
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'ranking'] });
    },
  });
}

/**
 * Hook mutation pour enregistrer un problème de facture (legacy).
 */
export function useRecordInvoiceIssue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (issueData) => recordSupplierInvoiceIssue(issueData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'supplier', variables.supplierId] });
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring', 'ranking'] });
    },
  });
}

// ============================================================================
// HOOK COMBINÉ PRINCIPAL
// ============================================================================

/**
 * Hook combiné pour la page Scoring Fournisseurs.
 * Combine les nouveaux et anciens hooks pour une utilisation simplifiée.
 */
export function useSupplierScoring(options = {}) {
  const {
    limit = 50,
    selectedSupplierId,
    page = 1,
    perPage = 20,
    filters = {}
  } = options;

  const queryClient = useQueryClient();

  // Nouveaux hooks
  const overview = useSupplierScoringOverview();
  const suppliersPaginated = useSuppliersPaginated({ page, perPage, ...filters });
  const alerts = useSupplierAlerts({ limit: 10 });
  const criteria = useScoringCriteria();

  // Legacy hooks (pour rétrocompatibilité)
  const ranking = useSuppliersRanking({ limit });
  const dimensions = useScoringDimensions();

  // Détails du fournisseur sélectionné
  const selectedSupplier = useSupplierDetails(selectedSupplierId);
  const selectedHistory = useSupplierHistoryById(selectedSupplierId);

  // Mutations
  const compareMutation = useCompareSuppliers();
  const recordDeliveryMutation = useRecordDelivery();
  const recordIssueMutation = useRecordInvoiceIssue();
  const recalculateMutation = useRecalculateScores();
  const updateCriteriaMutation = useUpdateScoringCriteria();

  return {
    // Nouveaux hooks
    overview,
    suppliersPaginated,
    alerts,
    criteria,

    // Legacy hooks
    ranking,
    dimensions,

    // Fournisseur sélectionné
    selectedSupplier,
    selectedHistory,

    // Computed
    isLoading: overview.isLoading || suppliersPaginated.isLoading,
    isError: overview.isError || suppliersPaginated.isError,
    suppliers: suppliersPaginated.data?.data?.suppliers || suppliersPaginated.data?.suppliers || [],
    totalSuppliers: suppliersPaginated.data?.data?.total || suppliersPaginated.data?.total || 0,
    topSuppliers: ranking.data?.slice(0, 5) || [],
    bottomSuppliers: ranking.data?.slice(-5).reverse() || [],

    // Mutations
    compare: compareMutation,
    recordDelivery: recordDeliveryMutation,
    recordIssue: recordIssueMutation,
    recalculate: recalculateMutation,
    updateCriteria: updateCriteriaMutation,

    // Actions
    refetchAll: () => {
      queryClient.invalidateQueries({ queryKey: ['supplier-scoring'] });
    },
    refetchOverview: () => overview.refetch(),
    refetchSuppliers: () => suppliersPaginated.refetch(),
    refetchAlerts: () => alerts.refetch(),
  };
}

export default useSupplierScoring;
