import clsx from 'clsx';
import { Package } from 'lucide-react';
import Button from './Button.jsx';

/**
 * EmptyState - Composant pour les états vides contextuels et actionnables
 * Remplace les "Aucune donnée" génériques
 */
export default function EmptyState({
  icon: Icon = Package,
  title = 'Aucun élément',
  description,
  actions = [],
  size = 'md',
  className,
}) {
  const sizes = {
    sm: {
      container: 'py-6 px-4',
      icon: 'h-8 w-8',
      iconContainer: 'p-3',
      title: 'text-sm',
      description: 'text-xs',
    },
    md: {
      container: 'py-10 px-6',
      icon: 'h-12 w-12',
      iconContainer: 'p-4',
      title: 'text-base',
      description: 'text-sm',
    },
    lg: {
      container: 'py-16 px-8',
      icon: 'h-16 w-16',
      iconContainer: 'p-5',
      title: 'text-lg',
      description: 'text-base',
    },
  };

  const s = sizes[size];

  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center text-center',
        s.container,
        className
      )}
    >
      <div
        className={clsx(
          'rounded-full bg-slate-100 text-slate-400 mb-4',
          s.iconContainer
        )}
      >
        <Icon className={s.icon} strokeWidth={1.5} aria-hidden="true" />
      </div>

      <h3 className={clsx('font-semibold text-slate-900', s.title)}>
        {title}
      </h3>

      {description && (
        <p className={clsx('mt-1 text-slate-500 max-w-sm', s.description)}>
          {description}
        </p>
      )}

      {actions.length > 0 && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {actions.map((action, index) => (
            <Button
              key={action.label}
              variant={index === 0 ? (action.variant || 'brand') : (action.variant || 'ghost')}
              size={size === 'lg' ? 'md' : 'sm'}
              onClick={action.onClick}
              disabled={action.disabled}
              loading={action.loading}
            >
              {action.icon && <action.icon className="h-4 w-4" aria-hidden="true" />}
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Variantes prédéfinies pour les cas d'usage courants
 */
export function EmptySearch({ onReset, className }) {
  return (
    <EmptyState
      icon={({ className: cn }) => (
        <svg className={cn} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
      )}
      title="Aucun résultat"
      description="Essayez de modifier vos critères de recherche ou vos filtres."
      actions={onReset ? [{ label: 'Réinitialiser les filtres', onClick: onReset, variant: 'subtle' }] : []}
      className={className}
    />
  );
}

export function EmptyList({ itemName = 'élément', onAdd, className }) {
  return (
    <EmptyState
      title={`Aucun ${itemName}`}
      description={`Commencez par ajouter votre premier ${itemName}.`}
      actions={onAdd ? [{ label: `Ajouter un ${itemName}`, onClick: onAdd }] : []}
      className={className}
    />
  );
}

export function EmptyError({ onRetry, className }) {
  return (
    <EmptyState
      icon={({ className: cn }) => (
        <svg className={cn} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      )}
      title="Une erreur est survenue"
      description="Impossible de charger les données. Veuillez réessayer."
      actions={onRetry ? [{ label: 'Réessayer', onClick: onRetry }] : []}
      className={className}
    />
  );
}

export function EmptyData({ className }) {
  return (
    <EmptyState
      icon={({ className: cn }) => (
        <svg className={cn} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
        </svg>
      )}
      title="Pas de données disponibles"
      description="Les données apparaîtront ici une fois disponibles."
      className={className}
    />
  );
}
