import { useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu,
  Search,
  Bell,
  HelpCircle,
  User,
  LogOut,
  Settings,
  ChevronDown,
  Command,
  X,
  Store,
  UtensilsCrossed,
  Brain,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../hooks/useAuth.js';
import { useTenant } from '../context/TenantContext.jsx';
import { useCommandBar } from '../contexts/CommandBarContext.jsx';
import { navigationSections } from './routes.jsx';

// ============================================================================
// TOPBAR 2025 - Design System from mockups/topbar.html
// ============================================================================

// Tenant icons mapping
const tenantIcons = {
  epicerie: Store,
  restaurant: UtensilsCrossed,
  intelligence: Brain,
};

const tenantLabels = {
  epicerie: 'Épicerie',
  restaurant: 'Restaurant',
  intelligence: 'Intelligence',
};

export default function TopBar({ onMenuToggle }) {
  const { user, logout } = useAuth();
  const { tenant, setTenant, availableTenants } = useTenant();
  const { open: openCommandBar } = useCommandBar();
  const location = useLocation();
  const navigate = useNavigate();

  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showTenantMenu, setShowTenantMenu] = useState(false);

  // Notifications mockées
  const notifications = [
    { id: 1, type: 'alert', message: 'Stock critique: Tomates', time: '2 min', severity: 'critical' },
    { id: 2, type: 'success', message: 'Facture METRO importée', time: '15 min', severity: 'success' },
    { id: 3, type: 'info', message: 'Nouvelle prévision disponible', time: '1h', severity: 'info' },
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

  const TenantIcon = tenantIcons[tenant?.code] || Store;

  return (
    <header className="topbar-container">
      <div className="topbar-inner">
        {/* LEFT SECTION */}
        <div className="topbar-left">
          {/* Mobile menu button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onMenuToggle}
            className="lg:hidden topbar-icon-btn"
          >
            <Menu className="w-5 h-5" />
          </motion.button>

          {/* Tenant Selector */}
          <div className="relative hidden md:block">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowTenantMenu(!showTenantMenu)}
              className="tenant-selector"
            >
              <div className="tenant-icon">
                <TenantIcon className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <span className="tenant-name">{tenantLabels[tenant?.code] || 'Sélectionner'}</span>
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </motion.button>

            {/* Tenant dropdown */}
            <AnimatePresence>
              {showTenantMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowTenantMenu(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute left-0 top-full mt-2 w-48 z-50 topbar-dropdown"
                  >
                    {(availableTenants || ['epicerie', 'restaurant', 'intelligence']).map((t) => {
                      const code = typeof t === 'string' ? t : t.code;
                      const Icon = tenantIcons[code] || Store;
                      const isActive = tenant?.code === code;
                      return (
                        <motion.button
                          key={code}
                          whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                          onClick={() => {
                            setTenant?.({ code, label: tenantLabels[code] });
                            setShowTenantMenu(false);
                          }}
                          className={clsx(
                            'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
                            isActive ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 hover:text-white'
                          )}
                        >
                          <Icon className="w-4 h-4" />
                          {tenantLabels[code]}
                        </motion.button>
                      );
                    })}
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          {/* Breadcrumb */}
          <div className="topbar-breadcrumb hidden md:flex">
            <span className="text-slate-500">{currentSection?.label || 'Accueil'}</span>
            {currentPage && currentPage.path !== '/' && (
              <>
                <span className="breadcrumb-separator">/</span>
                <span className="breadcrumb-current">{currentPage.label}</span>
              </>
            )}
          </div>
        </div>

        {/* CENTER SECTION - Search */}
        <div className="topbar-center">
          <motion.button
            onClick={openCommandBar}
            className="topbar-search"
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <Search className="search-icon" />
            <span className="search-placeholder">Rechercher produits, factures, fournisseurs...</span>
            <kbd className="search-shortcut">
              <Command className="w-3 h-3" />K
            </kbd>
          </motion.button>

          {/* Mobile search button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={openCommandBar}
            className="sm:hidden topbar-icon-btn"
          >
            <Search className="w-5 h-5" />
          </motion.button>
        </div>

        {/* RIGHT SECTION */}
        <div className="topbar-right">
          {/* Notifications */}
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowNotifications(!showNotifications)}
              className="topbar-icon-btn"
            >
              <Bell className="w-[18px] h-[18px]" />
              {unreadCount > 0 && (
                <span className="notification-badge">{unreadCount}</span>
              )}
            </motion.button>

            {/* Notifications dropdown */}
            <AnimatePresence>
              {showNotifications && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 top-full mt-2 w-96 z-50 topbar-dropdown"
                  >
                    <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                      <h3 className="text-sm font-semibold text-white">Notifications</h3>
                      <button className="text-xs text-blue-400 hover:text-blue-300">
                        Tout marquer comme lu
                      </button>
                    </div>
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
                          <button className="p-1 rounded-lg hover:bg-white/10">
                            <X className="w-3 h-3 text-slate-500" />
                          </button>
                        </motion.div>
                      ))}
                    </div>
                    <div className="px-4 py-3 border-t border-white/10 bg-white/5">
                      <button className="w-full text-center text-xs text-blue-400 hover:text-blue-300">
                        Voir toutes les notifications
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          {/* Help button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="topbar-icon-btn hidden sm:flex"
          >
            <HelpCircle className="w-[18px] h-[18px]" />
          </motion.button>

          {/* User menu */}
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="topbar-user"
            >
              <div className="user-avatar">
                {getInitials(user?.username)}
              </div>
              <div className="user-info hidden sm:block">
                <div className="user-name">{user?.username || 'Utilisateur'}</div>
                <div className="user-role">{user?.role || 'Administrateur'}</div>
              </div>
              <ChevronDown className="w-3 h-3 text-slate-500 hidden sm:block" />
            </motion.button>

            {/* User dropdown */}
            <AnimatePresence>
              {showUserMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 top-full mt-2 w-64 z-50 topbar-dropdown"
                  >
                    {/* User info header */}
                    <div className="px-4 py-4 border-b border-white/10 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10">
                      <div className="flex items-center gap-3">
                        <div className="user-avatar-lg">
                          {getInitials(user?.username)}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-white">{user?.username}</p>
                          <p className="text-xs text-slate-400">{user?.email || `${user?.username}@example.com`}</p>
                          <span className="inline-flex items-center mt-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-[10px] text-emerald-400 font-medium">
                            {user?.role || 'admin'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Menu items */}
                    <div className="py-2">
                      <motion.button
                        whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-400 hover:text-white"
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
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-400 hover:text-white"
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
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-rose-400 hover:text-rose-300"
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
