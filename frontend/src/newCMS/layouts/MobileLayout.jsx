import MobileBottomNav from '../components/MobileBottomNav.jsx';
import ToastManager from '../components/ToastManager.jsx';

/**
 * Layout mobile générique avec barre de navigation inférieure.
 */
export default function MobileLayout({ children, navItems = [], header }) {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {header}
      <div className="flex-1 overflow-auto pb-20">{children}</div>
      <MobileBottomNav items={navItems} />
      <ToastManager />
    </div>
  );
}
