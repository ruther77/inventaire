import InlineTag from './InlineTag.jsx';

const severityTone = {
  critical: 'danger',
  warning: 'warning',
  info: 'info',
};

export default function AlertList({ alerts = [] }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-800/50 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-white">Alertes</span>
        <InlineTag label={`${alerts.length} élément(s)`} tone="info" />
      </div>
      <div className="space-y-2">
        {alerts.map((alert, idx) => (
          <div
            key={alert.id || idx}
            className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-white">{alert.title || alert.message}</span>
              <InlineTag label={alert.severity || 'info'} tone={severityTone[alert.severity] || 'info'} />
            </div>
            {alert.message && <p className="text-xs text-slate-400 mt-1">{alert.message}</p>}
          </div>
        ))}
        {alerts.length === 0 && (
          <p className="text-sm text-slate-500">Aucune alerte.</p>
        )}
      </div>
    </div>
  );
}
