/**
 * Service de gestion du stockage offline avec IndexedDB
 *
 * Gère le cache des données essentielles et la queue des mutations en attente
 * pour permettre le fonctionnement de l'application en mode déconnecté.
 *
 * Structure de la base de données :
 * - Store 'cache' : Données critiques (produits, fournisseurs, transactions)
 * - Store 'mutations' : Queue des mutations en attente de synchronisation
 * - Store 'metadata' : Métadonnées (dernière sync, version, etc.)
 */

const DB_NAME = 'inventaire-offline';
const DB_VERSION = 1;

// Stores de la base de données
const STORES = {
  CACHE: 'cache',
  MUTATIONS: 'mutations',
  METADATA: 'metadata',
};

// Clés de cache pour les différentes entités
export const CACHE_KEYS = {
  PRODUCTS: 'products',
  VENDORS: 'vendors',
  CATEGORIES: 'categories',
  FINANCE_TRANSACTIONS: 'finance_transactions',
  FINANCE_ACCOUNTS: 'finance_accounts',
  RESTAURANT_PLATS: 'restaurant_plats',
  RESTAURANT_INGREDIENTS: 'restaurant_ingredients',
  COCKPIT_OVERVIEW: 'cockpit_overview',
};

/**
 * Initialise et retourne la connexion à IndexedDB
 * @returns {Promise<IDBDatabase>}
 */
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      reject(new Error('Erreur lors de l\'ouverture de IndexedDB'));
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Store pour le cache des données
      if (!db.objectStoreNames.contains(STORES.CACHE)) {
        const cacheStore = db.createObjectStore(STORES.CACHE, { keyPath: 'key' });
        cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
      }

      // Store pour les mutations en attente
      if (!db.objectStoreNames.contains(STORES.MUTATIONS)) {
        const mutationsStore = db.createObjectStore(STORES.MUTATIONS, {
          keyPath: 'id',
          autoIncrement: true
        });
        mutationsStore.createIndex('timestamp', 'timestamp', { unique: false });
        mutationsStore.createIndex('type', 'type', { unique: false });
        mutationsStore.createIndex('status', 'status', { unique: false });
      }

      // Store pour les métadonnées
      if (!db.objectStoreNames.contains(STORES.METADATA)) {
        db.createObjectStore(STORES.METADATA, { keyPath: 'key' });
      }
    };
  });
}

/**
 * Sauvegarde des données dans le cache
 * @param {string} key - Clé de cache (utiliser CACHE_KEYS)
 * @param {any} data - Données à mettre en cache
 * @returns {Promise<void>}
 */
export async function saveToCache(key, data) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.CACHE], 'readwrite');
    const store = transaction.objectStore(STORES.CACHE);

    const cacheEntry = {
      key,
      data,
      timestamp: Date.now(),
    };

    await new Promise((resolve, reject) => {
      const request = store.put(cacheEntry);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });

    db.close();
  } catch (error) {
    console.error(`Erreur lors de la sauvegarde en cache (${key}):`, error);
    throw error;
  }
}

/**
 * Charge des données depuis le cache
 * @param {string} key - Clé de cache (utiliser CACHE_KEYS)
 * @returns {Promise<any|null>} Données en cache ou null si non trouvé
 */
export async function loadFromCache(key) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.CACHE], 'readonly');
    const store = transaction.objectStore(STORES.CACHE);

    const data = await new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    db.close();

    return data ? data.data : null;
  } catch (error) {
    console.error(`Erreur lors du chargement du cache (${key}):`, error);
    return null;
  }
}

/**
 * Vérifie si des données sont en cache et leur fraîcheur
 * @param {string} key - Clé de cache
 * @param {number} maxAge - Age maximum en millisecondes (par défaut: 5 minutes)
 * @returns {Promise<boolean>}
 */
export async function isCacheValid(key, maxAge = 5 * 60 * 1000) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.CACHE], 'readonly');
    const store = transaction.objectStore(STORES.CACHE);

    const entry = await new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    db.close();

    if (!entry) return false;

    const age = Date.now() - entry.timestamp;
    return age < maxAge;
  } catch (error) {
    console.error(`Erreur lors de la vérification du cache (${key}):`, error);
    return false;
  }
}

/**
 * Supprime une entrée du cache
 * @param {string} key - Clé de cache à supprimer
 * @returns {Promise<void>}
 */
export async function clearCacheEntry(key) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.CACHE], 'readwrite');
    const store = transaction.objectStore(STORES.CACHE);

    await new Promise((resolve, reject) => {
      const request = store.delete(key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });

    db.close();
  } catch (error) {
    console.error(`Erreur lors de la suppression du cache (${key}):`, error);
    throw error;
  }
}

/**
 * Vide tout le cache
 * @returns {Promise<void>}
 */
export async function clearAllCache() {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.CACHE], 'readwrite');
    const store = transaction.objectStore(STORES.CACHE);

    await new Promise((resolve, reject) => {
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });

    db.close();
  } catch (error) {
    console.error('Erreur lors de la suppression du cache:', error);
    throw error;
  }
}

/**
 * Ajoute une mutation dans la queue pour synchronisation ultérieure
 * @param {Object} mutation - Mutation à ajouter
 * @param {string} mutation.type - Type de mutation (CREATE, UPDATE, DELETE)
 * @param {string} mutation.endpoint - Endpoint API à appeler
 * @param {string} mutation.method - Méthode HTTP (POST, PUT, PATCH, DELETE)
 * @param {any} mutation.payload - Données de la mutation
 * @param {Object} mutation.metadata - Métadonnées additionnelles
 * @returns {Promise<number>} ID de la mutation dans la queue
 */
export async function queueMutation(mutation) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.MUTATIONS], 'readwrite');
    const store = transaction.objectStore(STORES.MUTATIONS);

    const mutationEntry = {
      ...mutation,
      timestamp: Date.now(),
      status: 'pending',
      attempts: 0,
      createdAt: new Date().toISOString(),
    };

    const id = await new Promise((resolve, reject) => {
      const request = store.add(mutationEntry);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    db.close();

    console.log(`Mutation ajoutée à la queue (ID: ${id}):`, mutation.type);
    return id;
  } catch (error) {
    console.error('Erreur lors de l\'ajout de la mutation:', error);
    throw error;
  }
}

/**
 * Récupère toutes les mutations en attente
 * @returns {Promise<Array>} Liste des mutations en attente
 */
export async function getPendingMutations() {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.MUTATIONS], 'readonly');
    const store = transaction.objectStore(STORES.MUTATIONS);
    const index = store.index('status');

    const mutations = await new Promise((resolve, reject) => {
      const request = index.getAll('pending');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    db.close();

    return mutations.sort((a, b) => a.timestamp - b.timestamp);
  } catch (error) {
    console.error('Erreur lors de la récupération des mutations:', error);
    return [];
  }
}

/**
 * Met à jour le statut d'une mutation
 * @param {number} id - ID de la mutation
 * @param {string} status - Nouveau statut (pending, processing, completed, failed)
 * @param {string} error - Message d'erreur si échec
 * @returns {Promise<void>}
 */
export async function updateMutationStatus(id, status, error = null) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.MUTATIONS], 'readwrite');
    const store = transaction.objectStore(STORES.MUTATIONS);

    const mutation = await new Promise((resolve, reject) => {
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    if (mutation) {
      mutation.status = status;
      mutation.lastAttempt = Date.now();
      mutation.attempts = (mutation.attempts || 0) + 1;

      if (error) {
        mutation.error = error;
      }

      await new Promise((resolve, reject) => {
        const request = store.put(mutation);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    }

    db.close();
  } catch (error) {
    console.error(`Erreur lors de la mise à jour de la mutation ${id}:`, error);
    throw error;
  }
}

/**
 * Supprime une mutation de la queue
 * @param {number} id - ID de la mutation à supprimer
 * @returns {Promise<void>}
 */
export async function deleteMutation(id) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.MUTATIONS], 'readwrite');
    const store = transaction.objectStore(STORES.MUTATIONS);

    await new Promise((resolve, reject) => {
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });

    db.close();
  } catch (error) {
    console.error(`Erreur lors de la suppression de la mutation ${id}:`, error);
    throw error;
  }
}

/**
 * Vide toutes les mutations terminées ou échouées
 * @returns {Promise<number>} Nombre de mutations supprimées
 */
export async function clearCompletedMutations() {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.MUTATIONS], 'readwrite');
    const store = transaction.objectStore(STORES.MUTATIONS);

    const allMutations = await new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    let deletedCount = 0;

    for (const mutation of allMutations) {
      if (mutation.status === 'completed' || mutation.status === 'failed') {
        await new Promise((resolve, reject) => {
          const request = store.delete(mutation.id);
          request.onsuccess = () => {
            deletedCount++;
            resolve();
          };
          request.onerror = () => reject(request.error);
        });
      }
    }

    db.close();

    return deletedCount;
  } catch (error) {
    console.error('Erreur lors du nettoyage des mutations:', error);
    return 0;
  }
}

/**
 * Sauvegarde une métadonnée
 * @param {string} key - Clé de la métadonnée
 * @param {any} value - Valeur à sauvegarder
 * @returns {Promise<void>}
 */
export async function saveMetadata(key, value) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.METADATA], 'readwrite');
    const store = transaction.objectStore(STORES.METADATA);

    await new Promise((resolve, reject) => {
      const request = store.put({ key, value, timestamp: Date.now() });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });

    db.close();
  } catch (error) {
    console.error(`Erreur lors de la sauvegarde de la métadonnée ${key}:`, error);
    throw error;
  }
}

/**
 * Charge une métadonnée
 * @param {string} key - Clé de la métadonnée
 * @returns {Promise<any|null>}
 */
export async function loadMetadata(key) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORES.METADATA], 'readonly');
    const store = transaction.objectStore(STORES.METADATA);

    const data = await new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    db.close();

    return data ? data.value : null;
  } catch (error) {
    console.error(`Erreur lors du chargement de la métadonnée ${key}:`, error);
    return null;
  }
}

/**
 * Statistiques de stockage offline
 * @returns {Promise<Object>}
 */
export async function getStorageStats() {
  try {
    const db = await openDB();

    // Compter les entrées de cache
    const cacheTransaction = db.transaction([STORES.CACHE], 'readonly');
    const cacheStore = cacheTransaction.objectStore(STORES.CACHE);
    const cacheCount = await new Promise((resolve, reject) => {
      const request = cacheStore.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    // Compter les mutations
    const mutationsTransaction = db.transaction([STORES.MUTATIONS], 'readonly');
    const mutationsStore = mutationsTransaction.objectStore(STORES.MUTATIONS);
    const mutationsCount = await new Promise((resolve, reject) => {
      const request = mutationsStore.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    // Compter les mutations en attente
    const pendingMutations = await getPendingMutations();

    db.close();

    return {
      cacheEntries: cacheCount,
      totalMutations: mutationsCount,
      pendingMutations: pendingMutations.length,
      completedMutations: mutationsCount - pendingMutations.length,
    };
  } catch (error) {
    console.error('Erreur lors de la récupération des statistiques:', error);
    return {
      cacheEntries: 0,
      totalMutations: 0,
      pendingMutations: 0,
      completedMutations: 0,
    };
  }
}
