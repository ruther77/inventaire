/**
 * Types TypeScript pour le mode offline
 *
 * Note: Ce fichier sert de documentation des types.
 * Le projet utilise JavaScript mais ces types peuvent être utiles
 * pour la migration vers TypeScript ou pour la documentation.
 */

// ============================================================================
// Hook useOffline
// ============================================================================

export interface UseOfflineReturn {
  /** true si l'utilisateur est en ligne */
  isOnline: boolean;
  /** true si l'utilisateur était hors ligne et vient de se reconnecter */
  wasOffline: boolean;
  /** Date de la dernière connexion en ligne */
  lastOnlineAt: Date | null;
  /** Date du début de la déconnexion */
  offlineSince: Date | null;
}

// ============================================================================
// Offline Context
// ============================================================================

export interface Mutation {
  /** ID de la mutation (auto-incrémenté) */
  id: number;
  /** Type de mutation */
  type: 'CREATE' | 'UPDATE' | 'DELETE';
  /** Endpoint API à appeler */
  endpoint: string;
  /** Méthode HTTP */
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** Données de la mutation */
  payload: unknown;
  /** Statut de la mutation */
  status: 'pending' | 'processing' | 'completed' | 'failed';
  /** Timestamp de création */
  timestamp: number;
  /** Date de création */
  createdAt: string;
  /** Nombre de tentatives */
  attempts: number;
  /** Timestamp de la dernière tentative */
  lastAttempt?: number;
  /** Message d'erreur si échec */
  error?: string;
  /** Métadonnées additionnelles */
  metadata?: MutationMetadata;
}

export interface MutationMetadata {
  /** Callback appelé en cas de succès */
  onSuccess?: (data: unknown) => void;
  /** Callback appelé en cas d'erreur */
  onError?: (error: Error) => void;
  /** Données additionnelles personnalisées */
  [key: string]: unknown;
}

export interface StorageStats {
  /** Nombre d'entrées en cache */
  cacheEntries: number;
  /** Nombre total de mutations */
  totalMutations: number;
  /** Nombre de mutations en attente */
  pendingMutations: number;
  /** Nombre de mutations terminées */
  completedMutations: number;
}

export interface OfflineContextValue {
  /** État de connexion */
  isOnline: boolean;
  /** true si vient de se reconnecter */
  wasOffline: boolean;
  /** Date de dernière connexion */
  lastOnlineAt: Date | null;
  /** Date du début de la déconnexion */
  offlineSince: Date | null;

  /** Liste des mutations en attente */
  pendingMutations: Mutation[];
  /** Ajouter une mutation à la queue */
  addPendingMutation: (mutation: Omit<Mutation, 'id' | 'status' | 'timestamp' | 'createdAt' | 'attempts'>) => Promise<number>;
  /** Synchroniser toutes les mutations en attente */
  syncPendingMutations: () => Promise<void>;
  /** true si synchronisation en cours */
  isSyncing: boolean;
  /** Message d'erreur de synchronisation */
  syncError: string | null;

  /** Statistiques de stockage */
  storageStats: StorageStats;
  /** Rafraîchir les statistiques */
  refreshStats: () => Promise<void>;
}

// ============================================================================
// Offline Storage
// ============================================================================

export interface CacheEntry<T = unknown> {
  /** Clé de cache */
  key: string;
  /** Données en cache */
  data: T;
  /** Timestamp de mise en cache */
  timestamp: number;
}

export interface MetadataEntry<T = unknown> {
  /** Clé de métadonnée */
  key: string;
  /** Valeur de la métadonnée */
  value: T;
  /** Timestamp de création */
  timestamp: number;
}

export type CacheKey =
  | 'products'
  | 'vendors'
  | 'categories'
  | 'finance_transactions'
  | 'finance_accounts'
  | 'restaurant_plats'
  | 'restaurant_ingredients'
  | 'cockpit_overview';

// ============================================================================
// Offline Mutation Hook
// ============================================================================

export interface UseOfflineMutationOptions<TData = unknown, TVariables = unknown> {
  /** Fonction de mutation */
  mutationFn: (variables: TVariables) => Promise<TData>;
  /** Endpoint API */
  endpoint: string;
  /** Méthode HTTP */
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** Type de mutation */
  mutationType?: 'CREATE' | 'UPDATE' | 'DELETE';
  /** Callback de succès */
  onSuccess?: (data: TData, variables: TVariables, context?: unknown) => void;
  /** Callback d'erreur */
  onError?: (error: Error, variables: TVariables, context?: unknown) => void;
  /** Métadonnées additionnelles */
  metadata?: Record<string, unknown>;
}

export interface MutationQueuedResponse {
  /** Indique si l'opération a réussi */
  success: boolean;
  /** Indique si la mutation est en queue */
  queued: true;
  /** Message informatif */
  message: string;
}

// ============================================================================
// API Responses
// ============================================================================

export interface ApiErrorResponse {
  /** Message d'erreur */
  message: string;
  /** Code d'erreur */
  code?: string;
  /** Détails additionnels */
  details?: unknown;
}

// ============================================================================
// React Query Extensions
// ============================================================================

export interface QueryRetryContext {
  /** Nombre de tentatives échouées */
  failureCount: number;
  /** Erreur de la tentative */
  error: Error;
}

export type NetworkMode = 'online' | 'always' | 'offlineFirst';

export interface QueryOptions {
  /** Mode réseau */
  networkMode?: NetworkMode;
  /** Stratégie de retry */
  retry?: boolean | number | ((failureCount: number, error: Error) => boolean);
  /** Délai entre les retries */
  retryDelay?: number | ((attemptIndex: number) => number);
  /** Rafraîchir à la reconnexion */
  refetchOnReconnect?: boolean;
  /** Durée de validité du cache */
  staleTime?: number;
  /** Durée de conservation du cache */
  gcTime?: number;
  /** Rafraîchir au focus de la fenêtre */
  refetchOnWindowFocus?: boolean;
}

export interface MutationOptions {
  /** Mode réseau */
  networkMode?: NetworkMode;
  /** Stratégie de retry */
  retry?: boolean | number | ((failureCount: number, error: Error) => boolean);
}
