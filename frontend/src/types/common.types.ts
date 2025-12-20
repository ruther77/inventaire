/**
 * Types utilitaires communs utilisés dans l'application
 */

// Types de base
export type UUID = string;
export type ISODateString = string;
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

// Types pour les réponses paginées
export interface PaginationParams {
  page?: number;
  size?: number;
  perPage?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages?: number;
  hasMore?: boolean;
}

// Types pour les filtres de date
export interface DateRangeFilter {
  dateFrom?: ISODateString;
  dateTo?: ISODateString;
  startDate?: ISODateString;
  endDate?: ISODateString;
}

// Types pour les réponses API standard
export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  error?: string;
  meta?: Record<string, unknown>;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

// Types pour les statuts
export type Status = 'pending' | 'success' | 'error' | 'idle';
export type Severity = 'low' | 'medium' | 'high' | 'critical';

// Types pour les tris
export type SortOrder = 'asc' | 'desc';

export interface SortParams {
  sortBy?: string;
  sortOrder?: SortOrder;
  sort?: string;
}

// Types pour la recherche
export interface SearchParams {
  q?: string;
  search?: string;
}

// Types pour les entités avec ID
export interface Entity {
  id: number | string;
  createdAt?: ISODateString;
  updatedAt?: ISODateString;
}

// Types pour les filtres génériques
export type FilterValue = string | number | boolean | string[] | number[] | null | undefined;

export interface Filters extends Record<string, FilterValue> {
  entityId?: number;
}

// Types pour les sélections
export interface SelectOption<T = string | number> {
  value: T;
  label: string;
  disabled?: boolean;
}

// Types pour les statistiques
export interface Metric {
  value: number;
  label: string;
  trend?: number;
  previousValue?: number;
  unit?: string;
}

// Types pour les alertes/notifications
export interface Alert {
  id: number | string;
  type: 'info' | 'warning' | 'error' | 'success';
  severity?: Severity;
  message: string;
  timestamp: ISODateString;
  acknowledged?: boolean;
}

// Types pour les opérations asynchrones
export interface AsyncState<T> {
  data: Nullable<T>;
  isLoading: boolean;
  isError: boolean;
  error: Nullable<Error | ApiError>;
}

// Types pour les événements
export type EventHandler<T = void> = (data: T) => void | Promise<void>;

// Types pour les formulaires
export type FormStatus = 'idle' | 'submitting' | 'success' | 'error';

export interface FormState<T = unknown> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  status: FormStatus;
}

// Types pour les permissions
export type Permission = 'read' | 'write' | 'delete' | 'admin';

export interface PermissionSet {
  [resource: string]: Permission[];
}

// Helper types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OmitStrict<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
