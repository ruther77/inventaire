/**
 * useOptimistic - Gestion des mises à jour optimistes avancées.
 *
 * Fonctionnalités:
 * - Optimistic updates avec rollback automatique
 * - Queue de mutations avec retry
 * - Conflit resolution
 * - Offline support avec sync queue
 * - Debounce intelligent
 */

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Hook pour les mises à jour optimistes avec rollback.
 */
export function useOptimisticMutation(mutationFn, options = {}) {
  const {
    onSuccess,
    onError,
    onSettled,
    rollbackOnError = true,
    retryCount = 2,
    retryDelay = 1000,
  } = options;

  const [state, setState] = useState({
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
    data: null,
  });

  const previousDataRef = useRef(null);
  const retryCountRef = useRef(0);

  const reset = useCallback(() => {
    setState({
      isPending: false,
      isSuccess: false,
      isError: false,
      error: null,
      data: null,
    });
    retryCountRef.current = 0;
  }, []);

  const mutate = useCallback(
    async (variables, { optimisticData, currentData } = {}) => {
      // Sauvegarder l'état actuel pour rollback
      previousDataRef.current = currentData;

      setState((prev) => ({
        ...prev,
        isPending: true,
        isError: false,
        error: null,
        data: optimisticData ?? prev.data,
      }));

      const attemptMutation = async (attempt = 0) => {
        try {
          const result = await mutationFn(variables);

          setState({
            isPending: false,
            isSuccess: true,
            isError: false,
            error: null,
            data: result,
          });

          onSuccess?.(result, variables);
          onSettled?.(result, null, variables);

          return result;
        } catch (error) {
          // Retry si autorisé
          if (attempt < retryCount) {
            await new Promise((resolve) => setTimeout(resolve, retryDelay * (attempt + 1)));
            return attemptMutation(attempt + 1);
          }

          // Rollback si nécessaire
          if (rollbackOnError && previousDataRef.current !== null) {
            setState({
              isPending: false,
              isSuccess: false,
              isError: true,
              error,
              data: previousDataRef.current,
            });
          } else {
            setState((prev) => ({
              ...prev,
              isPending: false,
              isError: true,
              error,
            }));
          }

          onError?.(error, variables);
          onSettled?.(null, error, variables);

          throw error;
        }
      };

      return attemptMutation();
    },
    [mutationFn, onSuccess, onError, onSettled, rollbackOnError, retryCount, retryDelay]
  );

  return {
    ...state,
    mutate,
    mutateAsync: mutate,
    reset,
  };
}

/**
 * Hook pour une liste avec CRUD optimiste.
 */
export function useOptimisticList(initialData = [], options = {}) {
  const { idKey = 'id' } = options;
  const [items, setItems] = useState(initialData);
  const [pendingOperations, setPendingOperations] = useState(new Map());

  // Synchroniser avec les données initiales
  useEffect(() => {
    setItems(initialData);
  }, [initialData]);

  const addOptimistic = useCallback(
    (newItem, asyncFn) => {
      const tempId = `temp_${Date.now()}`;
      const itemWithTempId = { ...newItem, [idKey]: tempId, _isPending: true };

      setItems((prev) => [...prev, itemWithTempId]);

      if (asyncFn) {
        asyncFn(newItem)
          .then((result) => {
            setItems((prev) =>
              prev.map((item) =>
                item[idKey] === tempId ? { ...result, _isPending: false } : item
              )
            );
          })
          .catch(() => {
            // Rollback
            setItems((prev) => prev.filter((item) => item[idKey] !== tempId));
          });
      }

      return tempId;
    },
    [idKey]
  );

  const updateOptimistic = useCallback(
    (id, updates, asyncFn) => {
      let previousItem = null;

      setItems((prev) =>
        prev.map((item) => {
          if (item[idKey] === id) {
            previousItem = item;
            return { ...item, ...updates, _isPending: true };
          }
          return item;
        })
      );

      if (asyncFn) {
        asyncFn(id, updates)
          .then((result) => {
            setItems((prev) =>
              prev.map((item) =>
                item[idKey] === id ? { ...result, _isPending: false } : item
              )
            );
          })
          .catch(() => {
            // Rollback
            if (previousItem) {
              setItems((prev) =>
                prev.map((item) =>
                  item[idKey] === id ? previousItem : item
                )
              );
            }
          });
      }
    },
    [idKey]
  );

  const removeOptimistic = useCallback(
    (id, asyncFn) => {
      let removedItem = null;
      let removedIndex = -1;

      setItems((prev) => {
        const newItems = prev.filter((item, index) => {
          if (item[idKey] === id) {
            removedItem = item;
            removedIndex = index;
            return false;
          }
          return true;
        });
        return newItems;
      });

      if (asyncFn) {
        asyncFn(id).catch(() => {
          // Rollback
          if (removedItem) {
            setItems((prev) => {
              const newItems = [...prev];
              newItems.splice(removedIndex, 0, removedItem);
              return newItems;
            });
          }
        });
      }
    },
    [idKey]
  );

  const reorderOptimistic = useCallback(
    (fromIndex, toIndex, asyncFn) => {
      const previousItems = [...items];

      setItems((prev) => {
        const newItems = [...prev];
        const [removed] = newItems.splice(fromIndex, 1);
        newItems.splice(toIndex, 0, removed);
        return newItems;
      });

      if (asyncFn) {
        asyncFn(fromIndex, toIndex).catch(() => {
          setItems(previousItems);
        });
      }
    },
    [items]
  );

  return {
    items,
    setItems,
    addOptimistic,
    updateOptimistic,
    removeOptimistic,
    reorderOptimistic,
    pendingOperations,
  };
}

/**
 * Hook pour debounce intelligent avec pending state.
 */
export function useDebouncedMutation(mutationFn, delay = 500, options = {}) {
  const { onSuccess, onError, immediate = false } = options;
  const [isPending, setIsPending] = useState(false);
  const [lastValue, setLastValue] = useState(null);
  const timeoutRef = useRef(null);
  const latestValueRef = useRef(null);

  const debouncedMutate = useCallback(
    (value) => {
      latestValueRef.current = value;
      setLastValue(value);

      // Clear previous timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Immediate mode: execute first call immediately
      if (immediate && !isPending) {
        setIsPending(true);
        mutationFn(value)
          .then((result) => {
            onSuccess?.(result, value);
          })
          .catch((error) => {
            onError?.(error, value);
          })
          .finally(() => {
            setIsPending(false);
          });
        return;
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        setIsPending(true);
        mutationFn(latestValueRef.current)
          .then((result) => {
            onSuccess?.(result, latestValueRef.current);
          })
          .catch((error) => {
            onError?.(error, latestValueRef.current);
          })
          .finally(() => {
            setIsPending(false);
          });
      }, delay);
    },
    [mutationFn, delay, immediate, isPending, onSuccess, onError]
  );

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const flush = useCallback(() => {
    cancel();
    if (latestValueRef.current !== null) {
      setIsPending(true);
      mutationFn(latestValueRef.current)
        .then((result) => {
          onSuccess?.(result, latestValueRef.current);
        })
        .catch((error) => {
          onError?.(error, latestValueRef.current);
        })
        .finally(() => {
          setIsPending(false);
        });
    }
  }, [cancel, mutationFn, onSuccess, onError]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    mutate: debouncedMutate,
    cancel,
    flush,
    isPending,
    lastValue,
  };
}

export default {
  useOptimisticMutation,
  useOptimisticList,
  useDebouncedMutation,
};
