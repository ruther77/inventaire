import { useEffect, useRef } from 'react';
import { Command, Search, X } from 'lucide-react';

export default function CommandBar({
  open,
  onClose,
  actions,
  onSelect,
  query,
  onQueryChange,
}) {
  const inputRef = useRef(null);

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/70 backdrop-blur-sm p-6">
      <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-slate-900/90 shadow-2xl">
        <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3">
          <div className="flex items-center gap-2 rounded-lg bg-white/5 px-2 py-1 text-xs text-slate-400">
            <Command className="h-3.5 w-3.5" />
            <span>Command Bar</span>
          </div>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => onQueryChange?.(e.target.value)}
              placeholder="Rechercher une action ou une vue (ex: finance, import facture, alertes)"
              className="w-full rounded-lg bg-slate-800/80 pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 outline-none border border-white/5 focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/20"
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  onClose?.();
                }
              }}
            />
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
            aria-label="Fermer la command bar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[420px] overflow-y-auto">
          {actions.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-slate-500">
              Aucune action trouvée
            </div>
          ) : (
            <ul className="divide-y divide-white/5">
              {actions.map((action) => (
                <li key={action.id}>
                  <button
                    onClick={() => {
                      onSelect?.(action);
                      onClose?.();
                    }}
                    className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-white/5 transition-colors"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-slate-300">
                      {action.icon ? <action.icon className="h-4 w-4" /> : <Command className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">{action.label}</p>
                      {action.description && (
                        <p className="text-xs text-slate-500">{action.description}</p>
                      )}
                    </div>
                    {action.shortcut && (
                      <span className="rounded border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-400">
                        {action.shortcut}
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
