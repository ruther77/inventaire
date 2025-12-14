/**
 * SkipLinks - Liens de navigation rapide pour l'accessibilité.
 *
 * Fonctionnalités:
 * - Navigation au clavier pour sauter au contenu principal
 * - Support de zones multiples (nav, main, footer)
 * - Visible uniquement au focus (Tab)
 * - Conforme WCAG 2.1 AAA
 */

import { useState, useCallback } from 'react';

const defaultLinks = [
  { id: 'main-content', label: 'Aller au contenu principal' },
  { id: 'main-navigation', label: 'Aller à la navigation' },
  { id: 'search', label: 'Aller à la recherche' },
];

export default function SkipLinks({ links = defaultLinks }) {
  const [isVisible, setIsVisible] = useState(false);

  const handleFocus = useCallback(() => setIsVisible(true), []);
  const handleBlur = useCallback(() => setIsVisible(false), []);

  const handleClick = useCallback((e, targetId) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      // Rendre focusable temporairement si nécessaire
      if (!target.hasAttribute('tabindex')) {
        target.setAttribute('tabindex', '-1');
        target.addEventListener('blur', () => target.removeAttribute('tabindex'), { once: true });
      }
      target.focus();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  return (
    <nav
      aria-label="Liens d'accès rapide"
      className={`
        fixed left-0 top-0 z-[9999]
        transition-transform duration-200
        ${isVisible ? 'translate-y-0' : '-translate-y-full'}
      `}
    >
      <ul className="flex gap-1 bg-slate-900 p-2">
        {links.map(({ id, label }) => (
          <li key={id}>
            <a
              href={`#${id}`}
              onClick={(e) => handleClick(e, id)}
              onFocus={handleFocus}
              onBlur={handleBlur}
              className="
                block rounded-lg bg-brand-600 px-4 py-2
                text-sm font-semibold text-white
                transition-colors duration-150
                hover:bg-brand-700
                focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-2 focus:ring-offset-slate-900
              "
            >
              {label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
