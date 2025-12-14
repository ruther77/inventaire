import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  runBankReconciliation,
  fetchUnmatchedTransactions,
  fetchUnmatchedInvoices,
  createManualMatch,
  fetchSupplierAliases,
  createSupplierAlias,
  deleteSupplierAlias,
  fetchReconciliationSummary,
} from '../api/client.js';
import { useAuth } from './useAuth.js';

/**
 * Hook pour récupérer le résumé du rapprochement bancaire.
 * @param {number} daysBack - Nombre de jours à analyser (défaut: 90)
 */
export function useReconciliationSummary(daysBack = 90) {
  return useQuery({
    queryKey: ['reconciliation', 'summary', daysBack],
    queryFn: () => fetchReconciliationSummary(daysBack),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000,   // 30 minutes
  });
}

/**
 * Hook pour récupérer les transactions non rapprochées.
 * @param {Object} filters - Filtres (daysBack, minAmount)
 */
export function useUnmatchedTransactions(filters = {}) {
  const { daysBack = 90, minAmount = 0 } = filters;
  return useQuery({
    queryKey: ['reconciliation', 'unmatched', 'transactions', daysBack, minAmount],
    queryFn: () => fetchUnmatchedTransactions({ daysBack, minAmount }),
    staleTime: 2 * 60 * 1000, // 2 minutes
    select: (data) => data?.items || (Array.isArray(data) ? data : []),
  });
}

/**
 * Hook pour récupérer les factures non rapprochées.
 * @param {number} daysBack - Nombre de jours à analyser
 */
export function useUnmatchedInvoices(daysBack = 90) {
  return useQuery({
    queryKey: ['reconciliation', 'unmatched', 'invoices', daysBack],
    queryFn: () => fetchUnmatchedInvoices(daysBack),
    staleTime: 2 * 60 * 1000,
    select: (data) => data?.items || (Array.isArray(data) ? data : []),
  });
}

/**
 * Hook pour récupérer les alias fournisseurs.
 */
export function useSupplierAliases() {
  return useQuery({
    queryKey: ['reconciliation', 'aliases'],
    queryFn: fetchSupplierAliases,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook mutation pour lancer le rapprochement automatique.
 */
export function useRunReconciliation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params) => runBankReconciliation(params),
    onSuccess: () => {
      // Invalider toutes les queries de rapprochement
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
    },
  });
}

/**
 * Hook mutation pour créer un rapprochement manuel.
 */
export function useCreateManualMatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => createManualMatch(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation', 'unmatched'] });
      queryClient.invalidateQueries({ queryKey: ['reconciliation', 'summary'] });
    },
  });
}

/**
 * Hook mutation pour créer un alias fournisseur.
 */
export function useCreateSupplierAlias() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => createSupplierAlias(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation', 'aliases'] });
    },
  });
}

/**
 * Hook mutation pour supprimer un alias fournisseur.
 */
export function useDeleteSupplierAlias() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (aliasId) => deleteSupplierAlias(aliasId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation', 'aliases'] });
    },
  });
}

/**
 * Hook combiné pour toutes les données de rapprochement.
 * Utile pour la page principale.
 */
export function useBankReconciliation(filters = {}) {
  const { daysBack = 90, minAmount = 0 } = filters;
  const { isAuthenticated } = useAuth();

  const summary = useQuery({
    queryKey: ['reconciliation', 'summary', daysBack],
    queryFn: () => fetchReconciliationSummary(daysBack),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    enabled: isAuthenticated,
  });

  const transactions = useQuery({
    queryKey: ['reconciliation', 'unmatched', 'transactions', daysBack, minAmount],
    queryFn: () => fetchUnmatchedTransactions({ daysBack, minAmount }),
    staleTime: 2 * 60 * 1000,
    select: (data) => data?.items || (Array.isArray(data) ? data : []),
    enabled: isAuthenticated,
  });

  const invoices = useQuery({
    queryKey: ['reconciliation', 'unmatched', 'invoices', daysBack],
    queryFn: () => fetchUnmatchedInvoices(daysBack),
    staleTime: 2 * 60 * 1000,
    select: (data) => data?.items || (Array.isArray(data) ? data : []),
    enabled: isAuthenticated,
  });

  // Only fetch aliases when authenticated (not always needed on page load)
  const aliases = useQuery({
    queryKey: ['reconciliation', 'aliases'],
    queryFn: fetchSupplierAliases,
    staleTime: 10 * 60 * 1000,
    enabled: isAuthenticated,
  });

  const runReconciliation = useRunReconciliation();
  const createMatch = useCreateManualMatch();
  const createAlias = useCreateSupplierAlias();
  const deleteAlias = useDeleteSupplierAlias();

  return {
    // Queries
    summary,
    transactions,
    invoices,
    aliases,
    // Computed
    isLoading: summary.isLoading || transactions.isLoading || invoices.isLoading,
    isError: summary.isError || transactions.isError || invoices.isError,
    // Mutations
    runReconciliation,
    createMatch,
    createAlias,
    deleteAlias,
    // Actions
    refetchAll: () => {
      summary.refetch();
      transactions.refetch();
      invoices.refetch();
    },
  };
}

export default useBankReconciliation;
