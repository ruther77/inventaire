/**
 * Types pour les entités métier de l'application
 */

import type { ISODateString, Entity, Nullable } from './common.types';

// ============================================================================
// PRODUITS & CATALOGUE
// ============================================================================

export interface Product extends Entity {
  code: string;
  name: string;
  category: string;
  supplier: string;
  price: number;
  priceHT?: number;
  priceTTC?: number;
  margin?: number;
  marginPercent?: number;
  quantity?: number;
  stock?: number;
  stockQuantity?: number;
  unit?: string;
  barcode?: string;
  ean?: string;
  description?: string;
  image?: string;
  isActive?: boolean;
  tva?: number;
  minStock?: number;
  maxStock?: number;
  lastPurchasePrice?: number;
  lastPurchaseDate?: ISODateString;
}

export interface Category {
  id: number;
  name: string;
  slug?: string;
  description?: string;
  parentId?: number;
  color?: string;
  icon?: string;
}

export interface Vendor {
  id: number;
  name: string;
  code?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  zipCode?: string;
  country?: string;
  isActive?: boolean;
  paymentTerms?: number;
  notes?: string;
}

// ============================================================================
// INVENTAIRE & MOUVEMENTS
// ============================================================================

export type MovementType = 'ENTREE' | 'SORTIE' | 'AJUSTEMENT' | 'INVENTAIRE';

export interface Movement {
  id: number;
  productId: number;
  product?: Product;
  type: MovementType;
  quantity: number;
  date: ISODateString;
  username?: string;
  userId?: number;
  reason?: string;
  reference?: string;
  supplier?: string;
  cost?: number;
  notes?: string;
}

export interface InventorySummary {
  totalProducts: number;
  totalValue: number;
  totalValueHT?: number;
  totalValueTTC?: number;
  lowStockProducts: number;
  outOfStockProducts: number;
  categories?: Record<string, number>;
  lastUpdate?: ISODateString;
}

export interface StockLevel {
  productId: number;
  product?: Product;
  quantity: number;
  minStock: number;
  maxStock: number;
  status: 'ok' | 'low' | 'out' | 'overstock';
  daysRemaining?: number;
  reorderPoint?: number;
  safetyStock?: number;
}

// ============================================================================
// FACTURES & IMPORTS
// ============================================================================

export interface InvoiceLine {
  lineNumber?: number;
  code?: string;
  name: string;
  quantity: number;
  unit?: string;
  priceHT: number;
  priceTTC?: number;
  tva?: number;
  totalHT?: number;
  totalTTC?: number;
  productId?: number;
  matched?: boolean;
  confidence?: number;
  suggestions?: Product[];
}

export interface Invoice {
  id: string;
  invoiceNumber?: string;
  supplier: string;
  date: ISODateString;
  totalHT: number;
  totalTTC: number;
  tva: number;
  lines: InvoiceLine[];
  status?: 'pending' | 'imported' | 'validated' | 'error';
  filename?: string;
  notes?: string;
  username?: string;
}

export interface InvoiceImportResult {
  success: boolean;
  message?: string;
  created?: number;
  updated?: number;
  errors?: string[];
  invoice?: Invoice;
}

// ============================================================================
// RESTAURANT & FOOD COST
// ============================================================================

export interface Ingredient {
  id: number;
  name: string;
  code?: string;
  productId?: number;
  product?: Product;
  unitPrice: number;
  unit: string;
  category?: string;
  supplier?: string;
  lastUpdate?: ISODateString;
}

export interface PlatIngredient {
  ingredientId: number;
  ingredient?: Ingredient;
  name: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  totalCost: number;
  costPercentage?: number;
}

export interface Plat {
  id: number;
  name: string;
  nom?: string;
  category?: string;
  categorie?: string;
  prixVenteTTC: number;
  prix_vente_ttc?: number;
  coutMatiere: number;
  cout_matiere?: number;
  margePct: number;
  marge_pct?: number;
  foodCostPct: number;
  food_cost_pct?: number;
  margeBrute?: number;
  ingredients?: PlatIngredient[];
  isActive?: boolean;
  description?: string;
  image?: string;
}

export interface RestaurantSales {
  date: ISODateString;
  revenue: number;
  orders: number;
  averageTicket: number;
  topPlats?: Array<{
    platId: number;
    name: string;
    quantity: number;
    revenue: number;
  }>;
}

export interface FoodCostAnalysis {
  period: string;
  actualFoodCostPct: number;
  targetFoodCostPct: number;
  variance: number;
  totalRevenue: number;
  totalCost: number;
  platsAnalysis?: Array<{
    platId: number;
    name: string;
    foodCostPct: number;
    quantity: number;
    impact: number;
  }>;
}

// ============================================================================
// FINANCE & TRANSACTIONS
// ============================================================================

export interface FinanceAccount {
  id: number;
  entityId: number;
  name: string;
  type: 'bank' | 'cash' | 'credit' | 'other';
  accountNumber?: string;
  bankName?: string;
  balance: number;
  currency?: string;
  isActive: boolean;
  iban?: string;
  bic?: string;
}

export interface FinanceCategory {
  id: number;
  entityId?: number;
  name: string;
  type: 'income' | 'expense' | 'transfer';
  code?: string;
  description?: string;
  parentId?: number;
  color?: string;
  icon?: string;
  isSystem?: boolean;
}

export interface FinanceTransaction {
  id: number;
  entityId: number;
  accountId: number;
  account?: FinanceAccount;
  categoryId?: number;
  category?: FinanceCategory;
  dateOperation: ISODateString;
  date_operation?: ISODateString;
  dateValeur?: ISODateString;
  date_valeur?: ISODateString;
  description: string;
  amount: number;
  balance?: number;
  type?: 'debit' | 'credit';
  reference?: string;
  supplier?: string;
  notes?: string;
  tags?: string[];
  isReconciled?: boolean;
  reconciliationId?: number;
}

export interface FinanceRule {
  id: number;
  entityId?: number;
  name: string;
  pattern: string;
  categoryId: number;
  category?: FinanceCategory;
  priority?: number;
  isActive: boolean;
  matchType?: 'contains' | 'startsWith' | 'endsWith' | 'exact' | 'regex';
  conditions?: Record<string, unknown>;
}

export interface FinanceDashboard {
  income: number;
  expenses: number;
  balance: number;
  period: string;
  incomeByCategory?: Record<string, number>;
  expensesByCategory?: Record<string, number>;
  trends?: {
    income: number;
    expenses: number;
  };
}

// ============================================================================
// SUPPLIER SCORING
// ============================================================================

export interface SupplierScore {
  supplierId: number | string;
  supplierName: string;
  score: number;
  trend: 'up' | 'down' | 'stable';
  dimensions: {
    reliability?: number;
    quality?: number;
    pricing?: number;
    delivery?: number;
    service?: number;
  };
  metrics?: {
    totalOrders?: number;
    onTimeDeliveryRate?: number;
    averageQuality?: number;
    priceVariance?: number;
  };
  alerts?: Array<{
    type: string;
    severity: 'low' | 'medium' | 'high';
    message: string;
  }>;
  lastUpdate?: ISODateString;
}

export interface SupplierScoreHistory {
  date: ISODateString;
  score: number;
  dimensions: Record<string, number>;
}

// ============================================================================
// COCKPIT & KPIS
// ============================================================================

export interface KPI {
  id: string;
  label: string;
  value: number;
  unit?: string;
  trend?: number;
  previousValue?: number;
  change?: number;
  changePercent?: number;
  status?: 'good' | 'warning' | 'critical';
  target?: number;
  icon?: string;
  color?: string;
}

export interface CockpitAlert {
  id: number | string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  title: string;
  message: string;
  timestamp: ISODateString;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: ISODateString;
  entityId?: number;
  entityType?: string;
  actions?: Array<{
    label: string;
    action: string;
  }>;
}

// ============================================================================
// AUDIT & HISTORIQUE
// ============================================================================

export interface AuditEntry {
  id: number;
  timestamp: ISODateString;
  userId: number;
  username?: string;
  action: string;
  entity: string;
  entityId: number | string;
  changes?: Record<string, unknown>;
  oldValue?: unknown;
  newValue?: unknown;
  ip?: string;
  userAgent?: string;
  severity?: 'info' | 'warning' | 'error' | 'critical';
}

// ============================================================================
// UTILISATEURS & AUTH
// ============================================================================

export interface User {
  id: number;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  fullName?: string;
  role?: string;
  permissions?: string[];
  isActive?: boolean;
  lastLogin?: ISODateString;
  avatar?: string;
}

export interface AuthState {
  user: Nullable<User>;
  token: Nullable<string>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  user: User;
  expiresIn?: number;
}

// ============================================================================
// TENANT & MULTI-ENTITÉS
// ============================================================================

export interface Tenant {
  id: number;
  name: string;
  slug?: string;
  type?: 'restaurant' | 'epicerie' | 'other';
  settings?: Record<string, unknown>;
  isActive?: boolean;
}
