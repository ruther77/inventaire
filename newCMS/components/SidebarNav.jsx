import { ChevronLeft, Menu } from 'lucide-react';

export default function SidebarNav({
  sections = [],
  extras = [],
  activePath,
  collapsed,
  onToggle,
  onNavigate,
}) {
  return (
    <div
      className={`${collapsed ? 'w-16' : 'w-64'} flex h-screen flex-col border-r border-white/10 bg-slate-950/80 backdrop-blur-sm transition-all duration-200`}
    >
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-4">
        {!collapsed && (
          <div className="text-lg font-semibold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            newCMS
          </div>
        )}
        <button
          onClick={onToggle}
          className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"
          aria-label="Basculer la sidebar"
        >
          {collapsed ? <Menu className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </div>

      <nav className="flex-1 space-y-2 overflow-y-auto px-2 py-3">
        {sections.map((section) => {
          const Icon = section.icon;
          const isActive = activePath === section.path;

          return (
            <button
              key={section.id}
              onClick={() => onNavigate?.(section.path)}
              className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all ${
                isActive
                  ? `bg-${section.gradient?.split(' ')[0]?.replace('from-', '') ?? 'blue-500'}/20 text-white border border-${section.gradient?.split(' ')[0]?.replace('from-', '') ?? 'blue-500'}/30`
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5">
                <Icon className="h-4 w-4" />
              </div>
              {!collapsed && (
                <div className="flex-1 text-left">
                  <div className="font-medium">{section.label}</div>
                  <div className="text-xs text-slate-500">{section.description || section.path}</div>
                </div>
              )}
            </button>
          );
        })}

        {extras.length > 0 && (
          <div className="pt-3">
            {!collapsed && <p className="px-3 pb-2 text-xs uppercase tracking-wide text-slate-500">Extensions</p>}
            {extras.map((item) => {
              const Icon = item.icon;
              const isActive = activePath === item.path;
              return (
                <button
                  key={item.path}
                  onClick={() => onNavigate?.(item.path)}
                  className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all ${
                    isActive
                      ? 'bg-white/10 text-white border border-white/10'
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5">
                    <Icon className="h-4 w-4" />
                  </div>
                  {!collapsed && (
                    <div className="flex-1 text-left">
                      <div className="font-medium">{item.label}</div>
                      <div className="text-xs text-slate-500">{item.description}</div>
                    </div>
                  )}
                  {item.badge && (
                    <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-xs text-rose-300">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </nav>

      {!collapsed && (
        <div className="border-t border-white/10 px-3 py-4">
          <div className="rounded-xl border border-white/10 bg-gradient-to-br from-blue-500/10 to-purple-500/10 px-3 py-3">
            <p className="text-xs text-slate-500">UX Next-Gen 2025</p>
            <p className="text-sm font-medium text-white">6 vues principales + alertes</p>
          </div>
        </div>
      )}
    </div>
  );
}
