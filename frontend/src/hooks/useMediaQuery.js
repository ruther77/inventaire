import { useState, useEffect, useMemo } from 'react';

/**
 * useMediaQuery - Hook pour détecter les media queries
 *
 * @param {string} query - Media query (ex: "(min-width: 768px)")
 * @returns {boolean} - True si la query match
 */
export default function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (event) => setMatches(event.matches);

    // Utiliser addEventListener (moderne) avec fallback sur addListener
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      // Fallback pour Safari < 14
      mediaQuery.addListener(handler);
      return () => mediaQuery.removeListener(handler);
    }
  }, [query]);

  return matches;
}

/**
 * Breakpoints Tailwind par défaut
 */
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

/**
 * useBreakpoint - Hook pour les breakpoints Tailwind
 *
 * @param {'sm' | 'md' | 'lg' | 'xl' | '2xl'} breakpoint
 * @returns {boolean} - True si >= breakpoint
 */
export function useBreakpoint(breakpoint) {
  const query = `(min-width: ${breakpoints[breakpoint]})`;
  return useMediaQuery(query);
}

/**
 * useBreakpoints - Hook pour avoir tous les breakpoints
 *
 * @returns {Object} - { isSm, isMd, isLg, isXl, is2xl, current }
 */
export function useBreakpoints() {
  const isSm = useMediaQuery(`(min-width: ${breakpoints.sm})`);
  const isMd = useMediaQuery(`(min-width: ${breakpoints.md})`);
  const isLg = useMediaQuery(`(min-width: ${breakpoints.lg})`);
  const isXl = useMediaQuery(`(min-width: ${breakpoints.xl})`);
  const is2xl = useMediaQuery(`(min-width: ${breakpoints['2xl']})`);

  const current = useMemo(() => {
    if (is2xl) return '2xl';
    if (isXl) return 'xl';
    if (isLg) return 'lg';
    if (isMd) return 'md';
    if (isSm) return 'sm';
    return 'xs';
  }, [isSm, isMd, isLg, isXl, is2xl]);

  return { isSm, isMd, isLg, isXl, is2xl, current };
}

/**
 * useIsMobile - Shortcut pour mobile (< md)
 */
export function useIsMobile() {
  return !useBreakpoint('md');
}

/**
 * useIsTablet - Shortcut pour tablet (md à lg)
 */
export function useIsTablet() {
  const isMd = useBreakpoint('md');
  const isLg = useBreakpoint('lg');
  return isMd && !isLg;
}

/**
 * useIsDesktop - Shortcut pour desktop (>= lg)
 */
export function useIsDesktop() {
  return useBreakpoint('lg');
}

/**
 * usePrefersDarkMode - Détecter la préférence système
 */
export function usePrefersDarkMode() {
  return useMediaQuery('(prefers-color-scheme: dark)');
}

/**
 * usePrefersReducedMotion - Détecter si l'utilisateur préfère moins d'animations
 */
export function usePrefersReducedMotion() {
  return useMediaQuery('(prefers-reduced-motion: reduce)');
}

/**
 * useOrientation - Détecter l'orientation de l'écran
 */
export function useOrientation() {
  const isPortrait = useMediaQuery('(orientation: portrait)');
  return isPortrait ? 'portrait' : 'landscape';
}
