import { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { navigationSections } from '@/app/routes.jsx';

/**
 * Hook pour gérer la navigation mobile bottom bar
 *
 * Fonctionnalités:
 * - Détecte la route active
 * - Gère l'état ouvert/fermé du menu "Plus"
 * - Fournit la liste des items principaux et secondaires
 * - Helper pour déterminer quel item de navigation est actif
 */
export default function useMobileNav() {
  const location = useLocation();
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);

  // Items principaux de la bottom nav (les 4 premiers + "Plus")
  const primaryItems = useMemo(() => {
    return [
      {
        id: 'cockpit',
        label: 'Cockpit',
        path: '/',
        section: navigationSections.find(s => s.id === 'cockpit'),
      },
      {
        id: 'operations',
        label: 'Ops',
        path: '/operations',
        section: navigationSections.find(s => s.id === 'operations'),
      },
      {
        id: 'finances',
        label: 'Finance',
        path: '/finances',
        section: navigationSections.find(s => s.id === 'finances'),
      },
      {
        id: 'restaurant',
        label: 'Resto',
        path: '/restaurant/overview',
        section: navigationSections.find(s => s.id === 'restaurant'),
      },
    ];
  }, []);

  // Items secondaires (affichés dans le menu "Plus")
  const secondaryItems = useMemo(() => {
    return [
      {
        id: 'intelligence',
        label: 'Intelligence',
        path: '/intelligence',
        section: navigationSections.find(s => s.id === 'intelligence'),
      },
      {
        id: 'parametres',
        label: 'Paramètres',
        path: '/parametres',
        section: navigationSections.find(s => s.id === 'parametres'),
      },
    ];
  }, []);

  // Vérifier si un item est actif
  const isItemActive = useCallback((path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  }, [location.pathname]);

  // Trouver l'item actif (primaire ou secondaire)
  const activeItem = useMemo(() => {
    // Chercher dans les items primaires
    const primaryActive = primaryItems.find(item => isItemActive(item.path));
    if (primaryActive) return primaryActive;

    // Chercher dans les items secondaires
    const secondaryActive = secondaryItems.find(item => isItemActive(item.path));
    return secondaryActive || null;
  }, [primaryItems, secondaryItems, isItemActive]);

  // Est-ce qu'un des items secondaires est actif?
  const isSecondaryActive = useMemo(() => {
    return secondaryItems.some(item => isItemActive(item.path));
  }, [secondaryItems, isItemActive]);

  // Ouvrir le menu "Plus"
  const openMoreMenu = useCallback(() => {
    setIsMoreMenuOpen(true);
  }, []);

  // Fermer le menu "Plus"
  const closeMoreMenu = useCallback(() => {
    setIsMoreMenuOpen(false);
  }, []);

  // Toggle le menu "Plus"
  const toggleMoreMenu = useCallback(() => {
    setIsMoreMenuOpen(prev => !prev);
  }, []);

  // Fermer le menu quand on change de route
  useEffect(() => {
    setIsMoreMenuOpen(false);
  }, [location.pathname]);

  // Empêcher le scroll du body quand le menu est ouvert
  useEffect(() => {
    if (isMoreMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isMoreMenuOpen]);

  return {
    // Items
    primaryItems,
    secondaryItems,
    activeItem,

    // État
    isMoreMenuOpen,
    isSecondaryActive,

    // Actions
    openMoreMenu,
    closeMoreMenu,
    toggleMoreMenu,

    // Helpers
    isItemActive,
  };
}
