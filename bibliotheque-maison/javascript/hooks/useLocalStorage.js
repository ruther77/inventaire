import { useState, useEffect, useCallback } from 'react';

/**
 * Hook pour gérer le localStorage avec synchronisation entre onglets
 * @param {string} key - La clé du localStorage
 * @param {any} initialValue - La valeur initiale
 * @returns {[any, Function]} [valeur, fonction de mise à jour]
 */
export function useLocalStorage(key, initialValue) {
  const readValue = useCallback(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key]);

  const [storedValue, setStoredValue] = useState(readValue);

  const setValue = useCallback(
    (value) => {
      if (typeof window === 'undefined') {
        return;
      }
      try {
        const newValue = value instanceof Function ? value(storedValue) : value;
        setStoredValue(newValue);
        window.localStorage.setItem(key, JSON.stringify(newValue));
        window.dispatchEvent(
          new CustomEvent('local-storage', { detail: { key, newValue } })
        );
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setStoredValue(JSON.parse(e.newValue));
        } catch (error) {
          console.warn(`Error parsing localStorage value for key "${key}":`, error);
        }
      }
    };

    const handleLocalStorageChange = (e) => {
      if (e.detail.key === key) {
        setStoredValue(e.detail.newValue);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('local-storage', handleLocalStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('local-storage', handleLocalStorageChange);
    };
  }, [key]);

  return [storedValue, setValue];
}
