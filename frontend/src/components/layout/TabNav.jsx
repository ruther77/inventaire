import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import clsx from 'clsx';

// ============================================================================
// TAB NAV - Navigation par onglets pour vues unifiées
// ============================================================================

/**
 * TabNav - Composant de navigation par onglets
 *
 * @param {Array} tabs - Liste des onglets [{id, label, icon, path, badge}]
 * @param {string} activeTab - ID de l'onglet actif
 * @param {function} onTabChange - Callback de changement d'onglet
 * @param {string} variant - 'pills' | 'underline' | 'cards'
 * @param {string} size - 'sm' | 'md' | 'lg'
 * @param {boolean} useRouting - Utiliser react-router pour la navigation
 * @param {string} className - Classes CSS additionnelles
 */
export default function TabNav({
  tabs,
  activeTab,
  onTabChange,
  variant = 'pills',
  size = 'md',
  useRouting = false,
  className = '',
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const tabsRef = useRef(null);
  const [indicatorStyle, setIndicatorStyle] = useState({});

  // Déterminer l'onglet actif basé sur la route si useRouting
  const currentTab = useRouting
    ? tabs.find((tab) => location.pathname === tab.path)?.id || tabs[0]?.id
    : activeTab;

  // Mettre à jour l'indicateur animé
  useEffect(() => {
    if (variant === 'underline' && tabsRef.current) {
      const activeElement = tabsRef.current.querySelector(`[data-tab-id="${currentTab}"]`);
      if (activeElement) {
        setIndicatorStyle({
          width: activeElement.offsetWidth,
          left: activeElement.offsetLeft,
        });
      }
    }
  }, [currentTab, variant, tabs]);

  const handleTabClick = (tab) => {
    if (useRouting && tab.path) {
      navigate(tab.path);
    }
    onTabChange?.(tab.id);
  };

  const sizeClasses = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2 gap-2',
    lg: 'text-base px-5 py-2.5 gap-2.5',
  };

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  // Variant: Pills (default)
  if (variant === 'pills') {
    return (
      <nav
        ref={tabsRef}
        className={clsx(
          'flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-white/10',
          className
        )}
      >
        {tabs.map((tab) => {
          const isActive = currentTab === tab.id;
          const Icon = tab.icon;

          return (
            <motion.button
              key={tab.id}
              data-tab-id={tab.id}
              onClick={() => handleTabClick(tab)}
              className={clsx(
                'relative flex items-center font-medium rounded-lg transition-all',
                sizeClasses[size],
                isActive
                  ? 'text-white'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              )}
              whileTap={{ scale: 0.98 }}
            >
              {isActive && (
                <motion.div
                  layoutId="tab-pill-bg"
                  className="absolute inset-0 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-lg border border-white/10"
                  transition={{ type: 'spring', duration: 0.4 }}
                />
              )}
              <span className="relative flex items-center gap-2">
                {Icon && <Icon className={iconSizes[size]} />}
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className={clsx(
                    'px-1.5 py-0.5 rounded-full text-[10px] font-bold',
                    isActive ? 'bg-white/20 text-white' : 'bg-white/10 text-slate-400'
                  )}>
                    {tab.badge}
                  </span>
                )}
              </span>
            </motion.button>
          );
        })}
      </nav>
    );
  }

  // Variant: Underline
  if (variant === 'underline') {
    return (
      <nav
        ref={tabsRef}
        className={clsx('relative flex items-center gap-1 border-b border-white/10', className)}
      >
        {tabs.map((tab) => {
          const isActive = currentTab === tab.id;
          const Icon = tab.icon;

          return (
            <button
              key={tab.id}
              data-tab-id={tab.id}
              onClick={() => handleTabClick(tab)}
              className={clsx(
                'relative flex items-center font-medium transition-all pb-3',
                sizeClasses[size],
                isActive ? 'text-white' : 'text-slate-400 hover:text-white'
              )}
            >
              {Icon && <Icon className={iconSizes[size]} />}
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={clsx(
                  'px-1.5 py-0.5 rounded-full text-[10px] font-bold',
                  isActive ? 'bg-blue-500/20 text-blue-400' : 'bg-white/10 text-slate-400'
                )}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
        {/* Animated underline indicator */}
        <motion.div
          className="absolute bottom-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
          initial={false}
          animate={indicatorStyle}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        />
      </nav>
    );
  }

  // Variant: Cards
  if (variant === 'cards') {
    return (
      <nav
        ref={tabsRef}
        className={clsx('flex items-stretch gap-2', className)}
      >
        {tabs.map((tab) => {
          const isActive = currentTab === tab.id;
          const Icon = tab.icon;

          return (
            <motion.button
              key={tab.id}
              data-tab-id={tab.id}
              onClick={() => handleTabClick(tab)}
              className={clsx(
                'relative flex flex-col items-center justify-center min-w-[100px] rounded-xl transition-all',
                'px-4 py-3 gap-1',
                isActive
                  ? 'bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 text-white'
                  : 'bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10'
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {Icon && <Icon className={clsx(iconSizes[size], isActive && 'text-blue-400')} />}
              <span className="text-xs font-medium">{tab.label}</span>
              {tab.badge && (
                <span className={clsx(
                  'absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold',
                  isActive ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-300'
                )}>
                  {tab.badge}
                </span>
              )}
            </motion.button>
          );
        })}
      </nav>
    );
  }

  return null;
}

// ============================================================================
// TAB PANEL - Conteneur pour le contenu des onglets
// ============================================================================

export function TabPanel({ children, tabId, activeTab, className = '' }) {
  if (tabId !== activeTab) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ============================================================================
// TAB CONTENT - Wrapper avec animation pour contenu d'onglet
// ============================================================================

export function TabContent({ children, className = '' }) {
  return (
    <div className={clsx('mt-6', className)}>
      {children}
    </div>
  );
}
