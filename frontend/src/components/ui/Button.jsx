import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

const baseStyles =
  'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-[background-color,border-color,color,transform,box-shadow] duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-[0.98]';

const variants = {
  primary:
    'bg-slate-900 text-white shadow-lg shadow-slate-900/20 hover:-translate-y-0.5 hover:bg-slate-800 hover:shadow-xl hover:shadow-slate-900/30 focus-visible:outline-slate-900 active:shadow-md',
  subtle:
    'bg-white text-slate-900 ring-1 ring-inset ring-slate-200 hover:bg-slate-50 hover:ring-slate-300 active:bg-slate-100',
  ghost:
    'bg-transparent text-slate-700 hover:bg-slate-100 focus-visible:outline-slate-400 active:bg-slate-200',
  brand:
    'bg-brand-600 text-white shadow-lg shadow-brand-600/30 hover:-translate-y-0.5 hover:bg-brand-500 hover:shadow-xl hover:shadow-brand-600/40 focus-visible:outline-brand-600 active:shadow-md',
  destructive:
    'bg-rose-600 text-white shadow-lg shadow-rose-600/30 hover:-translate-y-0.5 hover:bg-rose-500 hover:shadow-xl hover:shadow-rose-600/40 focus-visible:outline-rose-600 active:shadow-md',
  outline:
    'bg-transparent text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 hover:ring-slate-400 active:bg-slate-100',
};

const sizes = {
  xs: 'px-3 py-2 text-xs min-h-[36px]',
  sm: 'px-4 py-2 text-xs min-h-[40px]',
  md: 'px-5 py-2.5 text-sm min-h-[44px]',
  lg: 'px-6 py-3 text-sm min-h-[48px]',
  xl: 'px-8 py-4 text-base min-h-[52px]',
};

export default function Button({
  as: Component = 'button',
  type = 'button',
  variant = 'primary',
  size = 'md',
  className,
  iconOnly = false,
  loading = false,
  disabled = false,
  children,
  ...props
}) {
  const isDisabled = disabled || loading;
  const componentProps =
    Component === 'button' ? { type, disabled: isDisabled, ...props } : props;

  return (
    <Component
      className={clsx(
        baseStyles,
        variants[variant],
        iconOnly ? 'rounded-xl p-2.5 min-w-[44px] min-h-[44px]' : sizes[size],
        isDisabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className,
      )}
      aria-disabled={isDisabled}
      aria-busy={loading}
      {...componentProps}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {children}
    </Component>
  );
}
