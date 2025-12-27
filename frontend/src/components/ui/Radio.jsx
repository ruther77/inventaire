import { forwardRef, useId, createContext, useContext } from 'react';
import clsx from 'clsx';

const RadioGroupContext = createContext(null);

/**
 * Radio - Bouton radio accessible
 * Design: Dark mode avec accent emerald
 */
const Radio = forwardRef(function Radio(
  {
    label,
    description,
    value,
    checked: controlledChecked,
    onChange: controlledOnChange,
    disabled = false,
    className = '',
    ...rest
  },
  ref
) {
  const generatedId = useId();
  const inputId = rest.id || generatedId;
  const descriptionId = `${inputId}-description`;

  // Use context if available (when inside RadioGroup)
  const group = useContext(RadioGroupContext);
  const isChecked = group ? group.value === value : controlledChecked;
  const handleChange = group ? () => group.onChange(value) : () => controlledOnChange?.(!controlledChecked);
  const isDisabled = disabled || group?.disabled;

  return (
    <div
      className={clsx(
        'flex items-start gap-3 cursor-pointer group',
        isDisabled && 'cursor-not-allowed opacity-50',
        className
      )}
      onClick={() => !isDisabled && handleChange()}
    >
      <div
        ref={ref}
        role="radio"
        aria-checked={isChecked}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={isDisabled ? -1 : 0}
        className={clsx(
          'w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-200',
          'border-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
          isChecked
            ? 'border-emerald-500'
            : 'border-white/20 group-hover:border-white/40',
          isDisabled && 'pointer-events-none'
        )}
        onKeyDown={(e) => {
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            !isDisabled && handleChange();
          }
        }}
        {...rest}
      >
        {isChecked && (
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 transition-transform duration-200" />
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
  );
});

/**
 * RadioGroup - Groupe de radios avec gestion de l'état
 */
export function RadioGroup({
  children,
  label,
  value,
  onChange,
  disabled = false,
  orientation = 'vertical',
  className = ''
}) {
  return (
    <RadioGroupContext.Provider value={{ value, onChange, disabled }}>
      <div
        className={clsx('flex flex-col gap-3', className)}
        role="radiogroup"
        aria-label={label}
      >
        {label && (
          <span className="text-sm font-medium text-slate-300">{label}</span>
        )}
        <div className={clsx(
          'flex gap-3',
          orientation === 'vertical' ? 'flex-col' : 'flex-row flex-wrap'
        )}>
          {children}
        </div>
      </div>
    </RadioGroupContext.Provider>
  );
}

export default Radio;
