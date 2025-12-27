import { forwardRef, useId } from 'react';

const baseStyles =
  'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 disabled:cursor-not-allowed disabled:bg-white/5 disabled:text-slate-500';

/**
 * Composant Select.
 *
 * Menu déroulant accessible avec support des labels, messages d'erreur et textes d'aide.
 * Génère automatiquement les IDs et attributs ARIA pour une accessibilité optimale.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {string} [props.className] - Classes CSS additionnelles pour le select
 * @param {React.ReactNode} props.children - Options du select (éléments <option>)
 * @param {string} [props.label] - Label du champ affiché au-dessus
 * @param {string} [props.error] - Message d'erreur (affiche le champ en état d'erreur)
 * @param {string} [props.helperText] - Texte d'aide affiché sous le champ
 * @param {boolean} [props.required] - Marque le champ comme requis (affiche un astérisque)
 * @param {boolean} [props.disabled] - Désactive le champ
 * @param {string} [props.id] - ID personnalisé (auto-généré si non fourni)
 * @param {string} [props.aria-label] - Label ARIA pour les lecteurs d'écran
 * @param {string} [props.aria-describedby] - IDs des éléments descriptifs supplémentaires
 * @param {React.Ref} ref - Ref forwarded vers l'élément select
 *
 * @example
 * <Select label="Pays" required>
 *   <option value="">Sélectionner un pays</option>
 *   <option value="fr">France</option>
 *   <option value="be">Belgique</option>
 * </Select>
 *
 * @example
 * <Select
 *   label="Catégorie"
 *   error={errors.category}
 *   helperText="Choisissez la catégorie principale"
 * >
 *   <option value="">-- Sélectionner --</option>
 *   <option value="food">Alimentation</option>
 *   <option value="supplies">Fournitures</option>
 * </Select>
 */
const Select = forwardRef(function Select(props, ref) {
  const {
    className = '',
    children,
    label,
    error,
    helperText,
    required,
    disabled,
    id: providedId,
    'aria-label': ariaLabel,
    'aria-describedby': ariaDescribedBy,
    ...rest
  } = props;

  const generatedId = useId();
  const id = providedId || generatedId;
  const errorId = `${id}-error`;
  const helperTextId = `${id}-helper`;

  // Build aria-describedby
  const describedByIds = [
    error && errorId,
    helperText && helperTextId,
    ariaDescribedBy,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={id}
          className="mb-1.5 block text-sm font-medium text-slate-300"
        >
          {label}
          {required && (
            <span className="ml-1 text-rose-500" aria-label="requis">
              *
            </span>
          )}
        </label>
      )}

      <select
        ref={ref}
        id={id}
        className={`${baseStyles} ${error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/30' : ''} ${className}`}
        aria-label={!label ? ariaLabel : undefined}
        aria-describedby={describedByIds || undefined}
        aria-invalid={error ? 'true' : undefined}
        aria-required={required ? 'true' : undefined}
        disabled={disabled}
        {...rest}
      >
        {children}
      </select>

      {helperText && !error && (
        <p id={helperTextId} className="mt-1.5 text-xs text-slate-400">
          {helperText}
        </p>
      )}

      {error && (
        <p
          id={errorId}
          className="mt-1.5 text-xs text-rose-400"
          role="alert"
          aria-live="polite"
        >
          {error}
        </p>
      )}
    </div>
  );
});

export default Select;
