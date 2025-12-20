import { useState, useEffect, useCallback } from 'react';

/**
 * Hook personnalisé pour gérer les notifications push PWA
 *
 * Fonctionnalités:
 * - Demande de permission pour les notifications
 * - Souscription aux notifications push
 * - Désinscription des notifications push
 * - Suivi de l'état de la souscription
 * - Gestion de la clé VAPID pour l'authentification
 *
 * @returns {Object} État et méthodes pour gérer les notifications push
 */
export function usePushNotifications() {
  // État de permission des notifications
  const [permission, setPermission] = useState(() => {
    if (!('Notification' in window)) return 'unsupported';
    return Notification.permission;
  });

  // État de souscription
  const [subscription, setSubscription] = useState(null);

  // État de chargement
  const [isLoading, setIsLoading] = useState(false);

  // État d'erreur
  const [error, setError] = useState(null);

  // État de support des notifications push
  const [isSupported, setIsSupported] = useState(false);

  // Service Worker registration
  const [registration, setRegistration] = useState(null);

  /**
   * Clé VAPID publique pour l'authentification des push notifications
   * TODO: Remplacer par votre vraie clé VAPID en production
   * Pour générer une clé VAPID: npx web-push generate-vapid-keys
   */
  const VAPID_PUBLIC_KEY = 'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U';

  /**
   * Convertit une clé VAPID base64 en Uint8Array
   */
  const urlBase64ToUint8Array = useCallback((base64String) => {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }, []);

  /**
   * Vérifie le support des notifications push
   */
  useEffect(() => {
    const checkSupport = () => {
      const supported =
        'Notification' in window &&
        'serviceWorker' in navigator &&
        'PushManager' in window;

      setIsSupported(supported);

      if (!supported) {
        console.warn('[Push] Notifications push non supportées');
      }
    };

    checkSupport();
  }, []);

  /**
   * Récupère le Service Worker registration
   */
  useEffect(() => {
    if (!isSupported) return;

    const getRegistration = async () => {
      try {
        const reg = await navigator.serviceWorker.ready;
        setRegistration(reg);
        console.log('[Push] Service Worker prêt');
      } catch (error) {
        console.error('[Push] Erreur lors de la récupération du SW:', error);
        setError(error);
      }
    };

    getRegistration();
  }, [isSupported]);

  /**
   * Vérifie la souscription existante
   */
  useEffect(() => {
    if (!registration) return;

    const checkSubscription = async () => {
      try {
        const existingSub = await registration.pushManager.getSubscription();
        setSubscription(existingSub);

        if (existingSub) {
          console.log('[Push] Souscription existante trouvée');
        }
      } catch (error) {
        console.error('[Push] Erreur lors de la vérification de la souscription:', error);
        setError(error);
      }
    };

    checkSubscription();
  }, [registration]);

  /**
   * Écoute les changements de permission
   */
  useEffect(() => {
    if (!isSupported) return;

    const handlePermissionChange = () => {
      setPermission(Notification.permission);
    };

    // Note: l'API permissions.query pour les notifications n'est pas universellement supportée
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions.query({ name: 'notifications' })
        .then((permissionStatus) => {
          permissionStatus.addEventListener('change', handlePermissionChange);
          return () => permissionStatus.removeEventListener('change', handlePermissionChange);
        })
        .catch((error) => {
          console.warn('[Push] Impossible de surveiller les changements de permission:', error);
        });
    }
  }, [isSupported]);

  /**
   * Demande la permission pour les notifications
   */
  const requestPermission = useCallback(async () => {
    if (!isSupported) {
      setError(new Error('Les notifications push ne sont pas supportées'));
      return { success: false, permission: 'unsupported' };
    }

    if (permission === 'granted') {
      console.log('[Push] Permission déjà accordée');
      return { success: true, permission: 'granted' };
    }

    try {
      setIsLoading(true);
      setError(null);

      console.log('[Push] Demande de permission...');
      const result = await Notification.requestPermission();

      setPermission(result);

      if (result === 'granted') {
        console.log('[Push] Permission accordée');
        return { success: true, permission: result };
      } else {
        console.log('[Push] Permission refusée:', result);
        return { success: false, permission: result };
      }
    } catch (error) {
      console.error('[Push] Erreur lors de la demande de permission:', error);
      setError(error);
      return { success: false, permission: 'denied', error };
    } finally {
      setIsLoading(false);
    }
  }, [isSupported, permission]);

  /**
   * Souscrit aux notifications push
   */
  const subscribe = useCallback(async () => {
    if (!isSupported) {
      setError(new Error('Les notifications push ne sont pas supportées'));
      return { success: false, error: 'not_supported' };
    }

    if (!registration) {
      setError(new Error('Service Worker non disponible'));
      return { success: false, error: 'no_service_worker' };
    }

    if (permission !== 'granted') {
      console.log('[Push] Permission non accordée, demande en cours...');
      const permResult = await requestPermission();
      if (!permResult.success) {
        return { success: false, error: 'permission_denied' };
      }
    }

    try {
      setIsLoading(true);
      setError(null);

      console.log('[Push] Souscription aux notifications push...');

      const applicationServerKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey,
      });

      setSubscription(sub);
      console.log('[Push] Souscription réussie:', sub);

      // Ici, vous devriez envoyer la souscription à votre backend
      // await sendSubscriptionToBackend(sub);

      return {
        success: true,
        subscription: sub.toJSON(),
      };
    } catch (error) {
      console.error('[Push] Erreur lors de la souscription:', error);
      setError(error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  }, [isSupported, registration, permission, requestPermission, urlBase64ToUint8Array, VAPID_PUBLIC_KEY]);

  /**
   * Se désabonne des notifications push
   */
  const unsubscribe = useCallback(async () => {
    if (!subscription) {
      console.warn('[Push] Aucune souscription à annuler');
      return { success: true, message: 'no_subscription' };
    }

    try {
      setIsLoading(true);
      setError(null);

      console.log('[Push] Désinscription des notifications push...');

      const success = await subscription.unsubscribe();

      if (success) {
        setSubscription(null);
        console.log('[Push] Désinscription réussie');

        // Ici, vous devriez informer votre backend de la désinscription
        // await removeSubscriptionFromBackend(subscription);

        return { success: true };
      } else {
        throw new Error('La désinscription a échoué');
      }
    } catch (error) {
      console.error('[Push] Erreur lors de la désinscription:', error);
      setError(error);
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  }, [subscription]);

  /**
   * Envoie une notification de test (côté client uniquement)
   */
  const sendTestNotification = useCallback(async () => {
    if (permission !== 'granted') {
      console.warn('[Push] Permission non accordée pour les notifications');
      return { success: false, error: 'permission_denied' };
    }

    try {
      // Envoie une notification locale de test
      const notification = new Notification('Test de notification', {
        body: 'Ceci est une notification de test locale',
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        tag: 'test-notification',
        vibrate: [200, 100, 200],
      });

      console.log('[Push] Notification de test envoyée');

      // Auto-ferme après 5 secondes
      setTimeout(() => {
        notification.close();
      }, 5000);

      return { success: true };
    } catch (error) {
      console.error('[Push] Erreur lors de l\'envoi de la notification de test:', error);
      return { success: false, error: error.message };
    }
  }, [permission]);

  /**
   * Obtient les informations de souscription
   */
  const getSubscriptionInfo = useCallback(() => {
    if (!subscription) {
      return null;
    }

    const subJSON = subscription.toJSON();
    return {
      endpoint: subJSON.endpoint,
      keys: subJSON.keys,
      expirationTime: subscription.expirationTime,
    };
  }, [subscription]);

  /**
   * Vérifie si l'utilisateur est souscrit
   */
  const isSubscribed = useCallback(() => {
    return subscription !== null;
  }, [subscription]);

  return {
    // États
    permission,
    subscription,
    isLoading,
    error,
    isSupported,
    isSubscribed: isSubscribed(),

    // Méthodes
    requestPermission,
    subscribe,
    unsubscribe,
    sendTestNotification,
    getSubscriptionInfo,

    // Utilitaires
    urlBase64ToUint8Array,
  };
}

export default usePushNotifications;
