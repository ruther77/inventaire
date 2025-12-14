import { useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu,
  Search,
  Bell,
  User,
  LogOut,
  Settings,
  ChevronDown,
  Command,
  Sparkles,
  Calendar,
  Building2,
  RefreshCw,
  Check,
  X,
  AlertTriangle,
  TrendingUp,
  Package,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../hooks/useAuth.js';
import { useTenant } from '../context/TenantContext.jsx';
import { useCommandBar } from '../contexts/CommandBarContext.jsx';
import { navigationSections } from './routes.jsx';

// ============================================================================
// TOPBAR 2025 - Contextuelle avec Command Bar
// ============================================================================

export default function TopBar({ onMenuToggle }) {
  const { user, logout } = useAuth();
  const { tenant } = useTenant();
  const { open: openCommandBar, currentContext } = useCommandBar();
  const location = useLocation();
  const navigate = useNavigate();

  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showContextMenu, setShowContextMenu] = useState(false);

  // Notifications mockées (à remplacer par vraies données)
  const notifications = [
    { id: 1, type: 'alert', message: 'Stock critique: Tomates', time: '2 min', severity: 'critical' },
    { id: 2, type: 'success', message: 'Facture METRO importée', time: '15 min', severity: 'success' },
    { id: 3, type: 'info', message: 'Nouvelle prévision disponible', time: '1h', severity: 'info' },
    { id: 4, type: 'warning', message: '3 anomalies détectées', time: '2h', severity: 'warning' },
  ];

  const unreadCount = notifications.length;

  // Contexte actuel basé sur la route
  const currentSection = useMemo(() => {
    const path = location.pathname;
    return navigationSections.find((section) =>
      section.routes.some((route) => {
        if (route.path === '/') return path === '/';
        return path.startsWith(route.path.split('/').slice(0, 2).join('/'));
      })
    ) || navigationSections[0];
  }, [location.pathname]);

  // Page actuelle
  const currentPage = useMemo(() => {
    const path = location.pathname;
    for (const section of navigationSections) {
      const route = section.routes.find((r) => r.path === path);
      if (route) return route;
    }
    return null;
  }, [location.pathname]);

  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-rose-500';
      case 'warning': return 'bg-amber-500';
      case 'success': return 'bg-emerald-500';
      default: return 'bg-blue-500';
    }
  };

  return (
    <header className="topbar">
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onMenuToggle}
          className="lg:hidden btn-icon"
        >
          <Menu className="w-5 h-5" />
        </motion.button>

        {/* Context indicator (Section + Page) */}
        <div className="hidden md:flex items-center gap-2">
          {/* Section badge */}
          <motion.div
            className={clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-xl',
              'bg-gradient-to-r',
              currentSection?.gradient || 'from-slate-500 to-slate-600',
              'text-white text-xs font-medium'
            )}
          >
            {currentSection?.icon && <currentSection.icon className="w-3.5 h-3.5" />}
            <span>{currentSection?.label || 'Accueil'}</span>
          </motion.div>

          {/* Page indicator */}
          {currentPage && currentPage.path !== '/' && (
            <>
              <span className="text-slate-600">/</span>
              <span className="text-sm text-slate-400">{currentPage.label}</span>
            </>
          )}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Search bar / Command Bar trigger */}
        <motion.button
          onClick={openCommandBar}
          className={clsx(
            'hidden sm:flex items-center gap-3 px-4 py-2.5 rounded-xl',
            'bg-white/5 border border-white/10 text-slate-400',
            'hover:bg-white/10 hover:border-white/20 hover:text-white',
            'transition-all duration-200 min-w-[280px]'
          )}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          <Search className="w-4 h-4" />
          <span className="flex-1 text-left text-sm">Rechercher...</span>
          <kbd className="flex items-center gap-0.5 px-2 py-1 rounded-md bg-white/10 text-[10px] text-slate-500 font-mono">
            <Command className="w-3 h-3" />K
          </kbd>
        </motion.button>

        {/* Mobile search button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={openCommandBar}
          className="sm:hidden btn-icon"
        >
          <Search className="w-5 h-5" />
        </motion.button>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Quick action button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/operations/factures')}
            className="hidden lg:flex items-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 text-emerald-400 text-sm font-medium transition-all hover:from-emerald-500/30 hover:to-teal-500/30"
          >
            <Package className="w-4 h-4" />
            <span>Import</span>
          </motion.button>

          {/* Notifications */}
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowNotifications(!showNotifications)}
              className="btn-icon relative"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-rose-500 text-[10px] font-bold text-white flex items-center justify-center"
                >
                  {unreadCount}
                </motion.span>
              )}
            </motion.button>

            {/* Notifications dropdown */}
            <AnimatePresence>
              {showNotifications && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowNotifications(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    className="absolute right-0 top-full mt-2 w-96 z-50 glass-panel-elevated rounded-2xl overflow-hidden"
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                      <h3 className="text-sm font-semibold text-white">Notifications</h3>
                      <button className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
                        Tout marquer comme lu
                      </button>
                    </div>

                    {/* Notifications list */}
                    <div className="max-h-96 overflow-y-auto">
                      {notifications.map((notif) => (
                        <motion.div
                          key={notif.id}
                          whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                          className="flex items-start gap-3 px-4 py-3 cursor-pointer border-b border-white/5 last:border-0"
                        >
                          <div className={clsx('w-2 h-2 mt-2 rounded-full', getSeverityColor(notif.severity))} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white">{notif.message}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{notif.time}</p>
                          </div>
                          <button className="p-1 rounded-lg hover:bg-white/10 transition-colors">
                            <X className="w-3 h-3 text-slate-500" />
                          </button>
                        </motion.div>
                      ))}
                    </div>

                    {/* Footer */}
                    <div className="px-4 py-3 border-t border-white/10 bg-white/5">
                      <button className="w-full text-center text-xs text-blue-400 hover:text-blue-300 transition-colors">
                        Voir toutes les notifications
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          {/* User menu */}
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-semibold">
                {getInitials(user?.username)}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium text-white">{user?.username || 'Utilisateur'}</p>
                <p className="text-[10px] text-slate-500 uppercase tracking-wide">
                  {tenant?.label || 'Inventaire Pro'}
                </p>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-500" />
            </motion.button>

            {/* User dropdown */}
            <AnimatePresence>
              {showUserMenu && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowUserMenu(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    className="absolute right-0 top-full mt-2 w-64 z-50 glass-panel-elevated rounded-2xl overflow-hidden"
                  >
                    {/* User info header */}
                    <div className="px-4 py-4 border-b border-white/10 bg-gradient-to-br from-blue-500/10 to-purple-500/10">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-lg font-semibold">
                          {getInitials(user?.username)}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-white">{user?.username}</p>
                          <p className="text-xs text-slate-400">{user?.email || `${user?.username}@example.com`}</p>
                          <span className="inline-flex items-center mt-1 px-2 py-0.5 rounded-full bg-blue-500/20 text-[10px] text-blue-400 font-medium">
                            {user?.role || 'admin'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Menu items */}
                    <div className="py-2">
                      <motion.button
                        whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-400 hover:text-white transition-colors"
                      >
                        <User className="w-4 h-4" />
                        Mon profil
                      </motion.button>
                      <motion.button
                        whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                        onClick={() => {
                          setShowUserMenu(false);
                          navigate('/parametres/audit');
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-400 hover:text-white transition-colors"
                      >
                        <Settings className="w-4 h-4" />
                        Paramètres
                      </motion.button>
                    </div>

                    {/* Logout */}
                    <div className="py-2 border-t border-white/10">
                      <motion.button
                        whileHover={{ backgroundColor: 'rgba(244,63,94,0.1)' }}
                        onClick={logout}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-rose-400 hover:text-rose-300 transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        Se déconnecter
                      </motion.button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </header>
  );
}
