/**
 * EmptyState - États vides avancés et actionnables.
 *
 * Fonctionnalités:
 * - Illustrations contextuelles
 * - Actions primaires/secondaires
 * - Variantes par type de contenu
 * - Animations subtiles
 * - Suggestions contextuelles
 */

import { memo } from 'react';

// Illustrations SVG inline
const illustrations = {
  empty: (
    <svg className="h-32 w-32" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="100" cy="100" r="80" className="fill-slate-100" />
      <rect x="60" y="70" width="80" height="60" rx="4" className="fill-slate-200" />
      <rect x="70" y="80" width="60" height="4" rx="2" className="fill-slate-300" />
      <rect x="70" y="90" width="40" height="4" rx="2" className="fill-slate-300" />
      <rect x="70" y="100" width="50" height="4" rx="2" className="fill-slate-300" />
      <circle cx="140" cy="140" r="25" className="fill-brand-100" />
      <path d="M130 140l8 8 12-16" className="stroke-brand-500" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  ),
  search: (
    <svg className="h-32 w-32" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="100" cy="100" r="80" className="fill-slate-100" />
      <circle cx="90" cy="90" r="30" className="stroke-slate-300" strokeWidth="4" fill="none" />
      <line x1="112" y1="112" x2="140" y2="140" className="stroke-slate-300" strokeWidth="4" strokeLinecap="round" />
      <circle cx="90" cy="90" r="15" className="fill-slate-200" />
    </svg>
  ),
  error: (
    <svg className="h-32 w-32" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="100" cy="100" r="80" className="fill-rose-50" />
      <circle cx="100" cy="100" r="40" className="fill-rose-100" />
      <path d="M100 75v30" className="stroke-rose-400" strokeWidth="4" strokeLinecap="round" />
      <circle cx="100" cy="120" r="3" className="fill-rose-400" />
    </svg>
  ),
  success: (
    <svg className="h-32 w-32" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="100" cy="100" r="80" className="fill-emerald-50" />
      <circle cx="100" cy="100" r="40" className="fill-emerald-100" />
      <path d="M80 100l15 15 25-30" className="stroke-emerald-500" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  ),
  noData: (
    <svg className="h-32 w-32" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="100" cy="100" r="80" className="fill-slate-100" />
      <rect x="55" y="60" width="90" height="80" rx="8" className="fill-white stroke-slate-200" strokeWidth="2" />
      <line x1="70" y1="85" x2="130" y2="85" className="stroke-slate-200" strokeWidth="2" />
      <line x1="70" y1="105" x2="130" y2="105" className="stroke-slate-200" strokeWidth="2" />
      <line x1="70" y1="125" x2="100" y2="125" className="stroke-slate-200" strokeWidth="2" />
    </svg>
  ),
  import: (
    <svg className="h-32 w-32" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="100" cy="100" r="80" className="fill-sky-50" />
      <rect x="60" y="50" width="80" height="100" rx="4" className="fill-white stroke-sky-200" strokeWidth="2" />
      <path d="M100 80v40M80 100l20 20 20-20" className="stroke-sky-400" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  ),
};

// Presets par type de contenu
const presets = {
  products: {
    illustration: 'import',
    title: 'Aucun produit dans le catalogue',
    description: 'Commencez par importer une facture fournisseur ou créez manuellement vos produits.',
    hint: 'Astuce : L\'import automatique reconnaît les factures Metro, Promocash et Brake.',
  },
  invoices: {
    illustration: 'import',
    title: 'Aucune facture importée',
    description: 'Importez vos factures PDF ou CSV pour alimenter automatiquement le catalogue.',
  },
  transactions: {
    illustration: 'noData',
    title: 'Aucune transaction',
    description: 'Importez un relevé bancaire pour visualiser vos transactions.',
  },
  priceHistory: {
    illustration: 'noData',
    title: 'Pas d\'historique de prix',
    description: 'L\'historique se remplit lors de l\'import de factures.',
    hint: 'Importez vos factures pour reconstruire l\'historique des 2 dernières années.',
  },
  search: {
    illustration: 'search',
    title: 'Aucun résultat',
    description: 'Essayez de modifier vos critères de recherche.',
  },
  error: {
    illustration: 'error',
    title: 'Une erreur est survenue',
    description: 'Impossible de charger les données. Veuillez réessayer.',
  },
  noAlerts: {
    illustration: 'success',
    title: 'Aucune alerte active',
    description: 'Tout est en ordre ! Vos marges et stocks sont dans les seuils configurés.',
  },
};

function EmptyState({
  // Preset ou custom
  preset,

  // Custom props (override preset)
  illustration = 'empty',
  title,
  description,
  hint,

  // Actions
  primaryAction,
  secondaryAction,

  // Styling
  size = 'md',
  className = '',
}) {
  // Merge preset avec props custom
  const presetData = preset ? presets[preset] : {};
  const finalIllustration = illustration || presetData.illustration || 'empty';
  const finalTitle = title || presetData.title || 'Aucune donnée';
  const finalDescription = description || presetData.description;
  const finalHint = hint || presetData.hint;

  const sizes = {
    sm: 'py-8',
    md: 'py-12',
    lg: 'py-16',
  };

  return (
    <div
      className={`
        flex flex-col items-center justify-center text-center
        ${sizes[size]}
        ${className}
      `}
      role="status"
      aria-label={finalTitle}
    >
      {/* Illustration */}
      <div className="mb-6 transition-transform duration-300 hover:scale-105">
        {typeof finalIllustration === 'string'
          ? illustrations[finalIllustration] || illustrations.empty
          : finalIllustration}
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-slate-900">{finalTitle}</h3>

      {/* Description */}
      {finalDescription && (
        <p className="mt-2 max-w-md text-sm text-slate-500">{finalDescription}</p>
      )}

      {/* Hint */}
      {finalHint && (
        <p className="mt-3 max-w-md rounded-lg bg-slate-50 px-4 py-2 text-xs text-slate-600">
          💡 {finalHint}
        </p>
      )}

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {primaryAction && (
            <button
              onClick={primaryAction.onClick}
              disabled={primaryAction.disabled}
              className="
                inline-flex items-center gap-2 rounded-xl
                bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white
                shadow-sm transition-all duration-150
                hover:bg-brand-700 hover:shadow-md
                focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2
                disabled:cursor-not-allowed disabled:opacity-50
              "
            >
              {primaryAction.icon}
              {primaryAction.label}
            </button>
          )}
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              disabled={secondaryAction.disabled}
              className="
                inline-flex items-center gap-2 rounded-xl
                px-5 py-2.5 text-sm font-semibold text-slate-700
                transition-all duration-150
                hover:bg-slate-100
                focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2
                disabled:cursor-not-allowed disabled:opacity-50
              "
            >
              {secondaryAction.icon}
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default memo(EmptyState);
