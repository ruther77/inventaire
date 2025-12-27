import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Toaster } from 'sonner';
import { motion } from 'framer-motion';
import SidebarNav from './SidebarNav.jsx';
import TopBar from './TopBar.jsx';
import CommandBar from '../components/layout/CommandBar.jsx';
import BottomNav from '../components/layout/BottomNav.jsx';
import { CommandBarProvider } from '../contexts/CommandBarContext.jsx';
import OfflineBanner from '../components/feedback/OfflineBanner.jsx';

// ============================================================================
// APP SHELL 2025 - Unified Layout avec sidebar collapsible
// ============================================================================

// Routes qui n'affichent pas la TopBar (ont leur propre header)
const ROUTES_WITHOUT_TOPBAR = ['/operations'];

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  // Largeur du sidebar selon l'état
  const sidebarWidth = sidebarCollapsed ? 72 : 260;

  // Vérifier si la route actuelle doit masquer la TopBar
  const hideTopBar = ROUTES_WITHOUT_TOPBAR.some(
    (route) => location.pathname === route || location.pathname.startsWith(route + '/')
  );

  return (
    <CommandBarProvider>
      <div className="flex min-h-screen">
        {/* Bannière Offline/Online */}
        <OfflineBanner />

        {/* Sidebar */}
        <SidebarNav
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main content area - dynamic padding */}
        <motion.div
          className="flex flex-1 flex-col pb-16 lg:pb-0"
          initial={false}
          animate={{ paddingLeft: typeof window !== 'undefined' && window.innerWidth >= 1024 ? sidebarWidth : 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          {/* TopBar - Masquée sur certaines routes qui ont leur propre header */}
          {!hideTopBar && <TopBar onMenuToggle={() => setSidebarOpen(true)} />}

          {/* Page content */}
          <main className="flex-1 px-4 pb-12 pt-6 sm:px-6 lg:px-8">
            <div className="mx-auto w-full max-w-7xl">
              <Outlet />
            </div>
          </main>

          {/* Footer */}
          <footer className="px-6 py-4 border-t border-white/5">
            <div className="mx-auto max-w-7xl flex items-center justify-between text-xs text-slate-600">
              <p>© 2025 Inventaire Pro. Tous droits réservés.</p>
              <p>v2.0.0</p>
            </div>
          </footer>
        </motion.div>

        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'rgba(15, 15, 25, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#f8fafc',
              backdropFilter: 'blur(20px)',
            },
            className: 'glass-panel-elevated',
          }}
          richColors
          closeButton
        />

        {/* Command Bar (⌘K) */}
        <CommandBar />

        {/* Navigation mobile */}
        <BottomNav />
      </div>
    </CommandBarProvider>
  );
}
