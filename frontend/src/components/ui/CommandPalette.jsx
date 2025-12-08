import { useState, useEffect, useMemo, useRef, useCallback, createContext, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  ArrowRight,
  FileText,
  Settings,
  Home,
  Package,
  TrendingUp,
  Upload,
  Wallet,
  Calculator,
  BarChart3,
  Command,
  CornerDownLeft,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import clsx from 'clsx';
import useHotkeys from '../../hooks/useHotkeys.js';
import useDebounce from '../../hooks/useDebounce.js';

// Context pour le CommandPalette
const CommandPaletteContext = createContext(null);

export function useCommandPalette() {
  const context = useContext(CommandPaletteContext);
  if (!context) {
    throw new Error('useCommandPalette must be used within CommandPaletteProvider');
  }
  return context;
}

/**
 * CommandPaletteProvider - Provider pour le state global du command palette
 */
export function CommandPaletteProvider({ children, commands = [] }) {
  const [isOpen, setIsOpen] = useState(false);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((v) => !v), []);

  // Raccourci global Ctrl+K / Cmd+K
  useHotkeys('ctrl+k', open, { preventDefault: true });
  useHotkeys('meta+k', open, { preventDefault: true });

  const value = useMemo(
    () => ({ isOpen, open, close, toggle, commands }),
    [isOpen, open, close, toggle, commands]
  );

  return (
    <CommandPaletteContext.Provider value={value}>
      {children}
      <CommandPalette />
    </CommandPaletteContext.Provider>
  );
}

/**
 * CommandPalette - Interface de recherche/commandes rapide (Ctrl+K)
 * Pattern: Spotlight/Alfred style, keyboard navigation, fuzzy search
 */
function CommandPalette() {
  const { isOpen, close, commands: customCommands } = useCommandPalette();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  const debouncedQuery = useDebounce(query, 150);

  // Commands par défaut (navigation)
  const defaultCommands = useMemo(() => [
    {
      id: 'nav-home',
      title: 'Accueil',
      description: 'Retourner au dashboard principal',
      icon: Home,
      category: 'Navigation',
      action: () => navigate('/'),
      keywords: ['home', 'dashboard', 'accueil', 'pilotage'],
    },
    {
      id: 'nav-catalog',
      title: 'Catalogue',
      description: 'Gérer les produits et références',
      icon: Package,
      category: 'Navigation',
      action: () => navigate('/inventory'),
      keywords: ['products', 'produits', 'catalogue', 'inventory'],
    },
    {
      id: 'nav-stock',
      title: 'Mouvements de stock',
      description: 'Voir les entrées et sorties de stock',
      icon: TrendingUp,
      category: 'Navigation',
      action: () => navigate('/stock'),
      keywords: ['stock', 'inventory', 'movements', 'mouvements'],
    },
    {
      id: 'nav-import',
      title: 'Import factures',
      description: 'Importer et traiter des factures',
      icon: Upload,
      category: 'Navigation',
      action: () => navigate('/import'),
      keywords: ['import', 'factures', 'invoices', 'upload'],
    },
    {
      id: 'nav-portfolio',
      title: 'Portefeuille',
      description: 'Voir le capital et les liquidités',
      icon: Wallet,
      category: 'Navigation',
      action: () => navigate('/portfolio'),
      keywords: ['portfolio', 'wallet', 'capital', 'cash'],
    },
    {
      id: 'nav-prices',
      title: 'Suivi prix',
      description: 'Analyser l\'évolution des prix',
      icon: BarChart3,
      category: 'Navigation',
      action: () => navigate('/prices'),
      keywords: ['prices', 'prix', 'tarifs', 'evolution'],
    },
    {
      id: 'nav-forecast',
      title: 'Prévisions',
      description: 'Prévisions et analyses ARIMA',
      icon: Calculator,
      category: 'Navigation',
      action: () => navigate('/forecast'),
      keywords: ['forecast', 'previsions', 'arima', 'prediction'],
    },
    {
      id: 'action-new-invoice',
      title: 'Nouvelle facture',
      description: 'Importer une nouvelle facture fournisseur',
      icon: FileText,
      category: 'Actions',
      action: () => navigate('/import?action=new'),
      keywords: ['new', 'nouvelle', 'facture', 'invoice', 'create'],
    },
    {
      id: 'action-settings',
      title: 'Paramètres',
      description: 'Configurer l\'application',
      icon: Settings,
      category: 'Actions',
      action: () => navigate('/settings'),
      keywords: ['settings', 'parametres', 'config', 'preferences'],
    },
  ], [navigate]);

  const allCommands = useMemo(
    () => [...defaultCommands, ...customCommands],
    [defaultCommands, customCommands]
  );

  // Filtrer les commandes avec recherche fuzzy
  const filteredCommands = useMemo(() => {
    if (!debouncedQuery.trim()) {
      return allCommands;
    }

    const searchTerms = debouncedQuery.toLowerCase().split(' ').filter(Boolean);

    return allCommands
      .map((cmd) => {
        const searchableText = [
          cmd.title,
          cmd.description,
          ...(cmd.keywords || []),
        ]
          .join(' ')
          .toLowerCase();

        // Calculer un score de pertinence
        let score = 0;
        for (const term of searchTerms) {
          if (cmd.title.toLowerCase().includes(term)) score += 10;
          if (cmd.description?.toLowerCase().includes(term)) score += 5;
          if (cmd.keywords?.some((k) => k.includes(term))) score += 3;
          if (searchableText.includes(term)) score += 1;
        }

        return { ...cmd, score };
      })
      .filter((cmd) => cmd.score > 0)
      .sort((a, b) => b.score - a.score);
  }, [allCommands, debouncedQuery]);

  // Grouper par catégorie
  const groupedCommands = useMemo(() => {
    const groups = {};
    for (const cmd of filteredCommands) {
      const category = cmd.category || 'Autres';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(cmd);
    }
    return groups;
  }, [filteredCommands]);

  // Reset à l'ouverture
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [isOpen]);

  // Reset selection quand les résultats changent
  useEffect(() => {
    setSelectedIndex(0);
  }, [debouncedQuery]);

  // Navigation clavier
  const handleKeyDown = useCallback(
    (e) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((i) => Math.max(i - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action();
            close();
          }
          break;
        case 'Escape':
          e.preventDefault();
          close();
          break;
      }
    },
    [filteredCommands, selectedIndex, close]
  );

  // Scroll to selected
  useEffect(() => {
    const list = listRef.current;
    if (!list) return;

    const selected = list.querySelector('[data-selected="true"]');
    if (selected) {
      selected.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150"
        onClick={close}
      />

      {/* Panel */}
      <div
        className={clsx(
          'relative w-full max-w-xl',
          'bg-white rounded-2xl shadow-2xl',
          'ring-1 ring-slate-200',
          'animate-in zoom-in-95 slide-in-from-top duration-200',
          'overflow-hidden'
        )}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100">
          <Search className="h-5 w-5 text-slate-400 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Rechercher une page ou une action..."
            className="flex-1 text-sm text-slate-900 placeholder-slate-400 bg-transparent outline-none"
            autoComplete="off"
            autoCorrect="off"
            spellCheck={false}
          />
          <kbd className="hidden sm:flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium bg-slate-100 text-slate-500 rounded">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div
          ref={listRef}
          className="max-h-[50vh] overflow-y-auto overscroll-contain py-2"
        >
          {filteredCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-slate-500">
              Aucun résultat pour "{query}"
            </div>
          ) : (
            Object.entries(groupedCommands).map(([category, commands]) => (
              <div key={category}>
                <div className="px-4 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  {category}
                </div>
                {commands.map((cmd) => {
                  const globalIndex = filteredCommands.indexOf(cmd);
                  const isSelected = globalIndex === selectedIndex;
                  const Icon = cmd.icon;

                  return (
                    <button
                      key={cmd.id}
                      type="button"
                      data-selected={isSelected}
                      onClick={() => {
                        cmd.action();
                        close();
                      }}
                      onMouseEnter={() => setSelectedIndex(globalIndex)}
                      className={clsx(
                        'w-full flex items-center gap-3 px-4 py-2.5 text-left',
                        'transition-colors',
                        isSelected
                          ? 'bg-brand-50 text-brand-900'
                          : 'text-slate-700 hover:bg-slate-50'
                      )}
                    >
                      <div
                        className={clsx(
                          'flex-shrink-0 rounded-lg p-2',
                          isSelected ? 'bg-brand-100' : 'bg-slate-100'
                        )}
                      >
                        <Icon
                          className={clsx(
                            'h-4 w-4',
                            isSelected ? 'text-brand-600' : 'text-slate-500'
                          )}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{cmd.title}</p>
                        {cmd.description && (
                          <p className="text-xs text-slate-500 truncate">
                            {cmd.description}
                          </p>
                        )}
                      </div>
                      {isSelected && (
                        <ArrowRight className="h-4 w-4 text-brand-400 flex-shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-slate-100 bg-slate-50 text-xs text-slate-500">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <ArrowUp className="h-3 w-3" />
              <ArrowDown className="h-3 w-3" />
              naviguer
            </span>
            <span className="flex items-center gap-1">
              <CornerDownLeft className="h-3 w-3" />
              sélectionner
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Command className="h-3 w-3" />
            <span>K pour ouvrir</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CommandPalette;
