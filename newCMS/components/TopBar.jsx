import { Bell, CalendarDays, Command, Flame, Sparkles } from 'lucide-react';
import { useAlerts } from '../contexts/AlertsContext.jsx';
import { useTenant } from '../contexts/TenantContext.jsx';
import { useNow } from '../hooks/useNow.js';

export default function TopBar({ onToggleSidebar, sidebarCollapsed, onOpenCommandBar }) {
  const { tenants, activeTenantId, switchTenant, activeTenant } = useTenant();
  const { unreadCount } = useAlerts();
  const { time, date } = useNow();

  return (
    <div className="flex h-14 items-center justify-between border-b border-white/10 bg-slate-900/60 px-4 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300 hover:bg-white/10"
        >
          {sidebarCollapsed ? 'Ouvrir' : 'Fermer'}
        </button>

        <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5">
          <div className="h-2 w-2 rounded-full bg-emerald-400" />
          <select
            value={activeTenantId}
            onChange={(e) => switchTenant(Number(e.target.value))}
            className="bg-transparent text-sm font-medium text-white outline-none"
          >
            {tenants.map((tenant) => (
              <option key={tenant.id} value={tenant.id} className="bg-slate-900 text-slate-900">
                {tenant.name}
              </option>
            ))}
          </select>
        </div>

        <div className="hidden items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-400 md:flex">
          <CalendarDays className="h-4 w-4" />
          <span className="font-medium text-white">{date}</span>
          <span className="text-slate-500">•</span>
          <span className="text-white">{time}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onOpenCommandBar}
          className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-200 hover:border-blue-500/50 hover:text-white"
        >
          <Command className="h-4 w-4" />
          <span className="hidden md:inline">⌘K Rechercher</span>
        </button>

        <div className="hidden items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 md:flex">
          <Flame className="h-4 w-4 text-amber-400" />
          <span>Mode action</span>
          <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-amber-300">Zero-click</span>
        </div>

        <div className="hidden items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 md:flex">
          <Sparkles className="h-4 w-4 text-blue-400" />
          <span>Contexte</span>
          <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-blue-200">{activeTenant?.slug}</span>
        </div>

        <button className="relative rounded-lg border border-white/10 bg-white/5 p-2 text-slate-200 hover:border-rose-500/50 hover:text-white">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 min-w-[20px] items-center justify-center rounded-full bg-rose-500 px-1 text-xs font-semibold text-white">
              {unreadCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
