import clsx from 'clsx';

const variants = {
  default: 'glass-panel',
  elevated: 'glass-panel shadow-lg',
  outline: 'glass-panel',
  ghost: 'rounded-2xl bg-white/5',
  interactive: 'glass-panel hover:bg-white/10 hover:border-white/20 active:scale-[0.99] transition-all duration-200 cursor-pointer',
};

const paddings = {
  none: 'p-0',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
  xl: 'p-8',
};

/**
 * Composant Card.
 *
 * Conteneur de carte réutilisable avec effet glass morphism et différentes variantes visuelles.
 * Supporte les animations stagger et peut être rendu comme différents éléments sémantiques.
 * Utilise le design system dark theme avec bordures semi-transparentes et arrière-plans flous.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {React.ElementType} [props.as='section'] - Élément HTML à rendre ('div', 'section', 'article', etc.)
 * @param {string} [props.className] - Classes CSS additionnelles
 * @param {React.ReactNode} props.children - Contenu de la carte
 * @param {string} [props.padding='lg'] - Espacement interne ('none' | 'sm' | 'md' | 'lg' | 'xl')
 * @param {string} [props.variant='default'] - Variante visuelle ('default' | 'elevated' | 'outline' | 'ghost' | 'interactive')
 * @param {Function} [props.onClick] - Callback au clic (rend automatiquement la carte interactive)
 * @param {boolean} [props.stagger=false] - Active l'animation stagger
 * @param {number} [props.staggerIndex] - Index pour l'animation stagger (délai calculé automatiquement)
 *
 * @example
 * <Card variant="elevated" padding="lg">
 *   <h3>Titre de la carte</h3>
 *   <p>Contenu de la carte</p>
 * </Card>
 *
 * @example
 * <Card variant="interactive" onClick={handleClick}>
 *   Carte cliquable
 * </Card>
 */
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
 * CardHeader - En-tête de carte standardisé.
 *
 * Composant d'en-tête pour les cartes avec titre, description et zone d'action optionnelle.
 * Utilise un layout flex pour aligner le contenu à gauche et les actions à droite.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {string} [props.className] - Classes CSS additionnelles
 * @param {string} [props.title] - Titre principal de l'en-tête
 * @param {string} [props.description] - Description/sous-titre de l'en-tête
 * @param {React.ReactNode} [props.action] - Zone d'action (boutons, liens, etc.)
 * @param {React.ReactNode} [props.children] - Contenu personnalisé (prioritaire sur title/description/action)
 *
 * @example
 * <CardHeader
 *   title="Statistiques"
 *   description="Dernières 30 jours"
 *   action={<Button size="sm">Voir plus</Button>}
 * />
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
        {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
        {description && <p className="mt-1 text-[15px] leading-6 text-slate-200">{description}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

/**
 * CardContent - Corps de carte.
 *
 * Conteneur simple pour le contenu principal d'une carte.
 * Applique un espacement cohérent avec le design system.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {string} [props.className] - Classes CSS additionnelles
 * @param {React.ReactNode} props.children - Contenu de la carte
 *
 * @example
 * <CardContent>
 *   <p>Contenu de la carte</p>
 * </CardContent>
 */
export function CardContent({ className, children }) {
  return <div className={clsx('', className)}>{children}</div>;
}

/**
 * CardFooter - Pied de carte.
 *
 * Zone de pied de page pour les cartes avec bordure supérieure et alignement à droite par défaut.
 * Idéal pour les actions secondaires, boutons de validation, etc.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {string} [props.className] - Classes CSS additionnelles
 * @param {React.ReactNode} props.children - Contenu du pied de page (généralement des boutons)
 *
 * @example
 * <CardFooter>
 *   <Button variant="ghost">Annuler</Button>
 *   <Button variant="primary">Confirmer</Button>
 * </CardFooter>
 */
export function CardFooter({ className, children }) {
  return (
    <div className={clsx('mt-4 pt-4 border-t border-white/10 flex items-center justify-end gap-3', className)}>
      {children}
    </div>
  );
}
