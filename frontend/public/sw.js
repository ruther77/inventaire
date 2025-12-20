/**
 * Service Worker pour l'application Inventaire Épicerie
 * Gère le cache des ressources et les stratégies réseau
 */

const CACHE_VERSION = 'v1.6.0';
const CACHE_NAME = `inventaire-epicerie-${CACHE_VERSION}`;

// Ressources essentielles à mettre en cache lors de l'installation
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  '/offline.html',
];

// Patterns d'URL pour les différentes stratégies
const API_PATTERNS = [
  /\/api\//,
  /\/auth\//,
];

const ASSET_PATTERNS = [
  /\.js$/,
  /\.css$/,
  /\.woff2?$/,
  /\.png$/,
  /\.jpg$/,
  /\.jpeg$/,
  /\.svg$/,
  /\.webp$/,
];

/**
 * Événement d'installation du Service Worker
 * Met en cache les ressources statiques essentielles
 */
self.addEventListener('install', (event) => {
  console.log('[SW] Installation du Service Worker', CACHE_VERSION);

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Mise en cache des ressources statiques');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        // Force l'activation immédiate du nouveau SW
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Erreur lors de la mise en cache initiale:', error);
      })
  );
});

/**
 * Événement d'activation du Service Worker
 * Nettoie les anciens caches
 */
self.addEventListener('activate', (event) => {
  console.log('[SW] Activation du Service Worker', CACHE_VERSION);

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              // Supprime tous les caches qui ne correspondent pas à la version actuelle
              return cacheName.startsWith('inventaire-epicerie-') && cacheName !== CACHE_NAME;
            })
            .map((cacheName) => {
              console.log('[SW] Suppression de l\'ancien cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        // Prend le contrôle de tous les clients immédiatement
        return self.clients.claim();
      })
  );
});

/**
 * Événement de récupération (fetch)
 * Applique les stratégies de cache appropriées
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignore les requêtes non-HTTP/HTTPS
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Ignore les requêtes Chrome extensions
  if (url.protocol === 'chrome-extension:') {
    return;
  }

  // Stratégie pour les appels API: Network First (avec fallback cache)
  if (API_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Stratégie pour les assets statiques: Network First pour JS/CSS (éviter cache obsolète)
  // Cache First uniquement pour les images/fonts
  if (ASSET_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    // JS et CSS: Network First pour toujours avoir la dernière version
    if (/\.(js|css)$/.test(url.pathname)) {
      event.respondWith(networkFirst(request));
    } else {
      // Images, fonts: Cache First
      event.respondWith(cacheFirst(request));
    }
    return;
  }

  // Stratégie pour la navigation: Network First avec fallback vers index.html
  if (request.mode === 'navigate') {
    event.respondWith(navigationHandler(request));
    return;
  }

  // Par défaut: Network First
  event.respondWith(networkFirst(request));
});

/**
 * Stratégie Cache First
 * Cherche d'abord dans le cache, puis réseau si non trouvé
 */
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Cache hit:', request.url);
      return cachedResponse;
    }

    console.log('[SW] Cache miss, fetching:', request.url);
    const networkResponse = await fetch(request);

    // Met en cache si la réponse est valide
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] Erreur cache-first:', error);
    throw error;
  }
}

/**
 * Stratégie Network First
 * Essaie le réseau d'abord, puis cache en fallback
 */
async function networkFirst(request) {
  try {
    console.log('[SW] Network first, fetching:', request.url);
    const networkResponse = await fetch(request);

    // Met en cache si la réponse est valide
    if (networkResponse && networkResponse.status === 200 && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      console.log('[SW] Cache fallback hit:', request.url);
      return cachedResponse;
    }

    console.error('[SW] Erreur network-first, pas de cache disponible:', error);
    throw error;
  }
}

/**
 * Gestionnaire spécial pour la navigation
 * Network First avec fallback vers index.html pour SPA routing, puis offline.html
 */
async function navigationHandler(request) {
  try {
    console.log('[SW] Navigation request:', request.url);
    const networkResponse = await fetch(request);

    // Met en cache la réponse
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Navigation network failed, trying cache');

    // Essaie le cache pour cette URL spécifique
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Fallback vers index.html pour le routing SPA
    console.log('[SW] Fallback to index.html for SPA routing');
    const indexCache = await caches.match('/index.html');
    if (indexCache) {
      return indexCache;
    }

    // Si aucun cache n'est disponible, affiche la page offline
    console.log('[SW] No cache available, showing offline page');
    const offlineResponse = await caches.match('/offline.html');
    if (offlineResponse) {
      return offlineResponse;
    }

    console.error('[SW] Erreur navigation, pas de fallback disponible:', error);
    throw error;
  }
}

/**
 * Événement de message pour communication avec l'application
 */
self.addEventListener('message', (event) => {
  console.log('[SW] Message reçu:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then((cache) => cache.addAll(event.data.urls))
    );
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys()
        .then((cacheNames) => Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        ))
    );
  }
});

/**
 * Événement de synchronisation en arrière-plan (background sync)
 */
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

/**
 * Fonction de synchronisation des données
 * Récupère et rejoue les mutations en attente depuis IndexedDB
 */
async function syncData() {
  try {
    console.log('[SW] Synchronisation des données en arrière-plan');

    // Ouvrir la base de données IndexedDB
    const db = await openIndexedDB();

    // Récupérer toutes les mutations en attente
    const pendingMutations = await getPendingMutationsFromDB(db);

    if (pendingMutations.length === 0) {
      console.log('[SW] Aucune mutation en attente');
      db.close();
      return;
    }

    console.log(`[SW] ${pendingMutations.length} mutation(s) à synchroniser`);

    let successCount = 0;
    let failureCount = 0;

    // Traiter chaque mutation
    for (const mutation of pendingMutations) {
      try {
        // Vérifier le nombre de tentatives pour éviter les boucles infinies
        const maxRetries = 5;
        if (mutation.attempts >= maxRetries) {
          console.warn(`[SW] Mutation ${mutation.id} a dépassé le nombre maximum de tentatives (${maxRetries})`);
          await updateMutationStatusInDB(db, mutation.id, 'failed', 'Nombre maximum de tentatives dépassé');
          failureCount++;
          continue;
        }

        // Calculer le délai de retry avec exponential backoff
        const retryDelay = calculateRetryDelay(mutation.attempts);
        const timeSinceLastAttempt = Date.now() - (mutation.lastAttempt || mutation.timestamp);

        // Si le délai n'est pas écoulé, passer cette mutation
        if (mutation.lastAttempt && timeSinceLastAttempt < retryDelay) {
          console.log(`[SW] Mutation ${mutation.id} en attente de retry (délai: ${retryDelay}ms)`);
          continue;
        }

        // Marquer comme "processing"
        await updateMutationStatusInDB(db, mutation.id, 'processing');

        // Construire les en-têtes de la requête
        const headers = {
          'Content-Type': 'application/json',
        };

        // Préparer les options de fetch
        const fetchOptions = {
          method: mutation.method,
          headers: headers,
          credentials: 'include', // Important pour les cookies HTTP-Only
        };

        // Ajouter le body pour les requêtes qui le supportent
        if (mutation.method !== 'GET' && mutation.method !== 'HEAD' && mutation.payload) {
          fetchOptions.body = JSON.stringify(mutation.payload);
        }

        // Construire l'URL complète
        const baseURL = self.location.origin;
        const apiPath = mutation.endpoint.startsWith('/') ? mutation.endpoint : `/${mutation.endpoint}`;
        const fullURL = `${baseURL}/api${apiPath}`;

        console.log(`[SW] Envoi de la mutation ${mutation.id}: ${mutation.method} ${fullURL}`);

        // Exécuter la requête
        const response = await fetch(fullURL, fetchOptions);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Mutation réussie
        console.log(`[SW] Mutation ${mutation.id} synchronisée avec succès`);
        await deleteMutationFromDB(db, mutation.id);
        successCount++;

        // Notifier le client du succès (si possible)
        await notifyClients({
          type: 'SYNC_SUCCESS',
          mutationId: mutation.id,
          mutationType: mutation.type,
        });

      } catch (error) {
        console.error(`[SW] Erreur lors de la synchronisation de la mutation ${mutation.id}:`, error);

        // Marquer comme échouée avec le message d'erreur
        await updateMutationStatusInDB(
          db,
          mutation.id,
          'failed',
          error.message || 'Erreur inconnue'
        );
        failureCount++;

        // Notifier le client de l'échec
        await notifyClients({
          type: 'SYNC_ERROR',
          mutationId: mutation.id,
          mutationType: mutation.type,
          error: error.message,
        });
      }
    }

    db.close();

    console.log(`[SW] Synchronisation terminée: ${successCount} réussie(s), ${failureCount} échouée(s)`);

    // Si toutes les mutations ont échoué, propager l'erreur pour que le sync soit réessayé
    if (failureCount > 0 && successCount === 0) {
      throw new Error(`Toutes les mutations ont échoué (${failureCount})`);
    }

  } catch (error) {
    console.error('[SW] Erreur de synchronisation:', error);
    throw error; // Propager l'erreur pour que le sync soit réessayé
  }
}

/**
 * Ouvre la base de données IndexedDB
 * @returns {Promise<IDBDatabase>}
 */
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('inventaire-offline', 1);

    request.onerror = () => {
      reject(new Error('Erreur lors de l\'ouverture de IndexedDB'));
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    // Pas besoin de onupgradeneeded car la DB est déjà créée par l'application
  });
}

/**
 * Récupère les mutations en attente depuis IndexedDB
 * @param {IDBDatabase} db
 * @returns {Promise<Array>}
 */
function getPendingMutationsFromDB(db) {
  return new Promise((resolve, reject) => {
    try {
      const transaction = db.transaction(['mutations'], 'readonly');
      const store = transaction.objectStore('mutations');
      const index = store.index('status');
      const request = index.getAll('pending');

      request.onsuccess = () => {
        const mutations = request.result || [];
        // Trier par timestamp (les plus anciennes d'abord)
        mutations.sort((a, b) => a.timestamp - b.timestamp);
        resolve(mutations);
      };

      request.onerror = () => {
        reject(new Error('Erreur lors de la récupération des mutations'));
      };
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Met à jour le statut d'une mutation dans IndexedDB
 * @param {IDBDatabase} db
 * @param {number} id
 * @param {string} status
 * @param {string} error
 * @returns {Promise<void>}
 */
function updateMutationStatusInDB(db, id, status, error = null) {
  return new Promise((resolve, reject) => {
    try {
      const transaction = db.transaction(['mutations'], 'readwrite');
      const store = transaction.objectStore('mutations');
      const getRequest = store.get(id);

      getRequest.onsuccess = () => {
        const mutation = getRequest.result;

        if (!mutation) {
          resolve();
          return;
        }

        mutation.status = status;
        mutation.lastAttempt = Date.now();
        mutation.attempts = (mutation.attempts || 0) + 1;

        if (error) {
          mutation.error = error;
        }

        const putRequest = store.put(mutation);

        putRequest.onsuccess = () => resolve();
        putRequest.onerror = () => reject(new Error('Erreur lors de la mise à jour de la mutation'));
      };

      getRequest.onerror = () => {
        reject(new Error('Erreur lors de la récupération de la mutation'));
      };
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Supprime une mutation de IndexedDB
 * @param {IDBDatabase} db
 * @param {number} id
 * @returns {Promise<void>}
 */
function deleteMutationFromDB(db, id) {
  return new Promise((resolve, reject) => {
    try {
      const transaction = db.transaction(['mutations'], 'readwrite');
      const store = transaction.objectStore('mutations');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Erreur lors de la suppression de la mutation'));
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Calcule le délai de retry avec exponential backoff
 * @param {number} attempts - Nombre de tentatives
 * @returns {number} Délai en millisecondes
 */
function calculateRetryDelay(attempts) {
  // Exponential backoff: 1s, 2s, 4s, 8s, 16s
  const baseDelay = 1000; // 1 seconde
  const maxDelay = 30000; // 30 secondes max
  const delay = Math.min(baseDelay * Math.pow(2, attempts), maxDelay);

  // Ajouter un peu de jitter pour éviter les pics de charge
  const jitter = Math.random() * 1000; // +/- 0-1s

  return delay + jitter;
}

/**
 * Notifie tous les clients connectés
 * @param {Object} message
 * @returns {Promise<void>}
 */
async function notifyClients(message) {
  try {
    const clients = await self.clients.matchAll({
      includeUncontrolled: true,
      type: 'window',
    });

    clients.forEach((client) => {
      client.postMessage(message);
    });
  } catch (error) {
    console.error('[SW] Erreur lors de la notification des clients:', error);
  }
}

/**
 * Événement de notification push
 * Parse les données et affiche une notification personnalisée
 */
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification reçue');

  // Parse les données de la notification
  let notificationData = {
    title: 'Inventaire Épicerie',
    body: 'Nouvelle notification',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    url: '/',
    tag: 'default',
    requireInteraction: false,
  };

  if (event.data) {
    try {
      const data = event.data.json();
      console.log('[SW] Push data:', data);

      notificationData = {
        title: data.title || notificationData.title,
        body: data.body || data.message || notificationData.body,
        icon: data.icon || notificationData.icon,
        badge: data.badge || notificationData.badge,
        url: data.url || data.click_action || notificationData.url,
        tag: data.tag || notificationData.tag,
        requireInteraction: data.requireInteraction || false,
        image: data.image,
        actions: data.actions || [],
        data: data.data || {},
      };
    } catch (error) {
      console.error('[SW] Erreur lors du parsing des données push:', error);
      // Fallback to text if JSON parsing fails
      notificationData.body = event.data.text();
    }
  }

  // Configuration des options de notification
  const options = {
    body: notificationData.body,
    icon: notificationData.icon,
    badge: notificationData.badge,
    image: notificationData.image,
    tag: notificationData.tag,
    requireInteraction: notificationData.requireInteraction,
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      url: notificationData.url,
      ...notificationData.data,
    },
    actions: notificationData.actions.length > 0 ? notificationData.actions : [
      {
        action: 'open',
        title: 'Ouvrir',
        icon: '/icon-192.png'
      },
      {
        action: 'close',
        title: 'Fermer',
        icon: '/icon-192.png'
      }
    ],
  };

  event.waitUntil(
    self.registration.showNotification(notificationData.title, options)
  );
});

/**
 * Événement de clic sur notification
 * Ouvre l'application et navigue vers l'URL appropriée
 */
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification cliquée:', event.action);

  event.notification.close();

  // Si l'utilisateur clique sur "close", ne fait rien
  if (event.action === 'close') {
    return;
  }

  // Récupère l'URL à ouvrir depuis les données de la notification
  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Vérifie si une fenêtre de l'app est déjà ouverte
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          const clientUrl = new URL(client.url);
          const targetUrl = new URL(urlToOpen, self.location.origin);

          // Si une fenêtre est déjà ouverte, la focus et navigue
          if (clientUrl.origin === targetUrl.origin) {
            return client.focus().then(() => {
              // Navigue vers l'URL cible si différente
              if (client.url !== targetUrl.href) {
                return client.navigate(targetUrl.href);
              }
            });
          }
        }

        // Si aucune fenêtre n'est ouverte, en ouvre une nouvelle
        return clients.openWindow(urlToOpen);
      })
  );
});

console.log('[SW] Service Worker chargé', CACHE_VERSION);
