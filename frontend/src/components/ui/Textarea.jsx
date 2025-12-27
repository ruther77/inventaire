import { forwardRef, useId } from 'react';
import clsx from 'clsx';

const baseClasses =
  'w-full rounded-xl border bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-500 transition-[border-color,box-shadow] duration-150 focus:outline-none focus:ring-2 disabled:opacity-60 disabled:cursor-not-allowed resize-y min-h-[100px]';

const stateClasses = {
  default: 'border-white/10 focus:border-emerald-500 focus:ring-emerald-500/30',
  error: 'border-rose-500/50 focus:border-rose-500 focus:ring-rose-500/30 bg-rose-500/10',
  success: 'border-emerald-500/50 focus:border-emerald-500 focus:ring-emerald-500/30',
};

/**
 * Textarea - Zone de texte multiligne accessible
 * Design: Dark mode cohérent avec Input
 */
const Textarea = forwardRef(function Textarea(
  {
    label,
    error,
    hint,
    success = false,
    required = false,
    maxLength,
    showCount = false,
    className = '',
    containerClassName = '',
    value = '',
    ...rest
  },
  ref
) {
  const generatedId = useId();
  const inputId = rest.id || generatedId;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;

  const state = error ? 'error' : success ? 'success' : 'default';
  const currentLength = typeof value === 'string' ? value.length : 0;

  const describedBy = [
    error && errorId,
    hint && !error && hintId,
  ].filter(Boolean).join(' ') || undefined;

  return (
    <div className={clsx('flex flex-col gap-1.5', containerClassName)}>
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-slate-300"
        >
          {label}
          {required && <span className="ml-1 text-rose-500">*</span>}
        </label>
      )}
      <textarea
        ref={ref}
        id={inputId}
        value={value}
        maxLength={maxLength}
        className={clsx(
          baseClasses,
          stateClasses[state],
          className
        )}
        aria-invalid={!!error}
        aria-describedby={describedBy}
        aria-required={required}
        {...rest}
      />
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1">
          {error && (
            <p id={errorId} className="text-xs text-rose-400 flex items-center gap-1" role="alert">
              <svg className="h-3 w-3 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </p>
          )}
          {hint && !error && (
            <p id={hintId} className="text-xs text-slate-400">
              {hint}
            </p>
          )}
        </div>
        {showCount && maxLength && (
          <span className={clsx(
            'text-xs',
            currentLength >= maxLength ? 'text-rose-400' : 'text-slate-500'
          )}>
            {currentLength}/{maxLength}
          </span>
        )}
      </div>
    </div>
  );
});

export default Textarea;
