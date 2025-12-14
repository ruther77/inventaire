/**
 * useQueryConfig - Configuration TanStack Query avec retry intelligent et offline support
 *
 * Phase 1 - Consolidation UX
 *
 * Features:
 * - Retry exponentiel automatique
 * - Détection offline/online
 * - Configuration par défaut optimisée
 * - États d'erreur récupérables
 */

import { useCallback, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Configuration par défaut pour les queries
 */
export const defaultQueryConfig = {
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 30 * 60 * 1000, // 30 minutes (anciennement cacheTime)
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  refetchOnWindowFocus: false,
  refetchOnReconnect: true,
};

/**
 * Configuration pour les mutations
 */
export const defaultMutationConfig = {
  retry: 1,
  retryDelay: 1000,
};

/**
 * Détecte le type d'erreur pour adapter le comportement
 */
export function getErrorType(error) {
  if (!error) return 'unknown';

  const message = error.message?.toLowerCase() || '';
  const status = error.response?.status || error.status;

  if (!navigator.onLine || message.includes('network') || message.includes('fetch failed')) {
    return 'network';
  }
  if (message.includes('timeout')) return 'timeout';
  if (status === 401) return 'auth';
  if (status === 403) return 'permission';
  if (status === 404) return 'not_found';
  if (status === 422 || status === 400) return 'validation';
  if (status >= 500) return 'server';

  return 'unknown';
}

/**
 * Détermine si l'erreur est récupérable (peut être retryée)
 */
export function isRetryableError(error) {
  const type = getErrorType(error);
  return ['network', 'timeout', 'server', 'unknown'].includes(type);
}

/**
 * Hook pour gérer l'état online/offline
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

/**
 * Hook pour invalider et refetch les queries après reconnexion
 */
export function useRefetchOnReconnect(queryKeys = []) {
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    if (!isOnline) {
      setWasOffline(true);
    } else if (wasOffline) {
      // Reconnexion détectée, refetch les queries spécifiées
      queryKeys.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key });
      });
      setWasOffline(false);
    }
  }, [isOnline, wasOffline, queryClient, queryKeys]);

  return { isOnline, wasOffline };
}

/**
 * Hook pour la gestion manuelle des retry avec backoff
 */
export function useManualRetry(onRetry, maxRetries = 3) {
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  const retry = useCallback(async () => {
    if (isRetrying || retryCount >= maxRetries) return false;

    setIsRetrying(true);
    try {
      await onRetry();
      setRetryCount(0);
      return true;
    } catch {
      setRetryCount((prev) => prev + 1);
      return false;
    } finally {
      setIsRetrying(false);
    }
  }, [onRetry, isRetrying, retryCount, maxRetries]);

  const reset = useCallback(() => {
    setRetryCount(0);
    setIsRetrying(false);
  }, []);

  return {
    retry,
    reset,
    retryCount,
    isRetrying,
    canRetry: retryCount < maxRetries,
    retriesLeft: maxRetries - retryCount,
  };
}

/**
 * Configuration query avec options de retry personnalisées
 */
export function createQueryOptions(options = {}) {
  const {
    enableRetry = true,
    retryOnNetworkError = true,
    retryOnServerError = true,
    maxRetries = 3,
    ...rest
  } = options;

  return {
    ...defaultQueryConfig,
    retry: enableRetry
      ? (failureCount, error) => {
          if (failureCount >= maxRetries) return false;

          const errorType = getErrorType(error);

          // Ne pas retry les erreurs d'auth ou de permission
          if (['auth', 'permission', 'not_found', 'validation'].includes(errorType)) {
            return false;
          }

          // Retry les erreurs réseau si activé
          if (errorType === 'network' && !retryOnNetworkError) {
            return false;
          }

          // Retry les erreurs serveur si activé
          if (errorType === 'server' && !retryOnServerError) {
            return false;
          }

          return true;
        }
      : false,
    ...rest,
  };
}

/**
 * Messages d'erreur par type
 */
export const errorMessages = {
  network: {
    title: 'Connexion impossible',
    description: 'Vérifiez votre connexion internet et réessayez.',
    canRetry: true,
  },
  timeout: {
    title: 'Délai dépassé',
    description: 'Le serveur met trop de temps à répondre.',
    canRetry: true,
  },
  auth: {
    title: 'Session expirée',
    description: 'Veuillez vous reconnecter.',
    canRetry: false,
    action: { label: 'Se reconnecter', href: '/login' },
  },
  permission: {
    title: 'Accès refusé',
    description: 'Vous n\'avez pas les droits nécessaires.',
    canRetry: false,
  },
  not_found: {
    title: 'Introuvable',
    description: 'La ressource demandée n\'existe pas.',
    canRetry: false,
  },
  validation: {
    title: 'Données invalides',
    description: 'Vérifiez les informations saisies.',
    canRetry: false,
  },
  server: {
    title: 'Erreur serveur',
    description: 'Un problème est survenu. Veuillez réessayer.',
    canRetry: true,
  },
  unknown: {
    title: 'Une erreur est survenue',
    description: 'Veuillez réessayer ou contacter le support.',
    canRetry: true,
  },
};

/**
 * Hook pour obtenir le message d'erreur approprié
 */
export function useErrorMessage(error) {
  const errorType = getErrorType(error);
  return errorMessages[errorType] || errorMessages.unknown;
}

export default {
  defaultQueryConfig,
  defaultMutationConfig,
  getErrorType,
  isRetryableError,
  useOnlineStatus,
  useRefetchOnReconnect,
  useManualRetry,
  createQueryOptions,
  errorMessages,
  useErrorMessage,
};
