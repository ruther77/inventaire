import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api, {
  fetchRestaurantDashboard,
  updateRestaurantIngredientPrice,
  fetchRestaurantIngredientPriceHistory,
  updateRestaurantPlatPrice,
  fetchRestaurantPlatPriceHistory,
  fetchRestaurantPriceHistoryOverview,
  fetchRestaurantForecastOverview,
  fetchRestaurantTvaSummary,
  fetchRestaurantConsumptions,
  fetchRestaurantPriceHistoryComparison,
  fetchRestaurantPlatMappings,
  syncRestaurantIngredients,
  fetchEpicerieProducts,
  updatePlatMapping,
  deletePlatMapping,
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

export const useRestaurantConsumptions = () =>
  useQuery({
    queryKey: ['restaurant', 'consumptions'],
    queryFn: fetchRestaurantConsumptions,
  });

export const useRestaurantPriceHistoryComparison = () =>
  useQuery({
    queryKey: ['restaurant', 'price-history-comparison'],
    queryFn: fetchRestaurantPriceHistoryComparison,
  });

export const useRestaurantPlatMappings = () =>
  useQuery({
    queryKey: ['restaurant', 'plat-mappings'],
    queryFn: fetchRestaurantPlatMappings,
  });

export const useSyncRestaurantIngredients = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: syncRestaurantIngredients,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'plat-mappings'] });
    },
  });
};

export const useEpicerieProducts = () =>
  useQuery({
    queryKey: ['epicerie', 'products'],
    queryFn: fetchEpicerieProducts,
  });

export const useUpdatePlatMapping = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ platId, payload }) => updatePlatMapping(platId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'plat-mappings'] });
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'consumptions'] });
    },
  });
};

export const useDeletePlatMapping = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (platId) => deletePlatMapping(platId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'plat-mappings'] });
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'consumptions'] });
    },
  });
};
