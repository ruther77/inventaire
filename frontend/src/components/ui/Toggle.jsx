import { forwardRef, useId } from 'react';
import clsx from 'clsx';

/**
 * Toggle - Interrupteur on/off accessible
 * Design: Dark mode avec accent emerald
 */
const Toggle = forwardRef(function Toggle(
  {
    label,
    description,
    checked = false,
    onChange,
    disabled = false,
    size = 'md',
    className = '',
    ...rest
  },
  ref
) {
  const generatedId = useId();
  const inputId = rest.id || generatedId;
  const descriptionId = `${inputId}-description`;

  const sizes = {
    sm: {
      track: 'w-9 h-5',
      thumb: 'w-4 h-4',
      translate: 'translate-x-4',
    },
    md: {
      track: 'w-12 h-[26px]',
      thumb: 'w-5 h-5',
      translate: 'translate-x-[22px]',
    },
    lg: {
      track: 'w-14 h-7',
      thumb: 'w-6 h-6',
      translate: 'translate-x-7',
    },
  };

  const currentSize = sizes[size];

  return (
    <div className={clsx('flex items-start gap-3', className)}>
      <button
        ref={ref}
        type="button"
        role="switch"
        id={inputId}
        aria-checked={checked}
        aria-describedby={description ? descriptionId : undefined}
        disabled={disabled}
        onClick={() => !disabled && onChange?.(!checked)}
        className={clsx(
          'relative flex-shrink-0 rounded-full transition-colors duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
          currentSize.track,
          checked ? 'bg-emerald-500' : 'bg-white/10',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        {...rest}
      >
        <span
          className={clsx(
            'absolute top-[3px] left-[3px] rounded-full bg-white shadow-sm transition-transform duration-200',
            currentSize.thumb,
            checked && currentSize.translate
          )}
        />
      </button>
      {(label || description) && (
        <div className="flex-1 min-w-0">
          {label && (
            <label
              htmlFor={inputId}
              className={clsx(
                'text-sm font-medium text-white cursor-pointer',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              {label}
            </label>
          )}
          {description && (
            <p
              id={descriptionId}
              className={clsx(
                'text-xs text-slate-400 mt-0.5',
                disabled && 'opacity-50'
              )}
            >
              {description}
            </p>
          )}
        </div>
      )}
    </div>
  );
});

/**
 * ToggleGroup - Groupe de toggles avec alignement
 */
export function ToggleGroup({ children, className = '' }) {
  return (
    <div className={clsx('flex flex-col gap-4', className)}>
      {children}
    </div>
  );
}

export default Toggle;
