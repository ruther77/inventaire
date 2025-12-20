import { useMemo } from 'react';
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  useOfflineCreate,
  useOfflineUpdate,
  useOfflineDelete,
} from './useOfflineMutation.js';
import {
  searchFinanceTransactions,
  suggestFinanceAutreTop,
  autocompleteFinanceCategories,
  batchCategorizeFinanceTransactions,
  updateFinanceTransaction,
  lockFinanceTransaction,
  importFinanceBankStatements,
  importFinanceBankStatementsPDF,
  runFinanceReconciliation,
  refreshFinanceAnomalies,
  fetchFinanceAnomalies,
  updateFinanceMatchStatus,
  fetchFinanceMatches,
  fetchFinanceAccounts,
  getFinanceAccount,
  createFinanceAccount,
  updateFinanceAccount,
  deleteFinanceAccount,
  deduplicateFinanceTransactions,
  refreshFinanceStats,
  // Phase 4: Feedback catégorisation
  recordCategoryFeedback,
  fetchCategoryFeedbackStats,
  fetchCommonCorrections,
} from '../api/client';

export const useFinanceTransactions = (filters = {}) => {
  // Stabiliser les valeurs des filtres pour éviter les re-renders inutiles
  const { entityId, accountId, categoryId, dateFrom, dateTo, amountMin, amountMax, q, size: filterSize } = filters;
  const size = filterSize || 100;

  // Créer une clé stable basée sur les valeurs primitives (pas l'objet)
  const queryKey = useMemo(
    () => ['finance', 'transactions', { entityId, accountId, categoryId, dateFrom, dateTo, amountMin, amountMax, q, size }],
    [entityId, accountId, categoryId, dateFrom, dateTo, amountMin, amountMax, q, size]
  );

  return useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam = 1 }) => searchFinanceTransactions({ ...filters, page: pageParam, size }),
    getNextPageParam: (lastPage) => {
      const total = lastPage?.total ?? 0;
      const page = lastPage?.page ?? 1;
      const sz = lastPage?.size ?? size;
      const maxPage = Math.ceil(total / sz);
      return page < maxPage ? page + 1 : undefined;
    },
    placeholderData: (previousData) => previousData,
  });
};

export const useFinanceAutreSuggestions = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'autre-top', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => suggestFinanceAutreTop(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useFinanceCategoriesAutocomplete = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'categories-autocomplete', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => autocompleteFinanceCategories(params),
    enabled: !!params.q,
    staleTime: 30 * 1000, // 30 seconds for autocomplete
  });
};

export const useFinanceBatchCategorize = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: '/finance/transactions/batch-categorize',
    mutationFn: batchCategorizeFinanceTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'autre-top'] });
    },
    metadata: {
      description: 'Catégorisation en masse de transactions',
    },
  });
};

export const useUpdateFinanceTransaction = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: (variables) => `/finance/transactions/${variables.transactionId}`,
    mutationFn: updateFinanceTransaction,
    onMutate: async ({ transactionId, payload }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['finance', 'transactions'] });

      // Snapshot previous value
      const previousData = queryClient.getQueriesData({ queryKey: ['finance', 'transactions'] });

      // Optimistically update all matching queries
      queryClient.setQueriesData({ queryKey: ['finance', 'transactions'] }, (old) => {
        if (!old?.pages) return old;

        return {
          ...old,
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items?.map((tx) =>
              tx.id === transactionId || tx.transaction_id === transactionId
                ? { ...tx, ...payload }
                : tx
            ),
          })),
        };
      });

      return { previousData };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousData) {
        context.previousData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'autre-top'] });
    },
    metadata: {
      description: 'Mise à jour d\'une transaction',
    },
  });
};

export const useLockFinanceTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: lockFinanceTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
    },
  });
};

export const useFinanceImport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importFinanceBankStatements,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
    },
  });
};

export const useFinanceImportPDF = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importFinanceBankStatementsPDF,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'imports'] });
    },
  });
};

export const useFinanceReconciliation = () =>
  useMutation({
    mutationFn: runFinanceReconciliation,
  });

export const useFinanceAnomalies = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'anomalies', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceAnomalies(params.severity),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useFinanceRefreshAnomalies = () =>
  useMutation({
    mutationFn: refreshFinanceAnomalies,
  });

export const useFinanceMatchStatus = () =>
  useMutation({
    mutationFn: updateFinanceMatchStatus,
  });

export const useFinanceMatches = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'matches', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceMatches(params.status),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// --- Accounts ---

export const useFinanceAccounts = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'accounts', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceAccounts(params),
    staleTime: 5 * 60 * 1000, // 5 minutes - accounts rarely change
  });
};

export const useFinanceAccount = (accountId) => {
  return useQuery({
    queryKey: ['finance', 'account', accountId],
    queryFn: () => getFinanceAccount(accountId),
    enabled: !!accountId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useCreateFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: '/finance/accounts',
    mutationFn: createFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
    },
    metadata: {
      description: 'Création d\'un compte bancaire',
    },
  });
};

export const useUpdateFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: (variables) => `/finance/accounts/${variables.accountId}`,
    mutationFn: updateFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'account'] });
    },
    metadata: {
      description: 'Mise à jour d\'un compte bancaire',
    },
  });
};

export const useDeleteFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useOfflineDelete({
    endpoint: (variables) => `/finance/accounts/${variables}`,
    mutationFn: deleteFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
    },
    metadata: {
      description: 'Suppression d\'un compte bancaire',
    },
  });
};

// --- Deduplication & Stats ---

export const useDeduplicateTransactions = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deduplicateFinanceTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'imports'] });
    },
  });
};

export const useRefreshFinanceStats = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshFinanceStats,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance'] });
    },
  });
};

// ============================================================================
// PHASE 4: FEEDBACK CATÉGORISATION (ML Learning Loop)
// ============================================================================

/**
 * Mutation pour enregistrer un feedback de correction de catégorie.
 * Utilisé quand un utilisateur corrige manuellement une catégorie prédite par l'IA.
 *
 * @example
 * const { mutate: recordFeedback } = useCategoryFeedback();
 * recordFeedback({
 *   transactionId: 123,
 *   payload: {
 *     actual_category_id: 5,
 *     predicted_category_id: 3,
 *     confidence_score: 0.85,
 *     correction_source: 'user_manual'
 *   }
 * });
 */
export const useCategoryFeedback = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ transactionId, payload }) => recordCategoryFeedback(transactionId, payload),
    onSuccess: () => {
      // Invalider les stats de feedback après enregistrement
      queryClient.invalidateQueries({ queryKey: ['finance', 'feedback'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
    },
  });
};

/**
 * Query pour récupérer les statistiques globales de feedback.
 * Retourne: total_corrections, unique_transactions, avg_wrong_confidence, etc.
 *
 * @example
 * const { data: stats, isLoading } = useCategoryFeedbackStats();
 * // stats = { total_corrections: 150, avg_wrong_confidence: 0.72, ... }
 */
export const useCategoryFeedbackStats = () => {
  return useQuery({
    queryKey: ['finance', 'feedback', 'stats'],
    queryFn: fetchCategoryFeedbackStats,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Query pour récupérer les patterns de correction les plus fréquents.
 * Utile pour créer des règles automatiques basées sur les corrections répétées.
 *
 * @param {number} limit - Nombre max de patterns à retourner (défaut: 10)
 *
 * @example
 * const { data: corrections } = useCommonCorrections(20);
 * // corrections = [{ from_category: 'Autre', to_category: 'Fournitures', count: 45 }, ...]
 */
export const useCommonCorrections = (limit = 10) => {
  const queryKey = useMemo(() => ['finance', 'feedback', 'common-corrections', limit], [limit]);
  return useQuery({
    queryKey,
    queryFn: () => fetchCommonCorrections(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
