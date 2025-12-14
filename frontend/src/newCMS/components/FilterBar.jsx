import { Filter, X } from 'lucide-react';

export default function FilterBar({ filters = [], onClear, children }) {
  const activeCount = filters.filter((f) => f.active).length;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-white/10 bg-slate-800/50 px-3 py-2">
      <div className="flex items-center gap-1 text-sm text-slate-300">
        <Filter className="h-4 w-4 text-slate-400" />
        <span>Filtres</span>
        {activeCount > 0 && (
          <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-xs text-blue-200">{activeCount}</span>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2 flex-1">{children}</div>
      {activeCount > 0 && (
        <button
          onClick={onClear}
          className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-slate-300 hover:bg-white/10"
        >
          <X className="h-3 w-3" /> Réinitialiser
        </button>
      )}
    </div>
  );
}
