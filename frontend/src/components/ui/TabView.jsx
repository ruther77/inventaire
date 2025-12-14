import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import clsx from 'clsx';

/**
 * TabView - Composant d'onglets avec sync URL et navigation clavier
 *
 * Features:
 * - Sync URL avec ?tab=xxx
 * - Navigation clavier (← →)
 * - Lazy loading des onglets
 * - Animation de transition
 * - Badges et icônes
 */
export default function TabView({
  tabs,
  defaultTab,
  paramName = 'tab',
  className,
  tabsClassName,
  contentClassName,
  variant = 'default',
  size = 'md',
  onChange,
  lazy = true,
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlTab = searchParams.get(paramName);
  const tabListRef = useRef(null);

  // Déterminer l'onglet actif (URL > default > premier)
  const validTabs = tabs.filter(t => !t.hidden);
  const defaultTabId = defaultTab || validTabs[0]?.id;
  const [activeTab, setActiveTab] = useState(
    validTabs.find(t => t.id === urlTab)?.id || defaultTabId
  );

  // Track des onglets déjà chargés (pour lazy loading)
  const [loadedTabs, setLoadedTabs] = useState(new Set([activeTab]));

  // Sync avec URL
  useEffect(() => {
    if (urlTab && validTabs.find(t => t.id === urlTab)) {
      setActiveTab(urlTab);
      setLoadedTabs(prev => new Set([...prev, urlTab]));
    }
  }, [urlTab, validTabs]);

  // Changer d'onglet
  const switchTab = useCallback((tabId) => {
    if (tabId === activeTab) return;

    setActiveTab(tabId);
    setLoadedTabs(prev => new Set([...prev, tabId]));

    // Update URL
    const newParams = new URLSearchParams(searchParams);
    if (tabId === defaultTabId) {
      newParams.delete(paramName);
    } else {
      newParams.set(paramName, tabId);
    }
    setSearchParams(newParams, { replace: true });

    onChange?.(tabId);
  }, [activeTab, defaultTabId, paramName, searchParams, setSearchParams, onChange]);

  // Navigation clavier
  const handleKeyDown = useCallback((e) => {
    const currentIndex = validTabs.findIndex(t => t.id === activeTab);

    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = currentIndex > 0 ? currentIndex - 1 : validTabs.length - 1;
      switchTab(validTabs[prevIndex].id);
      // Focus le bouton
      tabListRef.current?.querySelector(`[data-tab="${validTabs[prevIndex].id}"]`)?.focus();
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = currentIndex < validTabs.length - 1 ? currentIndex + 1 : 0;
      switchTab(validTabs[nextIndex].id);
      tabListRef.current?.querySelector(`[data-tab="${validTabs[nextIndex].id}"]`)?.focus();
    } else if (e.key === 'Home') {
      e.preventDefault();
      switchTab(validTabs[0].id);
      tabListRef.current?.querySelector(`[data-tab="${validTabs[0].id}"]`)?.focus();
    } else if (e.key === 'End') {
      e.preventDefault();
      switchTab(validTabs[validTabs.length - 1].id);
      tabListRef.current?.querySelector(`[data-tab="${validTabs[validTabs.length - 1].id}"]`)?.focus();
    }
  }, [activeTab, validTabs, switchTab]);

  // Styles selon variant
  const variants = {
    default: {
      list: 'flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10',
      tab: 'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
      tabActive: 'bg-white/15 text-white shadow-sm',
      tabInactive: 'text-slate-400 hover:text-white hover:bg-white/5',
    },
    pills: {
      list: 'flex gap-2',
      tab: 'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
      tabActive: 'bg-indigo-500 text-white',
      tabInactive: 'text-slate-400 hover:text-white hover:bg-white/10',
    },
    underline: {
      list: 'flex gap-6 border-b border-white/10',
      tab: 'pb-3 text-sm font-medium transition-all duration-200 relative',
      tabActive: 'text-white after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-indigo-500',
      tabInactive: 'text-slate-400 hover:text-white',
    },
    minimal: {
      list: 'flex gap-4',
      tab: 'px-2 py-1 text-sm font-medium transition-all duration-200',
      tabActive: 'text-white',
      tabInactive: 'text-slate-500 hover:text-slate-300',
    },
  };

  const sizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const style = variants[variant] || variants.default;

  const activeTabData = validTabs.find(t => t.id === activeTab);

  return (
    <div className={clsx('flex flex-col', className)}>
      {/* Tab List */}
      <div
        ref={tabListRef}
        role="tablist"
        aria-label="Onglets"
        className={clsx(style.list, tabsClassName)}
        onKeyDown={handleKeyDown}
      >
        {validTabs.map((tab, index) => (
          <button
            key={tab.id}
            data-tab={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => switchTab(tab.id)}
            disabled={tab.disabled}
            className={clsx(
              style.tab,
              sizes[size],
              activeTab === tab.id ? style.tabActive : style.tabInactive,
              tab.disabled && 'opacity-50 cursor-not-allowed',
              'flex items-center gap-2'
            )}
          >
            {tab.icon && <span className="flex-shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span className={clsx(
                'ml-1.5 px-1.5 py-0.5 text-xs rounded-full',
                activeTab === tab.id
                  ? 'bg-white/20 text-white'
                  : 'bg-white/10 text-slate-400'
              )}>
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className={clsx('mt-4 flex-1', contentClassName)}>
        {validTabs.map(tab => {
          const isActive = activeTab === tab.id;
          const shouldRender = lazy ? loadedTabs.has(tab.id) : true;

          if (!shouldRender) return null;

          return (
            <div
              key={tab.id}
              id={`tabpanel-${tab.id}`}
              role="tabpanel"
              aria-labelledby={tab.id}
              hidden={!isActive}
              className={clsx(
                'transition-opacity duration-200',
                isActive ? 'opacity-100' : 'opacity-0 absolute pointer-events-none'
              )}
            >
              {tab.content}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * useTabView - Hook pour gérer les onglets programmatiquement
 */
export function useTabView(tabs, options = {}) {
  const { paramName = 'tab', defaultTab } = options;
  const [searchParams, setSearchParams] = useSearchParams();

  const validTabs = tabs.filter(t => !t.hidden);
  const defaultTabId = defaultTab || validTabs[0]?.id;
  const currentTab = searchParams.get(paramName) || defaultTabId;

  const switchTab = useCallback((tabId) => {
    const newParams = new URLSearchParams(searchParams);
    if (tabId === defaultTabId) {
      newParams.delete(paramName);
    } else {
      newParams.set(paramName, tabId);
    }
    setSearchParams(newParams, { replace: true });
  }, [defaultTabId, paramName, searchParams, setSearchParams]);

  return { currentTab, switchTab, tabs: validTabs };
}
