import { useEffect, useCallback, useRef } from 'react';

/**
 * useHotkeys - Hook pour gérer les raccourcis clavier
 *
 * @param {string} keys - Combinaison de touches (ex: "ctrl+k", "shift+enter", "escape")
 * @param {Function} callback - Fonction à exécuter
 * @param {Object} options - Options
 * @param {boolean} options.enabled - Activer/désactiver le raccourci
 * @param {boolean} options.preventDefault - Empêcher le comportement par défaut
 * @param {boolean} options.enableOnFormTags - Activer dans les inputs/textarea
 * @param {Element} options.targetElement - Élément cible (défaut: document)
 */
export default function useHotkeys(
  keys,
  callback,
  {
    enabled = true,
    preventDefault = true,
    enableOnFormTags = false,
    targetElement = null,
  } = {}
) {
  const callbackRef = useRef(callback);

  // Mettre à jour la référence du callback
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const handleKeyDown = useCallback(
    (event) => {
      if (!enabled) return;

      // Ignorer si focus sur un input (sauf si enableOnFormTags)
      if (!enableOnFormTags) {
        const target = event.target;
        const tagName = target.tagName.toLowerCase();
        const isEditable =
          target.isContentEditable ||
          tagName === 'input' ||
          tagName === 'textarea' ||
          tagName === 'select';

        if (isEditable) return;
      }

      // Parser les touches
      const pressedKeys = parseKeys(keys);
      const eventKeys = getEventKeys(event);

      // Vérifier la correspondance
      if (keysMatch(pressedKeys, eventKeys)) {
        if (preventDefault) {
          event.preventDefault();
          event.stopPropagation();
        }
        callbackRef.current(event);
      }
    },
    [keys, enabled, preventDefault, enableOnFormTags]
  );

  useEffect(() => {
    const target = targetElement || document;
    target.addEventListener('keydown', handleKeyDown);
    return () => target.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, targetElement]);
}

/**
 * useHotkeysMap - Hook pour plusieurs raccourcis
 *
 * @param {Object} keyMap - Map de {raccourci: callback}
 * @param {Object} options - Options globales
 */
export function useHotkeysMap(keyMap, options = {}) {
  useEffect(() => {
    const handlers = [];

    Object.entries(keyMap).forEach(([keys, callback]) => {
      const handler = (event) => {
        const pressedKeys = parseKeys(keys);
        const eventKeys = getEventKeys(event);

        if (keysMatch(pressedKeys, eventKeys)) {
          if (options.preventDefault !== false) {
            event.preventDefault();
          }
          callback(event);
        }
      };

      document.addEventListener('keydown', handler);
      handlers.push(handler);
    });

    return () => {
      handlers.forEach((handler) => {
        document.removeEventListener('keydown', handler);
      });
    };
  }, [keyMap, options]);
}

// Helpers

function parseKeys(keyString) {
  const keys = keyString.toLowerCase().split('+');
  return {
    ctrl: keys.includes('ctrl') || keys.includes('control'),
    alt: keys.includes('alt'),
    shift: keys.includes('shift'),
    meta: keys.includes('meta') || keys.includes('cmd') || keys.includes('command'),
    key: keys.find(
      (k) =>
        !['ctrl', 'control', 'alt', 'shift', 'meta', 'cmd', 'command'].includes(k)
    ),
  };
}

function getEventKeys(event) {
  return {
    ctrl: event.ctrlKey,
    alt: event.altKey,
    shift: event.shiftKey,
    meta: event.metaKey,
    key: event.key.toLowerCase(),
  };
}

function keysMatch(expected, actual) {
  // Vérifier les modificateurs
  if (expected.ctrl !== actual.ctrl) return false;
  if (expected.alt !== actual.alt) return false;
  if (expected.shift !== actual.shift) return false;
  if (expected.meta !== actual.meta) return false;

  // Vérifier la touche principale
  if (!expected.key) return true;

  // Gérer les touches spéciales
  const keyAliases = {
    esc: 'escape',
    return: 'enter',
    space: ' ',
    spacebar: ' ',
    up: 'arrowup',
    down: 'arrowdown',
    left: 'arrowleft',
    right: 'arrowright',
  };

  const expectedKey = keyAliases[expected.key] || expected.key;
  const actualKey = keyAliases[actual.key] || actual.key;

  return expectedKey === actualKey;
}

/**
 * Composant pour afficher un raccourci clavier
 */
export function KeyboardShortcut({ keys, className = '' }) {
  const isMac =
    typeof navigator !== 'undefined' &&
    /Mac|iPod|iPhone|iPad/.test(navigator.platform);

  const formatKey = (key) => {
    const keyMap = {
      ctrl: isMac ? '⌃' : 'Ctrl',
      alt: isMac ? '⌥' : 'Alt',
      shift: '⇧',
      meta: isMac ? '⌘' : 'Win',
      cmd: '⌘',
      enter: '↵',
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
    };

    const lowerKey = key.toLowerCase();
    return keyMap[lowerKey] || key.toUpperCase();
  };

  const keyParts = keys.split('+').map(formatKey);

  return (
    <span className={`inline-flex items-center gap-0.5 ${className}`}>
      {keyParts.map((key, index) => (
        <kbd
          key={index}
          className="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-[10px] font-medium bg-slate-100 text-slate-600 rounded border border-slate-200"
        >
          {key}
        </kbd>
      ))}
    </span>
  );
}
