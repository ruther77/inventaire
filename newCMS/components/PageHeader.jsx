export default function PageHeader({ icon: Icon, title, description, actions = [] }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/70 to-slate-950/80 px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="rounded-xl bg-white/5 p-2">
              <Icon className="h-6 w-6 text-white" />
            </div>
          )}
          <div>
            <h1 className="text-xl font-bold text-white">{title}</h1>
            {description && <p className="text-sm text-slate-400">{description}</p>}
          </div>
        </div>

        {actions.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            {actions.map((action) => (
              <button
                key={action.label}
                onClick={action.onClick}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                  action.primary
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : 'bg-white/5 text-slate-200 hover:bg-white/10'
                }`}
              >
                {action.icon && <span className="mr-2 inline-flex h-4 w-4">{action.icon}</span>}
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
