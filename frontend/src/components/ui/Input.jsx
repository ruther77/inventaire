import { forwardRef } from 'react';

const baseClasses =
  'w-full rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200 disabled:opacity-60 disabled:cursor-not-allowed';

const Input = forwardRef(function Input(props, ref) {
  const { className = '', ...rest } = props;
  return <input ref={ref} className={`${baseClasses} ${className}`} {...rest} />;
});

export default Input;
