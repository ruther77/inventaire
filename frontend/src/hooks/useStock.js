/**
 * Module de hooks pour la gestion du stock et des mouvements.
 *
 * Ce module fournit:
 * - Les séries temporelles de mouvements de stock (graphiques)
 * - L'historique récent des mouvements
 * - Les ajustements manuels de stock (inventaires)
 *
 * @module hooks/useStock
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '../api/client.js';

/**
 * Récupère les mouvements de stock sous forme de série temporelle.
 * Utilisé pour afficher des graphiques d'évolution du stock.
 *
 * @param {Object} params - Paramètres de la requête
 * @param {number} params.windowDays - Fenêtre temporelle en jours
 * @param {number} [params.productId] - ID du produit à filtrer
 * @returns {Promise<Array>} Liste des mouvements avec dates
 */
const fetchTimeseries = async ({ windowDays, productId }) => {
  const params = new URLSearchParams();
  params.set('window_days', windowDays);
  if (productId) params.set('product_id', productId);
  const { data } = await api.get(`/stock/movements/timeseries?${params.toString()}`);
  return data.items ?? [];
};

/**
 * Récupère les mouvements de stock les plus récents.
 *
 * @param {Object} params - Paramètres de la requête
 * @param {number} params.limit - Nombre max de mouvements à retourner
 * @param {number} [params.productId] - ID du produit à filtrer
 * @returns {Promise<Array>} Liste des mouvements récents
 */
const fetchRecent = async ({ limit, productId }) => {
  const params = new URLSearchParams();
  params.set('limit', limit);
  if (productId) params.set('product_id', productId);
  const { data } = await api.get(`/stock/movements/recent?${params.toString()}`);
  return data.items ?? [];
};

/**
 * Hook pour récupérer les séries temporelles de mouvements de stock.
 *
 * Retourne les données formatées pour afficher un graphique d'évolution
 * du stock sur une période donnée.
 *
 * @param {Object} filters - Filtres de recherche
 * @param {number} filters.windowDays - Période en jours (7, 30, 90, etc.)
 * @param {number} [filters.productId] - ID du produit (optionnel)
 *
 * @returns {Object} Query avec les données de série temporelle
 *
 * @example
 * const { data: series } = useStockTimeseries({ windowDays: 30, productId: 10 });
 * // series = [
 * //   { date: '2025-01-01', quantity: 100, movement: +20 },
 * //   { date: '2025-01-02', quantity: 95, movement: -5 },
 * //   ...
 * // ]
 */
export function useStockTimeseries(filters) {
  return useQuery({
    queryKey: ['stock-timeseries', filters],
    queryFn: () => fetchTimeseries(filters),
    keepPreviousData: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook pour récupérer les mouvements de stock récents.
 *
 * Affiche l'historique récent des entrées/sorties de stock
 * (imports factures, ventes, ajustements, pertes).
 *
 * @param {Object} filters - Filtres de recherche
 * @param {number} filters.limit - Nombre max de mouvements
 * @param {number} [filters.productId] - ID du produit (optionnel)
 *
 * @returns {Object} Query avec les mouvements récents
 *
 * @example
 * const { data: movements } = useRecentMovements({ limit: 50 });
 * // movements = [
 * //   { id: 1, product: 'Tomates', quantity: +10, type: 'invoice', date: '...' },
 * //   { id: 2, product: 'Oignons', quantity: -3, type: 'sale', date: '...' },
 * //   ...
 * // ]
 */
export function useRecentMovements(filters) {
  return useQuery({
    queryKey: ['stock-recent', filters],
    queryFn: () => fetchRecent(filters),
    keepPreviousData: true,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook pour effectuer un ajustement manuel de stock (inventaire).
 *
 * Permet de corriger le stock en cas d'écart constaté lors d'un inventaire.
 * Crée automatiquement un mouvement de type 'adjustment' pour tracer la correction.
 *
 * @returns {Object} Mutation d'ajustement
 *
 * @example
 * const { mutate: adjustStock } = useStockAdjustment();
 *
 * // Après inventaire physique: on a compté 45 unités au lieu de 50
 * adjustStock({
 *   productId: 10,
 *   targetQuantity: 45,
 *   username: 'john.doe'
 * });
 */
export function useStockAdjustment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ productId, targetQuantity, username }) => {
      const { data } = await api.post('/stock/adjustments', {
        product_id: productId,
        target_quantity: targetQuantity,
        username,
      });
      return data;
    },
    onSuccess: () => {
      toast.success('Stock ajusté');
      // Invalider toutes les données de stock impactées
      queryClient.invalidateQueries({ queryKey: ['stock'] });
      queryClient.invalidateQueries({ queryKey: ['stock-timeseries'] });
      queryClient.invalidateQueries({ queryKey: ['stock-recent'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
    },
    onError: (error) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Ajustement impossible');
    },
  });
}
