import { useState, useEffect, createContext, useContext, useMemo, useCallback } from 'react';
import clsx from 'clsx';
import { Command, Keyboard } from 'lucide-react';
import useHotkeys, { useHotkeysMap } from '../../hooks/useHotkeys.js';
import Modal from './Modal.jsx';

// Context pour les raccourcis
const ShortcutsContext = createContext(null);

export function useShortcuts() {
  const context = useContext(ShortcutsContext);
  if (!context) {
    throw new Error('useShortcuts must be used within ShortcutsProvider');
  }
  return context;
}

/**
 * ShortcutsProvider - Provider pour les raccourcis clavier globaux
 */
export function ShortcutsProvider({ children, shortcuts = [] }) {
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  // Raccourci pour ouvrir l'aide (?)
  useHotkeys('shift+/', () => setIsHelpOpen(true), { preventDefault: true });

  // Construire le keyMap à partir des shortcuts
  const keyMap = useMemo(() => {
    const map = {};
    shortcuts.forEach((shortcut) => {
      if (shortcut.keys && shortcut.action) {
        map[shortcut.keys] = shortcut.action;
      }
    });
    return map;
  }, [shortcuts]);

  // Appliquer tous les raccourcis
  useHotkeysMap(keyMap);

  const value = useMemo(
    () => ({
      shortcuts,
      isHelpOpen,
      openHelp: () => setIsHelpOpen(true),
      closeHelp: () => setIsHelpOpen(false),
    }),
    [shortcuts, isHelpOpen]
  );

  return (
    <ShortcutsContext.Provider value={value}>
      {children}
      <ShortcutsHelpModal
        open={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
        shortcuts={shortcuts}
      />
    </ShortcutsContext.Provider>
  );
}

/**
 * ShortcutsHelpModal - Modal d'aide des raccourcis clavier
 */
function ShortcutsHelpModal({ open, onClose, shortcuts }) {
  // Grouper les raccourcis par catégorie
  const groupedShortcuts = useMemo(() => {
    const groups = {};
    shortcuts.forEach((shortcut) => {
      const category = shortcut.category || 'Général';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(shortcut);
    });
    return groups;
  }, [shortcuts]);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Raccourcis clavier"
      description="Utilisez ces raccourcis pour naviguer plus rapidement"
      size="lg"
    >
      <div className="grid gap-6 md:grid-cols-2">
        {Object.entries(groupedShortcuts).map(([category, items]) => (
          <div key={category}>
            <h4 className="text-sm font-semibold text-slate-900 mb-3">
              {category}
            </h4>
            <div className="space-y-2">
              {items.map((shortcut) => (
                <div
                  key={shortcut.keys}
                  className="flex items-center justify-between py-1.5"
                >
                  <span className="text-sm text-slate-600">
                    {shortcut.description}
                  </span>
                  <KeyCombo keys={shortcut.keys} />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-100 text-center">
        <p className="text-xs text-slate-500">
          Appuyez sur <KeyCombo keys="shift+/" className="inline-flex" /> pour afficher cette aide
        </p>
      </div>
    </Modal>
  );
}

/**
 * KeyCombo - Affiche une combinaison de touches
 */
export function KeyCombo({ keys, className }) {
  const isMac =
    typeof navigator !== 'undefined' &&
    /Mac|iPod|iPhone|iPad/.test(navigator.platform);

  const formatKey = (key) => {
    const keyMap = {
      ctrl: isMac ? '⌃' : 'Ctrl',
      control: isMac ? '⌃' : 'Ctrl',
      alt: isMac ? '⌥' : 'Alt',
      shift: '⇧',
      meta: '⌘',
      cmd: '⌘',
      command: '⌘',
      enter: '↵',
      return: '↵',
      escape: 'Esc',
      esc: 'Esc',
      space: '␣',
      tab: '⇥',
      backspace: '⌫',
      delete: '⌦',
      up: '↑',
      down: '↓',
      left: '←',
      right: '→',
      '/': '/',
      '?': '?',
    };

    const lowerKey = key.toLowerCase().trim();
    return keyMap[lowerKey] || key.toUpperCase();
  };

  const keyParts = keys.split('+').map((k) => formatKey(k));

  return (
    <span className={clsx('inline-flex items-center gap-1', className)}>
      {keyParts.map((key, index) => (
        <kbd
          key={index}
          className={clsx(
            'inline-flex items-center justify-center',
            'min-w-[1.5rem] h-6 px-1.5',
            'text-xs font-medium',
            'bg-slate-100 text-slate-600',
            'rounded border border-slate-200',
            'shadow-[0_1px_0_0_rgba(0,0,0,0.05)]'
          )}
        >
          {key}
        </kbd>
      ))}
    </span>
  );
}

/**
 * ShortcutHint - Indicateur de raccourci dans l'UI
 */
export function ShortcutHint({ keys, className }) {
  return (
    <span className={clsx('text-xs text-slate-400', className)}>
      <KeyCombo keys={keys} />
    </span>
  );
}

/**
 * GlobalShortcuts - Composant pour définir les raccourcis globaux de l'app
 */
export function GlobalShortcuts({ onNavigate, onOpenSearch, onNewItem }) {
  const shortcuts = useMemo(
    () => [
      // Navigation
      {
        keys: 'g+h',
        description: 'Aller à l\'accueil',
        category: 'Navigation',
        action: () => onNavigate?.('/'),
      },
      {
        keys: 'g+c',
        description: 'Aller au catalogue',
        category: 'Navigation',
        action: () => onNavigate?.('/inventory'),
      },
      {
        keys: 'g+s',
        description: 'Aller aux stocks',
        category: 'Navigation',
        action: () => onNavigate?.('/stock'),
      },
      {
        keys: 'g+i',
        description: 'Aller aux imports',
        category: 'Navigation',
        action: () => onNavigate?.('/import'),
      },
      {
        keys: 'g+p',
        description: 'Aller au portefeuille',
        category: 'Navigation',
        action: () => onNavigate?.('/portfolio'),
      },

      // Actions
      {
        keys: 'ctrl+k',
        description: 'Recherche rapide',
        category: 'Actions',
        action: onOpenSearch,
      },
      {
        keys: 'n',
        description: 'Nouvel élément',
        category: 'Actions',
        action: onNewItem,
      },
      {
        keys: 'escape',
        description: 'Fermer / Annuler',
        category: 'Actions',
        action: () => {}, // Géré par les composants individuels
      },

      // Aide
      {
        keys: 'shift+/',
        description: 'Afficher les raccourcis',
        category: 'Aide',
        action: () => {}, // Géré par le provider
      },
    ],
    [onNavigate, onOpenSearch, onNewItem]
  );

  return <ShortcutsProvider shortcuts={shortcuts} />;
}

/**
 * Hook pour créer des raccourcis séquentiels (ex: g puis h)
 */
export function useSequentialHotkey(sequence, callback, options = {}) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const keys = sequence.split('+');
  const timeoutRef = useState(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignorer si dans un input
      if (
        !options.enableOnFormTags &&
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)
      ) {
        return;
      }

      const expectedKey = keys[currentIndex].toLowerCase();
      const pressedKey = e.key.toLowerCase();

      if (pressedKey === expectedKey) {
        if (currentIndex === keys.length - 1) {
          // Séquence complète
          callback(e);
          setCurrentIndex(0);
        } else {
          // Avancer dans la séquence
          setCurrentIndex((i) => i + 1);

          // Reset après timeout
          clearTimeout(timeoutRef.current);
          timeoutRef.current = setTimeout(() => {
            setCurrentIndex(0);
          }, 1000);
        }
      } else if (currentIndex > 0) {
        // Reset si mauvaise touche
        setCurrentIndex(0);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      clearTimeout(timeoutRef.current);
    };
  }, [keys, currentIndex, callback, options.enableOnFormTags]);
}

export default KeyCombo;
