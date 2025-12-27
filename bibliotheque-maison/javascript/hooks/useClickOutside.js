import { useEffect } from 'react';

/**
 * Hook pour détecter les clics en dehors d'un élément
 * @param {React.RefObject} ref - Référence à l'élément DOM
 * @param {Function} handler - Fonction callback à appeler lors d'un clic extérieur
 */
export function useClickOutside(ref, handler) {
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      handler(event);
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}
