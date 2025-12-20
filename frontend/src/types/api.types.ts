/**
 * Types pour les réponses API et paramètres de requêtes
 */

import type {
  PaginatedResponse,
  DateRangeFilter,
  PaginationParams,
  SortParams,
  SearchParams,
  Filters,
} from './common.types';

import type {
  Product,
  Category,
  Vendor,
  Movement,
  InventorySummary,
  Invoice,
  InvoiceLine,
  InvoiceImportResult,
  Plat,
  Ingredient,
  RestaurantSales,
  FoodCostAnalysis,
  FinanceAccount,
  FinanceCategory,
  FinanceTransaction,
  FinanceRule,
  FinanceDashboard,
  SupplierScore,
  SupplierScoreHistory,
  KPI,
  CockpitAlert,
  AuditEntry,
  User,
  LoginResponse,
} from './models.types';

// ============================================================================
// PRODUITS & CATALOGUE
// ============================================================================

export interface FetchProductsParams extends SearchParams, PaginationParams, SortParams {
  category?: string;
  categories?: string[];
  supplier?: string;
  minPrice?: number;
  maxPrice?: number;
  inStock?: boolean;
  isActive?: boolean;
}

export type FetchProductsResponse = PaginatedResponse<Product>;

export interface CreateProductPayload {
  code: string;
  name: string;
  category: string;
  supplier?: string;
  price: number;
  quantity?: number;
  unit?: string;
  barcode?: string;
  tva?: number;
  minStock?: number;
  maxStock?: number;
}

export interface UpdateProductPayload extends Partial<CreateProductPayload> {
  id: number;
}

// ============================================================================
// INVENTAIRE
// ============================================================================

export type FetchInventorySummaryResponse = InventorySummary;

export interface SupplyPlanFilters extends SearchParams {
  targetCoverage?: number;
  alertThreshold?: number;
  minDailySales?: number;
  categories?: string[];
}

export interface SupplyPlanItem {
  productId: number;
  product: Product;
  currentStock: number;
  dailySales: number;
  daysRemaining: number;
  recommendedOrder: number;
  coverage: number;
  status: 'ok' | 'low' | 'critical';
}

export type FetchSupplyPlanResponse = SupplyPlanItem[];

// ============================================================================
// FACTURES
// ============================================================================

export interface ExtractInvoiceFromTextPayload {
  text: string;
  marginPercent?: number;
  supplierHint?: string;
}

export interface ExtractInvoiceFromFilePayload {
  file: File;
  marginPercent?: number;
  supplierHint?: string;
}

export interface ExtractInvoiceResponse {
  success: boolean;
  lines: InvoiceLine[];
  supplier?: string;
  invoiceNumber?: string;
  date?: string;
  totalHT?: number;
  totalTTC?: number;
  confidence?: number;
}

export interface ImportInvoicePayload {
  lines: InvoiceLine[];
  supplier: string;
  movementType: 'ENTREE' | 'SORTIE' | 'AJUSTEMENT';
  username: string;
  invoiceDate?: string;
}

export type ImportInvoiceResponse = InvoiceImportResult;

export interface FetchInvoiceHistoryFilters extends DateRangeFilter, PaginationParams {
  supplier?: string;
  invoiceId?: string;
}

export type FetchInvoiceHistoryResponse = Invoice[];

// ============================================================================
// RESTAURANT
// ============================================================================

export interface FetchRestaurantOverviewFilters extends DateRangeFilter {
  entityId?: number;
}

export interface RestaurantOverview {
  revenue: number;
  orders: number;
  averageTicket: number;
  foodCostPct: number;
  topPlats: Array<{
    platId: number;
    name: string;
    quantity: number;
    revenue: number;
  }>;
  alerts?: CockpitAlert[];
}

export type FetchRestaurantOverviewResponse = RestaurantOverview;

export interface FetchPlatDetailsResponse extends Plat {
  ingredients: Array<{
    ingredientId: number;
    name: string;
    quantity: number;
    unit: string;
    unitPrice: number;
    totalCost: number;
    costPercentage: number;
  }>;
}

export interface SimulatePlatPricePayload {
  prixVenteTTC?: number;
  ingredients?: Array<{
    ingredientId: number;
    quantity: number;
  }>;
}

export interface SimulatePlatPriceResponse {
  coutMatiere: number;
  margePct: number;
  foodCostPct: number;
  margeBrute: number;
}

export interface FetchFoodCostAnalysisFilters extends DateRangeFilter {
  period?: 'day' | 'week' | 'month' | 'year';
  targetFoodCost?: number;
}

export type FetchFoodCostAnalysisResponse = FoodCostAnalysis;

// ============================================================================
// FINANCE
// ============================================================================

export interface SearchFinanceTransactionsFilters extends DateRangeFilter, PaginationParams, SortParams, SearchParams {
  entityId?: number;
  accountId?: number;
  categoryId?: number;
  amountMin?: number;
  amountMax?: number;
}

export type SearchFinanceTransactionsResponse = PaginatedResponse<FinanceTransaction>;

export interface FetchFinanceAccountsFilters extends Filters {
  isActive?: boolean;
}

export type FetchFinanceAccountsResponse = FinanceAccount[];

export interface CreateFinanceAccountPayload {
  entityId: number;
  name: string;
  type: 'bank' | 'cash' | 'credit' | 'other';
  accountNumber?: string;
  bankName?: string;
  balance?: number;
  currency?: string;
  iban?: string;
  bic?: string;
}

export interface UpdateFinanceAccountPayload extends Partial<CreateFinanceAccountPayload> {
  accountId: number;
}

export interface FetchFinanceCategoriesFilters extends Filters {
  type?: 'income' | 'expense' | 'transfer';
}

export type FetchFinanceCategoriesResponse = FinanceCategory[];

export interface CreateFinanceCategoryPayload {
  entityId?: number;
  name: string;
  type: 'income' | 'expense' | 'transfer';
  code?: string;
  description?: string;
  parentId?: number;
  color?: string;
  icon?: string;
}

export interface BatchCategorizeTransactionsPayload {
  transactionIds: number[];
  categoryId: number;
}

export interface ImportBankStatementsPayload {
  accountId: number;
  file: File;
}

export interface ImportBankStatementsResponse {
  success: boolean;
  imported: number;
  duplicates: number;
  errors?: string[];
}

export interface FetchFinanceDashboardFilters extends DateRangeFilter, Filters {}

export type FetchFinanceDashboardResponse = FinanceDashboard;

export interface FetchFinanceRulesFilters extends Filters {
  isActive?: boolean;
}

export type FetchFinanceRulesResponse = FinanceRule[];

export interface CreateFinanceRulePayload {
  entityId?: number;
  name: string;
  pattern: string;
  categoryId: number;
  priority?: number;
  matchType?: 'contains' | 'startsWith' | 'endsWith' | 'exact' | 'regex';
}

export interface UpdateFinanceRulePayload extends Partial<CreateFinanceRulePayload> {
  id: number;
}

// ============================================================================
// SUPPLIER SCORING
// ============================================================================

export interface FetchSupplierScoreParams {
  supplierName: string;
  periodDays?: number;
}

export type FetchSupplierScoreResponse = SupplierScore;

export type FetchSuppliersRankingResponse = SupplierScore[];

export interface CompareSuppliersPayload {
  suppliers: string[];
}

export type CompareSuppliersResponse = SupplierScore[];

export interface FetchSupplierScoreHistoryParams {
  supplierName: string;
  limit?: number;
}

export type FetchSupplierScoreHistoryResponse = SupplierScoreHistory[];

export interface FetchSupplierScoringOverviewResponse {
  averageScore: number;
  totalSuppliers: number;
  topSuppliers: SupplierScore[];
  alerts: CockpitAlert[];
  trends: {
    score: number;
    reliability: number;
  };
}

export interface FetchSuppliersListParams extends PaginationParams, SortParams, SearchParams {
  minScore?: number;
  maxScore?: number;
  trend?: 'up' | 'down' | 'stable';
}

export type FetchSuppliersListResponse = PaginatedResponse<SupplierScore>;

export interface FetchSupplierDetailsResponse extends SupplierScore {
  contact?: {
    email?: string;
    phone?: string;
    address?: string;
  };
  recentOrders?: Array<{
    date: string;
    amount: number;
    status: string;
  }>;
  performance: {
    onTimeDeliveryRate: number;
    qualityScore: number;
    averageLeadTime: number;
  };
}

export interface RecalculateSupplierScoresPayload {
  supplierIds?: number[];
  forceRecalculate?: boolean;
}

export interface RecalculateSupplierScoresResponse {
  success: boolean;
  recalculated: number;
  errors?: string[];
}

// ============================================================================
// COCKPIT
// ============================================================================

export interface FetchCockpitOverviewResponse {
  kpis: KPI[];
  alerts: CockpitAlert[];
  summary: {
    revenue: number;
    expenses: number;
    profit: number;
    stockValue: number;
  };
  trends: {
    revenue: number;
    profit: number;
  };
}

export interface FetchCockpitAlertsFilters extends PaginationParams {
  severity?: 'low' | 'medium' | 'high' | 'critical';
  category?: string;
}

export type FetchCockpitAlertsResponse = CockpitAlert[];

// ============================================================================
// AUDIT TRAIL
// ============================================================================

export interface FetchAuditEntriesFilters extends DateRangeFilter, PaginationParams, SearchParams {
  action?: string;
  entity?: string;
  entityId?: number | string;
  userId?: number;
  severity?: 'info' | 'warning' | 'error' | 'critical';
}

export type FetchAuditEntriesResponse = PaginatedResponse<AuditEntry>;

// ============================================================================
// AUTH
// ============================================================================

export interface LoginPayload {
  username: string;
  password: string;
}

export type LoginApiResponse = LoginResponse;

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export type RegisterApiResponse = LoginResponse;

export interface RefreshTokenResponse {
  accessToken: string;
  expiresIn: number;
}
