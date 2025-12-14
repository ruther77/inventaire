import { useCallback, useRef, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// Cache global pour prefetch sans React Query
const prefetchCache = new Map();
const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Vérifie si une entrée du cache est valide.
 */
function isCacheValid(entry) {
  if (!entry) return false;
  return Date.now() - entry.timestamp < entry.ttl;
}

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

/**
 * usePrefetchOnVisible - Prefetch basé sur viewport (Intersection Observer).
 */
export function usePrefetchOnVisible(queryKey, queryFn, options = {}) {
  const queryClient = useQueryClient();
  const { threshold = 0.1, rootMargin = '100px', once = true, staleTime = 60000 } = options;
  const elementRef = useRef(null);
  const hasPrefetchedRef = useRef(false);

  useEffect(() => {
    if (!elementRef.current || (once && hasPrefetchedRef.current)) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && !hasPrefetchedRef.current) {
          queryClient.prefetchQuery({ queryKey, queryFn, staleTime });
          hasPrefetchedRef.current = true;
          if (once) observer.disconnect();
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(elementRef.current);
    return () => observer.disconnect();
  }, [queryClient, queryKey, queryFn, once, rootMargin, threshold, staleTime]);

  return elementRef;
}

/**
 * useStandaloneCache - Cache sans React Query.
 */
export function useStandaloneCache(cacheKey, fetchFn, options = {}) {
  const { ttl = DEFAULT_TTL, enabled = true, staleWhileRevalidate = true } = options;
  const [data, setData] = useState(() => {
    const cached = prefetchCache.get(cacheKey);
    return isCacheValid(cached) ? cached.data : null;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(
    async (force = false) => {
      if (!enabled) return null;

      const cached = prefetchCache.get(cacheKey);
      if (!force && isCacheValid(cached)) {
        setData(cached.data);
        return cached.data;
      }

      if (staleWhileRevalidate && cached) {
        setData(cached.data);
      }

      setIsLoading(true);
      setError(null);

      try {
        const result = await fetchFn();
        prefetchCache.set(cacheKey, { data: result, timestamp: Date.now(), ttl });
        setData(result);
        return result;
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [cacheKey, enabled, fetchFn, staleWhileRevalidate, ttl]
  );

  useEffect(() => {
    if (enabled && !prefetchCache.has(cacheKey)) {
      fetchData();
    }
  }, [cacheKey, enabled, fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: () => fetchData(true),
    invalidate: () => {
      prefetchCache.delete(cacheKey);
      setData(null);
    },
  };
}

/**
 * cacheUtils - Utilitaires pour gestion manuelle du cache.
 */
export const cacheUtils = {
  get: (key) => {
    const entry = prefetchCache.get(key);
    return isCacheValid(entry) ? entry.data : null;
  },
  set: (key, data, ttl = DEFAULT_TTL) => {
    prefetchCache.set(key, { data, timestamp: Date.now(), ttl });
  },
  invalidate: (key) => prefetchCache.delete(key),
  invalidateAll: () => prefetchCache.clear(),
  invalidatePattern: (pattern) => {
    const regex = new RegExp(pattern);
    for (const key of prefetchCache.keys()) {
      if (regex.test(key)) prefetchCache.delete(key);
    }
  },
};
