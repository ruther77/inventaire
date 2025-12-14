import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, X, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import { navigationSections } from './routes.jsx';

// ============================================================================
// ANIMATION VARIANTS - Premium 2025 Motion
// ============================================================================

const sidebarVariants = {
  hidden: { x: '-100%', opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      staggerChildren: 0.05,
    },
  },
  exit: {
    x: '-100%',
    opacity: 0,
    transition: { duration: 0.2 },
  },
};

const itemVariants = {
  hidden: { x: -20, opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: { type: 'spring', stiffness: 300, damping: 24 },
  },
};

const submenuVariants = {
  hidden: { height: 0, opacity: 0 },
  visible: {
    height: 'auto',
    opacity: 1,
    transition: {
      height: { type: 'spring', stiffness: 500, damping: 40 },
      opacity: { duration: 0.2 },
    },
  },
  exit: {
    height: 0,
    opacity: 0,
    transition: { duration: 0.15 },
  },
};

const glowVariants = {
  rest: { scale: 1, opacity: 0 },
  hover: {
    scale: 1.5,
    opacity: 0.5,
    transition: { duration: 0.3 },
  },
};

// ============================================================================
// SIDEBAR NAVIGATION COMPONENT
// ============================================================================

export default function SidebarNav({ isOpen, onClose }) {
  const location = useLocation();
  const [expandedSections, setExpandedSections] = useState(['cockpit']);
  const [hoveredItem, setHoveredItem] = useState(null);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile/desktop on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Auto-expand section based on current route
  useEffect(() => {
    const currentSection = navigationSections.find((section) =>
      section.routes.some((route) => {
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
    // Pour les vues unifiées, vérifier si on est sur le directPath ou une sous-route
    if (section.isUnified && section.directPath) {
      return location.pathname.startsWith(section.directPath);
    }
    return section.routes.some((route) => isRouteActive(route.path));
  };

  // Handle close for mobile
  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  return (
    <>
      {/* Overlay for mobile - clickable to close */}
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
        initial={!isMobile ? false : 'hidden'}
        animate={isOpen || !isMobile ? 'visible' : 'hidden'}
        exit="exit"
        variants={sidebarVariants}
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-72 flex flex-col',
          'glass-sidebar',
          isMobile && !isOpen && '-translate-x-full',
          'lg:translate-x-0'
        )}
      >
        {/* Logo & Brand */}
        <div className="flex items-center justify-between px-6 py-6 border-b border-white/5">
          <motion.div
            className="flex items-center gap-3"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -inset-1 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 opacity-30 blur-lg" />
            </div>
            <div>
              <h1 className="font-display text-lg font-bold text-white">Inventaire</h1>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Pro 2025</p>
            </div>
          </motion.div>

          {/* Close button (mobile) - larger touch target */}
          <button
            onClick={handleClose}
            className="lg:hidden p-3 -mr-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 active:bg-white/20 transition-colors"
            style={{
              touchAction: 'manipulation',
              minWidth: '48px',
              minHeight: '48px',
              WebkitTapHighlightColor: 'transparent'
            }}
            aria-label="Fermer le menu"
            type="button"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navigationSections.map((section, sectionIndex) => {
            const isExpanded = expandedSections.includes(section.id);
            const sectionActive = isSectionActive(section);
            const SectionIcon = section.icon;

            return (
              <motion.div
                key={section.id}
                variants={itemVariants}
                custom={sectionIndex}
              >
                {/* Section avec lien direct (Home ou Vue unifiée) */}
                {section.isHome || section.isUnified ? (
                  <NavLink
                    to={section.directPath || '/'}
                    onClick={handleClose}
                    className={({ isActive }) =>
                      clsx(
                        'group relative flex items-center gap-3 px-4 py-3 rounded-xl',
                        'transition-all duration-300',
                        isActive
                          ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/10 text-white'
                          : 'text-slate-400 hover:text-white hover:bg-white/5'
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {/* Glow effect */}
                        <motion.div
                          className={clsx(
                            'absolute left-0 top-1/2 -translate-y-1/2 w-1 rounded-full',
                            `bg-gradient-to-b ${section.gradient}`
                          )}
                          initial={{ height: 0, opacity: 0 }}
                          animate={{
                            height: isActive ? 32 : 0,
                            opacity: isActive ? 1 : 0,
                          }}
                          style={{
                            boxShadow: isActive ? `0 0 20px var(--color-accent-${section.color || 'blue'})` : 'none',
                          }}
                        />

                        <div className={clsx(
                          'relative p-2 rounded-lg',
                          isActive ? `bg-gradient-to-br ${section.gradient}` : 'bg-white/5'
                        )}>
                          <SectionIcon className="w-4 h-4" />
                          {isActive && (
                            <div className="absolute inset-0 rounded-lg bg-white/20 animate-pulse" />
                          )}
                        </div>

                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{section.label}</p>
                          <p className="text-[11px] text-slate-500 truncate">{section.description}</p>
                        </div>

                        {/* Active indicator dot */}
                        {isActive && (
                          <motion.div
                            layoutId={`activeIndicator-${section.id}`}
                            className={clsx(
                              'w-2 h-2 rounded-full',
                              section.color === 'emerald' ? 'bg-emerald-400' :
                              section.color === 'violet' ? 'bg-violet-400' :
                              section.color === 'pink' ? 'bg-pink-400' : 'bg-blue-400'
                            )}
                            style={{ boxShadow: `0 0 10px rgba(59, 130, 246, 0.8)` }}
                          />
                        )}
                      </>
                    )}
                  </NavLink>
                ) : (
                  <>
                    {/* Section header expandable */}
                    <button
                      onClick={() => toggleSection(section.id)}
                      onMouseEnter={() => setHoveredItem(section.id)}
                      onMouseLeave={() => setHoveredItem(null)}
                      className={clsx(
                        'group relative w-full flex items-center gap-3 px-4 py-3 rounded-xl',
                        'transition-all duration-300',
                        sectionActive
                          ? 'bg-white/5 text-white'
                          : 'text-slate-400 hover:text-white hover:bg-white/5'
                      )}
                    >
                      {/* Glow on hover */}
                      <motion.div
                        className={clsx(
                          'absolute left-0 top-1/2 -translate-y-1/2 w-1 rounded-full',
                          `bg-gradient-to-b ${section.gradient}`
                        )}
                        initial={{ height: 0, opacity: 0 }}
                        animate={{
                          height: sectionActive || hoveredItem === section.id ? 24 : 0,
                          opacity: sectionActive || hoveredItem === section.id ? 1 : 0,
                        }}
                        style={{
                          boxShadow: sectionActive ? `0 0 15px var(--color-accent-${section.color})` : 'none',
                        }}
                      />

                      <div className={clsx(
                        'relative p-2 rounded-lg transition-colors duration-200',
                        sectionActive ? `bg-gradient-to-br ${section.gradient}` : 'bg-white/5 group-hover:bg-white/10'
                      )}>
                        <SectionIcon className="w-4 h-4" />
                      </div>

                      <div className="flex-1 min-w-0 text-left">
                        <p className="font-medium text-sm">{section.label}</p>
                        <p className="text-[11px] text-slate-500 truncate">{section.description}</p>
                      </div>

                      <motion.div
                        animate={{ rotate: isExpanded ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                        className="text-slate-500"
                      >
                        <ChevronDown className="w-4 h-4" />
                      </motion.div>
                    </button>

                    {/* Submenu */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          variants={submenuVariants}
                          initial="hidden"
                          animate="visible"
                          exit="exit"
                          className="overflow-hidden"
                        >
                          <div className="ml-4 pl-4 mt-1 space-y-0.5 border-l border-white/5">
                            {section.routes.map((route) => {
                              const RouteIcon = route.icon;
                              const isActive = isRouteActive(route.path);

                              return (
                                <NavLink
                                  key={route.path}
                                  to={route.path}
                                  onClick={handleClose}
                                  className={clsx(
                                    'group relative flex items-center gap-3 px-3 py-2.5 rounded-lg',
                                    'transition-all duration-200',
                                    isActive
                                      ? 'bg-white/10 text-white'
                                      : 'text-slate-500 hover:text-white hover:bg-white/5 hover:pl-4'
                                  )}
                                >
                                  {/* Dot indicator */}
                                  <motion.div
                                    className={clsx(
                                      'absolute -left-4 w-1.5 h-1.5 rounded-full',
                                      isActive
                                        ? `bg-gradient-to-br ${section.gradient}`
                                        : 'bg-slate-700 group-hover:bg-slate-500'
                                    )}
                                    animate={{
                                      scale: isActive ? 1.2 : 1,
                                      boxShadow: isActive
                                        ? `0 0 8px var(--color-accent-${section.color})`
                                        : 'none',
                                    }}
                                  />

                                  <RouteIcon className={clsx(
                                    'w-4 h-4 transition-colors',
                                    isActive ? 'text-white' : 'text-slate-600 group-hover:text-slate-400'
                                  )} />

                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm truncate">{route.label}</p>
                                  </div>

                                  {isActive && (
                                    <ChevronRight className="w-3 h-3 text-slate-500" />
                                  )}
                                </NavLink>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </>
                )}
              </motion.div>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/5">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="relative overflow-hidden rounded-2xl p-4"
            style={{
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            {/* Animated gradient border */}
            <div className="absolute inset-0 rounded-2xl opacity-50">
              <div
                className="absolute inset-0 rounded-2xl"
                style={{
                  background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899, #3b82f6)',
                  backgroundSize: '300% 100%',
                  animation: 'border-flow 4s linear infinite',
                  opacity: 0.3,
                }}
              />
            </div>

            <div className="relative">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-blue-400" />
                <p className="text-xs font-semibold text-white">Pro Features</p>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Intelligence artificielle activée. Détection d'anomalies et prévisions en temps réel.
              </p>
            </div>
          </motion.div>

          {/* Version */}
          <p className="text-center text-[10px] text-slate-600 mt-4">
            v2.0.0 • Build 2025.12
          </p>
        </div>
      </motion.aside>
    </>
  );
}
