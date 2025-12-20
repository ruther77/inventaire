/**
 * ImportProgressToast - Notification de progression pour l'import de factures
 *
 * Fonctionnalités:
 * - Affiche une notification persistante pendant l'import
 * - Barre de progression animée
 * - Affiche les étapes: Extraction → Analyse → Import → Terminé
 * - Se transforme en succès/erreur à la fin
 * - Permet d'annuler l'import si possible
 *
 * Utilise:
 * - Framer Motion pour les animations
 * - Tailwind CSS pour le styling
 * - Toast system existant (compatibilité avec ToastProvider)
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Search,
  Database,
  CheckCircle2,
  XCircle,
  Loader2,
  X,
  AlertCircle
} from 'lucide-react';
import clsx from 'clsx';

// Statuts des jobs
const JobStatus = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

// Étapes de l'import
const ImportSteps = {
  EXTRACTION: {
    id: 'extraction',
    label: 'Extraction',
    icon: FileText,
    description: 'Lecture du fichier...',
  },
  ANALYSIS: {
    id: 'analysis',
    label: 'Analyse',
    icon: Search,
    description: 'Matching produits...',
  },
  IMPORT: {
    id: 'import',
    label: 'Import',
    icon: Database,
    description: 'Création des mouvements...',
  },
};

/**
 * Détermine l'étape actuelle basée sur le statut du job et le progress
 */
function getCurrentStep(jobStatus, progress = 0) {
  if (!jobStatus || jobStatus.status === JobStatus.PENDING) {
    return null;
  }

  if (jobStatus.status === JobStatus.COMPLETED || jobStatus.status === JobStatus.FAILED) {
    return 'completed';
  }

  // Progression basée sur le pourcentage
  if (progress < 33) return ImportSteps.EXTRACTION.id;
  if (progress < 66) return ImportSteps.ANALYSIS.id;
  return ImportSteps.IMPORT.id;
}

/**
 * Composant de barre de progression
 */
function ProgressBar({ progress, status }) {
  const isIndeterminate = progress === null || progress === undefined;

  return (
    <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
      {isIndeterminate ? (
        <motion.div
          className={clsx(
            'h-full rounded-full',
            status === JobStatus.FAILED ? 'bg-rose-500' : 'bg-blue-500'
          )}
          initial={{ width: '0%', x: '-100%' }}
          animate={{
            x: ['0%', '100%'],
            width: '40%'
          }}
          transition={{
            x: {
              repeat: Infinity,
              duration: 1.5,
              ease: 'easeInOut',
            },
          }}
        />
      ) : (
        <motion.div
          className={clsx(
            'h-full rounded-full',
            status === JobStatus.FAILED ? 'bg-rose-500' :
            status === JobStatus.COMPLETED ? 'bg-emerald-500' :
            'bg-blue-500'
          )}
          initial={{ width: '0%' }}
          animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      )}
    </div>
  );
}

/**
 * Indicateur d'étape
 */
function StepIndicator({ step, currentStepId, status }) {
  const StepIcon = step.icon;
  const isActive = currentStepId === step.id;
  const isPast = ['extraction', 'analysis', 'import'].indexOf(currentStepId) >
                 ['extraction', 'analysis', 'import'].indexOf(step.id);
  const isCompleted = status === JobStatus.COMPLETED && currentStepId === 'completed';
  const isFailed = status === JobStatus.FAILED;

  return (
    <motion.div
      className="flex flex-col items-center gap-1.5 flex-1"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Icon */}
      <motion.div
        className={clsx(
          'relative flex items-center justify-center rounded-full',
          'w-10 h-10 transition-colors duration-300',
          isActive && !isFailed && 'bg-blue-100 text-blue-600',
          isPast && !isFailed && 'bg-emerald-100 text-emerald-600',
          !isActive && !isPast && !isCompleted && 'bg-slate-100 text-slate-400',
          isFailed && isActive && 'bg-rose-100 text-rose-600'
        )}
        animate={isActive ? { scale: [1, 1.05, 1] } : { scale: 1 }}
        transition={{ duration: 2, repeat: isActive ? Infinity : 0 }}
      >
        {isActive && !isFailed && (
          <motion.div
            className="absolute inset-0 rounded-full bg-blue-400"
            initial={{ scale: 1, opacity: 0.5 }}
            animate={{ scale: 1.4, opacity: 0 }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
        <StepIcon className="w-5 h-5 relative z-10" />
      </motion.div>

      {/* Label */}
      <div className="text-center">
        <p className={clsx(
          'text-xs font-medium transition-colors',
          isActive && !isFailed && 'text-blue-600',
          isPast && !isFailed && 'text-emerald-600',
          !isActive && !isPast && !isCompleted && 'text-slate-400',
          isFailed && isActive && 'text-rose-600'
        )}>
          {step.label}
        </p>
      </div>
    </motion.div>
  );
}

/**
 * Composant principal ImportProgressToast
 */
export default function ImportProgressToast({
  jobStatus,
  fileName,
  onCancel,
  onDismiss,
  canCancel = false,
}) {
  const [progress, setProgress] = useState(0);
  const [currentMessage, setCurrentMessage] = useState('Démarrage...');

  const status = jobStatus?.status || JobStatus.PENDING;
  const currentStep = getCurrentStep(jobStatus, progress);

  // Simulation de progression pour le mode indéterminé
  useEffect(() => {
    if (status === JobStatus.PROCESSING) {
      // Calculer la progression basée sur les données du job si disponibles
      if (jobStatus?.progress !== undefined && jobStatus?.progress !== null) {
        setProgress(jobStatus.progress);
      } else {
        // Progression simulée si pas de données
        const interval = setInterval(() => {
          setProgress((prev) => {
            const increment = Math.random() * 5;
            const newProgress = prev + increment;
            // Plafonner à 95% jusqu'à ce que le job soit vraiment terminé
            return Math.min(95, newProgress);
          });
        }, 800);

        return () => clearInterval(interval);
      }
    } else if (status === JobStatus.COMPLETED) {
      setProgress(100);
    }
  }, [status, jobStatus?.progress]);

  // Mettre à jour le message en fonction de l'étape
  useEffect(() => {
    if (status === JobStatus.COMPLETED) {
      const summary = jobStatus?.summary;
      if (summary) {
        const { movements_created = 0, quantity_total = 0, products_created = 0 } = summary;
        setCurrentMessage(
          `${movements_created} mouvements, ${quantity_total} unités${
            products_created ? `, ${products_created} nouveaux produits` : ''
          }`
        );
      } else {
        setCurrentMessage('Import terminé avec succès');
      }
    } else if (status === JobStatus.FAILED) {
      setCurrentMessage(jobStatus?.error || 'Une erreur est survenue');
    } else if (currentStep === ImportSteps.EXTRACTION.id) {
      setCurrentMessage(ImportSteps.EXTRACTION.description);
    } else if (currentStep === ImportSteps.ANALYSIS.id) {
      setCurrentMessage(ImportSteps.ANALYSIS.description);
    } else if (currentStep === ImportSteps.IMPORT.id) {
      setCurrentMessage(ImportSteps.IMPORT.description);
    }
  }, [currentStep, status, jobStatus]);

  const isComplete = status === JobStatus.COMPLETED;
  const isFailed = status === JobStatus.FAILED;
  const isProcessing = status === JobStatus.PROCESSING;

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      className={clsx(
        'w-96 max-w-[calc(100vw-2rem)] rounded-2xl shadow-2xl overflow-hidden',
        'border-2',
        isComplete && 'bg-emerald-50 border-emerald-200',
        isFailed && 'bg-rose-50 border-rose-200',
        isProcessing && 'bg-white border-slate-200'
      )}
    >
      {/* Header */}
      <div className="px-5 pt-4 pb-3 flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {/* Status Icon */}
          <div className="flex-shrink-0 mt-0.5">
            <AnimatePresence mode="wait">
              {isProcessing && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  exit={{ opacity: 0, rotate: 90 }}
                >
                  <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                </motion.div>
              )}
              {isComplete && (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                >
                  <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                </motion.div>
              )}
              {isFailed && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                >
                  <XCircle className="w-6 h-6 text-rose-600" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h4 className={clsx(
              'text-sm font-semibold',
              isComplete && 'text-emerald-900',
              isFailed && 'text-rose-900',
              isProcessing && 'text-slate-900'
            )}>
              {isComplete ? 'Import terminé' : isFailed ? 'Échec de l\'import' : 'Import en cours'}
            </h4>
            {fileName && (
              <p className="text-xs text-slate-600 mt-0.5 truncate">
                {fileName}
              </p>
            )}
          </div>
        </div>

        {/* Close/Cancel button */}
        <button
          type="button"
          onClick={() => {
            if (isProcessing && canCancel && onCancel) {
              onCancel();
            } else if (onDismiss) {
              onDismiss();
            }
          }}
          className={clsx(
            'flex-shrink-0 rounded-lg p-1.5 transition-colors',
            'hover:bg-slate-200/60',
            isComplete && 'hover:bg-emerald-200/60',
            isFailed && 'hover:bg-rose-200/60'
          )}
          aria-label={isProcessing && canCancel ? 'Annuler' : 'Fermer'}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Progress Steps (uniquement en mode processing) */}
      {isProcessing && (
        <div className="px-5 pb-3">
          <div className="flex items-center justify-between gap-2">
            {Object.values(ImportSteps).map((step) => (
              <StepIndicator
                key={step.id}
                step={step}
                currentStepId={currentStep}
                status={status}
              />
            ))}
          </div>
        </div>
      )}

      {/* Message */}
      <div className="px-5 pb-3">
        <AnimatePresence mode="wait">
          <motion.p
            key={currentMessage}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className={clsx(
              'text-sm',
              isComplete && 'text-emerald-700 font-medium',
              isFailed && 'text-rose-700',
              isProcessing && 'text-slate-600'
            )}
          >
            {currentMessage}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Progress Bar */}
      <div className="px-5 pb-4">
        <ProgressBar progress={progress} status={status} />
        {isProcessing && (
          <p className="text-xs text-slate-500 mt-1.5">
            {progress < 100 ? `${Math.round(progress)}%` : 'Finalisation...'}
          </p>
        )}
      </div>

      {/* Warning pour les échecs */}
      {isFailed && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="px-5 pb-4"
        >
          <div className="flex items-start gap-2 text-xs text-rose-700 bg-rose-100/50 rounded-lg p-3">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p>
              Vérifiez le format du fichier et réessayez. Si le problème persiste, contactez le support.
            </p>
          </div>
        </motion.div>
      )}

      {/* Action buttons pour les états terminés */}
      {(isComplete || isFailed) && onDismiss && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-5 pb-4"
        >
          <button
            type="button"
            onClick={onDismiss}
            className={clsx(
              'w-full rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              isComplete && 'bg-emerald-600 hover:bg-emerald-700 text-white',
              isFailed && 'bg-rose-600 hover:bg-rose-700 text-white'
            )}
          >
            {isComplete ? 'Fermer' : 'J\'ai compris'}
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}
