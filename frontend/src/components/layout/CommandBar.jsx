import { useEffect, useRef, Fragment } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Command, ArrowRight, Clock, Zap, Navigation } from 'lucide-react';
import clsx from 'clsx';
import { useCommandBar } from '../../contexts/CommandBarContext.jsx';
import { useHotkeys } from '../../hooks/index.js';

// ============================================================================
// COMMAND BAR - Navigation rapide style Spotlight/Alfred
// ============================================================================

export default function CommandBar() {
  const {
    isOpen,
    open,
    close,
    query,
    setQuery,
    results,
    selectedIndex,
    setSelectedIndex,
    executeItem,
    handleKeyDown,
  } = useCommandBar();

  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Raccourci Cmd+K / Ctrl+K pour ouvrir
  useHotkeys('meta+k', open, { preventDefault: true });
  useHotkeys('ctrl+k', open, { preventDefault: true });

  // Focus sur l'input quand ouvert
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Scroll vers l'élément sélectionné
  useEffect(() => {
    if (listRef.current && results.length > 0) {
      const selectedElement = listRef.current.querySelector(`[data-index="${selectedIndex}"]`);
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex, results.length]);

  // Grouper les résultats par catégorie
  const groupedResults = results.reduce((acc, item) => {
    const category = item.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(item);
    return acc;
  }, {});

  const categoryLabels = {
    sections: 'Sections',
    navigation: 'Pages',
    actions: 'Actions rapides',
    context: 'Contexte actuel',
    recent: 'Récents',
    other: 'Autres',
  };

  const categoryIcons = {
    sections: Navigation,
    navigation: Search,
    actions: Zap,
    context: ArrowRight,
    recent: Clock,
    other: Clock,
  };

  // Calculer l'index global pour chaque item
  let globalIndex = 0;
  const itemsWithGlobalIndex = Object.entries(groupedResults).map(([category, items]) => ({
    category,
    items: items.map((item) => ({ ...item, globalIndex: globalIndex++ })),
  }));

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm"
            onClick={close}
          />

          {/* Command Bar Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-x-4 top-[10%] z-50 mx-auto max-w-2xl"
            onKeyDown={handleKeyDown}
          >
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/95 shadow-2xl shadow-black/50 backdrop-blur-xl">
              {/* Search Input */}
              <div className="flex items-center gap-3 border-b border-white/10 px-4 py-4">
                <Search className="h-5 w-5 text-slate-500" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Rechercher une page, action, produit..."
                  className="flex-1 bg-transparent text-base text-white placeholder-slate-500 outline-none"
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                />
                <div className="flex items-center gap-1">
                  <kbd className="flex h-6 items-center rounded-md border border-white/10 bg-white/5 px-2 text-[10px] font-medium text-slate-400">
                    <Command className="mr-0.5 h-3 w-3" />K
                  </kbd>
                </div>
              </div>

              {/* Results */}
              <div ref={listRef} className="max-h-[60vh] overflow-y-auto p-2">
                {results.length === 0 ? (
                  <div className="px-4 py-8 text-center">
                    <Search className="mx-auto mb-3 h-8 w-8 text-slate-600" />
                    <p className="text-sm text-slate-500">
                      Aucun résultat pour "{query}"
                    </p>
                    <p className="mt-1 text-xs text-slate-600">
                      Essayez "facture", "stock", "prévision"...
                    </p>
                  </div>
                ) : (
                  itemsWithGlobalIndex.map(({ category, items }) => (
                    <div key={category} className="mb-2">
                      {/* Category Header */}
                      <div className="flex items-center gap-2 px-3 py-2">
                        {(() => {
                          const Icon = categoryIcons[category] || Search;
                          return <Icon className="h-3 w-3 text-slate-600" />;
                        })()}
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-600">
                          {categoryLabels[category] || category}
                        </span>
                      </div>

                      {/* Items */}
                      {items.map((item) => (
                        <CommandBarItem
                          key={item.id}
                          item={item}
                          isSelected={item.globalIndex === selectedIndex}
                          onSelect={() => executeItem(item)}
                          onHover={() => setSelectedIndex(item.globalIndex)}
                          dataIndex={item.globalIndex}
                        />
                      ))}
                    </div>
                  ))
                )}
              </div>

              {/* Footer with shortcuts */}
              <div className="flex items-center justify-between border-t border-white/10 px-4 py-2.5">
                <div className="flex items-center gap-4 text-[10px] text-slate-600">
                  <span className="flex items-center gap-1">
                    <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5">↑↓</kbd>
                    <span>naviguer</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5">↵</kbd>
                    <span>sélectionner</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5">esc</kbd>
                    <span>fermer</span>
                  </span>
                </div>
                <div className="text-[10px] text-slate-600">
                  {results.length} résultat{results.length > 1 ? 's' : ''}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// ============================================================================
// COMMAND BAR ITEM
// ============================================================================

function CommandBarItem({ item, isSelected, onSelect, onHover, dataIndex }) {
  const Icon = item.icon || Search;

  return (
    <motion.button
      data-index={dataIndex}
      onClick={onSelect}
      onMouseEnter={onHover}
      className={clsx(
        'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors',
        isSelected
          ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white'
          : 'text-slate-400 hover:bg-white/5 hover:text-white'
      )}
      whileTap={{ scale: 0.98 }}
    >
      {/* Icon */}
      <div
        className={clsx(
          'flex h-9 w-9 items-center justify-center rounded-lg',
          isSelected
            ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
            : 'bg-white/5 text-slate-500'
        )}
      >
        <Icon className="h-4 w-4" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={clsx('text-sm font-medium truncate', isSelected ? 'text-white' : 'text-slate-300')}>
          {item.label}
        </p>
        {item.description && (
          <p className="text-xs text-slate-500 truncate">{item.description}</p>
        )}
      </div>

      {/* Action indicator */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-1 text-xs text-blue-400"
        >
          <span>Ouvrir</span>
          <ArrowRight className="h-3 w-3" />
        </motion.div>
      )}
    </motion.button>
  );
}
