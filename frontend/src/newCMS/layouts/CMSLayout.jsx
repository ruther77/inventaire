import { useCallback, useMemo, useState } from 'react';
import { routes, navigationSections, keyboardShortcuts } from '../routes.jsx';
import { CommandBar, SidebarNav, TopBar } from '../components';
import { useCommandBar } from '../hooks/useCommandBar.js';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts.js';
import { AlertsProvider } from '../contexts/AlertsContext.jsx';
import { TenantProvider } from '../contexts/TenantContext.jsx';

export default function CMSLayout({ children, activePath = '/', onNavigate }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleNavigate = useCallback(
    (path) => {
      if (onNavigate) {
        onNavigate(path);
      } else if (typeof window !== 'undefined') {
        window.history.pushState({}, '', path);
      }
    },
    [onNavigate]
  );

  const navActions = useMemo(
    () =>
      routes.map((route) => ({
        id: route.path,
        label: route.label,
        description: route.description,
        icon: route.icon,
        shortcut: keyboardShortcuts.find((s) => s.action.toLowerCase().includes(route.label.toLowerCase()))?.key,
        onSelect: () => handleNavigate(route.path),
      })),
    [handleNavigate]
  );

  const extraActions = useMemo(
    () => [
      {
        id: 'alerts',
        label: 'Ouvrir le centre d’alertes',
        description: 'Consulter et traiter les urgences',
        icon: routes.find((r) => r.path === '/alerts')?.icon,
        onSelect: () => handleNavigate('/alerts'),
      },
      {
        id: 'import',
        label: 'Lancer un import facture',
        description: 'Dropzone Ops - Zero-click async',
        onSelect: () => handleNavigate('/operations'),
      },
      {
        id: 'cashflow',
        label: 'Prévoir le cash 7j',
        description: 'Finance > Trésorerie',
        onSelect: () => handleNavigate('/finances'),
      },
    ],
    [handleNavigate]
  );

  const commandBar = useCommandBar([...navActions, ...extraActions]);

  const hotkeyHandlers = useMemo(() => {
    const mapping = {};
    routes.forEach((route, idx) => {
      const key = `cmd+${idx + 1}`;
      mapping[key] = (event) => {
        event.preventDefault();
        handleNavigate(route.path);
      };
    });
    mapping.esc = () => commandBar.close();
    return mapping;
  }, [commandBar, handleNavigate]);

  useKeyboardShortcuts(hotkeyHandlers);

  const sidebarSections = navigationSections.map((section) => ({
    ...section,
    description: routes.find((r) => r.path === section.path)?.description,
  }));
  const extraRoutes = routes.filter((route) => !navigationSections.find((section) => section.path === route.path));

  return (
    <TenantProvider>
      <AlertsProvider>
        <div className="flex min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
          <SidebarNav
            sections={sidebarSections}
            extras={extraRoutes}
            activePath={activePath}
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed((v) => !v)}
            onNavigate={handleNavigate}
          />

          <div className="flex flex-1 flex-col overflow-hidden">
            <TopBar
              sidebarCollapsed={sidebarCollapsed}
              onToggleSidebar={() => setSidebarCollapsed((v) => !v)}
              onOpenCommandBar={commandBar.open}
            />

            <main className="flex-1 overflow-auto p-6 space-y-6">{children}</main>
          </div>
        </div>

        <CommandBar
          open={commandBar.isOpen}
          onClose={commandBar.close}
          actions={commandBar.filteredActions}
          query={commandBar.query}
          onQueryChange={commandBar.setQuery}
          onSelect={(action) => action.onSelect?.()}
        />
      </AlertsProvider>
    </TenantProvider>
  );
}
