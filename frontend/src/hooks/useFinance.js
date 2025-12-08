import { useMemo } from 'react';
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  searchFinanceTransactions,
  suggestFinanceAutreTop,
  autocompleteFinanceCategories,
  batchCategorizeFinanceTransactions,
  importFinanceBankStatements,
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
} from '../api/client';

export const useFinanceTransactions = (filters = {}) => {
  const baseKey = useMemo(() => ['finance', 'transactions', filters], [filters]);
  const size = filters.size || 100;
  return useInfiniteQuery({
    queryKey: baseKey,
    queryFn: ({ pageParam = 1 }) => searchFinanceTransactions({ ...filters, page: pageParam, size }),
    getNextPageParam: (lastPage) => {
      const total = lastPage?.total ?? 0;
      const page = lastPage?.page ?? 1;
      const sz = lastPage?.size ?? size;
      const maxPage = Math.ceil(total / sz);
      return page < maxPage ? page + 1 : undefined;
    },
    keepPreviousData: true,
  });
};

export const useFinanceAutreSuggestions = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'autre-top', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => suggestFinanceAutreTop(params),
  });
};

export const useFinanceCategoriesAutocomplete = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'categories-autocomplete', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => autocompleteFinanceCategories(params),
    enabled: !!params.q,
  });
};

export const useFinanceBatchCategorize = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: batchCategorizeFinanceTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'autre-top'] });
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

export const useFinanceReconciliation = () =>
  useMutation({
    mutationFn: runFinanceReconciliation,
  });

export const useFinanceAnomalies = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'anomalies', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceAnomalies(params.severity),
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
  });
};

// --- Accounts ---

export const useFinanceAccounts = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'accounts', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceAccounts(params),
  });
};

export const useFinanceAccount = (accountId) => {
  return useQuery({
    queryKey: ['finance', 'account', accountId],
    queryFn: () => getFinanceAccount(accountId),
    enabled: !!accountId,
  });
};

export const useCreateFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
    },
  });
};

export const useUpdateFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'account'] });
    },
  });
};

export const useDeleteFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
    },
  });
};
