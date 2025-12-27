/**
 * Client API pour les communications avec le backend.
 *
 * Ce module centralise tous les appels HTTP vers l'API REST.
 * Utilise Axios avec intercepteurs pour:
 * - Ajout automatique du token JWT (via cookies HTTP-Only)
 * - Gestion des erreurs 401 (refresh token)
 * - Unwrapping automatique des enveloppes API {success, data, error, meta}
 * - Support du multi-tenant (header X-Tenant pour newcms)
 *
 * @module api/client
 */

import axios from 'axios';

/**
 * Client HTTP Axios centralisé pour toutes les interactions SPA ↔ FastAPI.
 * - `baseURL` est configurable via `VITE_API_BASE_URL`.
 * - Authentification via cookies HTTP-Only (envoyés automatiquement).
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Envoie automatiquement les cookies HTTP-Only
});

let unauthorizedHandler = null;

/**
 * Défini le token d'accès (no-op car gestion via cookies HTTP-Only).
 *
 * @deprecated Les tokens sont gérés automatiquement par les cookies HTTP-Only
 */
export const setAccessToken = () => {
  // No-op: les cookies sont gérés automatiquement par le navigateur
};

/**
 * Supprime le token d'accès (no-op car gestion via cookies HTTP-Only).
 *
 * @deprecated Les cookies sont supprimés par le backend via /auth/logout
 */
export const clearAccessToken = () => {
  // No-op: les cookies sont supprimés par le backend via /auth/logout
};

/**
 * Enregistre un handler pour les erreurs 401 (non autorisé).
 *
 * @param {Function} handler - Fonction callback à appeler sur erreur 401
 *
 * @example
 * registerUnauthorizedHandler(() => {
 *   navigate('/login');
 * });
 */
export const registerUnauthorizedHandler = (handler) => {
  unauthorizedHandler = handler;
};

api.interceptors.response.use(
  (response) => {
    // Unwrap API envelope {success, data, error, meta} if present
    // This makes response.data contain the actual payload
    if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
      response.data = response.data.data;
    }
    return response;
  },
  (error) => {
    if (error?.response?.status === 401 && typeof unauthorizedHandler === 'function') {
      unauthorizedHandler();
    }
    return Promise.reject(error);
  },
);

api.interceptors.request.use((config) => {
  if (config.url && config.url.startsWith('/newcms/')) {
    config.headers = config.headers || {};
    config.headers['X-Tenant'] = 2;
  }
  // Note: pas besoin d'ajouter le token, les cookies HTTP-Only sont envoyés automatiquement
  return config;
});

// ============================================================================
// CATALOGUE & INVENTAIRE
// ============================================================================

/**
 * Récupère la liste des produits du catalogue.
 *
 * @async
 * @param {Object} [params={}] - Paramètres de filtrage
 * @param {number} [params.page] - Numéro de page
 * @param {number} [params.per_page] - Résultats par page
 * @param {string} [params.q] - Recherche textuelle
 * @param {number} [params.category_id] - Filtrer par catégorie
 * @param {string} [params.supplier] - Filtrer par fournisseur
 *
 * @returns {Promise<Object>} Liste des produits avec métadonnées
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * const products = await fetchProducts({ page: 1, category_id: 5 });
 */
export const fetchProducts = async (params = {}) => {
  const { data } = await api.get('/catalog/products', { params });
  return data;
};

/**
 * Récupère les détails complets d'un produit.
 *
 * @async
 * @param {number} productId - ID du produit
 *
 * @returns {Promise<Object>} Détails du produit
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * const product = await fetchProductDetail(123);
 */
export const fetchProductDetail = async (productId) => {
  const { data } = await api.get(`/catalog/products/${productId}/detail`);
  return data;
};

/**
 * Récupère le résumé de l'inventaire.
 *
 * @async
 * @returns {Promise<Object>} Résumé de l'inventaire
 * @property {number} total_products - Nombre total de produits
 * @property {number} total_value - Valeur totale du stock
 * @property {number} low_stock_count - Produits en rupture
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * const summary = await fetchInventorySummary();
 */
export const fetchInventorySummary = async () => {
  const { data } = await api.get('/inventory/summary');
  return data;
};

// ============================================================================
// RESTAURANT - CONSOMMATIONS & INGREDIENTS
// ============================================================================

/**
 * Récupère les consommations restaurant par période.
 *
 * @async
 * @param {string} [period='all'] - Période ('all', 'month', 'week', etc.)
 *
 * @returns {Promise<Object>} Données de consommations
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * const consumptions = await fetchRestaurantConsumptions('month');
 */
export const fetchRestaurantConsumptions = async (period = 'all') => {
  const { data } = await api.get('/restaurant/consumptions', { params: { period } });
  return data;
};

/**
 * Récupère la comparaison de l'historique des prix.
 *
 * @async
 * @returns {Promise<Object>} Comparaison des prix dans le temps
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantPriceHistoryComparison = async () => {
  const { data } = await api.get('/restaurant/price-history/comparison');
  return data;
};

/**
 * Récupère la liste des produits épicerie.
 *
 * @async
 * @returns {Promise<Array>} Liste des produits épicerie
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchEpicerieProducts = async () => {
  const { data } = await api.get('/restaurant/epicerie/products');
  return data;
};

/**
 * Synchronise les prix des ingrédients restaurant avec l'épicerie.
 *
 * @async
 * @param {boolean} [forceUpdate=false] - Force la mise à jour même si déjà synchronisé
 *
 * @returns {Promise<Object>} Résultat de la synchronisation
 * @property {number} synced_count - Nombre d'ingrédients synchronisés
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * const result = await syncRestaurantIngredientPrices(true);
 */
export const syncRestaurantIngredientPrices = async (forceUpdate = false) => {
  const params = new URLSearchParams();
  if (forceUpdate) params.set('force_update', forceUpdate);
  const query = params.toString();
  const { data } = await api.post(query ? `/restaurant/ingredients/sync-prices?${query}` : '/restaurant/ingredients/sync-prices');
  return data;
};

/**
 * Récupère le statut de synchronisation des prix ingrédients.
 *
 * @async
 * @returns {Promise<Object>} Statut de synchronisation
 * @property {number} synced_count - Ingrédients synchronisés
 * @property {number} linked_count - Ingrédients liés à l'épicerie
 * @property {number} total_count - Total des ingrédients
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantPriceSyncStatus = async () => {
  const { data } = await api.get('/restaurant/ingredients/price-sync-status');
  const payload = data?.data ?? data;
  return {
    ...payload,
    synced_count: payload?.synced_count ?? payload?.synced ?? 0,
    linked_count: payload?.linked_count ?? payload?.linked_to_epicerie ?? 0,
    total_count: payload?.total_count ?? payload?.total_ingredients ?? 0,
  };
};

/**
 * Lie un ingrédient restaurant à un produit épicerie.
 *
 * @async
 * @param {number} ingredientId - ID de l'ingrédient restaurant
 * @param {number} epicerieProductId - ID du produit épicerie
 * @param {number} [ratio=1.0] - Ratio de conversion (défaut: 1.0)
 *
 * @returns {Promise<Object>} Ingrédient lié mis à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * await linkIngredientToEpicerie(123, 456, 0.5);
 */
export const linkIngredientToEpicerie = async (ingredientId, epicerieProductId, ratio = 1.0) => {
  const { data } = await api.put(`/restaurant/ingredients/${ingredientId}/link-epicerie`, {
    produit_epicerie_id: epicerieProductId,
    ratio,
  });
  return data;
};

/**
 * Délie un ingrédient restaurant d'un produit épicerie.
 *
 * @async
 * @param {number} ingredientId - ID de l'ingrédient restaurant
 *
 * @returns {Promise<Object>} Résultat de la suppression
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const unlinkIngredientFromEpicerie = async (ingredientId) => {
  const { data } = await api.delete(`/restaurant/ingredients/${ingredientId}/link-epicerie`);
  return data;
};

/**
 * Met à jour le ratio de conversion d'un ingrédient.
 *
 * @async
 * @param {number} ingredientId - ID de l'ingrédient
 * @param {number} ratio - Nouveau ratio
 *
 * @returns {Promise<Object>} Ingrédient mis à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateIngredientRatio = async (ingredientId, ratio) => {
  const { data } = await api.patch(`/restaurant/ingredients/${ingredientId}/ratio`, { ratio });
  return data;
};

/**
 * Met à jour le prix d'un ingrédient restaurant.
 *
 * @async
 * @param {number} ingredientId - ID de l'ingrédient
 * @param {Object} payload - Données de prix
 * @param {number} payload.price - Nouveau prix
 *
 * @returns {Promise<Object>} Ingrédient mis à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateRestaurantIngredientPrice = async (ingredientId, payload) => {
  const { data } = await api.patch(`/restaurant/ingredients/${ingredientId}/price`, payload);
  return data;
};

/**
 * Récupère l'historique des prix d'un ingrédient.
 *
 * @async
 * @param {number} ingredientId - ID de l'ingrédient
 *
 * @returns {Promise<Array>} Historique des prix
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantIngredientPriceHistory = async (ingredientId) => {
  const { data } = await api.get(`/restaurant/ingredients/${ingredientId}/price-history`);
  return data;
};

// ============================================================================
// RESTAURANT - PLATS & RECETTES
// ============================================================================

/**
 * Met à jour le prix de vente d'un plat.
 *
 * @async
 * @param {number} platId - ID du plat
 * @param {Object} payload - Données de prix
 * @param {number} payload.price - Nouveau prix de vente TTC
 *
 * @returns {Promise<Object>} Plat mis à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateRestaurantPlatPrice = async (platId, payload) => {
  const { data } = await api.patch(`/restaurant/plats/${platId}/price`, payload);
  return data;
};

/**
 * Ajoute un ingrédient à un plat.
 *
 * @async
 * @param {number} platId - ID du plat
 * @param {Object} payload - Données de l'ingrédient
 * @param {number} payload.ingredient_id - ID de l'ingrédient
 * @param {number} payload.quantity - Quantité utilisée
 *
 * @returns {Promise<Object>} Ingrédient ajouté
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const addIngredientToPlat = async (platId, payload) => {
  const { data } = await api.post(`/restaurant/plats/${platId}/ingredients`, payload);
  return data;
};

/**
 * Met à jour un ingrédient d'un plat.
 *
 * @async
 * @param {number} platId - ID du plat
 * @param {number} ingredientId - ID de l'ingrédient
 * @param {Object} payload - Nouvelles données
 * @param {number} [payload.quantity] - Nouvelle quantité
 *
 * @returns {Promise<Object>} Ingrédient mis à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateIngredientOnPlat = async (platId, ingredientId, payload) => {
  const { data } = await api.patch(`/restaurant/plats/${platId}/ingredients/${ingredientId}`, payload);
  return data;
};

/**
 * Retire un ingrédient d'un plat.
 *
 * @async
 * @param {number} platId - ID du plat
 * @param {number} ingredientId - ID de l'ingrédient à retirer
 *
 * @returns {Promise<Object>} Résultat de la suppression
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const removeIngredientFromPlat = async (platId, ingredientId) => {
  const { data } = await api.delete(`/restaurant/plats/${platId}/ingredients/${ingredientId}`);
  return data;
};

/**
 * Récupère l'historique des prix d'un plat.
 *
 * @async
 * @param {number} platId - ID du plat
 *
 * @returns {Promise<Array>} Historique des prix
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantPlatPriceHistory = async (platId) => {
  const { data } = await api.get(`/restaurant/plats/${platId}/price-history`);
  return data;
};

/**
 * Récupère la vue d'ensemble de l'historique des prix restaurant.
 *
 * @async
 * @returns {Promise<Object>} Vue d'ensemble des évolutions de prix
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantPriceHistoryOverview = async () => {
  const { data } = await api.get('/restaurant/prices/history');
  return data;
};

/**
 * Récupère la vue d'ensemble des prévisions restaurant.
 *
 * @async
 * @returns {Promise<Object>} Prévisions (ventes, consommations, etc.)
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantForecastOverview = async () => {
  const { data } = await api.get('/restaurant/forecasts/overview');
  return data;
};

/**
 * Récupère le résumé TVA des charges restaurant.
 *
 * @async
 * @param {Object} [filters={}] - Filtres de période
 * @param {string} [filters.dateFrom] - Date de début (YYYY-MM-DD)
 * @param {string} [filters.dateTo] - Date de fin (YYYY-MM-DD)
 *
 * @returns {Promise<Object>} Résumé TVA par taux
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantTvaSummary = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/charges/tva-summary?${query}` : '/restaurant/charges/tva-summary');
  return data;
};

/**
 * Récupère le dashboard restaurant global.
 *
 * @async
 * @returns {Promise<Object>} Métriques et KPIs du restaurant
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantDashboard = async () => {
  const { data } = await api.get('/restaurant/dashboard/overview');
  return data;
};

// ============================================================================
// RESTAURANT FOOD COST & OVERVIEW
// ============================================================================

/**
 * Récupère la vue d'ensemble restaurant avec food cost.
 *
 * @async
 * @param {Object} [filters={}] - Filtres de période
 * @param {string} [filters.dateFrom] - Date de début
 * @param {string} [filters.dateTo] - Date de fin
 *
 * @returns {Promise<Object>} Vue d'ensemble avec métriques food cost
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantOverview = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/overview?${query}` : '/restaurant/overview');
  return data;
};

/**
 * Récupère les détails complets d'un plat restaurant.
 *
 * @async
 * @param {number} platId - ID du plat
 *
 * @returns {Promise<Object>} Détails du plat avec coûts et ingrédients
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantPlatDetails = async (platId) => {
  const { data } = await api.get(`/restaurant/plats/${platId}/detail`);
  return data;
};

/**
 * Récupère la décomposition des coûts d'un plat par ingrédient.
 *
 * @async
 * @param {number} platId - ID du plat
 *
 * @returns {Promise<Array>} Liste des ingrédients avec coûts détaillés
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantPlatIngredients = async (platId) => {
  const { data } = await api.get(`/restaurant/plats/${platId}/cost-breakdown`);
  return data;
};

/**
 * Simule l'impact d'un changement de prix sur un plat.
 *
 * @async
 * @param {number} platId - ID du plat
 * @param {Object} payload - Paramètres de simulation
 * @param {number} [payload.new_price] - Nouveau prix simulé
 * @param {number} [payload.target_margin] - Marge cible
 *
 * @returns {Promise<Object>} Résultats de la simulation
 * @property {number} food_cost_pct - Food cost en %
 * @property {number} margin_pct - Marge en %
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const simulatePlatPrice = async (platId, payload) => {
  const { data } = await api.post(`/restaurant/plats/${platId}/simulate-price`, payload);
  return data;
};

/**
 * Récupère les alertes restaurant (food cost, stocks, etc.).
 *
 * @async
 * @param {Object} [filters={}] - Filtres d'alertes
 * @param {string} [filters.type] - Type d'alerte
 * @param {string} [filters.severity] - Sévérité (low, medium, high, critical)
 *
 * @returns {Promise<Array>} Liste des alertes
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantAlerts = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.type) params.set('type', filters.type);
  if (filters.severity) params.set('severity', filters.severity);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/alerts?${query}` : '/restaurant/alerts');
  return data;
};

/**
 * Récupère l'analyse food cost détaillée.
 *
 * @async
 * @param {Object} [filters={}] - Filtres d'analyse
 * @param {string} [filters.period] - Période d'analyse
 * @param {number} [filters.target_food_cost] - Food cost cible (%)
 * @param {string} [filters.dateFrom] - Date de début
 * @param {string} [filters.dateTo] - Date de fin
 *
 * @returns {Promise<Object>} Analyse food cost complète
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantFoodCostAnalysis = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.period) params.set('period', filters.period);
  if (filters.target_food_cost !== undefined) params.set('target_food_cost', filters.target_food_cost);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/food-cost/analysis?${query}` : '/restaurant/food-cost/analysis');
  return data;
};

// ---------------------------------------------------------------------------
// Restaurant Menus & Costs (Scénario 3.6)
// ---------------------------------------------------------------------------

/**
 * Récupère la vue d'ensemble des menus restaurant.
 *
 * @async
 * @returns {Promise<Object>} Vue d'ensemble des menus avec coûts
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchRestaurantMenusOverview = async () => {
  const { data } = await api.get('/restaurant/menus/overview');
  return data;
};

// ============================================================================
// POS - POINT OF SALE
// ============================================================================

/**
 * Effectue le checkout d'un panier POS.
 *
 * @async
 * @param {Object} payload - Données du panier
 * @param {Array} payload.items - Articles du panier
 * @param {string} payload.payment_method - Méthode de paiement
 *
 * @returns {Promise<Object>} Résultat de la transaction
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const checkoutCart = async (payload) => {
  const { data } = await api.post('/pos/checkout', payload);
  return data;
};

// ============================================================================
// CATALOGUE - CRUD PRODUITS
// ============================================================================

/**
 * Crée un nouveau produit dans le catalogue.
 *
 * @async
 * @param {Object} payload - Données du produit
 * @param {string} payload.name - Nom du produit
 * @param {string} [payload.code] - Code produit
 * @param {number} [payload.price] - Prix de vente
 * @param {number} [payload.cost] - Prix d'achat
 *
 * @returns {Promise<Object>} Produit créé
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const createProduct = async (payload) => {
  const { data } = await api.post('/catalog/products', payload);
  return data;
};

/**
 * Met à jour un produit existant.
 *
 * @async
 * @param {number} productId - ID du produit
 * @param {Object} payload - Données à mettre à jour
 *
 * @returns {Promise<Object>} Produit mis à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateProductRequest = async (productId, payload) => {
  const { data } = await api.patch(`/catalog/products/${productId}`, payload);
  return data;
};

/**
 * Supprime un produit du catalogue.
 *
 * @async
 * @param {number} productId - ID du produit à supprimer
 *
 * @returns {Promise<boolean>} true si succès
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const deleteProductRequest = async (productId) => {
  await api.delete(`/catalog/products/${productId}`);
  return true;
};

/**
 * Recherche un produit par code-barres.
 *
 * @async
 * @param {string} barcode - Code-barres EAN/UPC
 *
 * @returns {Promise<Object>} Produit trouvé
 * @throws {AxiosError} Si produit non trouvé ou erreur serveur
 *
 * @example
 * const product = await lookupProductByBarcode('3760123456789');
 */
export const lookupProductByBarcode = async (barcode) => {
  const { data } = await api.get(`/catalog/products/barcode/${encodeURIComponent(barcode)}`);
  return data;
};

// ============================================================================
// SUPPLY PLANNING - APPROVISIONNEMENT
// ============================================================================

/**
 * Récupère le plan d'approvisionnement recommandé.
 *
 * @async
 * @param {Object} [filters={}] - Filtres du plan
 * @param {number} [filters.targetCoverage=21] - Couverture cible en jours
 * @param {number} [filters.alertThreshold=7] - Seuil d'alerte en jours
 * @param {number} [filters.minDailySales=0] - Ventes min journalières
 * @param {Array<string>} [filters.categories] - Filtrer par catégories
 * @param {string} [filters.search] - Recherche textuelle
 *
 * @returns {Promise<Object>} Plan d'approvisionnement
 * @property {Array} items - Produits à commander
 * @property {Object} summary - Résumé du plan
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * const plan = await fetchSupplyPlan({ targetCoverage: 14, categories: ['FRUITS'] });
 */
export const fetchSupplyPlan = async (filters = {}) => {
  const params = new URLSearchParams();
  const target = filters.targetCoverage ?? 21;
  const alert = filters.alertThreshold ?? 7;
  const minSales = filters.minDailySales ?? 0;

  params.set('target_coverage', target);
  params.set('alert_threshold', alert);
  params.set('min_daily_sales', minSales);

  if (filters.categories && filters.categories.length > 0) {
    filters.categories.forEach((category) => {
      if (category) {
        params.append('categories', category);
      }
    });
  }

  if (filters.search) {
    params.set('search', filters.search);
  }

  const query = params.toString();
  const url = query ? `/supply/plan?${query}` : '/supply/plan';
  const { data } = await api.get(url);
  return data;
};

// ============================================================================
// AUDIT & DIAGNOSTICS
// ============================================================================

/**
 * Récupère les diagnostics d'audit (écarts, anomalies).
 *
 * @async
 * @param {Object} [filters={}] - Filtres de diagnostic
 * @param {Array<string>} [filters.categories] - Catégories à auditer
 * @param {Array<string>} [filters.levels] - Niveaux de sévérité
 * @param {number} [filters.minAbs] - Écart absolu min
 * @param {number} [filters.maxAbs] - Écart absolu max
 *
 * @returns {Promise<Array>} Liste des diagnostics
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchAuditDiagnostics = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.categories) {
    filters.categories.forEach((category) => {
      if (category) params.append('categories', category);
    });
  }
  if (filters.levels) {
    filters.levels.forEach((level) => {
      if (level) params.append('levels', level);
    });
  }
  if (filters.minAbs !== undefined) params.set('min_abs', filters.minAbs);
  if (filters.maxAbs !== undefined) params.set('max_abs', filters.maxAbs);
  const query = params.toString();
  const { data } = await api.get(query ? `/audit/diagnostics?${query}` : '/audit/diagnostics');
  return data;
};

/**
 * Récupère les actions d'audit en cours ou terminées.
 *
 * @async
 * @param {boolean} [includeClosed=false] - Inclure les actions fermées
 *
 * @returns {Promise<Array>} Liste des actions d'audit
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchAuditActions = async (includeClosed = false) => {
  const { data } = await api.get('/audit/actions', { params: { include_closed: includeClosed } });
  return data;
};

/**
 * Récupère les résolutions d'audit disponibles.
 *
 * @async
 * @returns {Promise<Array>} Types de résolutions possibles
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchAuditResolutions = async () => {
  const { data } = await api.get('/audit/resolutions');
  return data;
};

/**
 * Crée une affectation d'action d'audit.
 *
 * @async
 * @param {Object} payload - Données d'affectation
 * @param {number} payload.action_id - ID de l'action
 * @param {number} payload.user_id - ID de l'utilisateur assigné
 *
 * @returns {Promise<Object>} Affectation créée
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const createAuditAssignment = async (payload) => {
  const { data } = await api.post('/audit/assignments', payload);
  return data;
};

/**
 * Met à jour le statut d'une action d'audit.
 *
 * @async
 * @param {Object} params - Paramètres de mise à jour
 * @param {number} params.actionId - ID de l'action
 * @param {string} params.status - Nouveau statut
 * @param {string} [params.note] - Note de résolution
 *
 * @returns {Promise<Object>} Action mise à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateAuditActionStatus = async ({ actionId, status, note }) => {
  const { data } = await api.post(`/audit/actions/${actionId}/status`, { status, note });
  return data;
};

// ============================================================================
// INVOICES - EXTRACTION & IMPORT
// ============================================================================

/**
 * Extrait les données d'une facture à partir de texte.
 *
 * @async
 * @param {Object} params - Paramètres d'extraction
 * @param {string} params.text - Texte de la facture (OCR, copier-coller)
 * @param {number} params.marginPercent - Marge appliquée (%)
 * @param {string} [params.supplierHint] - Nom du fournisseur (aide l'IA)
 *
 * @returns {Promise<Object>} Facture extraite avec lignes détectées
 * @property {Array} lines - Lignes de facture extraites
 * @property {string} supplier - Fournisseur détecté
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const extractInvoiceFromText = async ({ text, marginPercent, supplierHint }) => {
  const payload = {
    text,
    margin_percent: marginPercent,
  };
  if (supplierHint) {
    payload.supplier_hint = supplierHint;
  }
  const { data } = await api.post('/invoices/extract', payload);
  return data;
};

/**
 * Extrait les données d'une facture à partir d'un fichier (PDF, image).
 *
 * @async
 * @param {Object} params - Paramètres d'extraction
 * @param {File} params.file - Fichier facture (PDF, JPG, PNG)
 * @param {number} params.marginPercent - Marge appliquée (%)
 * @param {string} [params.supplierHint] - Nom du fournisseur (aide l'IA)
 *
 * @returns {Promise<Object>} Facture extraite avec lignes détectées
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const extractInvoiceFromFile = async ({ file, marginPercent, supplierHint }) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('margin_percent', marginPercent);
  if (supplierHint) {
    formData.append('supplier_hint', supplierHint);
  }
  const { data } = await api.post('/invoices/extract/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

/**
 * Import "zero-click" d'une facture : extraction + matching + import auto.
 *
 * @async
 * @param {Object} params - Paramètres d'import
 * @param {File} params.file - Fichier facture
 * @param {number} [params.marginPercent=40] - Marge appliquée (%)
 * @param {string} [params.supplierHint=null] - Nom du fournisseur
 * @param {boolean} [params.autoConfirm=true] - Confirmation automatique
 *
 * @returns {Promise<Object>} Résultat de l'import automatique
 * @property {number} matched - Produits matchés automatiquement
 * @property {number} created - Nouveaux produits créés
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 *
 * @example
 * const result = await zeroClickInvoiceImport({
 *   file: pdfFile,
 *   marginPercent: 35,
 *   supplierHint: 'Metro'
 * });
 */
export const zeroClickInvoiceImport = async ({ file, marginPercent = 40, supplierHint = null, autoConfirm = true }) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('margin_percent', marginPercent);
  if (supplierHint) {
    formData.append('supplier_hint', supplierHint);
  }
  formData.append('auto_confirm', autoConfirm ? 'true' : 'false');

  const { data } = await api.post('/invoices/zero-click', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

/**
 * Lance un job zero-click asynchrone (pour gros fichiers).
 *
 * @async
 * @param {Object} params - Paramètres du job
 * @param {File} params.file - Fichier facture
 * @param {number} [params.marginPercent=40] - Marge (%)
 * @param {string} [params.supplierHint=null] - Fournisseur
 * @param {boolean} [params.autoConfirm=true] - Confirmation auto
 * @param {string} [params.sessionId=null] - ID session (groupement)
 *
 * @returns {Promise<Object>} Job créé
 * @property {string} job_id - ID du job pour polling
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const zeroClickInvoiceJob = async ({ file, marginPercent = 40, supplierHint = null, autoConfirm = true, sessionId = null }) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('margin_percent', marginPercent);
  if (supplierHint) {
    formData.append('supplier_hint', supplierHint);
  }
  formData.append('auto_confirm', autoConfirm ? 'true' : 'false');
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const { data } = await api.post('/invoices/zero-click/jobs', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

/**
 * Récupère le statut d'un job zero-click (polling).
 *
 * @async
 * @param {string} jobId - ID du job
 *
 * @returns {Promise<Object>} Statut du job
 * @property {string} status - pending|processing|completed|failed
 * @property {number} progress - Progression (0-100)
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchZeroClickJobStatus = async (jobId) => {
  const { data } = await api.get(`/invoices/zero-click/jobs/${jobId}`);
  return data;
};

/**
 * Récupère la liste des jobs zero-click récents.
 *
 * @async
 * @param {Object} [params={}] - Paramètres de recherche
 * @param {string} [params.status] - Filtrer par statut
 * @param {string} [params.sessionId] - Filtrer par session
 * @param {number} [params.limit=50] - Limite résultats
 * @param {number} [params.offset=0] - Offset pagination
 *
 * @returns {Promise<Array>} Liste des jobs
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchZeroClickJobs = async ({ status = null, sessionId = null, limit = 50, offset = 0 } = {}) => {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (sessionId) params.set('session_id', sessionId);
  if (limit) params.set('limit', limit);
  if (offset) params.set('offset', offset);
  const query = params.toString();
  const { data } = await api.get(query ? `/invoices/zero-click/jobs?${query}` : '/invoices/zero-click/jobs');
  return data;
};

/**
 * Récupère les sessions d'import de factures.
 *
 * @async
 * @param {Object} [params={}] - Paramètres de pagination
 * @param {number} [params.limit=50] - Limite résultats
 * @param {number} [params.offset=0] - Offset pagination
 *
 * @returns {Promise<Array>} Liste des sessions d'import
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchImportSessions = async ({ limit = 50, offset = 0 } = {}) => {
  const params = new URLSearchParams();
  if (limit) params.set('limit', limit);
  if (offset) params.set('offset', offset);
  const query = params.toString();
  const { data } = await api.get(query ? `/invoices/sessions?${query}` : '/invoices/sessions');
  return data;
};

/**
 * Récupère les détails d'une session d'import.
 *
 * @async
 * @param {string} sessionId - ID de la session
 *
 * @returns {Promise<Object>} Détails de la session avec jobs associés
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchImportSessionDetails = async (sessionId) => {
  const { data } = await api.get(`/invoices/sessions/${encodeURIComponent(sessionId)}`);
  return data;
};

/**
 * Importe les lignes d'une facture dans le système.
 *
 * @async
 * @param {Object} params - Paramètres d'import
 * @param {Array} params.lines - Lignes de facture
 * @param {string} params.supplier - Fournisseur
 * @param {string} params.movementType - Type mouvement (ENTREE/SORTIE)
 * @param {string} params.username - Utilisateur
 * @param {string} [params.invoiceDate] - Date facture (YYYY-MM-DD)
 *
 * @returns {Promise<Object>} Résultat de l'import
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const importInvoiceLines = async ({ lines, supplier, movementType, username, invoiceDate }) => {
  const { data } = await api.post('/invoices/import', {
    lines,
    supplier,
    movement_type: movementType,
    username,
    invoice_date: invoiceDate ?? null,
  });
  return data;
};

/**
 * Lie une ligne de facture à un produit existant.
 *
 * @async
 * @param {Object} params - Paramètres de liaison
 * @param {Object} params.line - Ligne de facture
 * @param {number} params.productId - ID du produit catalogue
 *
 * @returns {Promise<Object>} Ligne mise à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const linkInvoiceLine = async ({ line, productId }) => {
  const { data } = await api.post('/invoices/lines/link', {
    line,
    product_id: productId,
  });
  return data.line;
};

/**
 * Crée un nouveau produit à partir d'une ligne de facture.
 *
 * @async
 * @param {Object} params - Paramètres de création
 * @param {Object} params.line - Ligne de facture
 * @param {string} params.supplier - Fournisseur
 * @param {boolean} [params.initializeStock=false] - Initialiser le stock
 * @param {string} [params.invoiceDate] - Date facture
 *
 * @returns {Promise<Object>} Résumé de la création
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const createProductFromLine = async ({ line, supplier, initializeStock = false, invoiceDate }) => {
  const { data } = await api.post('/invoices/lines/create-product', {
    line,
    supplier,
    initialize_stock: Boolean(initializeStock),
    invoice_date: invoiceDate ?? null,
  });
  return data.summary;
};

/**
 * Confirme les mouvements de stock d'une facture.
 *
 * @async
 * @param {Object} params - Paramètres de confirmation
 * @param {Array} params.lines - Lignes à confirmer
 * @param {string} [params.movementType='ENTREE'] - Type mouvement
 * @param {string} params.supplier - Fournisseur
 * @param {string} [params.invoiceDate] - Date facture
 * @param {string} params.username - Utilisateur
 *
 * @returns {Promise<Object>} Résultat de la confirmation
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const confirmInvoiceStock = async ({ lines, movementType = 'ENTREE', supplier, invoiceDate, username }) => {
  const { data } = await api.post('/invoices/lines/confirm-stock', {
    lines,
    movement_type: movementType,
    supplier,
    invoice_date: invoiceDate ?? null,
    username,
  });
  return data;
};

/**
 * Importe une facture dans le catalogue avec création de produits.
 *
 * @async
 * @param {Object} params - Paramètres d'import
 * @param {Array} params.lines - Lignes de facture
 * @param {string} params.supplier - Fournisseur
 * @param {string} params.username - Utilisateur
 * @param {boolean} params.initializeStock - Initialiser les stocks
 * @param {string} [params.invoiceDate] - Date facture
 *
 * @returns {Promise<Object>} Résultat de l'import
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const importInvoiceToCatalog = async ({ lines, supplier, username, initializeStock, invoiceDate }) => {
  const { data } = await api.post('/invoices/catalog/import', {
    lines,
    supplier,
    username,
    initialize_stock: Boolean(initializeStock),
    invoice_date: invoiceDate ?? null,
  });
  return data;
};

/**
 * Récupère les suggestions de matching pour un produit.
 *
 * @async
 * @param {Object} params - Paramètres de recherche
 * @param {string} params.query - Texte de recherche
 * @param {number} [params.maxResults=5] - Nombre max de résultats
 * @param {number} [params.minScore=60.0] - Score min de similarité
 *
 * @returns {Promise<Array>} Suggestions de produits similaires
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchProductMatchSuggestions = async ({ query, maxResults = 5, minScore = 60.0 }) => {
  const params = new URLSearchParams();
  params.set('query', query);
  params.set('max_results', maxResults);
  params.set('min_score', minScore);
  const { data } = await api.get(`/invoices/match-suggestions?${params.toString()}`);
  return data.suggestions ?? [];
};

/**
 * Récupère l'historique des factures importées.
 *
 * @async
 * @param {Object} [filters={}] - Filtres de recherche
 * @param {string} [filters.supplier] - Filtrer par fournisseur
 * @param {string} [filters.invoiceId] - Filtrer par N° facture
 * @param {string} [filters.dateStart] - Date début
 * @param {string} [filters.dateEnd] - Date fin
 * @param {number} [filters.limit] - Limite résultats
 *
 * @returns {Promise<Array>} Historique des factures
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchInvoiceHistory = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.supplier) params.set('supplier', filters.supplier);
  if (filters.invoiceId) params.set('invoice_id', filters.invoiceId);
  if (filters.dateStart) params.set('date_start', filters.dateStart);
  if (filters.dateEnd) params.set('date_end', filters.dateEnd);
  if (filters.limit) params.set('limit', filters.limit);
  const query = params.toString();
  const { data } = await api.get(query ? `/invoices/history?${query}` : '/invoices/history');
  return data.items ?? [];
};

/**
 * Télécharge le fichier PDF d'une facture importée.
 *
 * @async
 * @param {string} invoiceId - ID de la facture
 *
 * @returns {Promise<AxiosResponse>} Réponse avec blob PDF
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const downloadInvoiceFile = async (invoiceId) => {
  const response = await api.get(`/invoices/history/${encodeURIComponent(invoiceId)}/file`, {
    responseType: 'blob',
  });
  return response;
};

// ============================================================================
// CATALOGUE - RÉFÉRENTIELS
// ============================================================================

/**
 * Récupère la liste des catégories de produits.
 *
 * @async
 * @returns {Promise<Array>} Liste des catégories
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchCategories = async () => {
  const { data } = await api.get('/catalog/categories');
  return data;
};

/**
 * Récupère la liste des fournisseurs.
 *
 * @async
 * @returns {Promise<Array>} Liste des fournisseurs
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchVendors = async () => {
  const { data} = await api.get('/catalog/vendors');
  return data;
};

// ============================================================================
// SALES - VENTES & MÉTRIQUES
// ============================================================================

/**
 * Récupère les métriques de ventes.
 *
 * @async
 * @param {Object} [filters={}] - Filtres de période
 * @param {string} [filters.dateStart] - Date début
 * @param {string} [filters.dateEnd] - Date fin
 * @param {Array<string>} [filters.categories] - Filtrer par catégories
 *
 * @returns {Promise<Object>} Métriques de ventes
 * @property {number} total_sales - Total des ventes
 * @property {number} avg_basket - Panier moyen
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchSalesMetrics = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateStart) params.set('date_start', filters.dateStart);
  if (filters.dateEnd) params.set('date_end', filters.dateEnd);
  if (filters.categories) {
    filters.categories.forEach((category) => {
      if (category) params.append('categories', category);
    });
  }
  const query = params.toString();
  const { data } = await api.get(query ? `/sales/metrics?${query}` : '/sales/metrics');
  return data;
};

/**
 * Récupère la projection de croissance des ventes.
 *
 * @async
 * @param {Object} [filters={}] - Filtres de période
 * @param {string} [filters.dateStart] - Date début
 * @param {string} [filters.dateEnd] - Date fin
 * @param {Array<string>} [filters.categories] - Filtrer par catégories
 *
 * @returns {Promise<Object>} Projection de croissance
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchSalesGrowthProjection = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateStart) params.set('date_start', filters.dateStart);
  if (filters.dateEnd) params.set('date_end', filters.dateEnd);
  if (filters.categories) {
    filters.categories.forEach((category) => {
      if (category) params.append('categories', category);
    });
  }
  const query = params.toString();
  const { data } = await api.get(query ? `/sales/growth?${query}` : '/sales/growth');
  return data;
};

export const fetchRestaurantSales = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/sales?${query}` : '/restaurant/sales');
  return data;
};

export const fetchRestaurantTopSellers = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  if (filters.limit) params.set('limit', filters.limit);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/top-sellers?${query}` : '/restaurant/top-sellers');
  return data;
};

export const fetchRestaurantCategoryBreakdown = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  const query = params.toString();
  const { data } = await api.get(
    query ? `/restaurant/category-breakdown?${query}` : '/restaurant/category-breakdown'
  );
  return data;
};

export const fetchRestaurantDailyRevenue = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/daily-revenue?${query}` : '/restaurant/daily-revenue');
  return data;
};

export const fetchPOSSalesOverview = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  const query = params.toString();
  const { data } = await api.get(query ? `/pos/sales/overview?${query}` : '/pos/sales/overview');
  return data;
};

export const fetchPOSTopProducts = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  if (filters.limit) params.set('limit', filters.limit);
  const query = params.toString();
  const { data } = await api.get(query ? `/pos/sales/top-products?${query}` : '/pos/sales/top-products');
  return data;
};

export const fetchPOSHourlySales = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  const query = params.toString();
  const { data } = await api.get(query ? `/pos/sales/hourly?${query}` : '/pos/sales/hourly');
  return data;
};

export const fetchPOSDailySales = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  const query = params.toString();
  const { data } = await api.get(query ? `/pos/sales/daily?${query}` : '/pos/sales/daily');
  return data;
};

export const fetchPOSCategorySales = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.start_date) params.set('start_date', filters.start_date);
  if (filters.end_date) params.set('end_date', filters.end_date);
  if (filters.entity_id) params.set('entity_id', filters.entity_id);
  const query = params.toString();
  const { data } = await api.get(query ? `/pos/sales/by-category?${query}` : '/pos/sales/by-category');
  return data;
};

// ============================================================================
// FINANCE - TRANSACTIONS & CATÉGORISATION
// ============================================================================

/**
 * Recherche des transactions financières avec filtres avancés.
 *
 * @async
 * @param {Object} [filters={}] - Filtres de recherche
 * @param {number} [filters.entityId] - ID entité
 * @param {number} [filters.accountId] - ID compte bancaire
 * @param {number} [filters.categoryId] - ID catégorie
 * @param {string} [filters.dateFrom] - Date début
 * @param {string} [filters.dateTo] - Date fin
 * @param {number} [filters.amountMin] - Montant min
 * @param {number} [filters.amountMax] - Montant max
 * @param {string} [filters.q] - Recherche textuelle
 * @param {number} [filters.page=1] - Page
 * @param {number} [filters.size=50] - Résultats/page
 * @param {string} [filters.sort='-date_operation'] - Tri
 *
 * @returns {Promise<Object>} Résultats paginés avec transactions
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const searchFinanceTransactions = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.accountId) params.set('account_id', filters.accountId);
  if (filters.categoryId) params.set('category_id', filters.categoryId);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.amountMin !== undefined && filters.amountMin !== null) params.set('amount_min', filters.amountMin);
  if (filters.amountMax !== undefined && filters.amountMax !== null) params.set('amount_max', filters.amountMax);
  if (filters.q) params.set('q', filters.q);
  params.set('page', filters.page ?? 1);
  params.set('size', filters.size ?? 50);
  params.set('sort', filters.sort ?? '-date_operation');
  const query = params.toString();
  const { data } = await api.get(`/finance/transactions/search?${query}`);
  return data;
};

/**
 * Suggère les catégories "Autre" les plus utilisées (pour catégorisation rapide).
 *
 * @async
 * @param {Object} [params={}] - Paramètres
 * @param {number} [params.entityId] - ID entité
 * @param {number} [params.limit=50] - Limite résultats
 *
 * @returns {Promise<Array>} Top catégories "Autre"
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const suggestFinanceAutreTop = async ({ entityId, limit = 50 } = {}) => {
  const params = new URLSearchParams();
  if (entityId) params.set('entity_id', entityId);
  params.set('limit', limit);
  const query = params.toString();
  const { data } = await api.get(`/finance/categories/suggestions/autre-top?${query}`);
  return data;
};

/**
 * Autocomplétion pour recherche de catégories financières.
 *
 * @async
 * @param {Object} params - Paramètres de recherche
 * @param {string} params.q - Texte recherché
 * @param {number} [params.entityId] - ID entité
 * @param {number} [params.limit=20] - Limite résultats
 *
 * @returns {Promise<Array>} Catégories correspondantes
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const autocompleteFinanceCategories = async ({ q, entityId, limit = 20 }) => {
  if (!q) return [];
  const params = new URLSearchParams();
  params.set('q', q);
  if (entityId) params.set('entity_id', entityId);
  params.set('limit', limit);
  const query = params.toString();
  const { data } = await api.get(`/finance/categories/suggestions/complete?${query}`);
  return data;
};

/**
 * Catégorise plusieurs transactions en une seule requête.
 *
 * @async
 * @param {Object} payload - Données de catégorisation
 * @param {Array<number>} payload.transaction_ids - IDs transactions
 * @param {number} payload.category_id - ID catégorie cible
 *
 * @returns {Promise<Object>} Résultat de la catégorisation en lot
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const batchCategorizeFinanceTransactions = async (payload) => {
  const { data } = await api.post('/finance/transactions/batch-categorize', payload);
  return data;
};

/**
 * Met à jour une transaction financière.
 *
 * @async
 * @param {Object} params - Paramètres
 * @param {number} params.transactionId - ID transaction
 * @param {Object} params.payload - Données à mettre à jour
 *
 * @returns {Promise<Object>} Transaction mise à jour
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateFinanceTransaction = async ({ transactionId, payload }) => {
  const { data } = await api.patch(`/finance/transactions/${transactionId}`, payload);
  return data;
};

/**
 * Verrouille une transaction (empêche modification).
 *
 * @async
 * @param {number} transactionId - ID transaction à verrouiller
 *
 * @returns {Promise<Object>} Transaction verrouillée
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const lockFinanceTransaction = async (transactionId) => {
  const { data } = await api.post(`/finance/transactions/${transactionId}/lock`);
  return data;
};

/**
 * Met à jour la catégorie d'une transaction (wrapper de batchCategorize).
 *
 * @async
 * @param {Object} params - Paramètres
 * @param {number} params.transactionId - ID transaction
 * @param {number} params.categoryId - ID nouvelle catégorie
 *
 * @returns {Promise<Object>} Résultat de la catégorisation
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const updateTransactionCategory = async ({ transactionId, categoryId }) => {
  const { data } = await api.post('/finance/transactions/batch-categorize', {
    transaction_ids: [transactionId],
    category_id: categoryId,
  });
  return data;
};

// ============================================================================
// FINANCE - FEEDBACK ML (Machine Learning Loop)
// ============================================================================

/**
 * Enregistre un feedback de correction de catégorie pour améliorer le ML.
 *
 * @async
 * @param {number} transactionId - ID de la transaction corrigée
 * @param {Object} payload - Données du feedback
 * @param {number} payload.actual_category_id - Catégorie correcte
 * @param {number} [payload.predicted_category_id] - Catégorie prédite (ML)
 * @param {number} [payload.confidence_score] - Score de confiance ML
 * @param {string} [payload.correction_source] - Source correction
 *
 * @returns {Promise<Object>} Feedback enregistré
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const recordCategoryFeedback = async (transactionId, payload) => {
  const { data } = await api.post(`/finance/transactions/${transactionId}/feedback`, payload);
  return data;
};

/**
 * Récupère les statistiques globales de feedback de catégorisation.
 *
 * @async
 * @returns {Promise<Object>} Statistiques de feedback
 * @property {number} total_corrections - Total corrections
 * @property {number} unique_transactions - Transactions uniques corrigées
 * @property {number} avg_wrong_confidence - Confiance moyenne des erreurs
 *
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchCategoryFeedbackStats = async () => {
  const { data } = await api.get('/finance/categorization/feedback/stats');
  return data;
};

/**
 * Récupère les patterns de corrections les plus fréquents.
 *
 * @async
 * @param {number} [limit=10] - Nombre max de patterns
 *
 * @returns {Promise<Array>} Patterns de correction fréquents
 * @throws {AxiosError} Si erreur réseau ou serveur
 */
export const fetchCommonCorrections = async (limit = 10) => {
  const { data } = await api.get(`/finance/categorization/feedback/common-corrections?limit=${limit}`);
  return data;
};

export const importFinanceBankStatements = async ({ accountId, file }) => {
  if (!accountId || !file) throw new Error('accountId et file requis');
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post(`/finance/bank-statements/import?account_id=${accountId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const importFinanceBankStatementsPDF = async ({ accountId, file }) => {
  if (!accountId || !file) throw new Error('accountId et file requis');
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post(`/finance/bank-statements/import-pdf?account_id=${accountId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const runFinanceReconciliation = async (payload) => {
  const { data } = await api.post('/finance/reconciliation/run', payload);
  return data;
};

export const refreshFinanceAnomalies = async (payload) => {
  const { data } = await api.post('/finance/anomalies/refresh', payload);
  return data;
};

export const fetchFinanceAnomalies = async (severity) => {
  const params = new URLSearchParams();
  if (severity) params.set('severity', severity);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/anomalies?${query}` : '/finance/anomalies');
  return data;
};

export const updateFinanceMatchStatus = async ({ matchId, status, note }) => {
  const { data } = await api.post(`/finance/reconciliation/${matchId}/status`, { status, note });
  return data;
};

export const fetchFinanceMatches = async (status) => {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/reconciliation/matches?${query}` : '/finance/reconciliation/matches');
  return data;
};

export const fetchFinanceImports = async () => {
  const { data } = await api.get('/finance/imports');
  return data;
};

export const deduplicateFinanceTransactions = async () => {
  const { data } = await api.post('/finance/deduplicate');
  return data;
};

export const refreshFinanceStats = async () => {
  const { data } = await api.post('/finance/stats/refresh');
  return data;
};

export const fetchFinanceAccounts = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.isActive !== undefined) params.set('is_active', filters.isActive);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/accounts?${query}` : '/finance/accounts');
  return data;
};

export const getFinanceAccount = async (accountId) => {
  const { data } = await api.get(`/finance/accounts/${accountId}`);
  return data;
};

export const createFinanceAccount = async (payload) => {
  const { data } = await api.post('/finance/accounts', payload);
  return data;
};

export const updateFinanceAccount = async ({ accountId, payload }) => {
  const { data } = await api.put(`/finance/accounts/${accountId}`, payload);
  return data;
};

export const deleteFinanceAccount = async (accountId) => {
  const { data } = await api.delete(`/finance/accounts/${accountId}`);
  return data;
};

export const fetchFinanceCategories = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.type) params.set('type', filters.type);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/categories?${query}` : '/finance/categories');
  return data;
};

export const createFinanceCategory = async (payload) => {
  const { data } = await api.post('/finance/categories', payload);
  return data;
};

export const fetchFinanceCostCenters = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.isActive !== undefined) params.set('is_active', filters.isActive);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/cost-centers?${query}` : '/finance/cost-centers');
  return data;
};

export const createFinanceCostCenter = async (payload) => {
  const { data } = await api.post('/finance/cost-centers', payload);
  return data;
};

export const fetchFinanceCategoryStats = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/categories/stats?${query}` : '/finance/categories/stats');
  return data;
};

export const fetchFinanceAccountsOverview = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  // Note: date_from/date_to not supported by this endpoint
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/accounts/overview?${query}` : '/finance/accounts/overview');
  return data;
};

export const fetchFinanceDashboardSummary = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/dashboard/summary?${query}` : '/finance/dashboard/summary');
  return data;
};

export const fetchFinanceTimeline = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.months !== undefined) params.set('months', filters.months);
  if (filters.granularity) params.set('granularity', filters.granularity);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/stats/timeline?${query}` : '/finance/stats/timeline');
  return data;
};

export const fetchFinanceCategoryBreakdown = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.months !== undefined) params.set('months', filters.months);
  if (filters.direction) params.set('direction', filters.direction);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/stats/category-breakdown?${query}` : '/finance/stats/category-breakdown');
  return data;
};

export const fetchFinanceTreasury = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/stats/treasury?${query}` : '/finance/stats/treasury');
  return data;
};

export const fetchFinanceRules = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.isActive !== undefined) params.set('is_active', filters.isActive);
  const query = params.toString();
  const { data } = await api.get(query ? `/finance/rules?${query}` : '/finance/rules');
  return data;
};

export const createFinanceRule = async (payload) => {
  const { data } = await api.post('/finance/rules', payload);
  return data;
};

export const updateFinanceRule = async (id, payload) => {
  const { data } = await api.patch(`/finance/rules/${id}`, payload);
  return data;
};

export const deleteFinanceRule = async (id) => {
  await api.delete(`/finance/rules/${id}`);
  return true;
};

export const fetchPriceHistory = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.supplier) params.set('supplier', filters.supplier);
  if (filters.code) params.set('code', filters.code);
  if (filters.search) params.set('search', filters.search);
  if (filters.dateStart) params.set('date_start', filters.dateStart);
  if (filters.dateEnd) params.set('date_end', filters.dateEnd);
  if (filters.limit) params.set('limit', filters.limit);
  const query = params.toString();
  const { data } = await api.get(query ? `/prices/history?${query}` : '/prices/history');
  return data?.items ?? [];
};

export const fetchCapitalOverview = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityId) params.set('entity_id', filters.entityId);
  const query = params.toString();
  const { data } = await api.get(query ? `/capital/overview?${query}` : '/capital/overview');
  return data;
};

export const fetchDashboardMetrics = async () => {
  const { data } = await api.get('/dashboard/metrics');
  return data;
};

// ============================================================================
// INVENTORY INTELLIGENCE
// ============================================================================

export const calculateEOQ = async (payload) => {
  const { data } = await api.post('/inventory-intelligence/eoq', payload);
  return data;
};

export const calculateSafetyStock = async (payload) => {
  const { data } = await api.post('/inventory-intelligence/safety-stock', payload);
  return data;
};

export const fetchReorderPoints = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.leadTimeDays) params.set('lead_time_days', filters.leadTimeDays);
  if (filters.serviceLevel) params.set('service_level', filters.serviceLevel);
  if (filters.onlyNeedsReorder) params.set('only_needs_reorder', filters.onlyNeedsReorder);
  const query = params.toString();
  const { data } = await api.get(query ? `/inventory-intelligence/reorder-points?${query}` : '/inventory-intelligence/reorder-points');
  return data;
};

export const fetchStockoutPredictions = async (horizonDays = 30) => {
  const { data } = await api.get(`/inventory-intelligence/stockout-predictions?horizon_days=${horizonDays}`);
  return data;
};

export const fetchDeadStock = async (rotationThreshold = 0.3) => {
  const { data } = await api.get(`/inventory-intelligence/dead-stock?rotation_threshold=${rotationThreshold}`);
  return data;
};

export const fetchABCXYZClassification = async () => {
  const { data } = await api.get('/inventory-intelligence/abc-xyz');
  return data;
};

export const fetchReorderSuggestions = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.leadTimeDays) params.set('lead_time_days', filters.leadTimeDays);
  if (filters.serviceLevel) params.set('service_level', filters.serviceLevel);
  const query = params.toString();
  const { data } = await api.get(query ? `/inventory-intelligence/reorder-suggestions?${query}` : '/inventory-intelligence/reorder-suggestions');
  return data;
};

export const fetchInventoryIntelligenceSummary = async () => {
  const { data } = await api.get('/inventory-intelligence/summary');
  return data;
};

// ============================================================================
// FORECASTING
// ============================================================================

export const forecastSales = async (payload = {}) => {
  const { data } = await api.post('/forecasting/sales', payload);
  return data;
};

export const fetchStockDepletionForecast = async (daysHorizon = 60) => {
  const { data } = await api.get(`/forecasting/stock-depletion?days_horizon=${daysHorizon}`);
  return data;
};

export const fetchCashFlowForecast = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.horizonDays) params.set('horizon_days', filters.horizonDays);
  if (filters.startingBalance !== undefined) params.set('starting_balance', filters.startingBalance);
  const query = params.toString();
  const { data } = await api.get(query ? `/forecasting/cash-flow?${query}` : '/forecasting/cash-flow');
  return data;
};

export const fetchPriceTrendForecast = async (productId, horizonDays = 30) => {
  const { data } = await api.get(`/forecasting/price-trend/${productId}?horizon_days=${horizonDays}`);
  return data;
};

export const fetchForecastingSummary = async () => {
  const { data } = await api.get('/forecasting/summary');
  return data;
};

// ============================================================================
// AUDIT TRAIL
// ============================================================================

export const fetchAuditEntries = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.startDate) params.set('start_date', filters.startDate);
  if (filters.endDate) params.set('end_date', filters.endDate);
  if (filters.action) params.set('action', filters.action);
  if (filters.entity) params.set('entity', filters.entity);
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.userId) params.set('user_id', filters.userId);
  if (filters.severity) params.set('severity', filters.severity);
  if (filters.search) params.set('search', filters.search);
  if (filters.limit) params.set('limit', filters.limit);
  if (filters.offset) params.set('offset', filters.offset);
  const query = params.toString();
  const { data } = await api.get(query ? `/audit-trail/entries?${query}` : '/audit-trail/entries');
  return data;
};

export const searchAuditEntries = async (payload) => {
  const { data } = await api.post('/audit-trail/search', payload);
  return data;
};

export const fetchEntityHistory = async (entity, entityId, limit = 50) => {
  const { data } = await api.get(`/audit-trail/entity/${entity}/${entityId}?limit=${limit}`);
  return data;
};

export const fetchUserActivity = async (userId, filters = {}) => {
  const params = new URLSearchParams();
  if (filters.startDate) params.set('start_date', filters.startDate);
  if (filters.limit) params.set('limit', filters.limit);
  const query = params.toString();
  const { data } = await api.get(query ? `/audit-trail/user/${userId}?${query}` : `/audit-trail/user/${userId}`);
  return data;
};

export const generateAuditReport = async (startDate, endDate) => {
  const { data } = await api.get(`/audit-trail/report?start_date=${startDate}&end_date=${endDate}`);
  return data;
};

export const fetchSecurityEvents = async (days = 7) => {
  const { data } = await api.get(`/audit-trail/security-events?days=${days}`);
  return data;
};

export const fetchRecentChanges = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entity) params.set('entity', filters.entity);
  if (filters.hours) params.set('hours', filters.hours);
  const query = params.toString();
  const { data } = await api.get(query ? `/audit-trail/recent-changes?${query}` : '/audit-trail/recent-changes');
  return data;
};

export const exportUserDataRGPD = async (userId) => {
  const { data } = await api.get(`/audit-trail/rgpd/export/${userId}`);
  return data;
};

export const anonymizeUserDataRGPD = async (userId) => {
  const { data } = await api.delete(`/audit-trail/rgpd/anonymize/${userId}`);
  return data;
};

export const fetchAuditSummary = async () => {
  const { data } = await api.get('/audit-trail/summary');
  return data;
};

// ============================================================================
// ANOMALY DETECTION
// ============================================================================

export const scanForAnomalies = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.entityTypes) params.set('entity_types', filters.entityTypes);
  if (filters.severityThreshold) params.set('severity_threshold', filters.severityThreshold);
  if (filters.daysBack) params.set('days_back', filters.daysBack);
  const query = params.toString();
  const { data } = await api.get(query ? `/anomaly-detection/scan?${query}` : '/anomaly-detection/scan');
  return data;
};

export const detectTransactionOutliers = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.daysBack) params.set('days_back', filters.daysBack);
  if (filters.zScoreThreshold) params.set('z_score_threshold', filters.zScoreThreshold);
  const query = params.toString();
  const { data } = await api.get(query ? `/anomaly-detection/transactions/outliers?${query}` : '/anomaly-detection/transactions/outliers');
  return data;
};

export const detectDuplicateInvoices = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.daysBack) params.set('days_back', filters.daysBack);
  if (filters.similarityThreshold) params.set('similarity_threshold', filters.similarityThreshold);
  const query = params.toString();
  const { data } = await api.get(query ? `/anomaly-detection/invoices/duplicates?${query}` : '/anomaly-detection/invoices/duplicates');
  return data;
};

export const detectInvoiceSequenceGaps = async (daysBack = 90) => {
  const { data } = await api.get(`/anomaly-detection/invoices/sequence-gaps?days_back=${daysBack}`);
  return data;
};

export const detectRoundAmounts = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.daysBack) params.set('days_back', filters.daysBack);
  if (filters.minAmount) params.set('min_amount', filters.minAmount);
  const query = params.toString();
  const { data } = await api.get(query ? `/anomaly-detection/transactions/round-amounts?${query}` : '/anomaly-detection/transactions/round-amounts');
  return data;
};

export const fetchAnomalySummary = async (filters = {}) => {
  const params = new URLSearchParams();
  // Support ancien format (nombre) et nouveau format (objet)
  if (typeof filters === 'number') {
    params.set('days_back', filters);
  } else {
    if (filters.daysBack) params.set('days_back', filters.daysBack);
    if (filters.severity) params.set('severity', filters.severity);
    if (filters.type) params.set('type', filters.type);
  }
  const query = params.toString();
  const { data } = await api.get(query ? `/anomaly-detection/summary?${query}` : '/anomaly-detection/summary');
  return data;
};

export const resolveAnomaly = async (anomalyId, resolutionNote) => {
  const { data } = await api.post(`/anomaly-detection/resolve/${anomalyId}?resolution_note=${encodeURIComponent(resolutionNote)}`);
  return data;
};

// ============================================================================
// MARGINS
// ============================================================================

export const calculateMargin = async (payload) => {
  const { data } = await api.post('/margins/calculate', payload);
  return data;
};

export const fetchProductMargins = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.category) params.set('category', filters.category);
  if (filters.minMarginPct !== undefined) params.set('min_margin_pct', filters.minMarginPct);
  if (filters.daysBack) params.set('days_back', filters.daysBack);
  if (filters.sortBy) params.set('sort_by', filters.sortBy);
  if (filters.limit) params.set('limit', filters.limit);
  const query = params.toString();
  const { data } = await api.get(query ? `/margins/products?${query}` : '/margins/products');
  return data;
};

export const fetchCategoryMargins = async (daysBack = 30) => {
  const { data } = await api.get(`/margins/categories?days_back=${daysBack}`);
  return data;
};

export const fetchProductPAMP = async (productId) => {
  const { data } = await api.get(`/margins/pamp/${productId}`);
  return data;
};

export const fetchDishMargins = async (minMarginPct) => {
  const params = new URLSearchParams();
  if (minMarginPct !== undefined) params.set('min_margin_pct', minMarginPct);
  const query = params.toString();
  const { data } = await api.get(query ? `/margins/dishes?${query}` : '/margins/dishes');
  return data;
};

export const fetchMarginAlerts = async (thresholdPct = 20) => {
  const { data } = await api.get(`/margins/alerts?threshold_pct=${thresholdPct}`);
  return data;
};

export const fetchMarginSummary = async (daysBack = 30) => {
  const { data } = await api.get(`/margins/summary?days_back=${daysBack}`);
  return data;
};

// ============================================================================
// BANK RECONCILIATION
// ============================================================================

export const runBankReconciliation = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.daysBack) params.set('days_back', filters.daysBack);
  if (filters.autoConfirmThreshold) params.set('auto_confirm_threshold', filters.autoConfirmThreshold);
  const query = params.toString();
  const { data } = await api.post(query ? `/bank-reconciliation/run?${query}` : '/bank-reconciliation/run');
  return data;
};

export const fetchUnmatchedTransactions = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.daysBack) params.set('days_back', filters.daysBack);
  if (filters.minAmount) params.set('min_amount', filters.minAmount);
  const query = params.toString();
  const { data } = await api.get(query ? `/bank-reconciliation/unmatched/transactions?${query}` : '/bank-reconciliation/unmatched/transactions');
  return data;
};

export const fetchUnmatchedInvoices = async (daysBack = 90) => {
  const { data } = await api.get(`/bank-reconciliation/unmatched/invoices?days_back=${daysBack}`);
  return data;
};

export const createManualMatch = async (payload) => {
  const { data } = await api.post('/bank-reconciliation/match/manual', payload);
  return data;
};

export const fetchSupplierAliases = async () => {
  const { data } = await api.get('/bank-reconciliation/aliases');
  return data;
};

export const createSupplierAlias = async (payload) => {
  const { data } = await api.post('/bank-reconciliation/aliases', payload);
  return data;
};

export const deleteSupplierAlias = async (aliasId) => {
  const { data } = await api.delete(`/bank-reconciliation/aliases/${aliasId}`);
  return data;
};

export const fetchReconciliationSummary = async (daysBack = 30) => {
  const { data } = await api.get(`/bank-reconciliation/summary?days_back=${daysBack}`);
  return data;
};

// ============================================================================
// RULES ENGINE
// ============================================================================

export const classifyTransaction = async (transaction, detectAnomalies = true) => {
  const params = new URLSearchParams();
  params.set('detect_anomalies', detectAnomalies);
  const { data } = await api.post(`/rules-engine/classify?${params.toString()}`, transaction);
  return data;
};

export const classifyTransactionsBatch = async (payload) => {
  const { data } = await api.post('/rules-engine/classify/batch', payload);
  return data;
};

export const fetchClassificationRules = async (activeOnly = true) => {
  const { data } = await api.get(`/rules-engine/rules?active_only=${activeOnly}`);
  return data;
};

export const createClassificationRule = async (payload) => {
  const { data } = await api.post('/rules-engine/rules', payload);
  return data;
};

export const recordClassificationFeedback = async (payload) => {
  const { data } = await api.post('/rules-engine/feedback', payload);
  return data;
};

export const bootstrapDefaultRules = async () => {
  const { data } = await api.post('/rules-engine/bootstrap');
  return data;
};

export const fetchClassificationStats = async (days = 30) => {
  const { data } = await api.get(`/rules-engine/stats?days=${days}`);
  return data;
};

export const suggestCategory = async (filters = {}) => {
  const params = new URLSearchParams();
  params.set('description', filters.description || '');
  if (filters.amount !== undefined) params.set('amount', filters.amount);
  if (filters.supplier) params.set('supplier', filters.supplier);
  const { data } = await api.get(`/rules-engine/suggest?${params.toString()}`);
  return data;
};

// ============================================================================
// SUPPLIER SCORING
// ============================================================================

export const fetchSupplierScore = async (supplierName, periodDays = 90) => {
  const { data } = await api.get(`/supplier-scoring/score/${encodeURIComponent(supplierName)}?period_days=${periodDays}`);
  return data;
};

export const fetchSuppliersRanking = async () => {
  const { data } = await api.get('/supplier-scoring/ranking');
  return data;
};

export const compareSuppliers = async (suppliers) => {
  const { data } = await api.post('/supplier-scoring/compare', { suppliers });
  return data;
};

export const recordSupplierDelivery = async (payload) => {
  const { data } = await api.post('/supplier-scoring/delivery', payload);
  return data;
};

export const recordSupplierInvoiceIssue = async (payload) => {
  const { data } = await api.post('/supplier-scoring/issue', payload);
  return data;
};

export const fetchScoringDimensions = async () => {
  const { data } = await api.get('/supplier-scoring/dimensions');
  return data;
};

export const fetchSupplierScoreHistory = async (supplierName, limit = 20) => {
  const { data } = await api.get(`/supplier-scoring/history/${encodeURIComponent(supplierName)}?limit=${limit}`);
  return data;
};

// --- Nouveaux endpoints Supplier Scoring Details ---

export const fetchSupplierScoringOverview = async () => {
  const { data } = await api.get('/supplier-scoring/overview');
  return data;
};

export const fetchSuppliersList = async ({ page = 1, perPage = 20, minScore, maxScore, trend, search, sortBy, sortOrder } = {}) => {
  const params = new URLSearchParams();
  params.set('page', page);
  params.set('per_page', perPage);
  if (minScore !== undefined) params.set('min_score', minScore);
  if (maxScore !== undefined) params.set('max_score', maxScore);
  if (trend) params.set('trend', trend);
  if (search) params.set('search', search);
  if (sortBy) params.set('sort_by', sortBy);
  if (sortOrder) params.set('sort_order', sortOrder);
  const { data } = await api.get(`/supplier-scoring/suppliers?${params.toString()}`);
  return data;
};

export const fetchSupplierDetails = async (supplierId) => {
  const { data } = await api.get(`/supplier-scoring/suppliers/${supplierId}`);
  return data;
};

export const fetchSupplierHistoryById = async (supplierId, { limit = 12, periodDays = 365 } = {}) => {
  const params = new URLSearchParams();
  params.set('limit', limit);
  params.set('period_days', periodDays);
  const { data } = await api.get(`/supplier-scoring/suppliers/${supplierId}/history?${params.toString()}`);
  return data;
};

export const fetchScoringCriteria = async () => {
  const { data } = await api.get('/supplier-scoring/criteria');
  return data;
};

export const updateScoringCriteria = async (criteria) => {
  const { data } = await api.put('/supplier-scoring/criteria', { criteria });
  return data;
};

export const fetchSupplierAlerts = async ({ severity, acknowledged, limit = 50 } = {}) => {
  const params = new URLSearchParams();
  if (severity) params.set('severity', severity);
  if (acknowledged !== undefined) params.set('acknowledged', acknowledged);
  params.set('limit', limit);
  const { data } = await api.get(`/supplier-scoring/alerts?${params.toString()}`);
  return data;
};

export const acknowledgeSupplierAlert = async (alertId) => {
  const { data } = await api.post(`/supplier-scoring/alerts/${alertId}/acknowledge`);
  return data;
};

export const recalculateSupplierScores = async ({ supplierIds, forceRecalculate = false } = {}) => {
  const { data } = await api.post('/supplier-scoring/recalculate', {
    supplier_ids: supplierIds,
    force_recalculate: forceRecalculate
  });
  return data;
};

// ============================================================================
// newCMS - Restaurant & Mobile (Scénarios 3.6 / 3.8)
// ============================================================================

export const fetchNewCMSRestaurantMenusOverview = async () => {
  const demoOverview = {
    metrics: {
      total_plats: 3,
      avg_food_cost_pct: 32.5,
      alerts_count: 1,
      top_plats: [
        { plat_id: 1, nom: 'Burger Signature', marge_pct: 68.0, prix_vente_ttc: 18, cout_matiere: 5.8 },
        { plat_id: 2, nom: 'Poke Saumon', marge_pct: 62.0, prix_vente_ttc: 16, cout_matiere: 6.1 },
        { plat_id: 3, nom: 'Tacos Vegan', marge_pct: 58.0, prix_vente_ttc: 14, cout_matiere: 5.9 },
      ],
    },
    plat_costs: [
      { plat_id: 1, nom: 'Burger Signature', prix_vente_ttc: 18, cout_matiere: 5.8, food_cost_pct: 32.2, marge_pct: 67.8 },
      { plat_id: 2, nom: 'Poke Saumon', prix_vente_ttc: 16, cout_matiere: 6.1, food_cost_pct: 38.1, marge_pct: 61.9 },
      { plat_id: 3, nom: 'Tacos Vegan', prix_vente_ttc: 14, cout_matiere: 5.9, food_cost_pct: 42.1, marge_pct: 57.9 },
    ],
    stock_locations: [],
    ingredient_alerts: [],
  };
  try {
    const { data } = await api.get('/newcms/restaurant/menus/overview');
    const payload = data?.metrics ? data : (data?.data ?? data);
    if (!payload) return demoOverview;
    return payload;
  } catch {
    return demoOverview;
  }
};

export const fetchNewCMSRestaurantPlatDetail = async (platId) => {
  const demoPlats = {
    1: {
      id: 1,
      nom: 'Burger Signature',
      categorie: 'Burgers',
      prix_vente_ttc: 18,
      cout_matiere: 5.8,
      marge_pct: 67.8,
      food_cost_pct: 32.2,
      ingredients: [
        { ingredient_id: 101, nom: 'Boeuf 180g', quantite: 0.18, unite: 'kg', unit_price: 14, total_cost: 2.52, cost_percentage: 43.4 },
        { ingredient_id: 102, nom: 'Bun brioché', quantite: 1, unite: 'pc', unit_price: 0.8, total_cost: 0.8, cost_percentage: 13.8 },
        { ingredient_id: 103, nom: 'Cheddar AOP', quantite: 2, unite: 'tr', unit_price: 0.35, total_cost: 0.7, cost_percentage: 12.1 },
        { ingredient_id: 104, nom: 'Pickles + sauce', quantite: 1, unite: 'set', unit_price: 0.6, total_cost: 0.6, cost_percentage: 10.3 },
      ],
    },
    2: {
      id: 2,
      nom: 'Poke Saumon',
      categorie: 'Bowls',
      prix_vente_ttc: 16,
      cout_matiere: 6.1,
      marge_pct: 61.9,
      food_cost_pct: 38.1,
      ingredients: [
        { ingredient_id: 201, nom: 'Saumon frais', quantite: 0.14, unite: 'kg', unit_price: 22, total_cost: 3.08, cost_percentage: 50.5 },
        { ingredient_id: 202, nom: 'Riz vinaigré', quantite: 0.18, unite: 'kg', unit_price: 2.5, total_cost: 0.45, cost_percentage: 7.4 },
        { ingredient_id: 203, nom: 'Avocat', quantite: 0.5, unite: 'pc', unit_price: 1.2, total_cost: 0.6, cost_percentage: 9.8 },
        { ingredient_id: 204, nom: 'Sauce + toppings', quantite: 1, unite: 'set', unit_price: 0.9, total_cost: 0.9, cost_percentage: 14.8 },
      ],
    },
    3: {
      id: 3,
      nom: 'Tacos Vegan',
      categorie: 'Veggie',
      prix_vente_ttc: 14,
      cout_matiere: 5.9,
      marge_pct: 57.9,
      food_cost_pct: 42.1,
      ingredients: [
        { ingredient_id: 301, nom: 'Tortilla maïs', quantite: 2, unite: 'pc', unit_price: 0.4, total_cost: 0.8, cost_percentage: 13.6 },
        { ingredient_id: 302, nom: 'Protéine soja', quantite: 0.12, unite: 'kg', unit_price: 8, total_cost: 0.96, cost_percentage: 16.3 },
        { ingredient_id: 303, nom: 'Guacamole', quantite: 0.08, unite: 'kg', unit_price: 10, total_cost: 0.8, cost_percentage: 13.6 },
        { ingredient_id: 304, nom: 'Légumes + sauce', quantite: 1, unite: 'set', unit_price: 1.4, total_cost: 1.4, cost_percentage: 23.7 },
      ],
    },
  };
  try {
    const { data } = await api.get(`/newcms/restaurant/plat/${platId}`);
    const raw = data?.id ? data : (data?.data ?? data);
    const sellingPrice = raw?.prix_vente_ttc ?? raw?.selling_price;
    const cost = raw?.cout_matiere ?? raw?.cost;
    const marginPct = raw?.marge_pct ?? raw?.margin_pct;
    const foodCostPct =
      raw?.food_cost_pct ??
      (sellingPrice && cost ? Number(((cost / sellingPrice) * 100).toFixed(2)) : undefined);
    const ingredients = (raw?.ingredients ?? []).map((ing) => ({
      ...ing,
      unit_price: ing.unit_price ?? ing.cout_unitaire ?? 0,
      total_cost: ing.total_cost ?? (ing.unit_price ?? 0) * (ing.quantite ?? 0),
      cost_percentage: ing.cost_percentage ?? 0,
      quantite: ing.quantite ?? ing.qty ?? 0,
      unite: ing.unite ?? ing.unit ?? null,
    }));
    if (!raw) {
      return demoPlats[platId] || demoPlats[1];
    }
    return {
      ...raw,
      prix_vente_ttc: sellingPrice,
      cout_matiere: cost,
      marge_pct: marginPct,
      marge_brute: raw?.marge_brute ?? raw?.margin ?? null,
      food_cost_pct: foodCostPct,
      ingredients,
    };
  } catch {
    return demoPlats[platId] || demoPlats[1];
  }
};

export const simulatePlatPriceNewCMS = async (platId, payload) => {
  const { data } = await api.post(`/restaurant/plats/${platId}/simulate-price`, payload);
  return data;
};

export const fetchNewCMSMobileInventory = async ({ page = 1, pageSize = 50, search } = {}) => {
  const params = new URLSearchParams();
  params.set('page', page);
  params.set('page_size', pageSize);
  if (search) params.set('search', search);
  const { data } = await api.get(`/newcms/mobile/inventory?${params.toString()}`);
  return data;
};

export const scanNewCMSMobileProduct = async (ean) => {
  const { data } = await api.post('/newcms/mobile/scan', { ean });
  return data;
};

export const adjustNewCMSMobileStock = async (payload) => {
  const { data } = await api.post('/newcms/mobile/adjust', payload);
  return data;
};

// ============================================================================
// RESTAURANT STOCK (INDÉPENDANT DE L'ÉPICERIE)
// ============================================================================

export const fetchRestaurantStockSummary = async () => {
  const { data } = await api.get('/restaurant/stock/summary');
  return data;
};

export const fetchRestaurantStockMovements = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.ingredientId) params.set('ingredient_id', filters.ingredientId);
  if (filters.source) params.set('source', filters.source);
  if (filters.typeMouvement) params.set('type_mouvement', filters.typeMouvement);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.limit) params.set('limit', filters.limit);
  if (filters.offset) params.set('offset', filters.offset);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/stock/movements?${query}` : '/restaurant/stock/movements');
  return data;
};

export const fetchRestaurantStockAnalytics = async (days = 30) => {
  const { data } = await api.get(`/restaurant/stock/analytics?days=${days}`);
  return data;
};

export const createRestaurantStockMovement = async (payload) => {
  const { data } = await api.post('/restaurant/stock/movements', payload);
  return data;
};

export const transferFromEpicerie = async (payload) => {
  const { data } = await api.post('/restaurant/stock/transfer-from-epicerie', payload);
  return data;
};

export const recordRestaurantConsumption = async (payload) => {
  const { data } = await api.post('/restaurant/stock/consumption', payload);
  return data;
};

export const adjustRestaurantStock = async (payload) => {
  const { data } = await api.post('/restaurant/stock/adjustment', payload);
  return data;
};

// ============================================================================
// COCKPIT UNIFIÉ
// ============================================================================

export const fetchCockpitOverview = async () => {
  const { data } = await api.get('/cockpit/overview');
  return data;
};

export const fetchCockpitLiveKPIs = async () => {
  const { data } = await api.get('/cockpit/kpis/live');
  return data;
};

export const fetchCockpitAlerts = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.severity) params.set('severity', filters.severity);
  if (filters.category) params.set('category', filters.category);
  if (filters.limit) params.set('limit', filters.limit);
  const query = params.toString();
  const { data } = await api.get(query ? `/cockpit/alerts?${query}` : '/cockpit/alerts');
  return data;
};

export const acknowledgeCockpitAlert = async (alertId) => {
  const { data } = await api.post(`/cockpit/alerts/${alertId}/acknowledge`);
  return data;
};

export const fetchCockpitHealth = async () => {
  const { data } = await api.get('/cockpit/health');
  return data;
};

// ============================================================================
// REPORTS EXPORTS
// ============================================================================

export const exportReport = async (type) => {
  const response = await api.get(`/reports/export/${type}`, {
    responseType: 'blob',
  });
  return response;
};

// ============================================================================
// SUPPLIERS CRUD
// ============================================================================

export const fetchSuppliers = async (params = {}) => {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', params.page);
  if (params.per_page) searchParams.set('per_page', params.per_page);
  if (params.search) searchParams.set('search', params.search);
  if (params.actif !== undefined) searchParams.set('actif', params.actif);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);
  const query = searchParams.toString();
  const { data } = await api.get(query ? `/suppliers?${query}` : '/suppliers');
  return data;
};

export const fetchSupplier = async (id) => {
  const { data } = await api.get(`/suppliers/${id}`);
  return data;
};

export const createSupplier = async (supplierData) => {
  const { data } = await api.post('/suppliers', supplierData);
  return data;
};

export const updateSupplier = async (id, supplierData) => {
  const { data } = await api.put(`/suppliers/${id}`, supplierData);
  return data;
};

export const deleteSupplier = async (id) => {
  await api.delete(`/suppliers/${id}`);
};

// ============================================================================
// UTILITAIRES
// ============================================================================

/**
 * Retourne l'URL de base de l'API pour construire des liens de téléchargement.
 *
 * @returns {string} URL de base de l'API (ex: '/api' ou 'https://api.example.com')
 *
 * @example
 * const pdfUrl = `${getApiBaseUrl()}/invoices/${id}/download`;
 */
export const getApiBaseUrl = () => api.defaults.baseURL ?? '/api';

export default api;
