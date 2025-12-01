import { Menu, Bell, Search, Sparkles, LogOut, ShieldAlert } from 'lucide-react';
import Button from '../components/ui/Button.jsx';
import { useTenant, tenants } from '../context/TenantContext.jsx';
import { useAuth } from '../hooks/useAuth.js';

export default function TopBar({ onMenuToggle }) {
  const { tenant, setTenant, isTenantLocked } = useTenant();
  const { user, logout } = useAuth();
  const appEnv = (import.meta.env.VITE_APP_ENV || 'dev').toLowerCase();
  const envLabel = appEnv === 'production' || appEnv === 'prod' ? 'PROD' : appEnv === 'staging' ? 'STAGING' : 'DEV';
  const envTone =
    envLabel === 'PROD' ? 'bg-red-100 text-red-700 border-red-200' : envLabel === 'STAGING' ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-emerald-100 text-emerald-700 border-emerald-200';

  const handleTenantChange = (event) => {
    const next = tenants.find((entry) => entry.code === event.target.value);
    if (next) {
      setTenant(next);
    }
  };

  const initials = (user?.username ?? tenant.code)
    .split(' ')
    .map((chunk) => chunk.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('');

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/60 bg-slate-50/60 px-4 py-4 backdrop-blur sm:px-8">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-4">
        <Button variant="ghost" className="lg:hidden" iconOnly onClick={onMenuToggle}>
          <Menu className="h-5 w-5" />
        </Button>
        <div className="relative hidden flex-1 items-center lg:flex">
          <Search className="absolute left-4 h-4 w-4 text-slate-400" />
          <input
            type="search"
            placeholder="Rechercher un produit ou une commande"
            className="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-12 pr-4 text-sm text-slate-700 shadow-sm focus:border-brand-400 focus:outline-none"
          />
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-3">
          <div className={`flex items-center gap-2 rounded-2xl border px-3 py-2 text-xs font-semibold uppercase tracking-wide ${envTone}`}>
            <ShieldAlert className="h-4 w-4" />
            <span>{envLabel}</span>
            <span className="rounded-lg bg-white/60 px-2 py-0.5 text-[11px] text-slate-700">{tenant.label}</span>
          </div>
          <Button variant="ghost" iconOnly>
            <Sparkles className="h-5 w-5 text-brand-500" />
          </Button>
          <Button variant="ghost" iconOnly>
            <Bell className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <div className="flex flex-col">
              <p className="text-xs uppercase tracking-wider text-slate-400">Environnement</p>
              <select
                value={tenant.code}
                onChange={handleTenantChange}
                disabled={isTenantLocked}
                className="border-none bg-transparent text-sm font-semibold text-slate-900 focus:outline-none disabled:cursor-not-allowed disabled:text-slate-400"
              >
                {tenants.map((entry) => (
                  <option key={entry.code} value={entry.code}>
                    {entry.label}
                  </option>
                ))}
              </select>
              {isTenantLocked && (
                <p className="text-[11px] text-slate-400">Déconnexion requise pour changer</p>
              )}
            </div>
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white">
              <div className="flex h-full w-full items-center justify-center font-semibold">{initials}</div>
            </div>
          </div>
          {user && (
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
              <div className="flex flex-col text-right">
                <p className="text-sm font-semibold text-slate-900">{user.username}</p>
                <p className="text-xs uppercase tracking-wider text-slate-400">{user.role}</p>
              </div>
              <Button variant="ghost" iconOnly title="Se déconnecter" onClick={logout}>
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
