import clsx from 'clsx';

const baseStyles =
  'inline-flex items-center justify-center gap-2 rounded-2xl font-medium transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2';

const variants = {
  primary:
    'bg-slate-900 text-white shadow-lg shadow-slate-900/20 hover:-translate-y-0.5 hover:bg-slate-800 focus-visible:outline-slate-900',
  subtle:
    'bg-white text-slate-900 ring-1 ring-inset ring-slate-200 hover:bg-slate-50',
  ghost:
    'bg-transparent text-slate-600 hover:bg-slate-200/60 focus-visible:outline-slate-300',
  brand:
    'bg-brand-600 text-white shadow-lg shadow-brand-600/30 hover:bg-brand-500 focus-visible:outline-brand-600',
};

const sizes = {
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-3 text-sm',
};

export default function Button({
  as: Component = 'button',
  type = 'button',
  variant = 'primary',
  size = 'md',
  className,
  iconOnly = false,
  ...props
}) {
  const componentProps =
    Component === 'button' ? { type, ...props } : props;

  return (
    <Component
      className={clsx(
        baseStyles,
        variants[variant],
        iconOnly ? 'rounded-2xl p-2' : sizes[size],
        className,
      )}
      {...componentProps}
    />
  );
}
