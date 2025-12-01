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

export const fetchPriceHistory = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.code) params.set('code', filters.code);
  if (filters.supplier) params.set('supplier', filters.supplier);
  if (filters.search) params.set('search', filters.search);
  if (filters.dateStart) params.set('date_start', filters.dateStart);
  if (filters.dateEnd) params.set('date_end', filters.dateEnd);
  params.set('limit', filters.limit ?? 500);
  const query = params.toString();
  const url = query ? `/prices/history?${query}` : '/prices/history';
  const { data } = await api.get(url);
  return data.items ?? [];
};

export const fetchCapitalOverview = async () => {
  const { data } = await api.get('/capital/overview');
  return data;
};

export const downloadCapitalSnapshotReport = async () => {
  const response = await api.get('/reports/export/capital_snapshot', {
    responseType: 'blob',
  });
  return response;
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

export const fetchRestaurantPriceHistoryOverview = async (limit = 12) => {
  const params = new URLSearchParams();
  params.set('limit', limit);
  const query = params.toString();
  const { data } = await api.get(`/restaurant/prices/history?${query}`);
  return data;
};

export const fetchRestaurantBankStatements = async (account) => {
  const params = new URLSearchParams();
  if (account) params.set('account', account);
  const query = params.toString();
  const { data } = await api.get(query ? `/restaurant/bank-statements?${query}` : '/restaurant/bank-statements');
  return data;
};

export const fetchRestaurantBankStatementSummary = async ({ account, months = 6, grouping = 'default' } = {}) => {
  const params = new URLSearchParams();
  if (account) params.set('account', account);
  if (months !== undefined && months !== null) params.set('months', months);
  if (grouping) params.set('grouping', grouping);
  const query = params.toString();
  const { data } = await api.get(`/restaurant/bank-statements/summary?${query}`);
  return data;
};

export const fetchRestaurantBankAccountsOverview = async () => {
  const { data } = await api.get('/restaurant/bank-accounts/overview');
  return data;
};

export const fetchRestaurantForecastOverview = async ({
  horizonDays = 30,
  granularity = 'weekly',
  top = 8,
} = {}) => {
  const params = new URLSearchParams();
  params.set('horizon_days', horizonDays);
  params.set('granularity', granularity);
  if (top) {
    params.set('top', top);
  }
  const query = params.toString();
  const { data } = await api.get(`/restaurant/forecasts/overview?${query}`);
  return data;
};

export const fetchRestaurantTvaSummary = async (months = 6) => {
  const params = new URLSearchParams();
  params.set('months', months);
  const query = params.toString();
  const { data } = await api.get(`/restaurant/charges/tva-summary?${query}`);
  return data;
};

export const createRestaurantBankStatement = async (payload) => {
  const { data } = await api.post('/restaurant/bank-statements', payload);
  return data;
};

export const updateRestaurantBankStatement = async (entryId, payload) => {
  const { data } = await api.patch(`/restaurant/bank-statements/${entryId}`, payload);
  return data;
};

export const importRestaurantBankStatementsPdf = async (account, file) => {
  const formData = new FormData();
  formData.append('account', account);
  formData.append('file', file);
  const { data } = await api.post('/restaurant/bank-statements/import-pdf', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const createExpenseFromBankStatement = async (entryId, payload) => {
  const { data } = await api.post(`/restaurant/bank-statements/${entryId}/create-expense`, payload);
  return data;
};

export const fetchDashboardMetrics = async () => {
  const { data } = await api.get('/dashboard/metrics');
  return data;
};

export const fetchReportsOverview = async () => {
  const { data } = await api.get('/reports/overview');
  return data;
};

export const fetchAdminOverview = async () => {
  const { data } = await api.get('/admin/overview');
  return data;
};

export const fetchAdminUsers = async () => {
  const { data } = await api.get('/admin/users');
  return data;
};

export const createBackupRequest = async ({ label } = {}) => {
  const { data } = await api.post('/admin/backups', label ? { label } : {});
  return data;
};

export const restoreBackupRequest = async (filename) => {
  if (!filename) throw new Error('Nom de sauvegarde requis');
  const { data } = await api.post(`/admin/backups/${encodeURIComponent(filename)}/restore`);
  return data;
};

export const deleteBackupRequest = async (filename) => {
  if (!filename) throw new Error('Nom de sauvegarde requis');
  await api.delete(`/admin/backups/${encodeURIComponent(filename)}`);
  return true;
};

export const fetchIntegrityReport = async () => {
  const { data } = await api.get('/admin/backups/integrity');
  return data;
};

export const fetchBackupSettings = async () => {
  const { data } = await api.get('/admin/settings');
  return data;
};

export const saveBackupSettingsRequest = async (payload) => {
  const { data } = await api.put('/admin/settings', payload);
  return data;
};

export const updateAdminUserRole = async ({ userId, role }) => {
  if (!userId) throw new Error('Utilisateur requis');
  const { data } = await api.post(`/admin/users/${userId}/role`, { role });
  return data;
};

export const resetAdminUserPassword = async ({ userId, newPassword }) => {
  if (!userId) throw new Error('Utilisateur requis');
  const { data } = await api.post(`/admin/users/${userId}/reset-password`, {
    new_password: newPassword ?? null,
  });
  return data;
};

export const fetchRestaurantDashboard = async () => {
  const { data } = await api.get('/restaurant/dashboard/overview');
  return data;
};

export default api;
