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
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && typeof unauthorizedHandler === 'function') {
      unauthorizedHandler();
    }
    return Promise.reject(error);
  },
);

api.interceptors.request.use((config) => {
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
  const { data } = await api.get('/categories');
  return data;
};

export const fetchVendors = async () => {
  const { data } = await api.get('/vendors');
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
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
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
  if (filters.entityId) params.set('entity_id', filters.entityId);
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.supplierId) params.set('supplier_id', filters.supplierId);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  const { data } = await api.get(query ? `/price-history?${query}` : '/price-history');
  return data;
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

export default api;
