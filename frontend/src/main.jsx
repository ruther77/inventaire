import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App.jsx';
import './styles.css';
import { TenantProvider } from './context/TenantContext.jsx';
import { AuthProvider } from './context/AuthContext.jsx';
import { ToastProvider } from './components/ui/Toast.jsx';
import { OfflineProvider } from './contexts/OfflineContext.jsx';

// Configuration du QueryClient avec gestion offline améliorée
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 30 * 60 * 1000, // 30 minutes (anciennement cacheTime)
      retry: (failureCount, error) => {
        // Ne pas réessayer si offline
        if (!navigator.onLine) return false;
        // Réessayer max 2 fois si erreur réseau
        if (error?.code === 'ERR_NETWORK') return failureCount < 2;
        // Ne pas réessayer pour les erreurs 4xx
        if (error?.response?.status >= 400 && error?.response?.status < 500) return false;
        return failureCount < 1;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true, // Rafraîchir quand la connexion revient
      networkMode: 'offlineFirst', // Utiliser le cache même offline
    },
    mutations: {
      networkMode: 'offlineFirst', // Permettre les mutations offline (via queue)
      retry: (failureCount, error) => {
        // Ne pas réessayer si offline (géré par la queue)
        if (!navigator.onLine) return false;
        // Réessayer max 1 fois si erreur réseau
        if (error?.code === 'ERR_NETWORK') return failureCount < 1;
        return false;
      },
    },
  },
});

/**
 * Enregistre le Service Worker pour le mode PWA
 */
async function registerServiceWorker() {
  // Vérifie si le Service Worker est supporté
  if (!('serviceWorker' in navigator)) {
    console.warn('[PWA] Service Workers are not supported in this browser');
    return null;
  }

  // N'enregistre pas le SW en développement (optionnel)
  // Décommenter la ligne ci-dessous pour désactiver le SW en dev
  // if (import.meta.env.DEV) {
  //   console.log('[PWA] Service Worker disabled in development mode');
  //   return null;
  // }

  try {
    console.log('[PWA] Registering Service Worker...');

    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
      updateViaCache: 'none', // Force la vérification des mises à jour
    });

    console.log('[PWA] Service Worker registered successfully:', registration);

    // Vérifie les mises à jour au chargement
    registration.update();

    // Écoute les changements d'état du SW
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      console.log('[PWA] New Service Worker found, installing...');

      newWorker?.addEventListener('statechange', () => {
        console.log('[PWA] Service Worker state:', newWorker.state);

        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // Un nouveau SW est disponible
          console.log('[PWA] New Service Worker available! Update recommended.');

          // Vous pouvez afficher une notification à l'utilisateur ici
          // Par exemple, via un toast ou un banner
          if (window.confirm('Une nouvelle version est disponible. Voulez-vous mettre à jour ?')) {
            newWorker.postMessage({ type: 'SKIP_WAITING' });
            window.location.reload();
          }
        }
      });
    });

    // Écoute les messages du Service Worker
    navigator.serviceWorker.addEventListener('message', (event) => {
      console.log('[PWA] Message from Service Worker:', event.data);

      if (event.data && event.data.type === 'RELOAD') {
        window.location.reload();
      }
    });

    // Recharge la page si le SW contrôleur change (après SKIP_WAITING)
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      console.log('[PWA] Controller changed, reloading...');
      window.location.reload();
    });

    return registration;
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
    return null;
  }
}

/**
 * Initialise l'application et enregistre le Service Worker
 */
async function initApp() {
  // Enregistre le Service Worker
  const swRegistration = await registerServiceWorker();

  // Affiche des infos de debug en développement
  if (import.meta.env.DEV) {
    console.log('[App] Running in development mode');
    console.log('[App] Service Worker registration:', swRegistration);
  }

  // Log les informations de connexion
  console.log('[App] Online status:', navigator.onLine);
  console.log('[App] Connection type:', navigator.connection?.effectiveType || 'unknown');

  // Écoute les changements de statut réseau
  window.addEventListener('online', () => {
    console.log('[App] Back online');
  });

  window.addEventListener('offline', () => {
    console.log('[App] Gone offline');
  });
}

// Initialise l'application
initApp();

/**
 * Point d'entrée React : on enveloppe toute l'application avec le client
 * TanStack Query (cache des requêtes HTTP) et le TenantProvider qui expose
 * l'entreprise active (épicerie vs restaurant).
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TenantProvider>
          <OfflineProvider>
            <ToastProvider position="bottom-right">
              <BrowserRouter>
                <App />
              </BrowserRouter>
            </ToastProvider>
          </OfflineProvider>
        </TenantProvider>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
