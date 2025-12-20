/**
 * usePageData - Hook wrapper pour queries avec loading/error automatiques
 *
 * Simplifie la gestion des états loading/error/success sur les pages.
 * Combine TanStack Query avec staleTime par domaine et composants d'erreur.
 *
 * @example
 * const { data, isReady, LoadingComponent, ErrorComponent } = usePageData({
 *   queryKey: ['finance', 'transactions'],
 *   queryFn: fetchTransactions,
 *   domain: 'finance',
 *   skeleton: <TransactionsSkeleton />,
 * });
 *
 * if (!isReady) return LoadingComponent || ErrorComponent;
 * return <TransactionsTable data={data} />;
 */

import { useQuery } from '@tanstack/react-query';
import { getStaleTime, createQueryOptions } from './useQueryConfig';

/**
 * Hook principal pour les données de page
 */
export function usePageData({
  queryKey,
  queryFn,
  domain = 'default',
  skeleton = null,
  enabled = true,
  select,
  ...queryOptions
}) {
  const staleTime = getStaleTime(domain);

  const query = useQuery({
    queryKey,
    queryFn,
    enabled,
    select,
    ...createQueryOptions({
      staleTime,
      ...queryOptions,
    }),
  });

  const {
    data,
    isLoading,
    isPending,
    isError,
    error,
    refetch,
    isFetching,
    isSuccess,
  } = query;

  // isReady = données disponibles (succès ou données en cache)
  const isReady = isSuccess && data !== undefined;

  // showLoading = premier chargement (pas de données)
  const showLoading = (isLoading || isPending) && !data;

  // showError = erreur sans données de fallback
  const showError = isError && !data;

  return {
    // Données
    data,

    // États
    isReady,
    isLoading: showLoading,
    isError: showError,
    isFetching,
    error,

    // Actions
    refetch,

    // Skeleton passé pour le PageWrapper
    skeleton,

    // Query complète si besoin d'accès avancé
    query,
  };
}

/**
 * Hook pour plusieurs queries en parallèle
 */
export function usePageQueries(queries) {
  const results = queries.map(({ queryKey, queryFn, domain = 'default', ...options }) => {
    const staleTime = getStaleTime(domain);
    return useQuery({
      queryKey,
      queryFn,
      ...createQueryOptions({ staleTime, ...options }),
    });
  });

  const isLoading = results.some(r => r.isLoading || r.isPending);
  const isError = results.some(r => r.isError);
  const isReady = results.every(r => r.isSuccess);
  const errors = results.filter(r => r.isError).map(r => r.error);

  return {
    results,
    isLoading,
    isError,
    isReady,
    errors,
    data: results.map(r => r.data),
  };
}

export default usePageData;
