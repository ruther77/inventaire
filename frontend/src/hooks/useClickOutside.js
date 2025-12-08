import { useEffect, useRef, useCallback } from 'react';

/**
 * useClickOutside - Détecte les clics en dehors d'un élément
 *
 * @param {Function} callback - Fonction à appeler lors d'un clic extérieur
 * @param {Object} options - Options
 * @param {boolean} options.enabled - Activer/désactiver la détection
 * @param {string[]} options.excludeSelectors - Sélecteurs CSS à exclure
 * @returns {React.RefObject} - Ref à attacher à l'élément
 */
export default function useClickOutside(
  callback,
  { enabled = true, excludeSelectors = [] } = {}
) {
  const ref = useRef(null);
  const callbackRef = useRef(callback);

  // Mettre à jour la référence du callback
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const handleClick = useCallback(
    (event) => {
      if (!enabled) return;
      if (!ref.current) return;

      const target = event.target;

      // Vérifier si le clic est dans l'élément
      if (ref.current.contains(target)) return;

      // Vérifier les sélecteurs exclus
      for (const selector of excludeSelectors) {
        if (target.closest(selector)) return;
      }

      callbackRef.current(event);
    },
    [enabled, excludeSelectors]
  );

  useEffect(() => {
    if (!enabled) return;

    // Utiliser mousedown pour capturer avant le focus change
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('touchstart', handleClick);

    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('touchstart', handleClick);
    };
  }, [enabled, handleClick]);

  return ref;
}

/**
 * useClickOutsideMultiple - Détecte les clics en dehors de plusieurs éléments
 *
 * @param {Function} callback - Fonction à appeler lors d'un clic extérieur
 * @param {number} count - Nombre de refs à créer
 * @returns {React.RefObject[]} - Array de refs
 */
export function useClickOutsideMultiple(callback, count = 2) {
  const refs = useRef([]);
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const handleClick = (event) => {
      const isOutside = refs.current.every(
        (ref) => !ref?.current?.contains(event.target)
      );

      if (isOutside) {
        callbackRef.current(event);
      }
    };

    document.addEventListener('mousedown', handleClick);
    document.addEventListener('touchstart', handleClick);

    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('touchstart', handleClick);
    };
  }, []);

  // Créer les refs si nécessaire
  while (refs.current.length < count) {
    refs.current.push({ current: null });
  }

  return refs.current.slice(0, count);
}

/**
 * useEscapeKey - Détecte l'appui sur Escape
 *
 * @param {Function} callback - Fonction à appeler
 * @param {boolean} enabled - Activer/désactiver
 */
export function useEscapeKey(callback, enabled = true) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        callbackRef.current(event);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [enabled]);
}

/**
 * useClickOutsideAndEscape - Combinaison des deux
 *
 * @param {Function} callback - Fonction à appeler
 * @param {Object} options - Options
 * @returns {React.RefObject} - Ref à attacher
 */
export function useClickOutsideAndEscape(callback, options = {}) {
  const ref = useClickOutside(callback, options);
  useEscapeKey(callback, options.enabled !== false);
  return ref;
}
