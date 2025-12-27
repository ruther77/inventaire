import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, X, ChevronLeft, Menu } from 'lucide-react';
import clsx from 'clsx';
import { navigationSections } from './routes.jsx';

// ============================================================================
// SIDEBAR NAVIGATION - Design 2025 (basé sur mockup)
// ============================================================================

// Mapping des icônes emoji par section/route
const emojiMap = {
  cockpit: '📊',
  operations: '📦',
  finances: '💳',
  restaurant: '🍽️',
  intelligence: '🧠',
  parametres: '⚙️',
  // Routes spécifiques
  '/': '📊',
  '/operations': '📦',
  '/operations/factures': '📄',
  '/operations/catalogue': '🛒',
  '/operations/stock': '📈',
  '/operations/prix': '💰',
  '/operations/approvisionnement': '🚚',
  '/intelligence/scoring/suppliers': '🏭',
  '/finances': '💳',
  '/finances/transactions': '💸',
  '/finances/comptes': '🏦',
  '/finances/rapprochement': '🔗',
  '/finances/imports': '📥',
  '/restaurant/plats': '🍽️',
  '/restaurant/ingredients': '🥬',
  '/restaurant/consommation': '📉',
  '/restaurant/charges': '💵',
  '/restaurant/previsions': '📅',
  '/restaurant/food-cost': '🧮',
  '/restaurant/link-epicerie': '🔗',
  '/intelligence': '🧠',
  '/parametres/audit': '🔍',
  '/parametres/regles': '📋',
};

const getEmoji = (sectionId, path) => {
  if (path && emojiMap[path]) return emojiMap[path];
  if (sectionId && emojiMap[sectionId]) return emojiMap[sectionId];
  return '📁';
};

// Badge component
function Badge({ count }) {
  if (!count) return null;
  return (
    <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-rose-500/20 text-rose-400">
      {count}
    </span>
  );
}

// Collapsed badge (just a dot)
function CollapsedBadge({ show }) {
  if (!show) return null;
  return (
    <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500" />
  );
}

export default function SidebarNav({ isOpen, onClose, isCollapsed = false, onToggleCollapse }) {
  const location = useLocation();
  const [expandedSections, setExpandedSections] = useState(['operations']);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Auto-expand section based on current route
  useEffect(() => {
    const currentSection = navigationSections.find((section) =>
      section.routes?.some((route) => {
        if (route.path === '/') return location.pathname === '/';
        return location.pathname.startsWith(route.path);
      })
    );
    if (currentSection && !expandedSections.includes(currentSection.id)) {
      setExpandedSections((prev) => [...prev, currentSection.id]);
    }
  }, [location.pathname]);

  const toggleSection = (sectionId) => {
    setExpandedSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((id) => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const isRouteActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const isSectionActive = (section) => {
    if (section.isUnified && section.directPath) {
      return location.pathname.startsWith(section.directPath);
    }
    if (section.isHome) {
      return location.pathname === '/';
    }
    return section.routes?.some((route) => isRouteActive(route.path));
  };

  const handleClose = () => onClose?.();

  const toggleCollapse = () => onToggleCollapse?.();

  // Sidebar width
  const sidebarWidth = isCollapsed ? 72 : 260;

  return (
    <>
      {/* Overlay for mobile */}
      <AnimatePresence>
        {isOpen && isMobile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={handleClose}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isMobile ? 260 : sidebarWidth,
          x: isMobile && !isOpen ? -260 : 0
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col',
          'bg-[rgba(15,15,25,0.98)] border-r border-white/10',
          isMobile && !isOpen && '-translate-x-full',
          'lg:translate-x-0'
        )}
      >
        {/* Header */}
        <div className={clsx(
          'flex items-center border-b border-white/10',
          isCollapsed ? 'justify-center px-3 py-5' : 'justify-between px-5 py-5'
        )}>
          {isCollapsed ? (
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-xl">
              📦
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-lg">
                📦
              </div>
              <span className="font-display text-lg font-semibold text-white">Inventaire</span>
            </div>
          )}

          {/* Close button (mobile) */}
          {isMobile && (
            <button
              onClick={handleClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
            >
              <X className="w-5 h-5" />
            </button>
          )}

          {/* Collapse toggle (desktop) */}
          {!isMobile && !isCollapsed && (
            <button
              onClick={toggleCollapse}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
              title="Réduire"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Expand button when collapsed */}
        {isCollapsed && !isMobile && (
          <button
            onClick={toggleCollapse}
            className="mx-3 mt-3 p-3 rounded-xl text-slate-400 hover:text-white hover:bg-white/5"
            title="Étendre"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        {/* Navigation */}
        <nav className={clsx(
          'flex-1 overflow-y-auto py-4',
          isCollapsed ? 'px-3' : 'px-3'
        )}>
          {navigationSections.map((section, idx) => {
            const isExpanded = expandedSections.includes(section.id);
            const sectionActive = isSectionActive(section);
            const emoji = getEmoji(section.id);

            // Divider before section (except first)
            const showDivider = idx > 0 && (idx === 1 || idx === 3 || idx === 4);

            return (
              <div key={section.id}>
                {showDivider && (
                  <div className={clsx(
                    'my-3',
                    isCollapsed ? 'mx-2 w-8 h-px bg-white/10' : 'h-px bg-white/10'
                  )} />
                )}

                {/* Section Title (expanded only) */}
                {!isCollapsed && idx > 0 && (
                  <div className="px-3 py-2 text-[11px] uppercase tracking-wider text-slate-500">
                    {section.label}
                  </div>
                )}

                {/* Home or Unified sections - direct link */}
                {(section.isHome || section.isUnified) ? (
                  <NavLink
                    to={section.directPath || '/'}
                    onClick={handleClose}
                    className={({ isActive }) =>
                      clsx(
                        'relative flex items-center gap-3 rounded-xl mb-1 transition-all',
                        isCollapsed ? 'w-12 h-12 justify-center mx-auto' : 'px-3 py-3',
                        isActive
                          ? 'bg-emerald-500/15 text-emerald-400'
                          : 'text-slate-400 hover:text-white hover:bg-white/5'
                      )
                    }
                    title={isCollapsed ? section.label : undefined}
                  >
                    <span className={clsx('text-lg', isCollapsed && 'text-xl')}>{emoji}</span>
                    {!isCollapsed && (
                      <span className="text-sm font-medium flex-1">{section.label}</span>
                    )}
                    <CollapsedBadge show={isCollapsed && section.badge} />
                  </NavLink>
                ) : (
                  <>
                    {/* Expandable section header */}
                    {isCollapsed ? (
                      // Collapsed: show first route as main icon
                      <NavLink
                        to={section.routes?.[0]?.path || '/'}
                        onClick={handleClose}
                        className={clsx(
                          'relative w-12 h-12 flex items-center justify-center rounded-xl mb-1 mx-auto transition-all',
                          sectionActive
                            ? 'bg-emerald-500/15 text-emerald-400'
                            : 'text-slate-400 hover:text-white hover:bg-white/5'
                        )}
                        title={section.label}
                      >
                        <span className="text-xl">{emoji}</span>
                        <CollapsedBadge show={section.badge} />
                      </NavLink>
                    ) : (
                      <>
                        <button
                          onClick={() => toggleSection(section.id)}
                          className={clsx(
                            'w-full flex items-center gap-3 px-3 py-3 rounded-xl mb-1 transition-all',
                            sectionActive
                              ? 'bg-white/5 text-white'
                              : 'text-slate-400 hover:text-white hover:bg-white/5'
                          )}
                        >
                          <span className="text-lg">{emoji}</span>
                          <span className="text-sm font-medium flex-1 text-left">{section.label}</span>
                          {section.badge && <Badge count={section.badge} />}
                          <motion.div
                            animate={{ rotate: isExpanded ? 180 : 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <ChevronDown className="w-4 h-4 text-slate-500" />
                          </motion.div>
                        </button>

                        {/* Submenu */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="overflow-hidden"
                            >
                              <div className="ml-4 pl-3 border-l border-white/5 space-y-0.5">
                                {section.routes?.map((route) => {
                                  const isActive = isRouteActive(route.path);
                                  const routeEmoji = getEmoji(null, route.path);

                                  return (
                                    <NavLink
                                      key={route.path}
                                      to={route.path}
                                      onClick={handleClose}
                                      className={clsx(
                                        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all',
                                        isActive
                                          ? 'bg-white/10 text-white'
                                          : 'text-slate-500 hover:text-white hover:bg-white/5'
                                      )}
                                    >
                                      <span className="text-base">{routeEmoji}</span>
                                      <span className="text-sm flex-1">{route.label}</span>
                                      {isActive && <ChevronRight className="w-3 h-3 text-slate-500" />}
                                    </NavLink>
                                  );
                                })}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </nav>

        {/* Footer - User Profile */}
        <div className={clsx(
          'border-t border-white/10',
          isCollapsed ? 'p-3' : 'p-4'
        )}>
          {isCollapsed ? (
            <div
              className="w-10 h-10 mx-auto rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-sm font-semibold text-white cursor-pointer"
              title="Jean Dupont - Admin"
            >
              JD
            </div>
          ) : (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/3 hover:bg-white/5 cursor-pointer transition-colors">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-sm font-semibold text-white">
                JD
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">Jean Dupont</p>
                <p className="text-xs text-slate-500">Admin</p>
              </div>
            </div>
          )}

          {/* Version */}
          {!isCollapsed && (
            <p className="text-center text-[10px] text-slate-600 mt-3">
              v2.0.0 • Inventaire Pro
            </p>
          )}
        </div>
      </motion.aside>
    </>
  );
}
