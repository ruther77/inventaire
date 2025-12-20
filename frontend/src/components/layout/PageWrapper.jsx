/**
 * PageWrapper - Composant qui gère automatiquement loading/error/contenu
 *
 * Élimine le "flash blanc" en affichant un skeleton pendant le chargement
 * et QueryErrorState en cas d'erreur.
 *
 * @example
 * // Avec usePageData
 * const pageData = usePageData({ queryKey, queryFn, domain: 'finance' });
 *
 * return (
 *   <PageWrapper
 *     pageData={pageData}
 *     skeleton={<TransactionsSkeleton />}
 *   >
 *     {(data) => <TransactionsTable data={data} />}
 *   </PageWrapper>
 * );
 *
 * // Ou avec query TanStack directe
 * const query = useFinanceTransactions();
 *
 * return (
 *   <PageWrapper
 *     query={query}
 *     skeleton={<TransactionsSkeleton />}
 *   >
 *     {(data) => <TransactionsTable data={data} />}
 *   </PageWrapper>
 * );
 */

import { motion, AnimatePresence } from 'framer-motion';
import QueryErrorState from '../feedback/QueryErrorState';
import { PageSkeleton } from '../ui/Skeleton';

/**
 * Animations de transition fluides
 */
const contentVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

/**
 * PageWrapper principal
 */
export default function PageWrapper({
  // Source de données (choisir l'un ou l'autre)
  pageData,   // Résultat de usePageData()
  query,      // Résultat de useQuery() direct

  // UI
  skeleton,   // Composant skeleton personnalisé
  children,   // Fonction (data) => ReactNode ou ReactNode

  // Options
  errorVariant = 'card', // 'card' | 'inline' | 'full'
  showRefetching = false, // Afficher indicateur pendant refetch
  minLoadingTime = 0,     // Temps minimum d'affichage du skeleton (évite flash)
  className = '',
}) {
  // Normaliser les sources de données
  const source = pageData || query || {};

  const {
    data,
    isLoading,
    isPending,
    isError,
    error,
    refetch,
    isFetching,
  } = source;

  // Déterminer l'état d'affichage
  const showLoading = (isLoading || isPending) && data === undefined;
  const showError = isError && data === undefined;
  const showContent = data !== undefined;
  const showRefetchIndicator = showRefetching && isFetching && showContent;

  // Skeleton à utiliser
  const SkeletonComponent = skeleton || <PageSkeleton />;

  // Render du contenu avec les données
  const renderContent = () => {
    if (typeof children === 'function') {
      return children(data);
    }
    return children;
  };

  return (
    <div className={`relative ${className}`}>
      {/* Indicateur de refetch */}
      {showRefetchIndicator && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 animate-pulse z-10" />
      )}

      <AnimatePresence mode="wait">
        {/* État: Chargement */}
        {showLoading && (
          <motion.div
            key="loading"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={contentVariants}
          >
            {SkeletonComponent}
          </motion.div>
        )}

        {/* État: Erreur */}
        {showError && (
          <motion.div
            key="error"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={contentVariants}
          >
            <QueryErrorState
              error={error}
              onRetry={refetch}
              variant={errorVariant}
            />
          </motion.div>
        )}

        {/* État: Contenu */}
        {showContent && (
          <motion.div
            key="content"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={contentVariants}
          >
            {renderContent()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * PageWrapper pour plusieurs queries
 */
export function MultiQueryWrapper({
  queries,    // Array de résultats useQuery
  skeleton,
  children,
  errorVariant = 'card',
  className = '',
}) {
  const isLoading = queries.some(q => q.isLoading || q.isPending);
  const isError = queries.some(q => q.isError);
  const allReady = queries.every(q => q.data !== undefined);
  const errors = queries.filter(q => q.isError);

  const showLoading = isLoading && !allReady;
  const showError = isError && !allReady;
  const showContent = allReady;

  const SkeletonComponent = skeleton || <PageSkeleton />;

  const renderContent = () => {
    const data = queries.map(q => q.data);
    if (typeof children === 'function') {
      return children(data);
    }
    return children;
  };

  return (
    <div className={`relative ${className}`}>
      <AnimatePresence mode="wait">
        {showLoading && (
          <motion.div
            key="loading"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={contentVariants}
          >
            {SkeletonComponent}
          </motion.div>
        )}

        {showError && (
          <motion.div
            key="error"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={contentVariants}
          >
            <QueryErrorState
              error={errors[0]?.error}
              onRetry={() => queries.forEach(q => q.refetch?.())}
              variant={errorVariant}
            />
          </motion.div>
        )}

        {showContent && (
          <motion.div
            key="content"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={contentVariants}
          >
            {renderContent()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * HOC pour wrapper une page entière
 */
export function withPageWrapper(Component, getPageDataOptions) {
  return function WrappedPage(props) {
    const { usePageData } = require('../hooks/usePageData');
    const pageData = usePageData(getPageDataOptions(props));

    return (
      <PageWrapper pageData={pageData} skeleton={pageData.skeleton}>
        {(data) => <Component {...props} data={data} />}
      </PageWrapper>
    );
  };
}
