import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';
import SidebarNav from './SidebarNav.jsx';
import TopBar from './TopBar.jsx';

export default function AppShell({ routes }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-100">
      <SidebarNav routes={routes} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-1 flex-col lg:pl-72">
        <TopBar onMenuToggle={() => setSidebarOpen(true)} />
        <main className="flex-1 px-4 pb-12 pt-6 sm:px-8">
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
            <Outlet />
          </div>
        </main>
      </div>
      <Toaster position="top-right" richColors closeButton />
    </div>
  );
}
