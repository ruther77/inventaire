import { useEffect } from 'react';

/**
 * Map keyboard shortcuts to callbacks, e.g. { 'ctrl+1': handler }
 */
export function useKeyboardShortcuts(shortcuts = {}) {
  useEffect(() => {
    const handler = (event) => {
      const key = event.key.toLowerCase();
      const parts = [];
      if (event.metaKey) parts.push('cmd');
      if (event.ctrlKey) parts.push('ctrl');
      if (event.altKey) parts.push('alt');
      if (event.shiftKey) parts.push('shift');
      parts.push(key);
      const signature = parts.join('+');

      const direct = shortcuts[signature] || shortcuts[key];
      if (direct) {
        direct(event);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts]);
}
