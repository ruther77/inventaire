/**
 * Module de hooks pour la détection des media queries et breakpoints responsive.
 * @module hooks/useMediaQuery
 */

import { useState, useEffect, useMemo } from 'react';

/**
 * Hook principal pour détecter les media queries CSS.
 *
 * Écoute les changements de media query en temps réel et retourne un booléen
 * indiquant si la query correspond à l'état actuel de la fenêtre.
 * Compatible avec les anciens navigateurs (Safari < 14).
 *
 * @param {string} query - Media query CSS (ex: "(min-width: 768px)")
 *
 * @returns {boolean} True si la query correspond, false sinon
 *
 * @example
 * const isLargeScreen = useMediaQuery('(min-width: 1024px)');
 * const isDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
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
 * Breakpoints Tailwind CSS par défaut.
 * Utilisés par les hooks useBreakpoint et useBreakpoints.
 *
 * @constant
 * @type {Object}
 * @property {string} sm - 640px
 * @property {string} md - 768px
 * @property {string} lg - 1024px
 * @property {string} xl - 1280px
 * @property {string} 2xl - 1536px
 */
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

/**
 * Hook pour détecter si la fenêtre est supérieure ou égale à un breakpoint Tailwind.
 *
 * Simplifie l'utilisation des breakpoints Tailwind en fournissant une API
 * plus intuitive que useMediaQuery brut.
 *
 * @param {'sm' | 'md' | 'lg' | 'xl' | '2xl'} breakpoint - Nom du breakpoint
 *
 * @returns {boolean} True si la largeur est >= au breakpoint
 *
 * @example
 * const isDesktop = useBreakpoint('lg'); // >= 1024px
 * const isMobileOrTablet = !useBreakpoint('lg'); // < 1024px
 */
export function useBreakpoint(breakpoint) {
  const query = `(min-width: ${breakpoints[breakpoint]})`;
  return useMediaQuery(query);
}

/**
 * Hook pour obtenir l'état de tous les breakpoints simultanément.
 *
 * Retourne un objet avec un booléen pour chaque breakpoint et le breakpoint
 * actuel détecté. Optimise les rendus en mémorisant le breakpoint courant.
 *
 * @returns {Object} État des breakpoints
 * @property {boolean} isSm - >= 640px
 * @property {boolean} isMd - >= 768px
 * @property {boolean} isLg - >= 1024px
 * @property {boolean} isXl - >= 1280px
 * @property {boolean} is2xl - >= 1536px
 * @property {string} current - Breakpoint actuel ('xs'|'sm'|'md'|'lg'|'xl'|'2xl')
 *
 * @example
 * const { current, isMd, isLg } = useBreakpoints();
 * if (current === 'xs') console.log('Mobile');
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
 * Hook raccourci pour détecter un appareil mobile.
 *
 * Considère comme mobile toute largeur < 768px (breakpoint md).
 *
 * @returns {boolean} True si mobile (< 768px)
 *
 * @example
 * const isMobile = useIsMobile();
 * if (isMobile) return <MobileLayout />;
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
