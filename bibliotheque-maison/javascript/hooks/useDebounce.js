import { useState, useEffect } from 'react';

/**
 * Hook qui debounce une valeur
 * @param {any} value - La valeur à debouncer
 * @param {number} delay - Le délai en millisecondes
 * @returns {any} La valeur debouncée
 */
export function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
