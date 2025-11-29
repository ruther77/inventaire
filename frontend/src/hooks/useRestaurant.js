import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api, {
  fetchRestaurantDashboard,
  updateRestaurantIngredientPrice,
  fetchRestaurantIngredientPriceHistory,
  updateRestaurantPlatPrice,
  fetchRestaurantPlatPriceHistory,
  fetchRestaurantPriceHistoryOverview,
  fetchRestaurantBankStatements,
  fetchRestaurantBankStatementSummary,
  fetchRestaurantBankAccountsOverview,
  fetchRestaurantForecastOverview,
  fetchRestaurantTvaSummary,
  createExpenseFromBankStatement,
  createRestaurantBankStatement,
  updateRestaurantBankStatement,
  importRestaurantBankStatementsPdf,
} from '../api/client.js';

export const useRestaurantCategories = () =>
  useQuery({ queryKey: ['restaurant', 'categories'], queryFn: async () => (await api.get('/restaurant/charges/categories')).data });

export const useCreateRestaurantCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (nom) => api.post('/restaurant/charges/categories', { nom }),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'categories']);
    },
  });
};

export const useRestaurantCostCenters = () =>
  useQuery({ queryKey: ['restaurant', 'cost-centers'], queryFn: async () => (await api.get('/restaurant/charges/cost-centers')).data });

export const useCreateRestaurantCostCenter = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (nom) => api.post('/restaurant/charges/cost-centers', { nom }),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'cost-centers']);
    },
  });
};

export const useRestaurantExpenses = () =>
  useQuery({ queryKey: ['restaurant', 'expenses'], queryFn: async () => (await api.get('/restaurant/charges/expenses')).data });

export const useCreateRestaurantExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => api.post('/restaurant/charges/expenses', payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'expenses']);
      queryClient.invalidateQueries(['restaurant', 'expense-summary']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};

export const useRestaurantExpenseSummary = () =>
  useQuery({ queryKey: ['restaurant', 'expense-summary'], queryFn: async () => (await api.get('/restaurant/charges/summary')).data });

export const useRestaurantIngredients = () =>
  useQuery({ queryKey: ['restaurant', 'ingredients'], queryFn: async () => (await api.get('/restaurant/ingredients')).data });

export const useCreateRestaurantIngredient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => api.post('/restaurant/ingredients', payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};

export const useRestaurantPlats = () =>
  useQuery({ queryKey: ['restaurant', 'plats'], queryFn: async () => (await api.get('/restaurant/plats')).data });

export const useCreateRestaurantPlat = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => api.post('/restaurant/plats', payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};

export const useAttachIngredientToPlat = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ platId, payload }) => api.post(`/restaurant/plats/${platId}/ingredients`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};


export const useUpdateRestaurantIngredientPrice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ingredientId, payload }) => updateRestaurantIngredientPrice(ingredientId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
      queryClient.invalidateQueries(['restaurant', 'prices', 'history']);
      if (variables?.ingredientId) {
        queryClient.invalidateQueries({
          queryKey: ['restaurant', 'ingredient', 'history', variables.ingredientId],
        });
      }
    },
  });
};


export const useRestaurantIngredientPriceHistory = (ingredientId) =>
  useQuery({
    queryKey: ['restaurant', 'ingredient', 'history', ingredientId],
    queryFn: () => fetchRestaurantIngredientPriceHistory(ingredientId),
    enabled: Boolean(ingredientId),
  });

export const useUpdateRestaurantPlatPrice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ platId, payload }) => updateRestaurantPlatPrice(platId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
      queryClient.invalidateQueries(['restaurant', 'prices', 'history']);
      if (variables?.platId) {
        queryClient.invalidateQueries({
          queryKey: ['restaurant', 'plat', 'history', variables.platId],
        });
      }
    },
  });
};

export const useRestaurantPlatPriceHistory = (platId) =>
  useQuery({
    queryKey: ['restaurant', 'plat', 'history', platId],
    queryFn: () => fetchRestaurantPlatPriceHistory(platId),
    enabled: Boolean(platId),
  });

export const useRestaurantPriceHistoryOverview = (limit = 12) =>
  useQuery({
    queryKey: ['restaurant', 'prices', 'history', limit],
    queryFn: () => fetchRestaurantPriceHistoryOverview(limit),
  });

export const useRestaurantDashboard = () =>
  useQuery({ queryKey: ['restaurant', 'dashboard'], queryFn: fetchRestaurantDashboard });


export const useRestaurantBankStatements = (account) =>
  useQuery({
    queryKey: ['restaurant', 'bank-statements', account ?? 'all'],
    queryFn: () => fetchRestaurantBankStatements(account),
  });

export const useRestaurantBankStatementSummary = (account, months = 6, grouping = 'default') =>
  useQuery({
    queryKey: ['restaurant', 'bank-statements-summary', account ?? 'all', months, grouping],
    queryFn: () => fetchRestaurantBankStatementSummary({ account, months, grouping }),
  });

export const useRestaurantBankAccountsOverview = () =>
  useQuery({
    queryKey: ['restaurant', 'bank-accounts', 'overview'],
    queryFn: fetchRestaurantBankAccountsOverview,
  });

export const useRestaurantForecastOverview = ({ horizonDays = 30, granularity = 'weekly', top = 8 } = {}) =>
  useQuery({
    queryKey: ['restaurant', 'forecasts', horizonDays, granularity, top],
    queryFn: () => fetchRestaurantForecastOverview({ horizonDays, granularity, top }),
  });

export const useRestaurantTvaSummary = (months = 6) =>
  useQuery({
    queryKey: ['restaurant', 'tva-summary', months],
    queryFn: () => fetchRestaurantTvaSummary(months),
  });

export const useCreateRestaurantBankStatement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => createRestaurantBankStatement(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'bank-statements', variables?.account]);
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'bank-statements-summary'] });
    },
  });
};

export const useUpdateRestaurantBankStatement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, payload }) => updateRestaurantBankStatement(entryId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'bank-statements', variables?.payload?.account]);
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'bank-statements-summary'] });
    },
  });
};

export const useImportRestaurantBankStatementsPdf = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ account, file }) => importRestaurantBankStatementsPdf(account, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'bank-statements', variables?.account]);
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'bank-statements-summary'] });
    },
  });
};

export const useCreateExpenseFromBankStatement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, payload }) => createExpenseFromBankStatement(entryId, payload),
    onSuccess: (_, variables) => {
      if (variables?.account) {
        queryClient.invalidateQueries(['restaurant', 'bank-statements', variables.account]);
      }
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'bank-statements-summary'] });
      queryClient.invalidateQueries(['restaurant', 'expenses']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};
