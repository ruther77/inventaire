import { useState, useEffect, useCallback } from 'react';

/**
 * Hook personnalisé pour gérer les fonctionnalités PWA
 *
 * Fonctionnalités:
 * - Détection de l'installabilité de l'application
 * - Gestion du prompt d'installation
 * - Détection du mode standalone (app installée)
 * - Gestion des mises à jour du Service Worker
 * - Détection du support PWA
 *
 * @returns {Object} État et méthodes pour gérer le PWA
 */
export function usePWA() {
  // État pour le prompt d'installation
  const [deferredPrompt, setDeferredPrompt] = useState(null);

  // État d'installabilité
  const [isInstallable, setIsInstallable] = useState(false);

  // État d'installation (app déjà installée)
  const [isInstalled, setIsInstalled] = useState(false);

  // État du mode standalone
  const [isStandalone, setIsStandalone] = useState(false);

  // État de mise à jour disponible
  const [updateAvailable, setUpdateAvailable] = useState(false);

  // Service Worker registration
  const [registration, setRegistration] = useState(null);

  // Support PWA
  const [isPWASupported, setIsPWASupported] = useState(false);

  /**
   * Détecte si l'application est en mode standalone
   */
  useEffect(() => {
    const checkStandalone = () => {
      // Vérifie si l'app est lancée en mode standalone
      const standalone =
        window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true ||
        document.referrer.includes('android-app://');

      setIsStandalone(standalone);
      setIsInstalled(standalone);
    };

    checkStandalone();

    // Écoute les changements de mode d'affichage
    const mediaQuery = window.matchMedia('(display-mode: standalone)');
    const handleChange = (e) => {
      setIsStandalone(e.matches);
      setIsInstalled(e.matches);
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else if (mediaQuery.addListener) {
      // Fallback pour les navigateurs plus anciens
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  /**
   * Détecte le support PWA
   */
  useEffect(() => {
    const supported = 'serviceWorker' in navigator && 'PushManager' in window;
    setIsPWASupported(supported);
  }, []);

  /**
   * Capture l'événement beforeinstallprompt
   */
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      console.log('[PWA] beforeinstallprompt event captured');

      // Empêche l'affichage automatique du prompt
      e.preventDefault();

      // Stocke l'événement pour l'utiliser plus tard
      setDeferredPrompt(e);
      setIsInstallable(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  /**
   * Détecte quand l'app a été installée
   */
  useEffect(() => {
    const handleAppInstalled = () => {
      console.log('[PWA] App successfully installed');
      setIsInstalled(true);
      setIsInstallable(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  /**
   * Gère les mises à jour du Service Worker
   */
  useEffect(() => {
    if (!registration) return;

    const handleUpdateFound = () => {
      const newWorker = registration.installing;

      if (!newWorker) return;

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          console.log('[PWA] New service worker available');
          setUpdateAvailable(true);
        }
      });
    };

    registration.addEventListener('updatefound', handleUpdateFound);

    // Vérifie les mises à jour périodiquement (toutes les heures)
    const updateInterval = setInterval(() => {
      console.log('[PWA] Checking for updates...');
      registration.update();
    }, 60 * 60 * 1000); // 1 heure

    return () => {
      registration.removeEventListener('updatefound', handleUpdateFound);
      clearInterval(updateInterval);
    };
  }, [registration]);

  /**
   * Affiche le prompt d'installation
   */
  const promptInstall = useCallback(async () => {
    if (!deferredPrompt) {
      console.warn('[PWA] Install prompt not available');
      return { outcome: 'unavailable' };
    }

    try {
      console.log('[PWA] Showing install prompt');

      // Affiche le prompt d'installation natif
      deferredPrompt.prompt();

      // Attend la réponse de l'utilisateur
      const { outcome } = await deferredPrompt.userChoice;

      console.log('[PWA] User choice:', outcome);

      // Nettoie le prompt
      setDeferredPrompt(null);
      setIsInstallable(false);

      if (outcome === 'accepted') {
        console.log('[PWA] User accepted the install prompt');
      } else {
        console.log('[PWA] User dismissed the install prompt');
      }

      return { outcome };
    } catch (error) {
      console.error('[PWA] Error showing install prompt:', error);
      return { outcome: 'error', error };
    }
  }, [deferredPrompt]);

  /**
   * Active la mise à jour du Service Worker
   */
  const activateUpdate = useCallback(() => {
    if (!registration || !registration.waiting) {
      console.warn('[PWA] No update waiting');
      return;
    }

    console.log('[PWA] Activating update...');

    // Envoie un message au SW en attente pour qu'il s'active
    registration.waiting.postMessage({ type: 'SKIP_WAITING' });

    // Recharge la page une fois le nouveau SW activé
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      console.log('[PWA] Reloading page for update...');
      window.location.reload();
    });
  }, [registration]);

  /**
   * Désinstalle le Service Worker (pour debug/développement)
   */
  const unregister = useCallback(async () => {
    if (!registration) {
      console.warn('[PWA] No service worker registered');
      return false;
    }

    try {
      const success = await registration.unregister();
      if (success) {
        console.log('[PWA] Service worker unregistered successfully');
        setRegistration(null);
      }
      return success;
    } catch (error) {
      console.error('[PWA] Error unregistering service worker:', error);
      return false;
    }
  }, [registration]);

  /**
   * Vide tous les caches
   */
  const clearCaches = useCallback(async () => {
    try {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      );
      console.log('[PWA] All caches cleared');
      return true;
    } catch (error) {
      console.error('[PWA] Error clearing caches:', error);
      return false;
    }
  }, []);

  /**
   * Obtient des informations sur les caches
   */
  const getCacheInfo = useCallback(async () => {
    try {
      const cacheNames = await caches.keys();
      const cacheInfo = await Promise.all(
        cacheNames.map(async (name) => {
          const cache = await caches.open(name);
          const keys = await cache.keys();
          return {
            name,
            size: keys.length,
            urls: keys.map(req => req.url)
          };
        })
      );
      return cacheInfo;
    } catch (error) {
      console.error('[PWA] Error getting cache info:', error);
      return [];
    }
  }, []);

  /**
   * Vérifie si l'app peut être partagée (Web Share API)
   */
  const canShare = useCallback(() => {
    return 'share' in navigator;
  }, []);

  /**
   * Partage du contenu via Web Share API
   */
  const share = useCallback(async (data) => {
    if (!canShare()) {
      console.warn('[PWA] Web Share API not supported');
      return { success: false, error: 'not_supported' };
    }

    try {
      await navigator.share(data);
      console.log('[PWA] Content shared successfully');
      return { success: true };
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('[PWA] Share cancelled by user');
        return { success: false, error: 'cancelled' };
      }
      console.error('[PWA] Error sharing:', error);
      return { success: false, error: error.message };
    }
  }, [canShare]);

  /**
   * Obtient les capacités de l'appareil
   */
  const getDeviceCapabilities = useCallback(() => {
    return {
      standalone: isStandalone,
      installed: isInstalled,
      installable: isInstallable,
      pwaSupported: isPWASupported,
      serviceWorkerSupported: 'serviceWorker' in navigator,
      pushSupported: 'PushManager' in window,
      notificationSupported: 'Notification' in window,
      shareSupported: canShare(),
      online: navigator.onLine,
      connectionType: navigator.connection?.effectiveType || 'unknown',
      isMobile: /iPhone|iPad|iPod|Android/i.test(navigator.userAgent),
      isIOS: /iPhone|iPad|iPod/i.test(navigator.userAgent),
      isAndroid: /Android/i.test(navigator.userAgent),
    };
  }, [isStandalone, isInstalled, isInstallable, isPWASupported, canShare]);

  return {
    // États
    isInstallable,
    isInstalled,
    isStandalone,
    updateAvailable,
    isPWASupported,
    registration,

    // Méthodes d'installation
    promptInstall,
    setRegistration,

    // Méthodes de mise à jour
    activateUpdate,

    // Méthodes de gestion
    unregister,
    clearCaches,
    getCacheInfo,

    // Méthodes de partage
    canShare,
    share,

    // Informations
    getDeviceCapabilities,
  };
}

export default usePWA;
