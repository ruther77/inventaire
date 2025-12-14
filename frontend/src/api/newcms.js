import api from './client.js';

// Cockpit
export const fetchCockpitOverview = async (params = {}) => {
  const { data } = await api.get('/newcms/cockpit', { params });
  return data;
};

export const fetchCockpitActions = async (params = {}) => {
  const { data } = await api.get('/newcms/cockpit/actions', { params });
  return data;
};

// Opérations
export const fetchOperationsOverview = async (params = {}) => {
  const { data } = await api.get('/newcms/operations/overview', { params });
  return data;
};

export const fetchOperationsCatalog = async (params = {}) => {
  const { data } = await api.get('/newcms/operations/catalog', { params });
  return data;
};

export const fetchOperationsStock = async (params = {}) => {
  const { data } = await api.get('/newcms/operations/stock', { params });
  return data;
};

export const fetchOperationsInvoices = async (params = {}) => {
  const { data } = await api.get('/newcms/operations/invoices', { params });
  return data;
};

// Finance
export const fetchFinanceOverview = async (params = {}) => {
  const { data } = await api.get('/newcms/finance/overview', { params });
  return data;
};

export const fetchFinanceTransactions = async (params = {}) => {
  const { data } = await api.get('/newcms/finance/transactions', { params });
  return data;
};

export const fetchFinanceRules = async () => {
  const { data } = await api.get('/newcms/finance/rules');
  return data;
};

export const fetchFinanceAccounts = async () => {
  const { data } = await api.get('/newcms/finance/accounts');
  return data;
};

export const fetchFinanceCategories = async () => {
  const { data } = await api.get('/newcms/finance/categories');
  return data;
};

// Restaurant
export const fetchRestaurantOverviewNewCMS = async (params = {}) => {
  const { data } = await api.get('/newcms/restaurant/overview', { params });
  return data;
};

export const fetchRestaurantMenusOverview = async () => {
  const { data } = await api.get('/newcms/restaurant/menus/overview');
  return data;
};

export const fetchRestaurantPlatDetail = async (platId) => {
  const { data } = await api.get(`/newcms/restaurant/plat/${platId}`);
  return data;
};

// Intelligence
export const fetchIntelligenceOverview = async () => {
  const { data } = await api.get('/newcms/intelligence/overview');
  return data;
};

export const fetchIntelligenceRecommendations = async (params = {}) => {
  const { data } = await api.get('/newcms/intelligence/recommendations', { params });
  return data;
};

export const fetchIntelligenceHealthScore = async () => {
  const { data } = await api.get('/newcms/intelligence/health-score');
  return data;
};

export const fetchIntelligenceMetricsSummary = async () => {
  const { data } = await api.get('/newcms/intelligence/metrics/summary');
  return data;
};

// Mobile
export const fetchMobileInventory = async (params = {}) => {
  const { data } = await api.get('/newcms/mobile/inventory', { params });
  return data;
};

// Alerts placeholder (si backend expose un endpoint dédié, on l’utilisera)
export const fetchNewCMSAlerts = async () => {
  const { data } = await api.get('/newcms/cockpit/actions', { params: { category: 'urgent' } });
  return data;
};

export default {
  fetchCockpitOverview,
  fetchCockpitActions,
  fetchOperationsOverview,
  fetchOperationsCatalog,
  fetchOperationsStock,
  fetchOperationsInvoices,
  fetchFinanceOverview,
  fetchFinanceTransactions,
  fetchFinanceRules,
  fetchFinanceAccounts,
  fetchFinanceCategories,
  fetchRestaurantOverviewNewCMS,
  fetchRestaurantMenusOverview,
  fetchRestaurantPlatDetail,
  fetchIntelligenceOverview,
  fetchIntelligenceRecommendations,
  fetchIntelligenceHealthScore,
  fetchIntelligenceMetricsSummary,
  fetchMobileInventory,
  fetchNewCMSAlerts,
};
