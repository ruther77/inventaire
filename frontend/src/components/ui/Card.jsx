import clsx from 'clsx';

const variants = {
  default: 'glass-panel',
  elevated: 'rounded-2xl bg-white shadow-lg border border-slate-100',
  outline: 'rounded-2xl bg-white border border-slate-200',
  ghost: 'rounded-2xl bg-slate-50/50',
  interactive: 'glass-panel hover:shadow-lg hover:border-slate-300 active:scale-[0.99] transition-all duration-200 cursor-pointer',
};

const paddings = {
  none: 'p-0',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
  xl: 'p-8',
};

export default function Card({
  as: Component = 'section',
  className,
  children,
  padding = 'lg',
  variant = 'default',
  onClick,
  stagger = false,
  staggerIndex,
}) {
  const isInteractive = onClick || variant === 'interactive';
  const actualVariant = isInteractive && variant === 'default' ? 'interactive' : variant;

  return (
    <Component
      className={clsx(
        variants[actualVariant],
        paddings[padding],
        stagger && 'stagger-item',
        className
      )}
      onClick={onClick}
      style={staggerIndex !== undefined ? { animationDelay: `${staggerIndex * 50}ms` } : undefined}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
    >
      {children}
    </Component>
  );
}

/**
 * CardHeader - En-tête de carte standardisé
 */
export function CardHeader({ className, title, description, action, children }) {
  if (children) {
    return (
      <div className={clsx('flex items-start justify-between gap-4 mb-4', className)}>
        {children}
      </div>
    );
  }

  return (
    <div className={clsx('flex items-start justify-between gap-4 mb-4', className)}>
      <div className="min-w-0 flex-1">
        {title && <h3 className="text-lg font-semibold text-slate-900">{title}</h3>}
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

/**
 * CardContent - Corps de carte
 */
export function CardContent({ className, children }) {
  return <div className={clsx('', className)}>{children}</div>;
}

/**
 * CardFooter - Pied de carte
 */
export function CardFooter({ className, children }) {
  return (
    <div className={clsx('mt-4 pt-4 border-t border-slate-100 flex items-center justify-end gap-3', className)}>
      {children}
    </div>
  );
}
