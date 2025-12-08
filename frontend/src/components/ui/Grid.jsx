import clsx from 'clsx';
import { spacing } from './design-tokens.js';

/**
 * Grid - Composant de grille responsive standardisé
 *
 * Utilise les tokens de design pour garantir la cohérence
 * Supporte les breakpoints responsive avec une API simple
 *
 * @example
 * <Grid cols={{ sm: 1, md: 2, lg: 3 }} gap="lg">
 *   <Card>...</Card>
 *   <Card>...</Card>
 *   <Card>...</Card>
 * </Grid>
 */

const colsClasses = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
  5: 'grid-cols-5',
  6: 'grid-cols-6',
  12: 'grid-cols-12',
};

const smColsClasses = {
  1: 'sm:grid-cols-1',
  2: 'sm:grid-cols-2',
  3: 'sm:grid-cols-3',
  4: 'sm:grid-cols-4',
  5: 'sm:grid-cols-5',
  6: 'sm:grid-cols-6',
};

const mdColsClasses = {
  1: 'md:grid-cols-1',
  2: 'md:grid-cols-2',
  3: 'md:grid-cols-3',
  4: 'md:grid-cols-4',
  5: 'md:grid-cols-5',
  6: 'md:grid-cols-6',
};

const lgColsClasses = {
  1: 'lg:grid-cols-1',
  2: 'lg:grid-cols-2',
  3: 'lg:grid-cols-3',
  4: 'lg:grid-cols-4',
  5: 'lg:grid-cols-5',
  6: 'lg:grid-cols-6',
};

const xlColsClasses = {
  1: 'xl:grid-cols-1',
  2: 'xl:grid-cols-2',
  3: 'xl:grid-cols-3',
  4: 'xl:grid-cols-4',
  5: 'xl:grid-cols-5',
  6: 'xl:grid-cols-6',
};

export default function Grid({
  as: Component = 'div',
  children,
  cols = 1,
  gap = 'lg',
  className,
  stagger = false,
  staggerFast = false,
  ...props
}) {
  // Gestion des colonnes responsive
  const getColsClasses = () => {
    if (typeof cols === 'number') {
      return colsClasses[cols] || 'grid-cols-1';
    }

    if (typeof cols === 'object') {
      const classes = [];

      // Base (mobile first)
      if (cols.base) classes.push(colsClasses[cols.base]);
      else classes.push('grid-cols-1');

      // Breakpoints
      if (cols.sm) classes.push(smColsClasses[cols.sm]);
      if (cols.md) classes.push(mdColsClasses[cols.md]);
      if (cols.lg) classes.push(lgColsClasses[cols.lg]);
      if (cols.xl) classes.push(xlColsClasses[cols.xl]);

      return classes.join(' ');
    }

    return 'grid-cols-1';
  };

  // Gestion du gap via tokens
  const gapClass = spacing[gap] || spacing.lg;

  return (
    <Component
      className={clsx(
        'grid',
        getColsClasses(),
        gapClass,
        stagger && 'stagger',
        staggerFast && 'stagger-fast',
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

/**
 * GridItem - Composant enfant optionnel pour contrôle granulaire
 */
export function GridItem({
  as: Component = 'div',
  children,
  span = 1,
  className,
  staggerIndex,
  ...props
}) {
  const spanClasses = {
    1: 'col-span-1',
    2: 'col-span-2',
    3: 'col-span-3',
    4: 'col-span-4',
    5: 'col-span-5',
    6: 'col-span-6',
    full: 'col-span-full',
  };

  return (
    <Component
      className={clsx(
        spanClasses[span] || 'col-span-1',
        staggerIndex !== undefined && 'stagger-item',
        className
      )}
      style={staggerIndex !== undefined ? { animationDelay: `${staggerIndex * 50}ms` } : undefined}
      {...props}
    >
      {children}
    </Component>
  );
}

/**
 * AutoGrid - Grille avec colonnes auto-fit
 * Idéal pour les grilles de cartes de taille égale
 */
export function AutoGrid({
  as: Component = 'div',
  children,
  minWidth = '280px',
  gap = 'lg',
  className,
  ...props
}) {
  const gapClass = spacing[gap] || spacing.lg;

  return (
    <Component
      className={clsx('grid', gapClass, className)}
      style={{
        gridTemplateColumns: `repeat(auto-fit, minmax(${minWidth}, 1fr))`,
      }}
      {...props}
    >
      {children}
    </Component>
  );
}

/**
 * MasonryGrid - Grille de type masonry avec CSS columns
 */
export function MasonryGrid({
  as: Component = 'div',
  children,
  columns = { sm: 1, md: 2, lg: 3 },
  gap = 'lg',
  className,
  ...props
}) {
  const gapValue = {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
    xl: '1.5rem',
    '2xl': '2rem',
  };

  return (
    <Component
      className={clsx(
        'columns-1',
        columns.sm && `sm:columns-${columns.sm}`,
        columns.md && `md:columns-${columns.md}`,
        columns.lg && `lg:columns-${columns.lg}`,
        className
      )}
      style={{ columnGap: gapValue[gap] || gapValue.lg }}
      {...props}
    >
      {children}
    </Component>
  );
}

/**
 * Stack - Layout vertical avec espacement cohérent
 */
export function Stack({
  as: Component = 'div',
  children,
  gap = 'lg',
  align = 'stretch',
  className,
  ...props
}) {
  const gapClass = spacing[gap] || spacing.lg;

  const alignClasses = {
    start: 'items-start',
    center: 'items-center',
    end: 'items-end',
    stretch: 'items-stretch',
  };

  return (
    <Component
      className={clsx(
        'flex flex-col',
        gapClass,
        alignClasses[align],
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

/**
 * Inline - Layout horizontal avec espacement cohérent
 */
export function Inline({
  as: Component = 'div',
  children,
  gap = 'md',
  align = 'center',
  justify = 'start',
  wrap = false,
  className,
  ...props
}) {
  const gapClass = spacing[gap] || spacing.md;

  const alignClasses = {
    start: 'items-start',
    center: 'items-center',
    end: 'items-end',
    baseline: 'items-baseline',
    stretch: 'items-stretch',
  };

  const justifyClasses = {
    start: 'justify-start',
    center: 'justify-center',
    end: 'justify-end',
    between: 'justify-between',
    around: 'justify-around',
    evenly: 'justify-evenly',
  };

  return (
    <Component
      className={clsx(
        'flex',
        gapClass,
        alignClasses[align],
        justifyClasses[justify],
        wrap && 'flex-wrap',
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

/**
 * Cluster - Groupe d'éléments avec wrap automatique
 */
export function Cluster({
  as: Component = 'div',
  children,
  gap = 'sm',
  className,
  ...props
}) {
  const gapClass = spacing[gap] || spacing.sm;

  return (
    <Component
      className={clsx('flex flex-wrap', gapClass, className)}
      {...props}
    >
      {children}
    </Component>
  );
}
