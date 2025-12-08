import clsx from 'clsx';

/**
 * Skeleton - Composant de chargement avec animations avancées
 *
 * Version 2.0 - Avec support shimmer, stagger et variants
 *
 * @example
 * <Skeleton className="h-4 w-32" />
 * <Skeleton variant="shimmer" className="h-4 w-32" />
 */

const baseClasses = 'rounded';

const variantClasses = {
  pulse: 'animate-pulse bg-slate-200',
  shimmer: 'skeleton-shimmer',
  static: 'bg-slate-200',
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
        'flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3',
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
    <div className={clsx('rounded-2xl border border-slate-100 p-4', className)}>
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

export default Skeleton;
