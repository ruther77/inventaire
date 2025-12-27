/**
 * Module de hooks pour la gestion du catalogue produits.
 *
 * Ce module fournit:
 * - La liste paginée des produits avec filtres
 * - Les détails enrichis d'un produit (stats, historique, mouvements)
 * - La normalisation automatique des formats de réponse API
 *
 * @module hooks/useProducts
 */
import { useQuery } from '@tanstack/react-query';
import { fetchProducts, fetchProductDetail } from '../api/client.js';

/**
 * Hook pour récupérer la liste des produits avec pagination et filtres.
 *
 * Normalise automatiquement les formats de réponse API (avec ou sans pagination).
 * Les données précédentes sont conservées pendant le chargement de la nouvelle page
 * pour éviter les sauts visuels.
 *
 * @param {Object} filters - Filtres et pagination
 * @param {number} [filters.page=1] - Numéro de page
 * @param {number} [filters.per_page=50] - Nombre de produits par page
 * @param {number} [filters.category_id] - Filtrer par catégorie
 * @param {string} [filters.q] - Recherche textuelle (nom, SKU, EAN)
 * @param {boolean} [filters.low_stock] - Filtrer uniquement stock bas
 * @param {boolean} [filters.out_of_stock] - Filtrer uniquement rupture
 *
 * @returns {Object} Query normalisée avec données et métadonnées
 * @property {Array} data - Liste des produits de la page courante
 * @property {Object} meta - Métadonnées de pagination (total, page, pages)
 * @property {boolean} isLoading - Indique si le chargement initial
 * @property {boolean} isFetching - Indique si chargement en cours
 *
 * @example
 * const { data: products, meta, isLoading } = useProducts({
 *   page: 1,
 *   per_page: 20,
 *   category_id: 5,
 *   low_stock: true
 * });
 *
 * console.log(`Page ${meta.page} / ${meta.pages} - Total: ${meta.total} produits`);
 *
 * products.forEach(product => {
 *   console.log(product.name, product.stock_actuel, product.prix_vente_ttc);
 * });
 */
export function useProducts(filters = { page: 1, per_page: 50 }) {
  const query = useQuery({
    queryKey: ['products', filters],
    queryFn: () => fetchProducts(filters),
    keepPreviousData: true, // Garde les données précédentes pendant le chargement
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });

  // Normaliser: extraire items si format {items, meta}, sinon tableau brut
  const rawData = query.data;
  const normalizedData = rawData?.items || (Array.isArray(rawData) ? rawData : []);
  const meta = rawData?.meta || { total: normalizedData.length };

  return {
    ...query,
    data: normalizedData,
    meta,
  };
}

/**
 * Hook pour récupérer le détail enrichi d'un produit.
 *
 * Retourne les informations complètes d'un produit incluant:
 * - Ventes des 30 derniers jours
 * - Taux de rotation du stock
 * - Tendances de consommation
 * - Historique des prix d'achat
 * - Mouvements de stock récents
 * - Prévisions de rupture
 *
 * Ces données dynamiques se rafraîchissent automatiquement quand
 * l'onglet reprend le focus.
 *
 * @param {number} productId - ID du produit à charger
 *
 * @returns {Object} Query avec les détails enrichis
 *
 * @example
 * const { data: product, isLoading } = useProductDetail(42);
 *
 * if (isLoading) return <Skeleton />;
 *
 * return (
 *   <div>
 *     <h1>{product.name}</h1>
 *     <p>Stock: {product.stock_actuel} unités</p>
 *     <p>Rotation: {product.rotation_days} jours</p>
 *     <p>Ventes 30j: {product.sales_30d} unités</p>
 *     <Chart data={product.price_history} />
 *   </div>
 * );
 */
export function useProductDetail(productId) {
  return useQuery({
    queryKey: ['product-detail', productId],
    queryFn: () => fetchProductDetail(productId),
    enabled: Boolean(productId), // Ne charge que si ID fourni
    staleTime: 30 * 1000, // 30 secondes - données dynamiques
    refetchOnWindowFocus: true, // Rafraîchir quand l'onglet reprend le focus
  });
}
