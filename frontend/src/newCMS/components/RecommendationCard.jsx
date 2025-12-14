import InlineTag from './InlineTag.jsx';

export default function RecommendationCard({ title, description, impact, priority = 'medium', actions = [] }) {
  const tone = priority === 'high' || priority === 'critical' ? 'danger' : priority === 'low' ? 'info' : 'warning';
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-800/50 p-4 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-semibold text-white">{title}</h4>
        <InlineTag label={priority.toUpperCase()} tone={tone} />
      </div>
      {description && <p className="text-sm text-slate-400">{description}</p>}
      {impact && <p className="text-sm text-emerald-300">Impact : {impact}</p>}
      {actions.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {actions.map((action, idx) => (
            <button
              key={idx}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                action.primary ? 'bg-blue-500 text-white hover:bg-blue-600' : 'bg-white/10 text-slate-200 hover:bg-white/20'
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
