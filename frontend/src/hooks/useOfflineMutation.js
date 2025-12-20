import { useMutation } from '@tanstack/react-query';
import { useOfflineContext } from '../contexts/OfflineContext.jsx';

/**
 * Hook personnalisé pour gérer les mutations avec support offline
 *
 * Similaire à useMutation de React Query, mais avec gestion automatique
 * de la queue offline quand la connexion est perdue.
 *
 * @param {Object} options - Options de mutation
 * @param {Function} options.mutationFn - Fonction de mutation
 * @param {string} options.endpoint - Endpoint API
 * @param {string} options.method - Méthode HTTP (POST, PUT, PATCH, DELETE)
 * @param {string} options.mutationType - Type de mutation (CREATE, UPDATE, DELETE)
 * @param {Function} options.onSuccess - Callback de succès
 * @param {Function} options.onError - Callback d'erreur
 * @param {Object} options.metadata - Métadonnées additionnelles
 *
 * @example
 * const createProduct = useOfflineMutation({
 *   mutationFn: (data) => api.post('/products', data),
 *   endpoint: '/products',
 *   method: 'POST',
 *   mutationType: 'CREATE',
 *   onSuccess: () => {
 *     queryClient.invalidateQueries(['products']);
 *   },
 * });
 */
export function useOfflineMutation({
  mutationFn,
  endpoint,
  method = 'POST',
  mutationType = 'CREATE',
  onSuccess,
  onError,
  metadata = {},
  ...reactQueryOptions
}) {
  const { isOnline, addPendingMutation } = useOfflineContext();

  return useMutation({
    mutationFn: async (variables) => {
      // Si online, exécuter normalement
      if (isOnline) {
        return await mutationFn(variables);
      }

      // Si offline, ajouter à la queue
      console.log(`[Offline] Ajout de la mutation ${mutationType} à la queue`);

      // Résoudre l'endpoint si c'est une fonction
      const resolvedEndpoint = typeof endpoint === 'function'
        ? endpoint(variables)
        : endpoint;

      await addPendingMutation({
        type: mutationType,
        endpoint: resolvedEndpoint,
        method,
        payload: variables,
        metadata: {
          ...metadata,
          onSuccess,
          onError,
        },
      });

      // Retourner une réponse optimiste
      return {
        success: true,
        queued: true,
        message: 'Modification enregistrée. Sera synchronisée quand la connexion sera rétablie.',
      };
    },
    onSuccess: (data, variables, context) => {
      // Appeler le callback de succès uniquement si pas en queue
      if (!data?.queued && onSuccess) {
        onSuccess(data, variables, context);
      }

      // Si en queue, afficher un message informatif
      if (data?.queued) {
        console.log('[Offline] Mutation ajoutée à la queue avec succès');
      }
    },
    onError: (error, variables, context) => {
      // Appeler le callback d'erreur
      if (onError) {
        onError(error, variables, context);
      }

      console.error('[Mutation] Erreur:', error);
    },
    ...reactQueryOptions,
  });
}

/**
 * Hook pour créer une mutation offline-aware pour les créations
 */
export function useOfflineCreate({ endpoint, mutationFn, ...options }) {
  return useOfflineMutation({
    endpoint,
    method: 'POST',
    mutationType: 'CREATE',
    mutationFn,
    ...options,
  });
}

/**
 * Hook pour créer une mutation offline-aware pour les mises à jour
 */
export function useOfflineUpdate({ endpoint, mutationFn, ...options }) {
  return useOfflineMutation({
    endpoint,
    method: 'PUT',
    mutationType: 'UPDATE',
    mutationFn,
    ...options,
  });
}

/**
 * Hook pour créer une mutation offline-aware pour les modifications partielles
 */
export function useOfflinePatch({ endpoint, mutationFn, ...options }) {
  return useOfflineMutation({
    endpoint,
    method: 'PATCH',
    mutationType: 'UPDATE',
    mutationFn,
    ...options,
  });
}

/**
 * Hook pour créer une mutation offline-aware pour les suppressions
 */
export function useOfflineDelete({ endpoint, mutationFn, ...options }) {
  return useOfflineMutation({
    endpoint,
    method: 'DELETE',
    mutationType: 'DELETE',
    mutationFn,
    ...options,
  });
}
