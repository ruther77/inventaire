import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchFinanceCategories,
  createFinanceCategory,
  fetchFinanceCostCenters,
  createFinanceCostCenter,
  fetchFinanceCategoryStats,
  fetchFinanceAccounts,
  fetchFinanceAccountsOverview,
  fetchFinanceDashboardSummary,
  fetchFinanceTimeline,
  fetchFinanceCategoryBreakdown,
  fetchFinanceTreasury,
  fetchFinanceRules,
  createFinanceRule,
  updateFinanceRule,
  deleteFinanceRule,
} from '../api/client';

export const useFinanceCategories = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'categories', filters],
    queryFn: () => fetchFinanceCategories(filters),
  });

export const useCreateFinanceCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createFinanceCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'categories'] });
    },
  });
};

export const useFinanceCostCenters = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'cost-centers', filters],
    queryFn: () => fetchFinanceCostCenters(filters),
  });

export const useCreateFinanceCostCenter = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createFinanceCostCenter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'cost-centers'] });
    },
  });
};

export const useFinanceAccounts = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'accounts', filters],
    queryFn: () => fetchFinanceAccounts(filters),
  });

export const useFinanceRules = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'rules', filters],
    queryFn: () => fetchFinanceRules(filters),
    retry: 1,
    staleTime: 30000,
  });

export const useFinanceCategoryStats = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'categories-stats', filters],
    queryFn: () => fetchFinanceCategoryStats(filters),
  });

export const useFinanceAccountsOverviewStats = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'accounts-overview', filters],
    queryFn: () => fetchFinanceAccountsOverview(filters),
  });

export const useFinanceDashboardSummary = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'dashboard-summary', filters],
    queryFn: () => fetchFinanceDashboardSummary(filters),
  });

export const useFinanceTimeline = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'timeline', filters],
    queryFn: () => fetchFinanceTimeline(filters),
    staleTime: 60000, // 1 minute
  });

export const useFinanceCategoryBreakdown = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'category-breakdown', filters],
    queryFn: () => fetchFinanceCategoryBreakdown(filters),
    staleTime: 60000,
  });

export const useFinanceTreasury = (filters = {}) =>
  useQuery({
    queryKey: ['finance', 'treasury', filters],
    queryFn: () => fetchFinanceTreasury(filters),
    staleTime: 60000,
  });

export const useFinanceRuleMutations = () => {
  const queryClient = useQueryClient();
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['finance', 'rules'] });
  };
  return {
    create: useMutation({
      mutationFn: createFinanceRule,
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: ({ id, payload }) => updateFinanceRule(id, payload),
      onSuccess: invalidate,
    }),
    remove: useMutation({
      mutationFn: deleteFinanceRule,
      onSuccess: invalidate,
    }),
  };
};
