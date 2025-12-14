import axios from 'axios';

/**
 * Client HTTP Axios centralisé pour toutes les interactions SPA ↔ FastAPI.
 * - `baseURL` est configurable via `VITE_API_BASE_URL`.
 * - Le header `Authorization: Bearer <token>` est géré via `setAccessToken`.
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

let unauthorizedHandler = null;
let currentToken = null;

export const setAccessToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    currentToken = token;
  } else {
    delete api.defaults.headers.common.Authorization;
    currentToken = null;
  }
};

export const clearAccessToken = () => {
  delete api.defaults.headers.common.Authorization;
  currentToken = null;
};

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
  if (currentToken) {
    const headers = config.headers ?? {};
    if (!headers.Authorization) {
      headers.Authorization = `Bearer ${currentToken}`;
    }
    config.headers = headers;
  }
  return config;
});

/**
 * Groupe de requêtes catalogue/inventaire/mouvements.
 */
export const fetchProducts = async (params = {}) => {
  const { data } = await api.get('/products', { params });
  return data;
};

export const fetchInventorySummary = async () => {
  const { data } = await api.get('/inventory/summary');
  return data;
};

export const fetchRestaurantConsumptions = async () => {
  const { data } = await api.get('/restaurant/consumptions');
  return data;
};

export const fetchRestaurantPriceHistoryComparison = async () => {
  const { data } = await api.get('/restaurant/price-history/comparison');
  return data;
};

export const fetchRestaurantPlatMappings = async () => {
  const { data } = await api.get('/restaurant/plats/mappings');
  return data;
};

export const syncRestaurantIngredients = async () => {
  const { data } = await api.post('/restaurant/ingredients/sync');
  return data;
};

export const fetchEpicerieProducts = async () => {
  const { data } = await api.get('/restaurant/epicerie/products');
  return data;
};

export const updatePlatMapping = async (platId, payload) => {
  const { data } = await api.put(`/restaurant/plats/${platId}/mapping`, payload);
  return data;
};

export const deletePlatMapping = async (platId) => {
  const { data } = await api.delete(`/restaurant/plats/${platId}/mapping`);
  return data;
};

export const updateRestaurantIngredientPrice = async (ingredientId, payload) => {
  const { data } = await api.patch(`/restaurant/ingredients/${ingredientId}/price`, payload);
  return data;
};

export const fetchRestaurantIngredientPriceHistory = async (ingredientId) => {
  const { data } = await api.get(`/restaurant/ingredients/${ingredientId}/price-history`);
  return data;
};

export const updateRestaurantPlatPrice = async (platId, payload) => {
  const { data } = await api.patch(`/restaurant/plats/${platId}/price`, payload);
  return data;
};

export const fetchRestaurantPlatPriceHistory = async (platId) => {
  const { data } = await api.get(`/restaurant/plats/${platId}/price-history`);
  return data;
};

export const fetchRestaurantPriceHistoryOverview = async () => {
  const { data } = await api.get('/restaurant/prices/history');
  return data;
};

export const fetchRestaurantForecastOverview = async () => {
  const { data } = await api.get('/restaurant/forecasts/overview');
  return data;
};

export const fetchRestaurantTvaSummary = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/charges/tva-summary?${query}` : '/restaurant/charges/tva-summary');
  return data;
};

export const fetchRestaurantDashboard = async () => {
  const { data } = await api.get('/restaurant/dashboard/overview');
  return data;
};

// ============================================================================
// RESTAURANT FOOD COST & OVERVIEW
// ============================================================================

export const fetchRestaurantOverview = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/overview?${query}` : '/restaurant/overview');
  return data;
};

export const fetchRestaurantPlatDetails = async (platId) => {
  const { data } = await api.get(`/restaurant/plats/${platId}/detail`);
  return data;
};

export const fetchRestaurantPlatIngredients = async (platId) => {
  const { data } = await api.get(`/restaurant/plats/${platId}/cost-breakdown`);
  return data;
};

export const simulatePlatPrice = async (platId, payload) => {
  const { data } = await api.post(`/restaurant/plats/${platId}/simulate-price`, payload);
  return data;
};

export const fetchRestaurantAlerts = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.type) params.set('type', filters.type);
  if (filters.severity) params.set('severity', filters.severity);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/alerts?${query}` : '/restaurant/alerts');
  return data;
};

export const fetchRestaurantFoodCostAnalysis = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.granularity) params.set('granularity', filters.granularity);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/food-cost/analysis?${query}` : '/restaurant/food-cost/analysis');
  return data;
};

// ---------------------------------------------------------------------------
// Restaurant Menus & Costs (Scénario 3.6)
// ---------------------------------------------------------------------------

export const fetchRestaurantMenusOverview = async () => {
  const { data } = await api.get('/restaurant/menus/overview');
  return data;
};

export const checkoutCart = async (payload) => {
  const { data } = await api.post('/pos/checkout', payload);
  return data;
};

export const createProduct = async (payload) => {
  const { data } = await api.post('/catalog/products', payload);
  return data;
};

export const updateProductRequest = async (productId, payload) => {
  const { data } = await api.patch(`/catalog/products/${productId}`, payload);
  return data;
};

export const deleteProductRequest = async (productId) => {
  await api.delete(`/catalog/products/${productId}`);
  return true;
};

export const lookupProductByBarcode = async (barcode) => {
  const { data } = await api.get(`/catalog/products/barcode/${encodeURIComponent(barcode)}`);
  return data;
};

/**
 * Flux planning / audit / stock : compose les queryparams et consomme les endpints correspondants.
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

export const fetchAuditActions = async (includeClosed = false) => {
  const { data } = await api.get('/audit/actions', { params: { include_closed: includeClosed } });
  return data;
};

export const fetchAuditResolutions = async () => {
  const { data } = await api.get('/audit/resolutions');
  return data;
};

export const createAuditAssignment = async (payload) => {
  const { data } = await api.post('/audit/assignments', payload);
  return data;
};

export const updateAuditActionStatus = async ({ actionId, status, note }) => {
  const { data } = await api.post(`/audit/actions/${actionId}/status`, { status, note });
  return data;
};

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

export const linkInvoiceLine = async ({ line, productId }) => {
  const { data } = await api.post('/invoices/lines/link', {
    line,
    product_id: productId,
  });
  return data.line;
};

export const createProductFromLine = async ({ line, supplier, initializeStock = false, invoiceDate }) => {
  const { data } = await api.post('/invoices/lines/create-product', {
    line,
    supplier,
    initialize_stock: Boolean(initializeStock),
    invoice_date: invoiceDate ?? null,
  });
  return data.summary;
};

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

export const downloadInvoiceFile = async (invoiceId) => {
  const response = await api.get(`/invoices/history/${encodeURIComponent(invoiceId)}/file`, {
    responseType: 'blob',
  });
  return response;
};

export const fetchCategories = async () => {
  const { data } = await api.get('/catalog/categories');
  return data;
};

export const fetchVendors = async () => {
  const { data } = await api.get('/catalog/vendors');
  return data;
};

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

// --- Finance (transactions/catégories refonte) ---

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

export const suggestFinanceAutreTop = async ({ entityId, limit = 50 } = {}) => {
  const params = new URLSearchParams();
  if (entityId) params.set('entity_id', entityId);
  params.set('limit', limit);
  const query = params.toString();
  const { data } = await api.get(`/finance/categories/suggestions/autre-top?${query}`);
  return data;
};

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

export const batchCategorizeFinanceTransactions = async (payload) => {
  const { data } = await api.post('/finance/transactions/batch-categorize', payload);
  return data;
};

export const updateTransactionCategory = async ({ transactionId, categoryId }) => {
  const { data } = await api.post('/finance/transactions/batch-categorize', {
    transaction_ids: [transactionId],
    category_id: categoryId,
  });
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
// UTILITAIRES
// ============================================================================

/**
 * Retourne l'URL de base de l'API pour construire des liens de téléchargement.
 */
export const getApiBaseUrl = () => api.defaults.baseURL ?? '/api';

export default api;
