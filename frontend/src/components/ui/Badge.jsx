import clsx from 'clsx';

/**
 * Badge - Composant de badge/tag pour afficher des statuts, labels, etc.
 */

const variants = {
  // Couleurs de statut
  default: 'bg-slate-100 text-slate-700 border-slate-200',
  brand: 'bg-brand-50 text-brand-700 border-brand-100',
  success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  error: 'bg-rose-50 text-rose-700 border-rose-200',
  info: 'bg-sky-50 text-sky-700 border-sky-200',

  // Variantes pleines
  'default-solid': 'bg-slate-600 text-white border-transparent',
  'brand-solid': 'bg-brand-600 text-white border-transparent',
  'success-solid': 'bg-emerald-600 text-white border-transparent',
  'warning-solid': 'bg-amber-500 text-white border-transparent',
  'error-solid': 'bg-rose-600 text-white border-transparent',
  'info-solid': 'bg-sky-600 text-white border-transparent',

  // Outline
  'default-outline': 'bg-transparent text-slate-700 border-slate-300',
  'brand-outline': 'bg-transparent text-brand-700 border-brand-300',
  'success-outline': 'bg-transparent text-emerald-700 border-emerald-300',
  'warning-outline': 'bg-transparent text-amber-700 border-amber-300',
  'error-outline': 'bg-transparent text-rose-700 border-rose-300',
  'info-outline': 'bg-transparent text-sky-700 border-sky-300',
};

const sizes = {
  xs: 'px-1.5 py-0.5 text-[10px]',
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1 text-sm',
};

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  removable = false,
  onRemove,
  icon: Icon,
  className,
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border font-medium',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {dot && (
        <span
          className={clsx(
            'h-1.5 w-1.5 rounded-full',
            variant.includes('solid') ? 'bg-current opacity-70' : getDotColor(variant)
          )}
          aria-hidden="true"
        />
      )}
      {Icon && <Icon className="h-3 w-3" aria-hidden="true" />}
      {children}
      {removable && (
        <button
          type="button"
          onClick={onRemove}
          className={clsx(
            'ml-0.5 -mr-1 rounded-full p-0.5',
            'hover:bg-black/10 focus:outline-none focus-visible:ring-1 focus-visible:ring-current',
            'transition-colors'
          )}
          aria-label="Supprimer"
        >
          <svg className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}
    </span>
  );
}

function getDotColor(variant) {
  const colors = {
    default: 'bg-slate-500',
    brand: 'bg-brand-500',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    error: 'bg-rose-500',
    info: 'bg-sky-500',
  };
  const baseVariant = variant.replace('-outline', '');
  return colors[baseVariant] || colors.default;
}

/**
 * StatusBadge - Badge préconfiguré pour les statuts courants
 */
export function StatusBadge({ status, label, size = 'sm' }) {
  const statusConfig = {
    active: { variant: 'success', label: label || 'Actif' },
    inactive: { variant: 'default', label: label || 'Inactif' },
    pending: { variant: 'warning', label: label || 'En attente' },
    error: { variant: 'error', label: label || 'Erreur' },
    draft: { variant: 'default', label: label || 'Brouillon' },
    published: { variant: 'success', label: label || 'Publié' },
    archived: { variant: 'default', label: label || 'Archivé' },
    critical: { variant: 'error', label: label || 'Critique' },
    ok: { variant: 'success', label: label || 'OK' },
    low: { variant: 'warning', label: label || 'Bas' },
  };

  const config = statusConfig[status] || { variant: 'default', label: status };

  return (
    <Badge variant={config.variant} size={size} dot>
      {config.label}
    </Badge>
  );
}

/**
 * CountBadge - Badge pour afficher un compteur
 */
export function CountBadge({ count, max = 99, variant = 'brand', className }) {
  const displayCount = count > max ? `${max}+` : count;

  if (count === 0) return null;

  return (
    <Badge
      variant={`${variant}-solid`}
      size="xs"
      className={clsx('min-w-[1.25rem] justify-center', className)}
    >
      {displayCount}
    </Badge>
  );
}

/**
 * BadgeGroup - Groupe de badges avec gestion du débordement
 */
export function BadgeGroup({ badges, max = 3, size = 'sm', className }) {
  const visibleBadges = badges.slice(0, max);
  const hiddenCount = badges.length - max;

  return (
    <div className={clsx('flex flex-wrap items-center gap-1', className)}>
      {visibleBadges.map((badge, index) => (
        <Badge key={index} variant={badge.variant} size={size}>
          {badge.label}
        </Badge>
      ))}
      {hiddenCount > 0 && (
        <Badge variant="default" size={size}>
          +{hiddenCount}
        </Badge>
      )}
    </div>
  );
}
