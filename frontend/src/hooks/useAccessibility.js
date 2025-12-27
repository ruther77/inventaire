/**
 * Module de hooks pour l'accessibilité avancée (a11y).
 *
 * Fournit des utilitaires pour rendre l'application accessible aux utilisateurs
 * en situation de handicap : gestion du focus, navigation clavier, lecteurs d'écran,
 * détection des préférences système (mouvement réduit, contraste élevé).
 *
 * @module hooks/useAccessibility
 *
 * Fonctionnalités:
 * - Focus trap pour modales/dialogs
 * - Focus restoration
 * - Keyboard navigation (roving tabindex)
 * - Screen reader announcements (live regions)
 * - Reduced motion detection
 * - High contrast detection
 * - Skip links
 */

import { useEffect, useRef, useCallback, useState } from 'react';

/**
 * Hook pour détecter la préférence système de mouvement réduit.
 *
 * Écoute la media query (prefers-reduced-motion: reduce) et retourne true
 * si l'utilisateur a activé cette option dans son système d'exploitation.
 * Permet de désactiver ou réduire les animations pour plus de confort.
 *
 * @returns {boolean} True si mouvement réduit préféré
 *
 * @example
 * const prefersReducedMotion = useReducedMotion();
 * const animationDuration = prefersReducedMotion ? 0 : 300;
 */
export function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(
    () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    if (!mediaQuery) return;

    const handler = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReducedMotion;
}

/**
 * Hook pour piéger le focus dans un conteneur (focus trap).
 *
 * Empêche le focus de sortir d'une zone définie (modale, dialog, menu)
 * en bouclant automatiquement entre le premier et le dernier élément focusable.
 * Restaure automatiquement le focus précédent à la désactivation.
 *
 * Essentiel pour l'accessibilité des modales conformes aux standards WCAG.
 *
 * @param {boolean} [isActive=true] - Activer ou désactiver le trap
 *
 * @returns {RefObject} Ref à attacher au conteneur
 *
 * @example
 * const trapRef = useFocusTrap(isModalOpen);
 * return (
 *   <div ref={trapRef} role="dialog">
 *     <button>Premier élément</button>
 *     <button>Dernier élément</button>
 *   </div>
 * );
 */
export function useFocusTrap(isActive = true) {
  const containerRef = useRef(null);
  const previousActiveElement = useRef(null);

  // Sauvegarder l'élément actif avant l'activation
  useEffect(() => {
    if (isActive) {
      previousActiveElement.current = document.activeElement;
    }
  }, [isActive]);

  // Restaurer le focus à la désactivation
  useEffect(() => {
    return () => {
      if (previousActiveElement.current && typeof previousActiveElement.current.focus === 'function') {
        previousActiveElement.current.focus();
      }
    };
  }, []);

  // Focus trap logic
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableSelector = [
      'button:not([disabled])',
      '[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    const getFocusableElements = () => {
      return Array.from(container.querySelectorAll(focusableSelector)).filter(
        (el) => el.offsetParent !== null // Visible elements only
      );
    };

    const handleKeyDown = (e) => {
      if (e.key !== 'Tab') return;

      const focusable = getFocusableElements();
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    // Focus le premier élément focusable
    const focusable = getFocusableElements();
    if (focusable.length > 0) {
      // Priorité: autofocus, puis premier élément
      const autofocus = container.querySelector('[autofocus]');
      (autofocus || focusable[0]).focus();
    }

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [isActive]);

  return containerRef;
}

/**
 * Hook pour créer des annonces aux lecteurs d'écran (screen readers).
 *
 * Crée une région ARIA live invisible qui annonce des messages aux utilisateurs
 * de lecteurs d'écran sans interrompre leur navigation.
 * Supporte deux niveaux de priorité : polite (par défaut) et assertive.
 *
 * @returns {Object} Fonctions d'annonce
 * @property {Function} announce - Annonce un message (priorité polite)
 * @property {Function} announceAssertive - Annonce urgente (priorité assertive)
 *
 * @example
 * const { announce, announceAssertive } = useAnnounce();
 * announce('Produit ajouté au panier');
 * announceAssertive('Erreur critique détectée');
 */
export function useAnnounce() {
  const announceRef = useRef(null);

  // Créer la région live au montage
  useEffect(() => {
    if (!announceRef.current) {
      const region = document.createElement('div');
      region.setAttribute('aria-live', 'polite');
      region.setAttribute('aria-atomic', 'true');
      region.setAttribute('role', 'status');
      region.className = 'sr-only';
      region.style.cssText = `
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
      `;
      document.body.appendChild(region);
      announceRef.current = region;
    }

    return () => {
      if (announceRef.current) {
        document.body.removeChild(announceRef.current);
        announceRef.current = null;
      }
    };
  }, []);

  const announce = useCallback((message, priority = 'polite') => {
    if (!announceRef.current) return;

    // Changer la priorité si nécessaire
    announceRef.current.setAttribute('aria-live', priority);

    // Clear puis set pour forcer l'annonce
    announceRef.current.textContent = '';
    requestAnimationFrame(() => {
      if (announceRef.current) {
        announceRef.current.textContent = message;
      }
    });
  }, []);

  const announceAssertive = useCallback(
    (message) => announce(message, 'assertive'),
    [announce]
  );

  return { announce, announceAssertive };
}

/**
 * Hook pour gérer les raccourcis clavier.
 */
export function useKeyboardShortcuts(shortcuts, enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e) => {
      const key = e.key.toLowerCase();
      const ctrl = e.ctrlKey || e.metaKey;
      const shift = e.shiftKey;
      const alt = e.altKey;

      for (const shortcut of shortcuts) {
        const {
          key: targetKey,
          ctrl: needsCtrl = false,
          shift: needsShift = false,
          alt: needsAlt = false,
          handler,
          preventDefault = true,
        } = shortcut;

        if (
          key === targetKey.toLowerCase() &&
          ctrl === needsCtrl &&
          shift === needsShift &&
          alt === needsAlt
        ) {
          if (preventDefault) {
            e.preventDefault();
          }
          handler(e);
          break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, enabled]);
}

/**
 * Hook pour gérer la navigation au clavier dans une liste.
 */
export function useRovingTabIndex(items, options = {}) {
  const { orientation = 'vertical', loop = true, onSelect } = options;
  const [activeIndex, setActiveIndex] = useState(0);
  const itemRefs = useRef([]);

  // Mettre à jour les refs
  const setItemRef = useCallback((index) => (el) => {
    itemRefs.current[index] = el;
  }, []);

  // Focus l'élément actif
  useEffect(() => {
    const activeItem = itemRefs.current[activeIndex];
    if (activeItem) {
      activeItem.focus();
    }
  }, [activeIndex]);

  // Gérer les touches
  const handleKeyDown = useCallback(
    (e) => {
      const isVertical = orientation === 'vertical';
      const prevKey = isVertical ? 'ArrowUp' : 'ArrowLeft';
      const nextKey = isVertical ? 'ArrowDown' : 'ArrowRight';
      const itemCount = items.length;

      let newIndex = activeIndex;

      switch (e.key) {
        case prevKey:
          e.preventDefault();
          if (loop) {
            newIndex = (activeIndex - 1 + itemCount) % itemCount;
          } else {
            newIndex = Math.max(0, activeIndex - 1);
          }
          break;
        case nextKey:
          e.preventDefault();
          if (loop) {
            newIndex = (activeIndex + 1) % itemCount;
          } else {
            newIndex = Math.min(itemCount - 1, activeIndex + 1);
          }
          break;
        case 'Home':
          e.preventDefault();
          newIndex = 0;
          break;
        case 'End':
          e.preventDefault();
          newIndex = itemCount - 1;
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          onSelect?.(items[activeIndex], activeIndex);
          return;
        default:
          return;
      }

      setActiveIndex(newIndex);
    },
    [activeIndex, items, orientation, loop, onSelect]
  );

  // Props pour chaque item
  const getItemProps = useCallback(
    (index) => ({
      ref: setItemRef(index),
      tabIndex: index === activeIndex ? 0 : -1,
      onKeyDown: handleKeyDown,
      onClick: () => {
        setActiveIndex(index);
        onSelect?.(items[index], index);
      },
      'aria-selected': index === activeIndex,
    }),
    [activeIndex, handleKeyDown, items, onSelect, setItemRef]
  );

  return {
    activeIndex,
    setActiveIndex,
    getItemProps,
  };
}

/**
 * Hook pour skip links (navigation rapide).
 */
export function useSkipLinks() {
  const [showSkipLinks, setShowSkipLinks] = useState(false);

  useEffect(() => {
    const handleFocus = () => setShowSkipLinks(true);
    const handleBlur = () => setShowSkipLinks(false);

    // Afficher les skip links au premier Tab
    const handleKeyDown = (e) => {
      if (e.key === 'Tab') {
        setShowSkipLinks(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return { showSkipLinks, setShowSkipLinks };
}

/**
 * Hook pour gérer les préférences de contraste élevé.
 */
export function useHighContrast() {
  const [prefersHighContrast, setPrefersHighContrast] = useState(
    () => window.matchMedia?.('(prefers-contrast: more)').matches ?? false
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia?.('(prefers-contrast: more)');
    if (!mediaQuery) return;

    const handler = (e) => setPrefersHighContrast(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersHighContrast;
}

export default {
  useReducedMotion,
  useFocusTrap,
  useAnnounce,
  useKeyboardShortcuts,
  useRovingTabIndex,
  useSkipLinks,
  useHighContrast,
};
