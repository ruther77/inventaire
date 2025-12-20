import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useOffline } from '../hooks/useOffline.js';
import {
  queueMutation,
  getPendingMutations,
  updateMutationStatus,
  deleteMutation,
  saveToCache,
  loadFromCache,
  getStorageStats,
  CACHE_KEYS,
} from '../services/offlineStorage.js';
import api from '../api/client.js';

const OfflineContext = createContext(null);

/**
 * Provider pour gérer l'état offline de l'application
 *
 * Responsabilités :
 * - Détecter le statut online/offline
 * - Gérer la queue des mutations en attente
 * - Synchroniser les données quand la connexion revient
 * - Mettre en cache les données essentielles
 */
export function OfflineProvider({ children }) {
  const { isOnline, wasOffline, lastOnlineAt, offlineSince } = useOffline();
  const queryClient = useQueryClient();

  const [pendingMutations, setPendingMutations] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState(null);
  const [storageStats, setStorageStats] = useState({
    cacheEntries: 0,
    totalMutations: 0,
    pendingMutations: 0,
    completedMutations: 0,
  });

  /**
   * Charge les mutations en attente depuis IndexedDB
   */
  const loadPendingMutations = useCallback(async () => {
    try {
      const mutations = await getPendingMutations();
      setPendingMutations(mutations);

      const stats = await getStorageStats();
      setStorageStats(stats);
    } catch (error) {
      console.error('Erreur lors du chargement des mutations en attente:', error);
    }
  }, []);

  /**
   * Ajoute une mutation à la queue pour synchronisation ultérieure
   */
  const addPendingMutation = useCallback(async (mutation) => {
    try {
      const id = await queueMutation(mutation);
      await loadPendingMutations();
      return id;
    } catch (error) {
      console.error('Erreur lors de l\'ajout de la mutation:', error);
      throw error;
    }
  }, [loadPendingMutations]);

  /**
   * Synchronise toutes les mutations en attente
   */
  const syncPendingMutations = useCallback(async () => {
    if (!isOnline || isSyncing || pendingMutations.length === 0) {
      return;
    }

    setIsSyncing(true);
    setSyncError(null);

    try {
      console.log(`Synchronisation de ${pendingMutations.length} mutations en attente...`);

      let successCount = 0;
      let errorCount = 0;

      for (const mutation of pendingMutations) {
        try {
          // Mettre à jour le statut à "processing"
          await updateMutationStatus(mutation.id, 'processing');

          // Exécuter la mutation
          const response = await api({
            method: mutation.method,
            url: mutation.endpoint,
            data: mutation.payload,
          });

          // Marquer comme complétée
          await updateMutationStatus(mutation.id, 'completed');
          await deleteMutation(mutation.id);
          successCount++;

          console.log(`Mutation ${mutation.id} synchronisée avec succès`);

          // Si la mutation a un callback de succès
          if (mutation.metadata?.onSuccess) {
            try {
              mutation.metadata.onSuccess(response.data);
            } catch (callbackError) {
              console.error('Erreur dans le callback de succès:', callbackError);
            }
          }
        } catch (error) {
          console.error(`Erreur lors de la synchronisation de la mutation ${mutation.id}:`, error);

          // Marquer comme échouée avec le message d'erreur
          await updateMutationStatus(
            mutation.id,
            'failed',
            error.response?.data?.message || error.message
          );
          errorCount++;

          // Si la mutation a un callback d'erreur
          if (mutation.metadata?.onError) {
            try {
              mutation.metadata.onError(error);
            } catch (callbackError) {
              console.error('Erreur dans le callback d\'erreur:', callbackError);
            }
          }
        }
      }

      console.log(`Synchronisation terminée: ${successCount} réussies, ${errorCount} échouées`);

      // Recharger les mutations en attente
      await loadPendingMutations();

      // Invalider les queries pour rafraîchir les données
      queryClient.invalidateQueries();

      if (errorCount > 0) {
        setSyncError(`${errorCount} mutation(s) ont échoué`);
      }
    } catch (error) {
      console.error('Erreur lors de la synchronisation:', error);
      setSyncError(error.message);
    } finally {
      setIsSyncing(false);
    }
  }, [isOnline, isSyncing, pendingMutations, queryClient, loadPendingMutations]);

  /**
   * Cache les données critiques pour utilisation offline
   */
  const cacheEssentialData = useCallback(async () => {
    if (!isOnline) return;

    try {
      // Cache des produits
      const productsCache = queryClient.getQueryData(['products']);
      if (productsCache) {
        await saveToCache(CACHE_KEYS.PRODUCTS, productsCache);
      }

      // Cache des fournisseurs
      const vendorsCache = queryClient.getQueryData(['vendors']);
      if (vendorsCache) {
        await saveToCache(CACHE_KEYS.VENDORS, vendorsCache);
      }

      // Cache des catégories
      const categoriesCache = queryClient.getQueryData(['categories']);
      if (categoriesCache) {
        await saveToCache(CACHE_KEYS.CATEGORIES, categoriesCache);
      }

      // Cache des comptes bancaires
      const accountsCache = queryClient.getQueryData(['finance', 'accounts']);
      if (accountsCache) {
        await saveToCache(CACHE_KEYS.FINANCE_ACCOUNTS, accountsCache);
      }

      // Cache du cockpit
      const cockpitCache = queryClient.getQueryData(['cockpit', 'overview']);
      if (cockpitCache) {
        await saveToCache(CACHE_KEYS.COCKPIT_OVERVIEW, cockpitCache);
      }

      console.log('Données essentielles mises en cache');
    } catch (error) {
      console.error('Erreur lors de la mise en cache des données:', error);
    }
  }, [isOnline, queryClient]);

  /**
   * Charge les données depuis le cache quand offline
   */
  const loadCachedData = useCallback(async () => {
    if (isOnline) return;

    try {
      // Charger les produits depuis le cache
      const cachedProducts = await loadFromCache(CACHE_KEYS.PRODUCTS);
      if (cachedProducts) {
        queryClient.setQueryData(['products'], cachedProducts);
      }

      // Charger les fournisseurs depuis le cache
      const cachedVendors = await loadFromCache(CACHE_KEYS.VENDORS);
      if (cachedVendors) {
        queryClient.setQueryData(['vendors'], cachedVendors);
      }

      // Charger les catégories depuis le cache
      const cachedCategories = await loadFromCache(CACHE_KEYS.CATEGORIES);
      if (cachedCategories) {
        queryClient.setQueryData(['categories'], cachedCategories);
      }

      // Charger les comptes bancaires depuis le cache
      const cachedAccounts = await loadFromCache(CACHE_KEYS.FINANCE_ACCOUNTS);
      if (cachedAccounts) {
        queryClient.setQueryData(['finance', 'accounts'], cachedAccounts);
      }

      // Charger le cockpit depuis le cache
      const cachedCockpit = await loadFromCache(CACHE_KEYS.COCKPIT_OVERVIEW);
      if (cachedCockpit) {
        queryClient.setQueryData(['cockpit', 'overview'], cachedCockpit);
      }

      console.log('Données chargées depuis le cache');
    } catch (error) {
      console.error('Erreur lors du chargement du cache:', error);
    }
  }, [isOnline, queryClient]);

  // Charger les mutations en attente au montage
  useEffect(() => {
    loadPendingMutations();
  }, [loadPendingMutations]);

  // Synchroniser quand la connexion revient
  useEffect(() => {
    if (isOnline && wasOffline && pendingMutations.length > 0) {
      console.log('Connexion rétablie - Démarrage de la synchronisation...');
      // Délai de 1 seconde pour laisser le temps à la connexion de se stabiliser
      const syncTimer = setTimeout(() => {
        syncPendingMutations();
      }, 1000);

      return () => clearTimeout(syncTimer);
    }
  }, [isOnline, wasOffline, pendingMutations.length, syncPendingMutations]);

  // Mettre en cache les données essentielles toutes les 2 minutes quand online
  useEffect(() => {
    if (!isOnline) return;

    cacheEssentialData(); // Cache initial

    const cacheInterval = setInterval(() => {
      cacheEssentialData();
    }, 2 * 60 * 1000); // Toutes les 2 minutes

    return () => clearInterval(cacheInterval);
  }, [isOnline, cacheEssentialData]);

  // Charger les données depuis le cache quand offline
  useEffect(() => {
    if (!isOnline) {
      loadCachedData();
    }
  }, [isOnline, loadCachedData]);

  const value = {
    // État de connexion
    isOnline,
    wasOffline,
    lastOnlineAt,
    offlineSince,

    // Mutations en attente
    pendingMutations,
    addPendingMutation,
    syncPendingMutations,
    isSyncing,
    syncError,

    // Statistiques
    storageStats,

    // Actions
    refreshStats: loadPendingMutations,
  };

  return (
    <OfflineContext.Provider value={value}>
      {children}
    </OfflineContext.Provider>
  );
}

/**
 * Hook pour accéder au contexte offline
 */
export function useOfflineContext() {
  const context = useContext(OfflineContext);

  if (!context) {
    throw new Error('useOfflineContext doit être utilisé dans un OfflineProvider');
  }

  return context;
}
