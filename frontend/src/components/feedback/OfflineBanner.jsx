import { motion, AnimatePresence } from 'framer-motion';
import { WifiOff, Wifi, CloudOff, RefreshCw, AlertCircle } from 'lucide-react';
import { useOfflineContext } from '../../contexts/OfflineContext.jsx';

/**
 * Bannière fixe en haut de l'écran pour indiquer le statut offline/online
 *
 * Affiche :
 * - Message "Mode hors-ligne" quand déconnecté
 * - Message "Connexion rétablie" quand reconnecté
 * - Nombre de mutations en attente
 * - État de synchronisation
 */
export default function OfflineBanner() {
  const {
    isOnline,
    wasOffline,
    offlineSince,
    pendingMutations,
    isSyncing,
    syncError,
  } = useOfflineContext();

  // Calculer la durée offline
  const getOfflineDuration = () => {
    if (!offlineSince) return '';

    const now = new Date();
    const duration = Math.floor((now - offlineSince) / 1000); // en secondes

    if (duration < 60) {
      return `${duration}s`;
    } else if (duration < 3600) {
      return `${Math.floor(duration / 60)}min`;
    } else {
      return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}min`;
    }
  };

  // Afficher la bannière si offline OU si vient de se reconnecter
  const showBanner = !isOnline || wasOffline;

  return (
    <AnimatePresence mode="wait">
      {showBanner && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          transition={{
            type: 'spring',
            stiffness: 400,
            damping: 30,
          }}
          className="fixed top-0 left-0 right-0 z-50"
        >
          {/* Bannière Offline */}
          {!isOnline && (
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-xl">
              <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    {/* Icône animée */}
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        rotate: [0, 10, -10, 0],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }}
                    >
                      <WifiOff className="h-5 w-5 sm:h-6 sm:w-6" />
                    </motion.div>

                    {/* Message principal */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
                      <span className="font-semibold text-sm sm:text-base">
                        Mode hors-ligne
                      </span>
                      <span className="text-xs sm:text-sm opacity-90">
                        {offlineSince && `Depuis ${getOfflineDuration()}`}
                      </span>
                    </div>
                  </div>

                  {/* Mutations en attente */}
                  {pendingMutations.length > 0 && (
                    <div className="flex items-center gap-2 text-xs sm:text-sm">
                      <CloudOff className="h-4 w-4" />
                      <span className="font-medium">
                        {pendingMutations.length} modification{pendingMutations.length > 1 ? 's' : ''} en attente
                      </span>
                    </div>
                  )}
                </div>

                {/* Message secondaire */}
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  transition={{ delay: 0.3 }}
                  className="mt-2 text-xs sm:text-sm opacity-90"
                >
                  Les modifications seront synchronisées automatiquement au retour de la connexion
                </motion.p>
              </div>
            </div>
          )}

          {/* Bannière Reconnexion */}
          {isOnline && wasOffline && (
            <div
              className={`shadow-xl ${
                syncError
                  ? 'bg-gradient-to-r from-red-500 to-rose-500'
                  : 'bg-gradient-to-r from-emerald-500 to-green-500'
              } text-white`}
            >
              <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    {/* Icône */}
                    {syncError ? (
                      <AlertCircle className="h-5 w-5 sm:h-6 sm:w-6" />
                    ) : isSyncing ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          ease: 'linear',
                        }}
                      >
                        <RefreshCw className="h-5 w-5 sm:h-6 sm:w-6" />
                      </motion.div>
                    ) : (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{
                          type: 'spring',
                          stiffness: 500,
                          damping: 15,
                        }}
                      >
                        <Wifi className="h-5 w-5 sm:h-6 sm:w-6" />
                      </motion.div>
                    )}

                    {/* Message */}
                    <div className="flex flex-col">
                      <span className="font-semibold text-sm sm:text-base">
                        {syncError
                          ? 'Erreur de synchronisation'
                          : isSyncing
                          ? 'Synchronisation en cours...'
                          : 'Connexion rétablie'}
                      </span>

                      {syncError && (
                        <span className="text-xs opacity-90 mt-1">
                          {syncError}
                        </span>
                      )}

                      {!syncError && !isSyncing && pendingMutations.length === 0 && (
                        <span className="text-xs opacity-90 mt-1">
                          Toutes les modifications ont été synchronisées
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Indicateur de progression */}
                  {isSyncing && pendingMutations.length > 0 && (
                    <div className="text-xs sm:text-sm font-medium">
                      {pendingMutations.length} en attente
                    </div>
                  )}
                </div>
              </div>

              {/* Barre de progression */}
              {isSyncing && (
                <motion.div
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{
                    duration: 1.5,
                    ease: 'easeInOut',
                  }}
                  className="h-1 bg-white/30 origin-left"
                />
              )}
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Version compacte pour mobile
 */
export function OfflineBannerCompact() {
  const { isOnline, wasOffline, pendingMutations, isSyncing } = useOfflineContext();

  const showBanner = !isOnline || wasOffline;

  return (
    <AnimatePresence mode="wait">
      {showBanner && (
        <motion.div
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -50, opacity: 0 }}
          transition={{
            type: 'spring',
            stiffness: 400,
            damping: 30,
          }}
          className="fixed top-0 left-0 right-0 z-50"
        >
          {!isOnline && (
            <div className="bg-amber-500 text-white px-4 py-2 text-center text-sm font-medium shadow-lg">
              <div className="flex items-center justify-center gap-2">
                <WifiOff className="h-4 w-4" />
                <span>Hors-ligne</span>
                {pendingMutations.length > 0 && (
                  <span className="ml-2 opacity-90">
                    ({pendingMutations.length})
                  </span>
                )}
              </div>
            </div>
          )}

          {isOnline && wasOffline && (
            <div
              className={`px-4 py-2 text-center text-sm font-medium shadow-lg ${
                isSyncing
                  ? 'bg-blue-500 text-white'
                  : 'bg-emerald-500 text-white'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                {isSyncing ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: 'linear',
                      }}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </motion.div>
                    <span>Synchronisation...</span>
                  </>
                ) : (
                  <>
                    <Wifi className="h-4 w-4" />
                    <span>En ligne</span>
                  </>
                )}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
