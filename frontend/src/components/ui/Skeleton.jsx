import clsx from 'clsx';

/**
 * Composant Skeleton.
 *
 * Indicateur de chargement avec animations pulse ou shimmer pour améliorer l'expérience utilisateur.
 * Supporte plusieurs variantes d'animation et peut être utilisé pour créer des layouts de chargement complexes.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {string} [props.className] - Classes CSS pour définir taille et forme (ex: "h-4 w-32")
 * @param {string} [props.variant='pulse'] - Type d'animation ('pulse' | 'shimmer' | 'static')
 * @param {boolean} [props.dark=false] - Active le mode sombre avec shimmer
 *
 * @example
 * <Skeleton className="h-4 w-32" />
 *
 * @example
 * <Skeleton variant="shimmer" className="h-10 w-full rounded-xl" />
 */

const baseClasses = 'rounded';

// Dark theme variants
const variantClasses = {
  pulse: 'animate-pulse bg-white/10',
  shimmer: 'skeleton',
  static: 'bg-white/10',
};

export function Skeleton({
  className,
  variant = 'pulse',
  dark = false,
  ...props
}) {
  return (
    <div
      className={clsx(
        baseClasses,
        dark ? 'skeleton-shimmer-dark' : variantClasses[variant],
        className
      )}
      aria-hidden="true"
      {...props}
    />
  );
}

/**
 * SkeletonText - Skeleton pour texte multiligne.
 *
 * Génère plusieurs lignes de skeleton pour simuler des paragraphes de texte.
 * La dernière ligne est automatiquement plus courte (75%) pour un rendu réaliste.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {number} [props.lines=1] - Nombre de lignes à afficher
 * @param {string} [props.className] - Classes CSS additionnelles
 * @param {string} [props.variant='pulse'] - Type d'animation
 * @param {boolean} [props.stagger=false] - Active l'animation stagger entre les lignes
 *
 * @example
 * <SkeletonText lines={3} variant="shimmer" />
 */
export function SkeletonText({
  lines = 1,
  className,
  variant = 'pulse',
  stagger = false,
}) {
  return (
    <div className={clsx('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant={variant}
          className={clsx(
            'h-4',
            i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full',
            stagger && 'stagger-item'
          )}
          style={stagger ? { animationDelay: `${i * 50}ms` } : undefined}
        />
      ))}
    </div>
  );
}

/**
 * SkeletonCircle - Skeleton circulaire.
 *
 * Skeleton de forme circulaire pour les avatars, icônes ou badges ronds.
 * Propose plusieurs tailles prédéfinies.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {string} [props.size='md'] - Taille du cercle ('xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl')
 * @param {string} [props.className] - Classes CSS additionnelles
 * @param {string} [props.variant='pulse'] - Type d'animation
 *
 * @example
 * <SkeletonCircle size="lg" variant="shimmer" />
 */
export function SkeletonCircle({
  size = 'md',
  className,
  variant = 'pulse',
}) {
  const sizes = {
    xs: 'h-6 w-6',
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
    xl: 'h-20 w-20',
    '2xl': 'h-24 w-24',
  };

  return (
    <Skeleton
      variant={variant}
      className={clsx('rounded-full', sizes[size], className)}
    />
  );
}

export function SkeletonAvatar({ size = 'md', className }) {
  return <SkeletonCircle size={size} className={className} variant="shimmer" />;
}

export function MetricCardSkeleton({ className, variant = 'shimmer' }) {
  return (
    <div className={clsx('metric', className)}>
      <Skeleton variant={variant} className="h-3 w-20" />
      <div className="flex items-end gap-3 mt-2">
        <Skeleton variant={variant} className="h-8 w-24" />
        <Skeleton variant={variant} className="h-5 w-12 rounded-full" />
      </div>
      <Skeleton variant={variant} className="h-4 w-32 mt-2" />
    </div>
  );
}

export function CardSkeleton({ className, variant = 'shimmer' }) {
  return (
    <div className={clsx('glass-panel p-6', className)}>
      <Skeleton variant={variant} className="h-5 w-32 mb-4" />
      <SkeletonText lines={3} variant={variant} />
    </div>
  );
}

export function TableRowSkeleton({
  columns = 4,
  className,
  variant = 'shimmer',
}) {
  return (
    <div className={clsx('flex items-center gap-4 py-3', className)}>
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton
          key={i}
          variant={variant}
          className={clsx('h-4', i === 0 ? 'w-32' : 'w-20')}
        />
      ))}
    </div>
  );
}

export function TableSkeleton({
  rows = 5,
  columns = 4,
  className,
  variant = 'shimmer',
  stagger = true,
}) {
  return (
    <div className={clsx('space-y-1', stagger && 'stagger-fast', className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className={stagger ? 'stagger-item' : undefined}>
          <TableRowSkeleton columns={columns} variant={variant} />
        </div>
      ))}
    </div>
  );
}

export function ListItemSkeleton({ className, variant = 'shimmer' }) {
  return (
    <div
      className={clsx(
        'flex items-center justify-between rounded-xl border border-white/10 px-4 py-3',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <Skeleton variant={variant} className="h-2 w-2 rounded-full" />
        <Skeleton variant={variant} className="h-4 w-32" />
      </div>
      <Skeleton variant={variant} className="h-4 w-16" />
    </div>
  );
}

export function ListSkeleton({
  items = 5,
  className,
  variant = 'shimmer',
  stagger = true,
}) {
  return (
    <div className={clsx('space-y-2', stagger && 'stagger-fast', className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className={stagger ? 'stagger-item' : undefined}>
          <ListItemSkeleton variant={variant} />
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton({ className, variant = 'shimmer' }) {
  return (
    <div className={clsx('h-64 flex items-end gap-2 p-4', className)}>
      {[40, 65, 45, 80, 55, 70, 50, 85, 60, 75].map((height, i) => (
        <Skeleton
          key={i}
          variant={variant}
          className="flex-1 rounded-t stagger-item"
          style={{
            height: `${height}%`,
            animationDelay: `${i * 30}ms`,
          }}
        />
      ))}
    </div>
  );
}

export function ProductCardSkeleton({ className, variant = 'shimmer' }) {
  return (
    <div className={clsx('rounded-2xl border border-white/10 bg-white/5 p-4', className)}>
      <Skeleton variant={variant} className="h-48 w-full rounded-xl mb-4" />
      <Skeleton variant={variant} className="h-4 w-3/4 mb-2" />
      <Skeleton variant={variant} className="h-3 w-1/2 mb-3" />
      <div className="flex justify-between">
        <Skeleton variant={variant} className="h-5 w-16" />
        <Skeleton variant={variant} className="h-5 w-12" />
      </div>
    </div>
  );
}

export function FormFieldSkeleton({ className, variant = 'shimmer' }) {
  return (
    <div className={clsx('space-y-1.5', className)}>
      <Skeleton variant={variant} className="h-4 w-20" />
      <Skeleton variant={variant} className="h-11 w-full rounded-xl" />
    </div>
  );
}

export function FormSkeleton({
  fields = 4,
  className,
  variant = 'shimmer',
  stagger = true,
}) {
  return (
    <div className={clsx('space-y-4', stagger && 'stagger-fast', className)}>
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className={stagger ? 'stagger-item' : undefined}>
          <FormFieldSkeleton variant={variant} />
        </div>
      ))}
    </div>
  );
}

/**
 * SidebarNavSkeleton - Skeleton pour la navigation latérale
 */
export function SidebarNavSkeleton({ items = 5, className }) {
  return (
    <div className={clsx('space-y-2 stagger-fast', className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div
          key={i}
          className="stagger-item flex flex-col gap-1 rounded-2xl border border-white/5 bg-white/5 px-4 py-3"
        >
          <div className="flex items-center gap-2">
            <Skeleton variant="shimmer" className="h-4 w-4 rounded" dark />
            <Skeleton variant="shimmer" className="h-4 w-24" dark />
          </div>
          <Skeleton variant="shimmer" className="h-3 w-32" dark />
        </div>
      ))}
    </div>
  );
}

/**
 * DashboardSkeleton - Skeleton complet pour le dashboard
 */
export function DashboardSkeleton({ className }) {
  return (
    <div className={clsx('space-y-6', className)}>
      {/* Hero skeleton */}
      <div className="glass-panel p-6 stagger-item">
        <Skeleton variant="shimmer" className="h-3 w-24 mb-2" />
        <Skeleton variant="shimmer" className="h-8 w-48 mb-2" />
        <Skeleton variant="shimmer" className="h-4 w-64" />
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 stagger-fast">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="stagger-item">
            <MetricCardSkeleton />
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CardSkeleton className="stagger-item" />
        <CardSkeleton className="stagger-item" />
      </div>
    </div>
  );
}

/**
 * PageSkeleton - Skeleton générique pour une page
 */
export function PageSkeleton({ className }) {
  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton variant="shimmer" className="h-8 w-48 mb-2" />
          <Skeleton variant="shimmer" className="h-4 w-64" />
        </div>
        <Skeleton variant="shimmer" className="h-10 w-32 rounded-xl" />
      </div>

      {/* Content */}
      <CardSkeleton />
    </div>
  );
}

/**
 * IntelligenceSkeleton - Skeleton pour la page Intelligence
 */
export function IntelligenceSkeleton({ className }) {
  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div>
        <Skeleton variant="shimmer" className="h-3 w-20 mb-2" />
        <Skeleton variant="shimmer" className="h-8 w-40 mb-1" />
        <Skeleton variant="shimmer" className="h-4 w-80" />
      </div>

      {/* Score + KPIs row */}
      <div className="grid gap-4 md:grid-cols-5">
        <div className="rounded-2xl border border-white/10 p-6 text-center">
          <Skeleton variant="shimmer" className="h-3 w-24 mx-auto mb-2" />
          <Skeleton variant="shimmer" className="h-12 w-16 mx-auto mb-1" />
          <Skeleton variant="shimmer" className="h-3 w-8 mx-auto" />
        </div>
        {Array.from({ length: 4 }).map((_, i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>

      {/* Forecasts */}
      <CardSkeleton />

      {/* Anomalies + Suppliers */}
      <div className="grid gap-6 lg:grid-cols-2">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );
}

/**
 * TransactionsSkeleton - Skeleton pour la page Transactions
 */
export function TransactionsSkeleton({ className }) {
  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton variant="shimmer" className="h-3 w-16 mb-2" />
          <Skeleton variant="shimmer" className="h-8 w-56" />
        </div>
        <div className="flex gap-2">
          <Skeleton variant="shimmer" className="h-10 w-28 rounded-xl" />
          <Skeleton variant="shimmer" className="h-10 w-24 rounded-xl" />
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} variant="shimmer" className="h-10 w-32 rounded-xl" />
        ))}
      </div>

      {/* Table */}
      <div className="glass-panel p-0">
        <TableSkeleton rows={10} columns={6} />
      </div>
    </div>
  );
}

/**
 * InvoiceImportSkeleton - Skeleton pour la page Import factures
 */
export function InvoiceImportSkeleton({ className }) {
  return (
    <div className={clsx('space-y-6', className)}>
      {/* Upload area */}
      <div className="rounded-2xl border-2 border-dashed border-white/20 p-12 text-center">
        <Skeleton variant="shimmer" className="h-16 w-16 mx-auto mb-4 rounded-full" />
        <Skeleton variant="shimmer" className="h-5 w-48 mx-auto mb-2" />
        <Skeleton variant="shimmer" className="h-4 w-64 mx-auto" />
      </div>

      {/* Document selector */}
      <div className="flex gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} variant="shimmer" className="h-10 w-28 rounded-xl" />
        ))}
      </div>

      {/* Lines editor */}
      <CardSkeleton />
    </div>
  );
}

export default Skeleton;
