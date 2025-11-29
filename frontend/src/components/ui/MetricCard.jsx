import clsx from 'clsx';

export default function MetricCard({ label, value, hint, trend }) {
  return (
    <div className="metric">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
        {label}
      </p>
      <div className="flex items-end gap-3">
        <p className="text-3xl font-semibold text-slate-900">{value}</p>
        {trend && (
          <span
            className={clsx(
              'rounded-full px-2 py-1 text-xs font-semibold',
              trend.startsWith('-')
                ? 'bg-rose-50 text-rose-600'
                : 'bg-emerald-50 text-emerald-600',
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
