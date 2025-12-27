import { forwardRef, useId } from 'react';
import clsx from 'clsx';
import { Check } from 'lucide-react';

/**
 * Checkbox - Case à cocher accessible
 * Design: Dark mode avec accent emerald
 */
const Checkbox = forwardRef(function Checkbox(
  {
    label,
    description,
    checked = false,
    indeterminate = false,
    onChange,
    disabled = false,
    error,
    className = '',
    ...rest
  },
  ref
) {
  const generatedId = useId();
  const inputId = rest.id || generatedId;
  const descriptionId = `${inputId}-description`;
  const errorId = `${inputId}-error`;

  return (
    <div className={clsx('flex flex-col gap-1', className)}>
      <div
        className={clsx(
          'flex items-start gap-3 cursor-pointer group',
          disabled && 'cursor-not-allowed opacity-50'
        )}
        onClick={() => !disabled && onChange?.(!checked)}
      >
        <div
          ref={ref}
          role="checkbox"
          aria-checked={indeterminate ? 'mixed' : checked}
          aria-describedby={description ? descriptionId : undefined}
          aria-invalid={!!error}
          tabIndex={disabled ? -1 : 0}
          className={clsx(
            'w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 transition-all duration-200',
            'border-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
            checked || indeterminate
              ? 'bg-emerald-500 border-emerald-500'
              : 'border-white/20 bg-transparent group-hover:border-white/40',
            error && !checked && 'border-rose-500/50',
            disabled && 'pointer-events-none'
          )}
          onKeyDown={(e) => {
            if (e.key === ' ' || e.key === 'Enter') {
              e.preventDefault();
              !disabled && onChange?.(!checked);
            }
          }}
          {...rest}
        >
          {checked && (
            <Check className="w-3.5 h-3.5 text-white" strokeWidth={3} />
          )}
          {indeterminate && !checked && (
            <div className="w-2.5 h-0.5 bg-white rounded-full" />
          )}
        </div>
        {(label || description) && (
          <div className="flex-1 min-w-0 pt-px">
            {label && (
              <span className="text-sm font-medium text-white">
                {label}
              </span>
            )}
            {description && (
              <p id={descriptionId} className="text-xs text-slate-400 mt-0.5">
                {description}
              </p>
            )}
          </div>
        )}
      </div>
      {error && (
        <p id={errorId} className="text-xs text-rose-400 ml-8" role="alert">
          {error}
        </p>
      )}
    </div>
  );
});

/**
 * CheckboxGroup - Groupe de checkboxes
 */
export function CheckboxGroup({ children, label, className = '' }) {
  return (
    <div className={clsx('flex flex-col gap-3', className)} role="group" aria-label={label}>
      {label && (
        <span className="text-sm font-medium text-slate-300">{label}</span>
      )}
      <div className="flex flex-col gap-3">
        {children}
      </div>
    </div>
  );
}

export default Checkbox;
