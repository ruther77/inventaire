import { forwardRef } from 'react';

const baseStyles =
  'w-full rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200';

const Select = forwardRef(function Select(props, ref) {
  const { className = '', children, ...rest } = props;
  return (
    <select ref={ref} className={`${baseStyles} ${className}`} {...rest}>
      {children}
    </select>
  );
});

export default Select;
