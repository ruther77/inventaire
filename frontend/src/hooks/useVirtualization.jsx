/**
 * useVirtualization - Virtualisation de listes pour performance.
 *
 * Fonctionnalités:
 * - Rendu seulement des éléments visibles
 * - Support scroll infini
 * - Dynamic row heights
 * - Overscan configurable
 * - Scroll to item
 */

import { useState, useRef, useCallback, useEffect, useMemo } from 'react';

/**
 * Hook de virtualisation pour listes de taille fixe.
 */
export function useVirtualList(items, options = {}) {
  const {
    itemHeight = 50,
    overscan = 5,
    containerHeight,
  } = options;

  const containerRef = useRef(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [height, setHeight] = useState(containerHeight || 0);

  // Observer pour la taille du container
  useEffect(() => {
    if (containerHeight) {
      setHeight(containerHeight);
      return;
    }

    const container = containerRef.current;
    if (!container) return;

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setHeight(entry.contentRect.height);
      }
    });

    resizeObserver.observe(container);
    setHeight(container.clientHeight);

    return () => resizeObserver.disconnect();
  }, [containerHeight]);

  // Handler de scroll optimisé
  const handleScroll = useCallback((e) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  // Calcul des indices visibles
  const { startIndex, endIndex, virtualItems, totalHeight } = useMemo(() => {
    const totalHeight = items.length * itemHeight;
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const visibleCount = Math.ceil(height / itemHeight);
    const endIndex = Math.min(items.length - 1, startIndex + visibleCount + overscan * 2);

    const virtualItems = [];
    for (let i = startIndex; i <= endIndex; i++) {
      virtualItems.push({
        index: i,
        item: items[i],
        style: {
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: itemHeight,
          transform: `translateY(${i * itemHeight}px)`,
        },
      });
    }

    return { startIndex, endIndex, virtualItems, totalHeight };
  }, [items, itemHeight, scrollTop, height, overscan]);

  // Scroll to specific item
  const scrollToItem = useCallback(
    (index, behavior = 'smooth') => {
      const container = containerRef.current;
      if (!container) return;

      const targetScroll = index * itemHeight;
      container.scrollTo({ top: targetScroll, behavior });
    },
    [itemHeight]
  );

  // Scroll to top/bottom
  const scrollToTop = useCallback(() => {
    containerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const scrollToBottom = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  }, []);

  return {
    containerRef,
    virtualItems,
    totalHeight,
    startIndex,
    endIndex,
    scrollToItem,
    scrollToTop,
    scrollToBottom,
    containerProps: {
      ref: containerRef,
      onScroll: handleScroll,
      style: {
        overflow: 'auto',
        position: 'relative',
        height: containerHeight || '100%',
      },
    },
    innerProps: {
      style: {
        height: totalHeight,
        width: '100%',
        position: 'relative',
      },
    },
  };
}

/**
 * Hook de virtualisation pour hauteurs dynamiques.
 */
export function useDynamicVirtualList(items, options = {}) {
  const {
    estimatedItemHeight = 50,
    overscan = 5,
    containerHeight,
    getItemKey = (item, index) => index,
  } = options;

  const containerRef = useRef(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [height, setHeight] = useState(containerHeight || 400);
  const measuredHeights = useRef(new Map());
  const [, forceUpdate] = useState(0);

  // Handler de scroll
  const handleScroll = useCallback((e) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  // Mesurer un item
  const measureItem = useCallback((index, element) => {
    if (!element) return;
    const key = getItemKey(items[index], index);
    const currentHeight = measuredHeights.current.get(key);
    const newHeight = element.getBoundingClientRect().height;

    if (currentHeight !== newHeight) {
      measuredHeights.current.set(key, newHeight);
      forceUpdate((n) => n + 1);
    }
  }, [items, getItemKey]);

  // Calculer les positions
  const { virtualItems, totalHeight, startIndex, endIndex } = useMemo(() => {
    const positions = [];
    let currentTop = 0;

    // Calculer toutes les positions
    for (let i = 0; i < items.length; i++) {
      const key = getItemKey(items[i], i);
      const itemHeight = measuredHeights.current.get(key) || estimatedItemHeight;
      positions.push({
        index: i,
        top: currentTop,
        height: itemHeight,
      });
      currentTop += itemHeight;
    }

    const totalHeight = currentTop;

    // Trouver les items visibles
    let startIndex = 0;
    let endIndex = items.length - 1;

    for (let i = 0; i < positions.length; i++) {
      if (positions[i].top + positions[i].height >= scrollTop - overscan * estimatedItemHeight) {
        startIndex = i;
        break;
      }
    }

    for (let i = positions.length - 1; i >= 0; i--) {
      if (positions[i].top <= scrollTop + height + overscan * estimatedItemHeight) {
        endIndex = i;
        break;
      }
    }

    // Créer les items virtuels
    const virtualItems = [];
    for (let i = startIndex; i <= endIndex; i++) {
      const pos = positions[i];
      virtualItems.push({
        index: i,
        item: items[i],
        key: getItemKey(items[i], i),
        measureRef: (el) => measureItem(i, el),
        style: {
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          transform: `translateY(${pos.top}px)`,
        },
      });
    }

    return { virtualItems, totalHeight, startIndex, endIndex };
  }, [items, scrollTop, height, overscan, estimatedItemHeight, getItemKey, measureItem]);

  return {
    containerRef,
    virtualItems,
    totalHeight,
    startIndex,
    endIndex,
    containerProps: {
      ref: containerRef,
      onScroll: handleScroll,
      style: {
        overflow: 'auto',
        position: 'relative',
        height: containerHeight || '100%',
      },
    },
    innerProps: {
      style: {
        height: totalHeight,
        width: '100%',
        position: 'relative',
      },
    },
  };
}

/**
 * Hook pour infinite scroll.
 */
export function useInfiniteScroll(options = {}) {
  const {
    hasMore = true,
    isLoading = false,
    onLoadMore,
    threshold = 200,
  } = options;

  const containerRef = useRef(null);
  const loadMoreRef = useRef(null);

  useEffect(() => {
    if (!hasMore || isLoading || !loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && hasMore && !isLoading) {
          onLoadMore?.();
        }
      },
      {
        root: containerRef.current,
        rootMargin: `${threshold}px`,
        threshold: 0,
      }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [hasMore, isLoading, onLoadMore, threshold]);

  return {
    containerRef,
    loadMoreRef,
    LoadMoreTrigger: ({ children }) => (
      <div ref={loadMoreRef}>
        {isLoading ? children || <DefaultLoader /> : null}
      </div>
    ),
  };
}

function DefaultLoader() {
  return (
    <div className="flex items-center justify-center py-4">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
    </div>
  );
}

export default {
  useVirtualList,
  useDynamicVirtualList,
  useInfiniteScroll,
};
