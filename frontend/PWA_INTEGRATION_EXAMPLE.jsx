/**
 * EXEMPLE D'INTÉGRATION PWA
 *
 * Ce fichier montre comment intégrer les fonctionnalités PWA
 * dans vos composants React.
 *
 * Vous pouvez copier ces exemples dans vos pages existantes.
 */

import React from 'react';
import { usePWA } from './src/hooks/usePWA';
import { useOfflineContext } from './src/contexts/OfflineContext';
import { InstallPWAButton, InstalledPWABadge } from './src/components/pwa/InstallPWAButton';
import { Smartphone, Download, Wifi, WifiOff, RefreshCw, Share2, Info } from 'lucide-react';

/**
 * 1. Banner d'installation automatique
 * À ajouter dans votre layout principal (App.jsx ou Layout.jsx)
 */
export function PWAInstallBanner() {
  return (
    <InstallPWAButton
      variant="banner"
      onInstall={() => {
        console.log('Application installée avec succès!');
        // Vous pouvez afficher un toast ici
      }}
      onDismiss={() => {
        console.log('Banner fermé par l\'utilisateur');
      }}
    />
  );
}

/**
 * 2. Indicateur de statut offline
 * À ajouter dans votre header ou footer
 */
export function OfflineStatusIndicator() {
  const { isOnline, pendingMutations, syncPendingMutations, isSyncing } = useOfflineContext();

  if (isOnline && pendingMutations.length === 0) {
    return null; // Tout va bien, rien à afficher
  }

  return (
    <div className={`fixed top-0 left-0 right-0 z-50 ${
      isOnline ? 'bg-yellow-500' : 'bg-red-500'
    } text-white px-4 py-2 text-sm`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {isOnline ? (
            <Wifi className="h-4 w-4" />
          ) : (
            <WifiOff className="h-4 w-4" />
          )}
          <span className="font-medium">
            {isOnline
              ? `${pendingMutations.length} action(s) en attente de synchronisation`
              : 'Mode hors ligne'}
          </span>
        </div>

        {isOnline && pendingMutations.length > 0 && (
          <button
            onClick={syncPendingMutations}
            disabled={isSyncing}
            className="flex items-center gap-2 px-3 py-1 bg-white text-yellow-700 rounded-lg hover:bg-yellow-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Sync...' : 'Synchroniser'}
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * 3. Page de paramètres PWA
 * Une page complète pour gérer le PWA
 */
export function PWASettingsPage() {
  const {
    isInstallable,
    isInstalled,
    isStandalone,
    updateAvailable,
    isPWASupported,
    promptInstall,
    activateUpdate,
    unregister,
    clearCaches,
    getCacheInfo,
    getDeviceCapabilities,
    share,
    canShare,
  } = usePWA();

  const { isOnline, pendingMutations, storageStats } = useOfflineContext();

  const [cacheInfo, setCacheInfo] = React.useState([]);
  const capabilities = getDeviceCapabilities();

  React.useEffect(() => {
    getCacheInfo().then(setCacheInfo);
  }, [getCacheInfo]);

  const handleClearCache = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir vider tous les caches ?')) {
      await clearCaches();
      setCacheInfo([]);
      window.location.reload();
    }
  };

  const handleUnregisterSW = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir désinstaller le Service Worker ?')) {
      await unregister();
      window.location.reload();
    }
  };

  const handleShare = async () => {
    const result = await share({
      title: 'Inventaire Épicerie',
      text: 'Découvrez cette application de gestion!',
      url: window.location.origin,
    });

    if (result.success) {
      console.log('Partagé avec succès');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          Paramètres PWA
        </h1>
        <p className="text-slate-600">
          Gérez l'installation et les fonctionnalités hors ligne
        </p>
      </div>

      {/* État de l'installation */}
      <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Smartphone className="h-5 w-5" />
          État de l'application
        </h2>

        <div className="space-y-3">
          <StatusItem
            label="Support PWA"
            value={isPWASupported}
          />
          <StatusItem
            label="Installable"
            value={isInstallable}
          />
          <StatusItem
            label="Installée"
            value={isInstalled}
          />
          <StatusItem
            label="Mode Standalone"
            value={isStandalone}
          />
          <StatusItem
            label="Mise à jour disponible"
            value={updateAvailable}
          />
          <StatusItem
            label="En ligne"
            value={isOnline}
          />
        </div>

        <div className="mt-6 flex gap-3 flex-wrap">
          {isInstallable && (
            <button
              onClick={promptInstall}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Installer l'application
            </button>
          )}

          {isInstalled && <InstalledPWABadge />}

          {updateAvailable && (
            <button
              onClick={activateUpdate}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Mettre à jour
            </button>
          )}

          {canShare() && (
            <button
              onClick={handleShare}
              className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors flex items-center gap-2"
            >
              <Share2 className="h-4 w-4" />
              Partager
            </button>
          )}
        </div>
      </section>

      {/* Capacités de l'appareil */}
      <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Info className="h-5 w-5" />
          Capacités de l'appareil
        </h2>

        <div className="grid grid-cols-2 gap-3">
          <CapabilityItem label="Service Worker" value={capabilities.serviceWorkerSupported} />
          <CapabilityItem label="Push Notifications" value={capabilities.pushSupported} />
          <CapabilityItem label="Notifications" value={capabilities.notificationSupported} />
          <CapabilityItem label="Partage" value={capabilities.shareSupported} />
          <CapabilityItem label="Mobile" value={capabilities.isMobile} />
          <CapabilityItem label="iOS" value={capabilities.isIOS} />
          <CapabilityItem label="Android" value={capabilities.isAndroid} />
          <CapabilityItem label="Connexion" value={capabilities.connectionType} text />
        </div>
      </section>

      {/* Stockage et cache */}
      <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          Stockage et cache
        </h2>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-sm text-slate-600">Mutations en attente</div>
              <div className="text-2xl font-bold text-slate-900">
                {pendingMutations.length}
              </div>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="text-sm text-slate-600">Entrées en cache</div>
              <div className="text-2xl font-bold text-slate-900">
                {storageStats.cacheEntries}
              </div>
            </div>
          </div>

          <div>
            <h3 className="font-medium text-slate-900 mb-2">Caches actifs</h3>
            {cacheInfo.length > 0 ? (
              <div className="space-y-2">
                {cacheInfo.map((cache, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center p-3 bg-slate-50 rounded-lg"
                  >
                    <span className="text-sm font-mono text-slate-700">
                      {cache.name}
                    </span>
                    <span className="text-sm text-slate-600">
                      {cache.size} entrée(s)
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Aucun cache actif</p>
            )}
          </div>
        </div>
      </section>

      {/* Actions avancées */}
      <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          Actions avancées
        </h2>

        <div className="space-y-3">
          <button
            onClick={handleClearCache}
            className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
          >
            Vider tous les caches
          </button>

          <button
            onClick={handleUnregisterSW}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Désinstaller le Service Worker
          </button>

          <p className="text-sm text-slate-500 mt-2">
            ⚠️ Ces actions nécessitent un rechargement de la page
          </p>
        </div>
      </section>
    </div>
  );
}

/**
 * Composants utilitaires
 */
function StatusItem({ label, value }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
      <span className="text-sm text-slate-600">{label}</span>
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
        value
          ? 'bg-green-100 text-green-800'
          : 'bg-slate-100 text-slate-600'
      }`}>
        {value ? 'Oui' : 'Non'}
      </span>
    </div>
  );
}

function CapabilityItem({ label, value, text = false }) {
  return (
    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
      <span className="text-sm text-slate-600">{label}</span>
      {text ? (
        <span className="text-sm font-medium text-slate-900">{value}</span>
      ) : (
        <div className={`w-3 h-3 rounded-full ${
          value ? 'bg-green-500' : 'bg-slate-300'
        }`} />
      )}
    </div>
  );
}

/**
 * 4. Bouton de partage (exemple simple)
 */
export function ShareButton({ title, text, url }) {
  const { share, canShare } = usePWA();

  if (!canShare()) {
    return null; // Ne rien afficher si le partage n'est pas supporté
  }

  const handleShare = async () => {
    const result = await share({ title, text, url });

    if (!result.success && result.error !== 'cancelled') {
      console.error('Erreur de partage:', result.error);
    }
  };

  return (
    <button
      onClick={handleShare}
      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
    >
      <Share2 className="h-4 w-4" />
      Partager
    </button>
  );
}

/**
 * 5. Hook personnalisé pour utilisation simplifiée
 */
export function usePWAStatus() {
  const pwa = usePWA();
  const offline = useOfflineContext();

  return {
    // États simples
    canInstall: pwa.isInstallable && !pwa.isInstalled,
    isInstalledApp: pwa.isInstalled || pwa.isStandalone,
    needsUpdate: pwa.updateAvailable,
    isOffline: !offline.isOnline,
    hasPendingSync: offline.pendingMutations.length > 0,

    // Actions
    install: pwa.promptInstall,
    update: pwa.activateUpdate,
    sync: offline.syncPendingMutations,
    share: pwa.share,

    // Infos
    pwa,
    offline,
  };
}

// Exemple d'utilisation du hook simplifié
export function SimplePWAComponent() {
  const {
    canInstall,
    isInstalledApp,
    needsUpdate,
    isOffline,
    hasPendingSync,
    install,
    update,
    sync,
  } = usePWAStatus();

  return (
    <div className="space-y-4 p-4">
      {canInstall && (
        <button
          onClick={install}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          Installer l'application
        </button>
      )}

      {needsUpdate && (
        <button
          onClick={update}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg"
        >
          Mettre à jour maintenant
        </button>
      )}

      {hasPendingSync && (
        <button
          onClick={sync}
          className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg"
        >
          Synchroniser {/* pendingMutations.length */} actions
        </button>
      )}

      {isOffline && (
        <div className="p-4 bg-red-100 text-red-800 rounded-lg">
          Vous êtes hors ligne
        </div>
      )}

      {isInstalledApp && (
        <div className="p-4 bg-green-100 text-green-800 rounded-lg">
          Application installée
        </div>
      )}
    </div>
  );
}

export default {
  PWAInstallBanner,
  OfflineStatusIndicator,
  PWASettingsPage,
  ShareButton,
  SimplePWAComponent,
  usePWAStatus,
};
