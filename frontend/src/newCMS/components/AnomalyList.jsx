import InlineTag from './InlineTag.jsx';

export default function AnomalyList({ anomalies = [] }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-800/50 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-white">Anomalies</span>
        <InlineTag label={`${anomalies.length} élément(s)`} tone="warning" />
      </div>
      <div className="space-y-2">
        {anomalies.map((item, idx) => (
          <div key={item.id || idx} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-white">{item.title || item.description}</p>
              <InlineTag label={item.severity || 'info'} tone={item.severity === 'critical' ? 'danger' : 'warning'} />
            </div>
            {item.description && <p className="text-xs text-slate-400 mt-1">{item.description}</p>}
            {item.impact !== undefined && (
              <p className="text-xs text-amber-300 mt-1">Impact : {item.impact}</p>
            )}
          </div>
        ))}
        {anomalies.length === 0 && <p className="text-sm text-slate-500">Aucune anomalie.</p>}
      </div>
    </div>
  );
}
