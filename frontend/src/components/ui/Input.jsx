import { forwardRef, useId } from 'react';
import clsx from 'clsx';

const baseClasses =
  'w-full rounded-xl border bg-white px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 transition-[border-color,box-shadow] duration-150 focus:outline-none focus:ring-2 disabled:opacity-60 disabled:cursor-not-allowed min-h-[44px]';

const stateClasses = {
  default: 'border-slate-200 focus:border-brand-500 focus:ring-brand-200',
  error: 'border-rose-400 focus:border-rose-500 focus:ring-rose-200 bg-rose-50/50',
  success: 'border-emerald-400 focus:border-emerald-500 focus:ring-emerald-200',
};

const Input = forwardRef(function Input(
  {
    label,
    error,
    hint,
    icon: Icon,
    iconPosition = 'left',
    success = false,
    required = false,
    className = '',
    containerClassName = '',
    ...rest
  },
  ref
) {
  const generatedId = useId();
  const inputId = rest.id || generatedId;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;

  const state = error ? 'error' : success ? 'success' : 'default';

  const describedBy = [
    error && errorId,
    hint && !error && hintId,
  ].filter(Boolean).join(' ') || undefined;

  return (
    <div className={clsx('flex flex-col gap-1.5', containerClassName)}>
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-slate-700"
        >
          {label}
          {required && <span className="ml-1 text-rose-500">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && iconPosition === 'left' && (
          <Icon
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
            aria-hidden="true"
          />
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            baseClasses,
            stateClasses[state],
            Icon && iconPosition === 'left' && 'pl-10',
            Icon && iconPosition === 'right' && 'pr-10',
            className
          )}
          aria-invalid={!!error}
          aria-describedby={describedBy}
          aria-required={required}
          {...rest}
        />
        {Icon && iconPosition === 'right' && (
          <Icon
            className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
            aria-hidden="true"
          />
        )}
      </div>
      {error && (
        <p id={errorId} className="text-xs text-rose-600 flex items-center gap-1" role="alert">
          <svg className="h-3 w-3 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
      {hint && !error && (
        <p id={hintId} className="text-xs text-slate-500">
          {hint}
        </p>
      )}
    </div>
  );
});

export default Input;
