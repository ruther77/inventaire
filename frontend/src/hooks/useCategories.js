/**
 * Module de hooks pour la gestion des catégories de produits.
 *
 * @module hooks/useCategories
 */
import { useQuery } from '@tanstack/react-query';
import { fetchCategories } from '../api/client.js';

/**
 * Hook pour récupérer la liste des catégories de produits.
 *
 * Retourne toutes les catégories du catalogue pour organiser
 * et filtrer les produits. Les catégories sont mises en cache
 * pendant 5 minutes car elles changent rarement.
 *
 * @returns {Object} Query avec la liste des catégories
 * @property {Array} data - Liste des catégories
 * @property {boolean} isLoading - Indique si les données chargent
 * @property {boolean} isError - Indique si erreur
 * @property {Function} refetch - Fonction pour recharger
 *
 * @example
 * const { data: categories, isLoading } = useCategories();
 *
 * // categories = [
 * //   { id: 1, name: 'Fruits & Légumes', count: 150 },
 * //   { id: 2, name: 'Viandes', count: 80 },
 * //   { id: 3, name: 'Épicerie', count: 200 }
 * // ]
 *
 * // Utiliser pour un select
 * <select>
 *   {categories?.map(cat => (
 *     <option key={cat.id} value={cat.id}>{cat.name}</option>
 *   ))}
 * </select>
 */
export function useCategories() {
  return useQuery({
    queryKey: ['catalog-categories'],
    queryFn: fetchCategories,
    staleTime: 5 * 60 * 1000, // 5 minutes - les catégories changent rarement
    refetchOnWindowFocus: false,
  });
}
