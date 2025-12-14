/**
 * AdaptiveDensity - Composants avec densité d'affichage adaptative.
 *
 * Fonctionnalités:
 * - Trois niveaux de densité (comfortable, compact, spacious)
 * - Adaptation automatique selon le device/viewport
 * - Persistance des préférences utilisateur
 * - Tables et listes avec densité variable
 */

import { createContext, useContext, useState, useCallback, useEffect, memo } from 'react';

// Densités disponibles
export const DENSITIES = {
  SPACIOUS: 'spacious',
  COMFORTABLE: 'comfortable',
  COMPACT: 'compact',
};

// Configuration des espacements par densité
const densityConfig = {
  [DENSITIES.SPACIOUS]: {
    padding: { x: 6, y: 5 },
    gap: 6,
    fontSize: 'base',
    lineHeight: 'relaxed',
    rowHeight: 64,
    iconSize: 6,
  },
  [DENSITIES.COMFORTABLE]: {
    padding: { x: 4, y: 3 },
    gap: 4,
    fontSize: 'sm',
    lineHeight: 'normal',
    rowHeight: 48,
    iconSize: 5,
  },
  [DENSITIES.COMPACT]: {
    padding: { x: 3, y: 2 },
    gap: 2,
    fontSize: 'xs',
    lineHeight: 'tight',
    rowHeight: 36,
    iconSize: 4,
  },
};

/**
 * Context pour la densité.
 */
const DensityContext = createContext({
  density: DENSITIES.COMFORTABLE,
  setDensity: () => {},
  config: densityConfig[DENSITIES.COMFORTABLE],
});

/**
 * Provider pour la densité.
 */
export function DensityProvider({
  children,
  defaultDensity = DENSITIES.COMFORTABLE,
  storageKey = 'app-density',
  adaptToViewport = true,
}) {
  const [density, setDensityState] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey);
      if (stored && Object.values(DENSITIES).includes(stored)) {
        return stored;
      }
    }
    return defaultDensity;
  });

  // Adapter automatiquement selon le viewport
  useEffect(() => {
    if (!adaptToViewport) return;

    const mediaQuery = window.matchMedia('(max-width: 768px)');

    const handleChange = (e) => {
      if (e.matches) {
        // Sur mobile, utiliser compact par défaut si pas de préférence
        const stored = localStorage.getItem(storageKey);
        if (!stored) {
          setDensityState(DENSITIES.COMPACT);
        }
      }
    };

    handleChange(mediaQuery);
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [adaptToViewport, storageKey]);

  const setDensity = useCallback((newDensity) => {
    setDensityState(newDensity);
    localStorage.setItem(storageKey, newDensity);
  }, [storageKey]);

  const config = densityConfig[density];

  return (
    <DensityContext.Provider value={{ density, setDensity, config }}>
      {children}
    </DensityContext.Provider>
  );
}

/**
 * Hook pour accéder à la densité.
 */
export function useDensity() {
  return useContext(DensityContext);
}

/**
 * DensityToggle - Toggle pour changer la densité.
 */
export const DensityToggle = memo(function DensityToggle({
  showLabels = true,
  size = 'md',
  className = '',
}) {
  const { density, setDensity } = useDensity();

  const sizes = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3',
  };

  const options = [
    { value: DENSITIES.SPACIOUS, icon: SpacingSpacious, label: 'Large' },
    { value: DENSITIES.COMFORTABLE, icon: SpacingComfortable, label: 'Normal' },
    { value: DENSITIES.COMPACT, icon: SpacingCompact, label: 'Compact' },
  ];

  return (
    <div className={`inline-flex items-center gap-1 rounded-lg bg-slate-100 p-1 ${className}`}>
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => setDensity(value)}
          title={label}
          className={`
            ${sizes[size]} rounded-md transition-all duration-150
            ${density === value
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
            }
          `}
        >
          <Icon className="h-4 w-4" />
          {showLabels && (
            <span className="ml-1.5 text-xs font-medium">{label}</span>
          )}
        </button>
      ))}
    </div>
  );
});

// Icônes pour les options de densité
function SpacingSpacious({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function SpacingComfortable({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  );
}

function SpacingCompact({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5h16M4 8h16M4 11h16M4 14h16M4 17h16M4 20h16" />
    </svg>
  );
}

/**
 * DenseTable - Table avec densité adaptative.
 */
export const DenseTable = memo(function DenseTable({
  columns,
  data,
  onRowClick,
  stickyHeader = false,
  className = '',
}) {
  const { density, config } = useDensity();

  const cellPadding = {
    [DENSITIES.SPACIOUS]: 'px-6 py-5',
    [DENSITIES.COMFORTABLE]: 'px-4 py-3',
    [DENSITIES.COMPACT]: 'px-3 py-2',
  };

  const fontSize = {
    [DENSITIES.SPACIOUS]: 'text-base',
    [DENSITIES.COMFORTABLE]: 'text-sm',
    [DENSITIES.COMPACT]: 'text-xs',
  };

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-slate-200">
        <thead className={stickyHeader ? 'sticky top-0 z-10 bg-slate-50' : 'bg-slate-50'}>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={`
                  ${cellPadding[density]} ${fontSize[density]}
                  text-left font-semibold text-slate-900
                  ${column.className || ''}
                `}
                style={{ width: column.width }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {data.map((row, rowIndex) => (
            <tr
              key={row.id || rowIndex}
              onClick={() => onRowClick?.(row, rowIndex)}
              className={onRowClick ? 'cursor-pointer hover:bg-slate-50' : ''}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={`
                    ${cellPadding[density]} ${fontSize[density]}
                    text-slate-700 ${column.cellClassName || ''}
                  `}
                >
                  {column.render ? column.render(row[column.key], row, rowIndex) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
});

/**
 * DenseList - Liste avec densité adaptative.
 */
export const DenseList = memo(function DenseList({
  items,
  renderItem,
  keyExtractor,
  emptyMessage = 'Aucun élément',
  className = '',
}) {
  const { density, config } = useDensity();

  const itemPadding = {
    [DENSITIES.SPACIOUS]: 'p-5',
    [DENSITIES.COMFORTABLE]: 'p-4',
    [DENSITIES.COMPACT]: 'p-2.5',
  };

  const gap = {
    [DENSITIES.SPACIOUS]: 'gap-4',
    [DENSITIES.COMFORTABLE]: 'gap-3',
    [DENSITIES.COMPACT]: 'gap-2',
  };

  if (!items || items.length === 0) {
    return (
      <div className="py-8 text-center text-slate-500">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${gap[density]} ${className}`}>
      {items.map((item, index) => (
        <div
          key={keyExtractor ? keyExtractor(item, index) : index}
          className={`${itemPadding[density]} rounded-xl border border-slate-200 bg-white transition-shadow hover:shadow-sm`}
        >
          {renderItem(item, index, { density, config })}
        </div>
      ))}
    </div>
  );
});

/**
 * DenseCard - Card avec densité adaptative.
 */
export const DenseCard = memo(function DenseCard({
  title,
  subtitle,
  children,
  footer,
  className = '',
}) {
  const { density } = useDensity();

  const padding = {
    [DENSITIES.SPACIOUS]: 'p-6',
    [DENSITIES.COMFORTABLE]: 'p-4',
    [DENSITIES.COMPACT]: 'p-3',
  };

  const titleSize = {
    [DENSITIES.SPACIOUS]: 'text-lg',
    [DENSITIES.COMFORTABLE]: 'text-base',
    [DENSITIES.COMPACT]: 'text-sm',
  };

  const subtitleSize = {
    [DENSITIES.SPACIOUS]: 'text-sm',
    [DENSITIES.COMFORTABLE]: 'text-xs',
    [DENSITIES.COMPACT]: 'text-xs',
  };

  return (
    <div className={`rounded-2xl border border-slate-200 bg-white ${className}`}>
      {(title || subtitle) && (
        <div className={`border-b border-slate-100 ${padding[density]}`}>
          {title && (
            <h3 className={`font-semibold text-slate-900 ${titleSize[density]}`}>
              {title}
            </h3>
          )}
          {subtitle && (
            <p className={`mt-1 text-slate-500 ${subtitleSize[density]}`}>
              {subtitle}
            </p>
          )}
        </div>
      )}

      <div className={padding[density]}>
        {children}
      </div>

      {footer && (
        <div className={`border-t border-slate-100 ${padding[density]}`}>
          {footer}
        </div>
      )}
    </div>
  );
});

/**
 * DenseGrid - Grid avec densité adaptative.
 */
export const DenseGrid = memo(function DenseGrid({
  children,
  columns = { default: 1, sm: 2, md: 3, lg: 4 },
  className = '',
}) {
  const { density } = useDensity();

  const gap = {
    [DENSITIES.SPACIOUS]: 'gap-6',
    [DENSITIES.COMFORTABLE]: 'gap-4',
    [DENSITIES.COMPACT]: 'gap-3',
  };

  const gridCols = `
    grid-cols-${columns.default}
    ${columns.sm ? `sm:grid-cols-${columns.sm}` : ''}
    ${columns.md ? `md:grid-cols-${columns.md}` : ''}
    ${columns.lg ? `lg:grid-cols-${columns.lg}` : ''}
    ${columns.xl ? `xl:grid-cols-${columns.xl}` : ''}
  `;

  return (
    <div className={`grid ${gridCols} ${gap[density]} ${className}`}>
      {children}
    </div>
  );
});

export default {
  DENSITIES,
  DensityProvider,
  useDensity,
  DensityToggle,
  DenseTable,
  DenseList,
  DenseCard,
  DenseGrid,
};
