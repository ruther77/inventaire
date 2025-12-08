import { useCallback, useRef, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

/**
 * usePrefetch - Hook pour précharger des données au survol
 *
 * @param {string[]} queryKey - Clé de la query React Query
 * @param {Function} queryFn - Fonction de fetch
 * @param {Object} options - Options
 * @returns {{ onMouseEnter: Function, onFocus: Function }}
 */
export default function usePrefetch(queryKey, queryFn, options = {}) {
  const queryClient = useQueryClient();
  const timeoutRef = useRef(null);
  const {
    delay = 100, // Délai avant prefetch (évite les survols accidentels)
    staleTime = 60000, // Durée de validité du cache
    enabled = true,
  } = options;

  const prefetch = useCallback(() => {
    if (!enabled) return;

    queryClient.prefetchQuery({
      queryKey,
      queryFn,
      staleTime,
    });
  }, [queryClient, queryKey, queryFn, staleTime, enabled]);

  const handleMouseEnter = useCallback(() => {
    if (delay > 0) {
      timeoutRef.current = setTimeout(prefetch, delay);
    } else {
      prefetch();
    }
  }, [prefetch, delay]);

  const handleMouseLeave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
    onFocus: prefetch, // Prefetch aussi au focus (accessibilité)
    prefetch, // Exposer pour usage manuel
  };
}

/**
 * usePrefetchOnIdle - Précharge des données pendant les temps morts
 *
 * @param {Array<{ queryKey: string[], queryFn: Function }>} queries
 */
export function usePrefetchOnIdle(queries) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!queries?.length) return;

    // Utiliser requestIdleCallback si disponible
    const schedulePreload = (callback) => {
      if ('requestIdleCallback' in window) {
        return window.requestIdleCallback(callback, { timeout: 2000 });
      }
      return setTimeout(callback, 1000);
    };

    const cancelPreload = (id) => {
      if ('cancelIdleCallback' in window) {
        window.cancelIdleCallback(id);
      } else {
        clearTimeout(id);
      }
    };

    const ids = [];

    queries.forEach((query, index) => {
      // Échelonner les prefetch pour ne pas surcharger
      const id = schedulePreload(() => {
        queryClient.prefetchQuery({
          queryKey: query.queryKey,
          queryFn: query.queryFn,
          staleTime: query.staleTime || 60000,
        });
      });
      ids.push(id);
    });

    return () => {
      ids.forEach(cancelPreload);
    };
  }, [queries, queryClient]);
}

/**
 * usePrefetchRoute - Précharge les données d'une route au survol du lien
 *
 * @param {string} route - Route cible
 * @param {Function} prefetchFn - Fonction qui déclenche les prefetch nécessaires
 */
export function usePrefetchRoute(route, prefetchFn) {
  const hasPreloaded = useRef(false);

  const handleInteraction = useCallback(() => {
    if (hasPreloaded.current) return;
    hasPreloaded.current = true;
    prefetchFn();
  }, [prefetchFn]);

  return {
    onMouseEnter: handleInteraction,
    onFocus: handleInteraction,
  };
}

/**
 * PrefetchLink - Composant Link avec prefetch intégré
 */
export function createPrefetchLink(queryClient) {
  return function PrefetchLink({
    to,
    queries = [],
    delay = 100,
    children,
    ...props
  }) {
    const timeoutRef = useRef(null);

    const prefetch = () => {
      queries.forEach(({ queryKey, queryFn, staleTime = 60000 }) => {
        queryClient.prefetchQuery({ queryKey, queryFn, staleTime });
      });
    };

    const handleMouseEnter = () => {
      timeoutRef.current = setTimeout(prefetch, delay);
    };

    const handleMouseLeave = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };

    useEffect(() => {
      return () => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      };
    }, []);

    // Utiliser le composant Link de react-router-dom
    const { Link } = require('react-router-dom');

    return (
      <Link
        to={to}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={prefetch}
        {...props}
      >
        {children}
      </Link>
    );
  };
}

/**
 * useOptimisticUpdate - Hook pour les mises à jour optimistes
 *
 * @param {string[]} queryKey - Clé de la query à mettre à jour
 * @returns {{ updateOptimistically: Function, rollback: Function }}
 */
export function useOptimisticUpdate(queryKey) {
  const queryClient = useQueryClient();
  const previousDataRef = useRef(null);

  const updateOptimistically = useCallback(
    async (updateFn) => {
      // Annuler les queries en cours
      await queryClient.cancelQueries({ queryKey });

      // Sauvegarder l'état précédent
      previousDataRef.current = queryClient.getQueryData(queryKey);

      // Mettre à jour de manière optimiste
      queryClient.setQueryData(queryKey, (old) => {
        if (typeof updateFn === 'function') {
          return updateFn(old);
        }
        return updateFn;
      });

      return previousDataRef.current;
    },
    [queryClient, queryKey]
  );

  const rollback = useCallback(() => {
    if (previousDataRef.current !== null) {
      queryClient.setQueryData(queryKey, previousDataRef.current);
    }
  }, [queryClient, queryKey]);

  return { updateOptimistically, rollback };
}

/**
 * useInfiniteScroll - Hook pour le chargement infini
 *
 * @param {Object} options
 * @param {Function} options.onLoadMore - Fonction appelée pour charger plus
 * @param {boolean} options.hasMore - S'il y a plus de données
 * @param {boolean} options.isLoading - Si un chargement est en cours
 * @param {number} options.threshold - Distance en pixels avant de déclencher (défaut: 200)
 * @returns {React.RefObject} - Ref à attacher au conteneur scrollable
 */
export function useInfiniteScroll({
  onLoadMore,
  hasMore,
  isLoading,
  threshold = 200,
}) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      if (isLoading || !hasMore) return;

      const { scrollTop, scrollHeight, clientHeight } = container;
      const distanceToBottom = scrollHeight - scrollTop - clientHeight;

      if (distanceToBottom < threshold) {
        onLoadMore();
      }
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, [onLoadMore, hasMore, isLoading, threshold]);

  return containerRef;
}
