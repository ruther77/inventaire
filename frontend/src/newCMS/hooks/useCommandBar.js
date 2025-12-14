import { useEffect, useMemo, useState } from 'react';

const normalize = (value) => value.toLowerCase().trim();

export function useCommandBar(initialActions = []) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [actions, setActions] = useState(initialActions);

  useEffect(() => {
    setActions(initialActions);
  }, [initialActions]);

  useEffect(() => {
    // Ouvre la barre avec ⌘K ou Ctrl+K
    const handler = (event) => {
      const isCmdK = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k';
      if (isCmdK) {
        event.preventDefault();
        setIsOpen((open) => !open);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const filteredActions = useMemo(() => {
    if (!query) return actions;
    const q = normalize(query);
    return actions.filter((action) => normalize(action.label).includes(q));
  }, [actions, query]);

  const registerActions = (extraActions) => {
    setActions((prev) => {
      const existingIds = new Set(prev.map((a) => a.id));
      const merged = [...prev];
      extraActions.forEach((action) => {
        if (!existingIds.has(action.id)) {
          merged.push(action);
        }
      });
      return merged;
    });
  };

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen((open) => !open),
    query,
    setQuery,
    actions,
    setActions,
    filteredActions,
    registerActions,
  };
}
