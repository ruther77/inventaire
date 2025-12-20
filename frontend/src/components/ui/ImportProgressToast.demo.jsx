/**
 * ImportProgressToast.demo.jsx - Page de démonstration interactive
 *
 * Pour visualiser et tester le composant ImportProgressToast
 * avec différents états et configurations.
 *
 * Usage:
 * 1. Créer une route: <Route path="/demo/import-progress" element={<ImportProgressToastDemo />} />
 * 2. Naviguer vers /demo/import-progress
 * 3. Tester les différents scénarios
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import ImportProgressToast from './ImportProgressToast';
import Card from './Card';
import Button from './Button';

// Scénarios de démonstration
const DEMO_SCENARIOS = {
  PROCESSING_START: {
    name: 'Début de traitement',
    jobStatus: {
      status: 'processing',
      progress: 0,
    },
  },
  PROCESSING_EXTRACTION: {
    name: 'Extraction (25%)',
    jobStatus: {
      status: 'processing',
      progress: 25,
    },
  },
  PROCESSING_ANALYSIS: {
    name: 'Analyse (50%)',
    jobStatus: {
      status: 'processing',
      progress: 50,
    },
  },
  PROCESSING_IMPORT: {
    name: 'Import (75%)',
    jobStatus: {
      status: 'processing',
      progress: 75,
    },
  },
  PROCESSING_FINAL: {
    name: 'Finalisation (95%)',
    jobStatus: {
      status: 'processing',
      progress: 95,
    },
  },
  SUCCESS: {
    name: 'Succès',
    jobStatus: {
      status: 'completed',
      progress: 100,
      summary: {
        movements_created: 42,
        quantity_total: 156,
        products_created: 3,
      },
    },
  },
  SUCCESS_NO_NEW_PRODUCTS: {
    name: 'Succès (sans nouveaux produits)',
    jobStatus: {
      status: 'completed',
      progress: 100,
      summary: {
        movements_created: 28,
        quantity_total: 94,
        products_created: 0,
      },
    },
  },
  FAILED: {
    name: 'Échec',
    jobStatus: {
      status: 'failed',
      error: 'Format de fichier invalide. Veuillez utiliser un fichier PDF, DOCX ou TXT.',
    },
  },
  FAILED_TIMEOUT: {
    name: 'Échec (timeout)',
    jobStatus: {
      status: 'failed',
      error: 'Le traitement a pris trop de temps. Veuillez réessayer avec un fichier plus petit.',
    },
  },
};

export default function ImportProgressToastDemo() {
  const [activeScenario, setActiveScenario] = useState('PROCESSING_START');
  const [fileName, setFileName] = useState('facture-metro-2025-01.pdf');
  const [showToast, setShowToast] = useState(true);
  const [autoPlay, setAutoPlay] = useState(false);

  // Auto-play: simule une progression automatique
  useEffect(() => {
    if (!autoPlay) return;

    const scenarios = [
      'PROCESSING_START',
      'PROCESSING_EXTRACTION',
      'PROCESSING_ANALYSIS',
      'PROCESSING_IMPORT',
      'PROCESSING_FINAL',
      'SUCCESS',
    ];

    let currentIndex = 0;
    const interval = setInterval(() => {
      currentIndex++;
      if (currentIndex >= scenarios.length) {
        setAutoPlay(false);
        return;
      }
      setActiveScenario(scenarios[currentIndex]);
    }, 2000);

    return () => clearInterval(interval);
  }, [autoPlay]);

  const currentScenario = DEMO_SCENARIOS[activeScenario];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-3">
            Import Progress Toast - Demo
          </h1>
          <p className="text-lg text-slate-600">
            Testez et visualisez les différents états du composant de notification
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Panneau de contrôle */}
          <div>
            <Card className="mb-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-4">
                Contrôles
              </h2>

              {/* Nom du fichier */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Nom du fichier
                </label>
                <input
                  type="text"
                  value={fileName}
                  onChange={(e) => setFileName(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="facture-metro-2025-01.pdf"
                />
              </div>

              {/* Affichage du toast */}
              <div className="mb-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showToast}
                    onChange={(e) => setShowToast(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-slate-700">
                    Afficher le toast
                  </span>
                </label>
              </div>

              {/* Auto-play */}
              <div className="mb-6">
                <Button
                  variant={autoPlay ? 'secondary' : 'brand'}
                  onClick={() => {
                    setAutoPlay(!autoPlay);
                    if (!autoPlay) {
                      setActiveScenario('PROCESSING_START');
                      setShowToast(true);
                    }
                  }}
                  className="w-full"
                >
                  {autoPlay ? 'Arrêter l\'animation' : 'Démo automatique'}
                </Button>
              </div>

              {/* Scénarios */}
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-3">
                  Scénarios
                </h3>
                <div className="grid gap-2">
                  {Object.entries(DEMO_SCENARIOS).map(([key, scenario]) => (
                    <button
                      key={key}
                      onClick={() => {
                        setActiveScenario(key);
                        setShowToast(true);
                        setAutoPlay(false);
                      }}
                      className={`
                        px-4 py-2 rounded-lg text-left text-sm font-medium transition-all
                        ${
                          activeScenario === key
                            ? 'bg-blue-500 text-white shadow-md'
                            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                        }
                      `}
                    >
                      {scenario.name}
                    </button>
                  ))}
                </div>
              </div>
            </Card>

            {/* Info sur le scénario actuel */}
            <Card>
              <h2 className="text-xl font-semibold text-slate-900 mb-4">
                Détails du scénario
              </h2>
              <div className="bg-slate-900 text-slate-100 rounded-lg p-4 font-mono text-sm overflow-auto">
                <pre>{JSON.stringify(currentScenario.jobStatus, null, 2)}</pre>
              </div>
            </Card>
          </div>

          {/* Aperçu */}
          <div>
            <Card>
              <h2 className="text-xl font-semibold text-slate-900 mb-4">
                Aperçu
              </h2>
              <p className="text-sm text-slate-600 mb-6">
                Le toast apparaît normalement en bas à droite de l'écran.
                Ici, il est affiché dans une zone délimitée pour la démo.
              </p>

              {/* Zone de prévisualisation */}
              <div className="relative bg-gradient-to-br from-slate-200 to-slate-300 rounded-2xl p-8 min-h-[500px] flex items-end justify-end">
                <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
                  Zone de prévisualisation
                </div>

                {showToast && (
                  <motion.div
                    key={activeScenario}
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.95 }}
                    transition={{ duration: 0.3 }}
                  >
                    <ImportProgressToast
                      jobStatus={currentScenario.jobStatus}
                      fileName={fileName}
                      onCancel={() => console.log('Cancel clicked')}
                      onDismiss={() => setShowToast(false)}
                      canCancel={currentScenario.jobStatus.status === 'processing'}
                    />
                  </motion.div>
                )}
              </div>
            </Card>

            {/* Instructions */}
            <Card className="mt-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-3">
                Instructions
              </h3>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 font-bold">1.</span>
                  <span>
                    Cliquez sur les différents scénarios pour voir les états du toast
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 font-bold">2.</span>
                  <span>
                    Utilisez la "Démo automatique" pour voir une progression complète
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 font-bold">3.</span>
                  <span>
                    Modifiez le nom du fichier pour tester l'affichage
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 font-bold">4.</span>
                  <span>
                    Cliquez sur le bouton de fermeture pour masquer le toast
                  </span>
                </li>
              </ul>
            </Card>

            {/* Caractéristiques */}
            <Card className="mt-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-3">
                Caractéristiques
              </h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                  <span className="text-slate-600">Animations fluides</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-slate-600">Barre de progression</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span className="text-slate-600">Étapes visuelles</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                  <span className="text-slate-600">États success/error</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-rose-500 rounded-full"></div>
                  <span className="text-slate-600">Annulation possible</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                  <span className="text-slate-600">Responsive</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
