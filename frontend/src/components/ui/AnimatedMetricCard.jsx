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
      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-200">{label}</p>
      <div className="flex items-end gap-3">
        <p className="text-3xl font-semibold text-white">{value}</p>
        {trend && (
          <span
            className={clsx(
              'rounded-full px-3 py-1 text-xs font-semibold',
              trend.startsWith('-') ? 'bg-rose-500/15 text-rose-200' : 'bg-emerald-500/15 text-emerald-200',
            )}
          >
            {trend}
          </span>
        )}
      </div>
      {hint && <p className="text-[15px] leading-6 text-slate-200">{hint}</p>}
    </div>
  );
}
