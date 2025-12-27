/**
 * Module de hooks pour l'historique des prix des produits.
 * @module hooks/usePriceHistory
 */

import { useQuery } from '@tanstack/react-query';
import { fetchPriceHistory } from '../api/client.js';

/**
 * Hook pour récupérer l'historique des prix d'un ou plusieurs produits.
 *
 * Permet de suivre l'évolution des prix dans le temps pour détecter les variations,
 * analyser les tendances et optimiser les stratégies de pricing.
 * Conserve les données précédentes pendant le chargement (keepPreviousData).
 *
 * @param {Object} filters - Filtres de recherche
 * @param {number} [filters.productId] - ID du produit spécifique
 * @param {string} [filters.startDate] - Date de début (ISO format)
 * @param {string} [filters.endDate] - Date de fin (ISO format)
 * @param {number} [filters.limit] - Nombre maximum d'entrées
 *
 * @returns {Object} Query TanStack avec l'historique des prix
 * @property {Array} data - Liste des changements de prix
 * @property {boolean} isLoading - État de chargement
 *
 * @example
 * const { data: history } = usePriceHistory({
 *   productId: 42,
 *   startDate: '2025-01-01',
 *   limit: 50
 * });
 */
export function usePriceHistory(filters) {
  return useQuery({
    queryKey: ['price-history', filters],
    queryFn: () => fetchPriceHistory(filters),
    keepPreviousData: true,
  });
}
