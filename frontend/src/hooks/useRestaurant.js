import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  useOfflineCreate,
  useOfflineUpdate,
  useOfflineDelete,
} from './useOfflineMutation.js';
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
  fetchEpicerieProducts,
  syncRestaurantIngredientPrices,
  fetchRestaurantPriceSyncStatus,
  linkIngredientToEpicerie,
  unlinkIngredientFromEpicerie,
  updateIngredientRatio,
  fetchRestaurantOverview,
  fetchRestaurantPlatDetails,
  fetchRestaurantPlatIngredients,
  simulatePlatPrice,
  fetchRestaurantAlerts,
  fetchRestaurantFoodCostAnalysis,
  fetchRestaurantMenusOverview,
} from '../api/client.js';

export const useRestaurantCategories = () =>
  useQuery({
    queryKey: ['restaurant', 'categories'],
    queryFn: async () => (await api.get('/restaurant/charges/categories')).data,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

export const useCreateRestaurantCategory = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: '/restaurant/charges/categories',
    mutationFn: (nom) => api.post('/restaurant/charges/categories', { nom }),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'categories']);
    },
    metadata: {
      description: 'Création d\'une catégorie de charges',
    },
  });
};

export const useRestaurantCostCenters = () =>
  useQuery({
    queryKey: ['restaurant', 'cost-centers'],
    queryFn: async () => (await api.get('/restaurant/charges/cost-centers')).data,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

export const useCreateRestaurantCostCenter = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: '/restaurant/charges/cost-centers',
    mutationFn: (nom) => api.post('/restaurant/charges/cost-centers', { nom }),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'cost-centers']);
    },
    metadata: {
      description: 'Création d\'un centre de coûts',
    },
  });
};

export const useRestaurantExpenses = () =>
  useQuery({
    queryKey: ['restaurant', 'expenses'],
    queryFn: async () => (await api.get('/restaurant/charges/expenses')).data,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

export const useCreateRestaurantExpense = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: '/restaurant/charges/expenses',
    mutationFn: (payload) => api.post('/restaurant/charges/expenses', payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'expenses']);
      queryClient.invalidateQueries(['restaurant', 'expense-summary']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Création d\'une charge',
    },
  });
};

export const useRestaurantExpenseSummary = () =>
  useQuery({
    queryKey: ['restaurant', 'expense-summary'],
    queryFn: async () => (await api.get('/restaurant/charges/summary')).data,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

export const useRestaurantIngredients = () =>
  useQuery({
    queryKey: ['restaurant', 'ingredients'],
    queryFn: async () => (await api.get('/restaurant/ingredients')).data,
    staleTime: 60 * 1000, // 1 minute
  });

export const useCreateRestaurantIngredient = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: '/restaurant/ingredients',
    mutationFn: (payload) => api.post('/restaurant/ingredients', payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Création d\'un ingrédient',
    },
  });
};

export const useUpdateRestaurantIngredient = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: (variables) => `/restaurant/ingredients/${variables.ingredientId}`,
    mutationFn: ({ ingredientId, payload }) => api.put(`/restaurant/ingredients/${ingredientId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Mise à jour d\'un ingrédient',
    },
  });
};

export const useDeleteRestaurantIngredient = () => {
  const queryClient = useQueryClient();
  return useOfflineDelete({
    endpoint: (variables) => `/restaurant/ingredients/${variables}`,
    mutationFn: (ingredientId) => api.delete(`/restaurant/ingredients/${ingredientId}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Suppression d\'un ingrédient',
    },
  });
};

export const useRestaurantPlats = () =>
  useQuery({
    queryKey: ['restaurant', 'plats'],
    queryFn: async () => (await api.get('/restaurant/plats')).data,
    staleTime: 60 * 1000, // 1 minute
  });

export const useCreateRestaurantPlat = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: '/restaurant/plats',
    mutationFn: (payload) => api.post('/restaurant/plats', payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Création d\'un plat',
    },
  });
};

export const useDeleteRestaurantPlat = () => {
  const queryClient = useQueryClient();
  return useOfflineDelete({
    endpoint: (variables) => `/restaurant/plats/${variables}`,
    mutationFn: (platId) => api.delete(`/restaurant/plats/${platId}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Suppression d\'un plat',
    },
  });
};

// Ingrédients d'un plat
export const useAddIngredientToPlat = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ platId, payload }) => {
      const { data } = await api.post(`/restaurant/plats/${platId}/ingredients`, payload);
      return data.data; // Extraire le plat mis à jour
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'plat', 'details', variables.platId]);
    },
  });
};

export const useUpdateIngredientOnPlat = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ platId, ingredientId, payload }) => {
      const { data } = await api.patch(`/restaurant/plats/${platId}/ingredients/${ingredientId}`, payload);
      return data.data; // Extraire le plat mis à jour
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'plat', 'details', variables.platId]);
    },
  });
};

export const useRemoveIngredientFromPlat = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ platId, ingredientId }) => {
      const { data } = await api.delete(`/restaurant/plats/${platId}/ingredients/${ingredientId}`);
      return data.data; // Extraire le plat mis à jour
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'plat', 'details', variables.platId]);
    },
  });
};

export const useAttachIngredientToPlat = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: (variables) => `/restaurant/plats/${variables.platId}/ingredients`,
    mutationFn: ({ platId, payload }) => api.post(`/restaurant/plats/${platId}/ingredients`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Ajout d\'un ingrédient à un plat',
    },
  });
};


export const useUpdateRestaurantIngredientPrice = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: (variables) => `/restaurant/ingredients/${variables.ingredientId}/price`,
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
    metadata: {
      description: 'Mise à jour du prix d\'un ingrédient',
    },
  });
};


export const useRestaurantIngredientPriceHistory = (ingredientId) =>
  useQuery({
    queryKey: ['restaurant', 'ingredient', 'history', ingredientId],
    queryFn: () => fetchRestaurantIngredientPriceHistory(ingredientId),
    enabled: Boolean(ingredientId),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

export const useUpdateRestaurantPlatPrice = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: (variables) => `/restaurant/plats/${variables.platId}/price`,
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
    metadata: {
      description: 'Mise à jour du prix d\'un plat',
    },
  });
};

export const useRestaurantPlatPriceHistory = (platId) =>
  useQuery({
    queryKey: ['restaurant', 'plat', 'history', platId],
    queryFn: () => fetchRestaurantPlatPriceHistory(platId),
    enabled: Boolean(platId),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

export const useRestaurantPriceHistoryOverview = (limit = 12) =>
  useQuery({
    queryKey: ['restaurant', 'prices', 'history', limit],
    queryFn: () => fetchRestaurantPriceHistoryOverview(limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

export const useRestaurantDashboard = () =>
  useQuery({
    queryKey: ['restaurant', 'dashboard'],
    queryFn: fetchRestaurantDashboard,
    staleTime: 60 * 1000, // 1 minute
  });


export const useRestaurantForecastOverview = ({ horizonDays = 30, granularity = 'weekly', top = 8 } = {}) =>
  useQuery({
    queryKey: ['restaurant', 'forecasts', horizonDays, granularity, top],
    queryFn: () => fetchRestaurantForecastOverview({ horizonDays, granularity, top }),
    staleTime: 5 * 60 * 1000, // 5 minutes - forecasts don't change often
  });

export const useRestaurantTvaSummary = (months = 6) =>
  useQuery({
    queryKey: ['restaurant', 'tva-summary', months],
    queryFn: () => fetchRestaurantTvaSummary(months),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

export const useRestaurantConsumptions = (period = 'all') =>
  useQuery({
    queryKey: ['restaurant', 'consumptions', period],
    queryFn: () => fetchRestaurantConsumptions(period),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

export const useRestaurantPriceHistoryComparison = () =>
  useQuery({
    queryKey: ['restaurant', 'price-history-comparison'],
    queryFn: fetchRestaurantPriceHistoryComparison,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

export const useEpicerieProducts = () =>
  useQuery({
    queryKey: ['epicerie', 'products'],
    queryFn: fetchEpicerieProducts,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

// ============================================================================
// RESTAURANT OVERVIEW & FOOD COST
// ============================================================================

export const useRestaurantOverview = (filters = {}) =>
  useQuery({
    queryKey: ['restaurant', 'overview', filters],
    queryFn: () => fetchRestaurantOverview(filters),
    staleTime: 60 * 1000, // 1 minute
  });

export const useRestaurantPlatDetails = (platId) =>
  useQuery({
    queryKey: ['restaurant', 'plat', 'details', platId],
    queryFn: () => fetchRestaurantPlatDetails(platId),
    enabled: Boolean(platId),
    staleTime: 60 * 1000, // 1 minute
  });

export const useRestaurantPlatIngredients = (platId) =>
  useQuery({
    queryKey: ['restaurant', 'plat', 'ingredients', platId],
    queryFn: () => fetchRestaurantPlatIngredients(platId),
    enabled: Boolean(platId),
    staleTime: 60 * 1000, // 1 minute
  });

export const useSimulatePlatPrice = () => {
  return useMutation({
    mutationFn: ({ platId, payload }) => simulatePlatPrice(platId, payload),
  });
};

export const useRestaurantAlerts = (filters = {}) =>
  useQuery({
    queryKey: ['restaurant', 'alerts', filters],
    queryFn: () => fetchRestaurantAlerts(filters),
    staleTime: 60 * 1000, // 1 minute
  });

export const useRestaurantFoodCostAnalysis = (filters = {}) =>
  useQuery({
    queryKey: ['restaurant', 'food-cost-analysis', filters],
    queryFn: () => fetchRestaurantFoodCostAnalysis(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

// ============================================================================
// RESTAURANT MENUS & COÛTS (Scénario 3.6)
// ============================================================================

export const useRestaurantMenusOverview = () =>
  useQuery({
    queryKey: ['restaurant', 'menus', 'overview'],
    queryFn: fetchRestaurantMenusOverview,
    staleTime: 5 * 60 * 1000,
  });

// ============================================================================
// INGRÉDIENT-ÉPICERIE LINKING
// ============================================================================

export const useLinkIngredientEpicerie = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ingredientId, epicerieProductId, ratio = 1.0 }) =>
      linkIngredientToEpicerie(ingredientId, epicerieProductId, ratio),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};

export const useUnlinkIngredientEpicerie = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ingredientId) => unlinkIngredientFromEpicerie(ingredientId),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};

export const useUpdateIngredientRatio = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ingredientId, ratio }) => updateIngredientRatio(ingredientId, ratio),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};

// ============================================================================
// PRICE SYNC FROM EPICERIE
// ============================================================================

export const useSyncIngredientPrices = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ forceUpdate = false } = {}) => syncRestaurantIngredientPrices(forceUpdate),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'price-sync-status']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
      queryClient.invalidateQueries(['restaurant', 'prices', 'history']);
    },
  });
};

export const usePriceSyncStatus = () =>
  useQuery({
    queryKey: ['restaurant', 'price-sync-status'],
    queryFn: fetchRestaurantPriceSyncStatus,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

// ============================================================================
// STOCK TRANSFERS FROM EPICERIE
// ============================================================================

export const useTransferFromEpicerie = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ingredientId, produitEpicerieId, quantite, commentaire }) =>
      api.post('/restaurant/stock/transfer-from-epicerie', {
        ingredient_id: ingredientId,
        produit_epicerie_id: produitEpicerieId,
        quantite,
        commentaire,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-stock'] });
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
  });
};

// ============================================================================
// RESTAURANT STOCK (Mouvements, Résumé, Analytiques)
// ============================================================================

export const useRestaurantStockMovements = (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.ingredientId) params.set('ingredient_id', filters.ingredientId);
  if (filters.source) params.set('source', filters.source);
  if (filters.type) params.set('type_mouvement', filters.type);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.limit) params.set('limit', filters.limit);

  return useQuery({
    queryKey: ['restaurant-stock', 'movements', filters],
    queryFn: async () => {
      const { data } = await api.get(`/restaurant/stock/movements?${params.toString()}`);
      return data.data || data;
    },
  });
};

export const useRestaurantStockSummary = () => {
  return useQuery({
    queryKey: ['restaurant-stock', 'summary'],
    queryFn: async () => {
      const { data } = await api.get('/restaurant/stock/summary');
      return data.data || data;
    },
  });
};

export const useRestaurantStockAnalytics = (days = 30) => {
  return useQuery({
    queryKey: ['restaurant-stock', 'analytics', days],
    queryFn: async () => {
      const { data } = await api.get(`/restaurant/stock/analytics?days=${days}`);
      return data.data || data;
    },
  });
};

export const useRestaurantStockDailyByCategory = (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.typeMouvement) params.set('type_mouvement', filters.typeMouvement);

  return useQuery({
    queryKey: ['restaurant-stock', 'daily-by-category', filters],
    queryFn: async () => {
      const { data } = await api.get(`/restaurant/stock/movements/daily-by-category?${params.toString()}`);
      return data.data || data;
    },
  });
};

export const useRestaurantStockDailyByPlat = (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);

  return useQuery({
    queryKey: ['restaurant-stock', 'daily-by-plat', filters],
    queryFn: async () => {
      const { data } = await api.get(`/restaurant/stock/movements/daily-by-plat?${params.toString()}`);
      return data.data || data;
    },
  });
};

export const useCreateRestaurantStockMovement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await api.post('/restaurant/stock/movements', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-stock'] });
      queryClient.invalidateQueries(['restaurant', 'ingredients']);
    },
  });
};
