import { useState, useEffect, useRef, useCallback, useMemo } from 'react';

/**
 * useDebounce - Retarde la mise à jour d'une valeur
 *
 * @param {any} value - Valeur à debouncer
 * @param {number} delay - Délai en ms (défaut: 300)
 * @returns {any} - Valeur debouncée
 */
export default function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * useDebouncedCallback - Retarde l'exécution d'une fonction
 *
 * @param {Function} callback - Fonction à debouncer
 * @param {number} delay - Délai en ms
 * @returns {Function} - Fonction debouncée
 */
export function useDebouncedCallback(callback, delay = 300) {
  const callbackRef = useRef(callback);
  const timeoutRef = useRef(null);

  // Mettre à jour la référence du callback
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const debouncedCallback = useCallback(
    (...args) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args);
      }, delay);
    },
    [delay]
  );

  // Cleanup au démontage
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Retourner aussi une méthode pour annuler et une pour exécuter immédiatement
  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

  const flush = useCallback(
    (...args) => {
      cancel();
      callbackRef.current(...args);
    },
    [cancel]
  );

  return useMemo(
    () => Object.assign(debouncedCallback, { cancel, flush }),
    [debouncedCallback, cancel, flush]
  );
}

/**
 * useThrottle - Limite la fréquence d'exécution d'une valeur
 *
 * @param {any} value - Valeur à throttler
 * @param {number} limit - Intervalle minimum en ms
 * @returns {any} - Valeur throttlée
 */
export function useThrottle(value, limit = 300) {
  const [throttledValue, setThrottledValue] = useState(value);
  const lastRan = useRef(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        setThrottledValue(value);
        lastRan.current = Date.now();
      }
    }, limit - (Date.now() - lastRan.current));

    return () => clearTimeout(handler);
  }, [value, limit]);

  return throttledValue;
}

/**
 * useThrottledCallback - Limite la fréquence d'exécution d'une fonction
 *
 * @param {Function} callback - Fonction à throttler
 * @param {number} limit - Intervalle minimum en ms
 * @returns {Function} - Fonction throttlée
 */
export function useThrottledCallback(callback, limit = 300) {
  const lastRan = useRef(0);
  const timeoutRef = useRef(null);
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return useCallback(
    (...args) => {
      const now = Date.now();

      if (now - lastRan.current >= limit) {
        callbackRef.current(...args);
        lastRan.current = now;
      } else {
        // Programmer une exécution pour la prochaine fenêtre disponible
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(() => {
          callbackRef.current(...args);
          lastRan.current = Date.now();
        }, limit - (now - lastRan.current));
      }
    },
    [limit]
  );
}

/**
 * useDebouncedState - useState avec debounce intégré
 *
 * @param {any} initialValue - Valeur initiale
 * @param {number} delay - Délai en ms
 * @returns {[any, Function, any]} - [debouncedValue, setValue, immediateValue]
 */
export function useDebouncedState(initialValue, delay = 300) {
  const [value, setValue] = useState(initialValue);
  const debouncedValue = useDebounce(value, delay);

  return [debouncedValue, setValue, value];
}
