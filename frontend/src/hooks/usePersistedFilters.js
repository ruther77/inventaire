import { useState, useEffect, useCallback } from 'react';

export const usePersistedFilters = (key, defaultFilters = {}) => {
  const storageKey = `filters_${key}`;

  const [filters, setFilters] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? { ...defaultFilters, ...JSON.parse(saved) } : defaultFilters;
    } catch {
      return defaultFilters;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(filters));
    } catch (e) {
      console.warn('Failed to persist filters:', e);
    }
  }, [storageKey, filters]);

  const updateFilter = useCallback((field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(defaultFilters);
  }, [defaultFilters]);

  return { filters, setFilters, updateFilter, resetFilters };
};

export default usePersistedFilters;
