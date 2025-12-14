import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'sonner';
import SidebarNav from './SidebarNav.jsx';
import TopBar from './TopBar.jsx';
import CommandBar from '../components/layout/CommandBar.jsx';
import BottomNav from '../components/layout/BottomNav.jsx';
import { CommandBarProvider } from '../contexts/CommandBarContext.jsx';

// ============================================================================
// PAGE TRANSITION VARIANTS - Simplified for performance
// ============================================================================

const pageVariants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.15,
      ease: 'easeOut',
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: 0.1,
    },
  },
};

// ============================================================================
// APP SHELL 2025 - Unified Layout
// ============================================================================

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <CommandBarProvider>
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <SidebarNav
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main content area */}
        <div className="flex flex-1 flex-col lg:pl-72 pb-16 lg:pb-0">
          {/* TopBar */}
          <TopBar onMenuToggle={() => setSidebarOpen(true)} />

          {/* Page content */}
          <main className="flex-1 px-4 pb-12 pt-6 sm:px-6 lg:px-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                variants={pageVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="mx-auto w-full max-w-7xl"
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </main>

          {/* Footer */}
          <footer className="px-6 py-4 border-t border-white/5">
            <div className="mx-auto max-w-7xl flex items-center justify-between text-xs text-slate-600">
              <p>© 2025 Inventaire Pro. Tous droits réservés.</p>
              <p>v2.0.0</p>
            </div>
          </footer>
        </div>

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
