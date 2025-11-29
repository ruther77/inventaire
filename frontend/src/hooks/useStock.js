import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../api/client.js';

const fetchTimeseries = async ({ windowDays, productId }) => {
  const params = new URLSearchParams();
  params.set('window_days', windowDays);
  if (productId) params.set('product_id', productId);
  const { data } = await api.get(`/stock/movements/timeseries?${params.toString()}`);
  return data.items ?? [];
};

const fetchRecent = async ({ limit, productId }) => {
  const params = new URLSearchParams();
  params.set('limit', limit);
  if (productId) params.set('product_id', productId);
  const { data } = await api.get(`/stock/movements/recent?${params.toString()}`);
  return data.items ?? [];
};

export function useStockTimeseries(filters) {
  return useQuery({
    queryKey: ['stock-timeseries', filters],
    queryFn: () => fetchTimeseries(filters),
    keepPreviousData: true,
  });
}

export function useRecentMovements(filters) {
  return useQuery({
    queryKey: ['stock-recent', filters],
    queryFn: () => fetchRecent(filters),
    keepPreviousData: true,
  });
}

export function useStockAdjustment() {
  return useMutation({
    mutationFn: async ({ productId, targetQuantity, username }) => {
      const { data } = await api.post('/stock/adjustments', {
        product_id: productId,
        target_quantity: targetQuantity,
        username,
      });
      return data;
    },
  });
}
