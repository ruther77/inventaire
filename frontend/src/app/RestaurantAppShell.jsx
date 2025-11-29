import { Link, Outlet, useLocation } from 'react-router-dom';
import { useTenant, tenants } from '../context/TenantContext.jsx';
import { useAuth } from '../hooks/useAuth.js';
import Button from '../components/ui/Button.jsx';
import { LogOut } from 'lucide-react';

const buildIsActive = (currentPath, targetPath) => {
  if (targetPath === '/') {
    return currentPath === '/';
  }
  return currentPath === targetPath || currentPath.startsWith(`${targetPath}/`);
};

export default function RestaurantAppShell({ routes }) {
  const location = useLocation();
  const { tenant, setTenant, isTenantLocked } = useTenant();
  const { user, logout } = useAuth();

  const handleTenantChange = (event) => {
    const nextCode = event.target.value;
    const nextTenant = tenants.find((entry) => entry.code === nextCode);
    if (nextTenant) {
      setTenant(nextTenant);
    }
  };

  return (
    <div className="restaurant-shell">
      <div className="restaurant-hero">
        <div className="restaurant-hero__content">
          <div>
            <p className="restaurant-hero__eyebrow">Restaurant HQ</p>
            <h1>Chef cockpit & rentabilité</h1>
            <p className="restaurant-hero__subtitle">
              Suivez vos charges, structurez les fiches techniques et pilotez la carte du jour
              sans polluer les écrans de l’épicerie.
            </p>
          </div>
          <div className="flex flex-col items-end gap-3">
            <div className="restaurant-tenant-picker">
              <label htmlFor="tenant-select">Environnement</label>
              <select
                id="tenant-select"
                value={tenant.code}
                onChange={handleTenantChange}
                disabled={isTenantLocked}
              >
                {tenants.map((entry) => (
                  <option key={entry.code} value={entry.code}>
                    {entry.label}
                  </option>
                ))}
              </select>
              {isTenantLocked && (
                <small className="text-slate-200/80">Reconnectez-vous pour changer d’entreprise.</small>
              )}
            </div>
            {user && (
              <div className="flex items-center gap-3 rounded-2xl border border-white/30 bg-white/10 px-3 py-2 text-white shadow-sm backdrop-blur">
                <div className="flex flex-col text-right">
                  <p className="text-sm font-semibold leading-tight text-white">{user.username}</p>
                  <p className="text-[11px] uppercase tracking-[0.25em] text-white/80">{user.role}</p>
                </div>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 text-white hover:bg-white/10"
                  onClick={logout}
                >
                  <LogOut className="h-4 w-4" />
                  <span className="text-sm font-semibold">Déconnexion</span>
                </Button>
              </div>
            )}
          </div>
        </div>
        <nav className="restaurant-nav">
          {routes.map((route) => {
            const active = buildIsActive(location.pathname, route.path);
            return (
              <Link
                key={route.path}
                to={route.path}
                className={active ? 'active' : undefined}
                title={route.description}
              >
                {route.label}
              </Link>
            );
          })}
        </nav>
      </div>
      <main className="restaurant-main">
        <div className="restaurant-panel">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
