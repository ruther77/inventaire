/**
 * ToastImportProgress - Extension du système Toast pour afficher la progression d'import
 *
 * Intégration avec le ToastProvider existant.
 * Utilise le même système de toast mais avec un contenu personnalisé pour les imports.
 *
 * Usage avec useToast():
 * const { toast } = useToast();
 * const toastId = toast.show({
 *   type: 'loading',
 *   title: 'Import en cours...',
 *   duration: 0,
 *   dismissible: false,
 *   custom: <ToastImportProgress jobStatus={jobStatus} fileName={fileName} />
 * });
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Search, Database, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

const ImportSteps = {
  EXTRACTION: { id: 'extraction', label: 'Extraction', icon: FileText },
  ANALYSIS: { id: 'analysis', label: 'Analyse', icon: Search },
  IMPORT: { id: 'import', label: 'Import', icon: Database },
};

/**
 * Détermine l'étape actuelle basée sur le statut et la progression
 */
function getCurrentStep(status, progress = 0) {
  if (!status || status === 'pending') return null;
  if (status === 'completed' || status === 'failed') return 'completed';

  if (progress < 33) return ImportSteps.EXTRACTION.id;
  if (progress < 66) return ImportSteps.ANALYSIS.id;
  return ImportSteps.IMPORT.id;
}

/**
 * Indicateur d'étape compact
 */
function MiniStepIndicator({ step, isActive, isPast, isFailed }) {
  const StepIcon = step.icon;

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300',
          isActive && !isFailed && 'bg-blue-500 text-white',
          isPast && !isFailed && 'bg-emerald-500 text-white',
          !isActive && !isPast && 'bg-slate-200 text-slate-400',
          isFailed && isActive && 'bg-rose-500 text-white'
        )}
      >
        <StepIcon className="w-4 h-4" />
      </div>
      <span
        className={clsx(
          'text-[10px] font-medium',
          isActive && !isFailed && 'text-blue-600',
          isPast && !isFailed && 'text-emerald-600',
          !isActive && !isPast && 'text-slate-400',
          isFailed && isActive && 'text-rose-600'
        )}
      >
        {step.label}
      </span>
    </div>
  );
}

/**
 * Composant principal ToastImportProgress
 */
export default function ToastImportProgress({ jobStatus, fileName }) {
  const [progress, setProgress] = useState(0);

  const status = jobStatus?.status || 'pending';
  const currentStep = getCurrentStep(status, progress);

  // Simulation de progression
  useEffect(() => {
    if (status === 'processing') {
      if (jobStatus?.progress !== undefined) {
        setProgress(jobStatus.progress);
      } else {
        const interval = setInterval(() => {
          setProgress((prev) => Math.min(95, prev + Math.random() * 5));
        }, 800);
        return () => clearInterval(interval);
      }
    } else if (status === 'completed') {
      setProgress(100);
    }
  }, [status, jobStatus?.progress]);

  const isComplete = status === 'completed';
  const isFailed = status === 'failed';

  return (
    <div className="w-full">
      {/* Header avec fichier */}
      {fileName && (
        <p className="text-xs text-slate-600 mb-2 truncate">
          {fileName}
        </p>
      )}

      {/* Steps (uniquement en processing) */}
      {status === 'processing' && (
        <div className="flex items-center justify-around mb-3">
          {Object.values(ImportSteps).map((step, index) => {
            const stepIndex = ['extraction', 'analysis', 'import'].indexOf(step.id);
            const currentIndex = ['extraction', 'analysis', 'import'].indexOf(currentStep);
            const isActive = currentStep === step.id;
            const isPast = currentIndex > stepIndex;

            return (
              <MiniStepIndicator
                key={step.id}
                step={step}
                isActive={isActive}
                isPast={isPast}
                isFailed={isFailed}
              />
            );
          })}
        </div>
      )}

      {/* Progress bar */}
      <div className="h-1 bg-slate-200 rounded-full overflow-hidden mb-2">
        <motion.div
          className={clsx(
            'h-full rounded-full',
            isFailed ? 'bg-rose-500' : isComplete ? 'bg-emerald-500' : 'bg-blue-500'
          )}
          initial={{ width: '0%' }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>

      {/* Message */}
      <AnimatePresence mode="wait">
        {status === 'completed' && jobStatus?.summary && (
          <motion.div
            key="summary"
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-2"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-emerald-700">
              {jobStatus.summary.movements_created || 0} mouvements,{' '}
              {jobStatus.summary.quantity_total || 0} unités
              {jobStatus.summary.products_created
                ? `, ${jobStatus.summary.products_created} nouveaux produits`
                : ''}
            </p>
          </motion.div>
        )}

        {status === 'failed' && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-2"
          >
            <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-rose-700">
              {jobStatus?.error || 'Une erreur est survenue'}
            </p>
          </motion.div>
        )}

        {status === 'processing' && (
          <motion.div
            key="progress"
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between"
          >
            <p className="text-xs text-slate-600">
              {currentStep === ImportSteps.EXTRACTION.id && 'Extraction du fichier...'}
              {currentStep === ImportSteps.ANALYSIS.id && 'Matching des produits...'}
              {currentStep === ImportSteps.IMPORT.id && 'Création des mouvements...'}
            </p>
            <span className="text-xs font-medium text-blue-600">
              {Math.round(progress)}%
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Hook helper pour utiliser facilement le toast de progression
 */
export function useImportProgressToast() {
  const [toastId, setToastId] = useState(null);

  const showImportProgress = (toast, fileName) => {
    const id = toast.show({
      type: 'loading',
      title: 'Import en cours...',
      duration: 0,
      dismissible: false,
      custom: <ToastImportProgress jobStatus={{ status: 'processing' }} fileName={fileName} />,
    });
    setToastId(id);
    return id;
  };

  const updateImportProgress = (toast, jobStatus, fileName) => {
    if (!toastId) return;

    // Mettre à jour le toast existant
    toast.dismiss(toastId);

    const newId = toast.show({
      type: jobStatus.status === 'completed' ? 'success' :
            jobStatus.status === 'failed' ? 'error' : 'loading',
      title: jobStatus.status === 'completed' ? 'Import terminé' :
             jobStatus.status === 'failed' ? 'Échec de l\'import' :
             'Import en cours...',
      duration: jobStatus.status === 'completed' || jobStatus.status === 'failed' ? 5000 : 0,
      dismissible: jobStatus.status === 'completed' || jobStatus.status === 'failed',
      custom: <ToastImportProgress jobStatus={jobStatus} fileName={fileName} />,
    });
    setToastId(newId);
  };

  const dismissImportProgress = (toast) => {
    if (toastId) {
      toast.dismiss(toastId);
      setToastId(null);
    }
  };

  return {
    toastId,
    showImportProgress,
    updateImportProgress,
    dismissImportProgress,
  };
}
