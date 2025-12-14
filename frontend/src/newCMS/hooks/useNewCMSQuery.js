import { useQuery } from '@tanstack/react-query';

const defaultOptions = {
  staleTime: 60 * 1000,
  retry: 1,
};

export function useNewCMSQuery(key, queryFn, options = {}) {
  return useQuery({
    queryKey: Array.isArray(key) ? key : [key],
    queryFn,
    ...defaultOptions,
    ...options,
  });
}
