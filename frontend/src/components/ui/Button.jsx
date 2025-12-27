import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

const baseStyles =
  'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-[background-color,border-color,color,transform,box-shadow] duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-[0.98]';

const variants = {
  primary:
    'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/20 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-blue-500/30 focus-visible:outline-blue-500 active:shadow-md',
  subtle:
    'bg-white/10 text-white ring-1 ring-inset ring-white/20 hover:bg-white/15 hover:ring-white/30 active:bg-white/20',
  ghost:
    'bg-transparent text-slate-300 hover:bg-white/10 focus-visible:outline-white/20 active:bg-white/15',
  brand:
    'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/30 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-blue-500/40 focus-visible:outline-blue-500 active:shadow-md',
  destructive:
    'bg-rose-600 text-white shadow-lg shadow-rose-600/30 hover:-translate-y-0.5 hover:bg-rose-500 hover:shadow-xl hover:shadow-rose-600/40 focus-visible:outline-rose-600 active:shadow-md',
  outline:
    'bg-transparent text-slate-300 ring-1 ring-inset ring-white/20 hover:bg-white/10 hover:ring-white/30 active:bg-white/15',
};

const sizes = {
  xs: 'px-3 py-2 text-xs min-h-[36px]',
  sm: 'px-4 py-2 text-xs min-h-[40px]',
  md: 'px-5 py-2.5 text-sm min-h-[44px]',
  lg: 'px-6 py-3 text-sm min-h-[48px]',
  xl: 'px-8 py-4 text-base min-h-[52px]',
};

/**
 * Composant Button.
 *
 * Bouton réutilisable avec plusieurs variantes visuelles, tailles et états.
 * Supporte les états de chargement, désactivé, et peut être rendu comme différents éléments HTML.
 * Accessible WCAG 2.1 avec focus visible et minimum touch target 44px.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {React.ElementType} [props.as='button'] - Élément HTML à rendre ('button', 'a', etc.)
 * @param {string} [props.type='button'] - Type HTML du bouton si as='button'
 * @param {string} [props.variant='primary'] - Variante visuelle ('primary' | 'subtle' | 'ghost' | 'brand' | 'destructive' | 'outline')
 * @param {string} [props.size='md'] - Taille du bouton ('xs' | 'sm' | 'md' | 'lg' | 'xl')
 * @param {string} [props.className] - Classes CSS additionnelles
 * @param {boolean} [props.iconOnly=false] - Active le mode icône seule (forme carrée)
 * @param {boolean} [props.loading=false] - Affiche un spinner de chargement
 * @param {boolean} [props.disabled=false] - Désactive le bouton
 * @param {React.ReactNode} [props.children] - Contenu du bouton
 *
 * @example
 * <Button variant="primary" onClick={handleClick}>
 *   Valider
 * </Button>
 *
 * @example
 * <Button variant="destructive" size="sm" loading>
 *   Suppression...
 * </Button>
 *
 * @example
 * <Button as="a" href="/dashboard" variant="ghost">
 *   Retour au tableau de bord
 * </Button>
 */
export default function Button({
  as: Component = 'button',
  type = 'button',
  variant = 'primary',
  size = 'md',
  className,
  iconOnly = false,
  loading = false,
  disabled = false,
  children,
  ...props
}) {
  const isDisabled = disabled || loading;
  const componentProps =
    Component === 'button' ? { type, disabled: isDisabled, ...props } : props;

  return (
    <Component
      className={clsx(
        baseStyles,
        variants[variant],
        iconOnly ? 'rounded-xl p-2.5 min-w-[44px] min-h-[44px]' : sizes[size],
        isDisabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className,
      )}
      aria-disabled={isDisabled}
      aria-busy={loading}
      {...componentProps}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {children}
    </Component>
  );
}
