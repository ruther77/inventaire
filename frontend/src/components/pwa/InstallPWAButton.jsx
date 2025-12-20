import React from 'react';
import { Download, Smartphone, X } from 'lucide-react';
import { usePWA } from '../../hooks/usePWA';
import { useLocalStorage } from '../../hooks/useLocalStorage';

/**
 * Bouton pour installer l'application en mode PWA
 * Affiche automatiquement quand l'app est installable
 * Peut être masqué définitivement par l'utilisateur
 *
 * @param {Object} props
 * @param {string} props.variant - Style du bouton: 'banner' | 'button' | 'floating'
 * @param {Function} props.onInstall - Callback après installation
 * @param {Function} props.onDismiss - Callback après fermeture
 * @returns {JSX.Element|null}
 */
export function InstallPWAButton({
  variant = 'banner',
  onInstall,
  onDismiss,
}) {
  const {
    isInstallable,
    isInstalled,
    isStandalone,
    promptInstall,
    getDeviceCapabilities,
  } = usePWA();

  // Stocke si l'utilisateur a masqué définitivement le prompt
  const [isDismissed, setIsDismissed] = useLocalStorage('pwa-install-dismissed', false);

  // Ne rien afficher si:
  // - L'app n'est pas installable
  // - L'app est déjà installée
  // - L'utilisateur a masqué le prompt
  if (!isInstallable || isInstalled || isStandalone || isDismissed) {
    return null;
  }

  const handleInstall = async () => {
    const result = await promptInstall();

    if (result.outcome === 'accepted') {
      console.log('[InstallPWAButton] User accepted installation');
      onInstall?.();
    } else if (result.outcome === 'dismissed') {
      console.log('[InstallPWAButton] User dismissed installation');
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  const capabilities = getDeviceCapabilities();
  const isMobile = capabilities.isMobile;

  // Variant: Banner (en haut ou en bas de l'écran)
  if (variant === 'banner') {
    return (
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg border-t border-blue-500">
        <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="flex-shrink-0">
                <Smartphone className="h-8 w-8" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">
                  Installer l'application
                </p>
                <p className="text-xs text-blue-100 mt-0.5">
                  {isMobile
                    ? 'Ajoutez Inventaire à votre écran d\'accueil pour un accès rapide'
                    : 'Installez l\'application pour une meilleure expérience'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={handleInstall}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white text-blue-700 font-medium text-sm rounded-lg hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600"
              >
                <Download className="h-4 w-4" />
                Installer
              </button>

              <button
                onClick={handleDismiss}
                className="p-2 hover:bg-blue-600 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600"
                aria-label="Fermer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Variant: Button (bouton simple)
  if (variant === 'button') {
    return (
      <button
        onClick={handleInstall}
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium text-sm rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        <Download className="h-4 w-4" />
        Installer l'application
      </button>
    );
  }

  // Variant: Floating (bouton flottant)
  if (variant === 'floating') {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={handleDismiss}
          className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors shadow-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          aria-label="Fermer"
        >
          <X className="h-3 w-3" />
        </button>

        <button
          onClick={handleInstall}
          className="flex items-center gap-3 px-5 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <Smartphone className="h-5 w-5" />
          <span className="text-sm">Installer</span>
        </button>
      </div>
    );
  }

  return null;
}

/**
 * Badge pour indiquer que l'app est installée
 */
export function InstalledPWABadge() {
  const { isInstalled, isStandalone } = usePWA();

  if (!isInstalled && !isStandalone) {
    return null;
  }

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-green-100 text-green-800 text-xs font-medium rounded-full">
      <Smartphone className="h-3.5 w-3.5" />
      Application installée
    </div>
  );
}

/**
 * Indicateur de mode standalone
 * Affiche un message discret quand l'app est en mode PWA
 */
export function StandaloneIndicator() {
  const { isStandalone } = usePWA();

  if (!isStandalone) {
    return null;
  }

  return (
    <div className="fixed top-2 right-2 z-50 pointer-events-none">
      <div className="px-2 py-1 bg-green-500 text-white text-xs font-medium rounded shadow-sm">
        PWA Mode
      </div>
    </div>
  );
}

export default InstallPWAButton;
