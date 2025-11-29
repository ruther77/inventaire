import clsx from 'clsx';
import { useEffect, useRef, useState } from 'react';

export default function AnimatedMetricCard({ label, value, hint, trend }) {
  const [pulse, setPulse] = useState(false);
  const prevValue = useRef(value);

  useEffect(() => {
    if (prevValue.current !== value) {
      setPulse(true);
      const timer = setTimeout(() => setPulse(false), 500);
      prevValue.current = value;
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [value]);

  return (
    <div
      className={clsx('metric transition-all duration-300', {
        'shadow-xl scale-105': pulse,
      })}
    >
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <div className="flex items-end gap-3">
        <p className="text-3xl font-semibold text-slate-900">{value}</p>
        {trend && (
          <span
            className={clsx(
              'rounded-full px-2 py-1 text-xs font-semibold',
              trend.startsWith('-') ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600',
            )}
          >
            {trend}
          </span>
        )}
      </div>
      {hint && <p className="text-sm text-slate-500">{hint}</p>}
    </div>
  );
}
