/**
 * Module de hooks pour la détection du statut de connexion réseau.
 * @module hooks/useOffline
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * Hook pour détecter et gérer le statut de connexion réseau (online/offline).
 *
 * Utilise l'API navigator.onLine et écoute les événements online/offline
 * pour détecter les changements de connectivité en temps réel.
 *
 * @returns {Object} État de connexion
 * @returns {boolean} isOnline - true si l'utilisateur est en ligne
 * @returns {boolean} wasOffline - true si l'utilisateur était hors ligne et vient de se reconnecter
 * @returns {Date|null} lastOnlineAt - Date de la dernière connexion en ligne
 * @returns {Date|null} offlineSince - Date du début de la déconnexion
 */
export function useOffline() {
  const [isOnline, setIsOnline] = useState(() => {
    // Initialisation avec l'état actuel du navigateur
    return typeof navigator !== 'undefined' ? navigator.onLine : true;
  });

  const [wasOffline, setWasOffline] = useState(false);
  const [lastOnlineAt, setLastOnlineAt] = useState(null);
  const [offlineSince, setOfflineSince] = useState(null);

  const handleOnline = useCallback(() => {
    setIsOnline(true);
    setLastOnlineAt(new Date());

    // Si on était offline avant, marquer wasOffline pour afficher le message de reconnexion
    if (!isOnline) {
      setWasOffline(true);
      setOfflineSince(null);

      // Réinitialiser wasOffline après 5 secondes
      setTimeout(() => {
        setWasOffline(false);
      }, 5000);
    }
  }, [isOnline]);

  const handleOffline = useCallback(() => {
    setIsOnline(false);
    setOfflineSince(new Date());
    setWasOffline(false);
  }, []);

  useEffect(() => {
    // Vérifier l'état initial
    if (navigator.onLine) {
      setLastOnlineAt(new Date());
    } else {
      setOfflineSince(new Date());
    }

    // Écouter les événements de changement de connectivité
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Cleanup - retirer les écouteurs lors du démontage
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  return {
    isOnline,
    wasOffline,
    lastOnlineAt,
    offlineSince,
  };
}
