import { forwardRef, useId } from 'react';

const baseStyles =
  'w-full rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500';

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
          className="mb-1.5 block text-sm font-medium text-slate-700"
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
        className={`${baseStyles} ${error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-200' : ''} ${className}`}
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
        <p id={helperTextId} className="mt-1.5 text-xs text-slate-500">
          {helperText}
        </p>
      )}

      {error && (
        <p
          id={errorId}
          className="mt-1.5 text-xs text-rose-600"
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
