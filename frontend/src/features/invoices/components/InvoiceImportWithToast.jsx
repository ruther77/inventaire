/**
 * InvoiceImportWithToast - Exemple d'intégration avec le système Toast existant
 *
 * Alternative à InvoiceZeroClickUpload qui utilise le ToastProvider existant
 * au lieu de créer un portail séparé.
 *
 * Avantages:
 * - Cohérence avec le reste de l'application
 * - Gestion centralisée des toasts
 * - Pas de duplication de code
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import { useToast } from '../../../components/ui/Toast.jsx';
import { useZeroClickJobWithProgress } from '../../../hooks/useImportProgress.js';
import ToastImportProgress from '../../../components/ui/ToastImportProgress.jsx';

export default function InvoiceImportWithToast({ onImportSuccess }) {
  const [marginPercent, setMarginPercent] = useState(40);
  const [supplier, setSupplier] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState(null);
  const [currentToastId, setCurrentToastId] = useState(null);

  const { toast } = useToast();

  const { startJob, isStarting, isPolling, jobStatus, reset } = useZeroClickJobWithProgress({
    onSuccess: (status) => {
      // Le toast sera mis à jour automatiquement via l'effet ci-dessous
      onImportSuccess?.(status.summary);
    },
    onError: (status) => {
      // Le toast sera mis à jour automatiquement via l'effet ci-dessous
      console.error('Import failed:', status.error);
    },
  });

  // Effet pour gérer l'affichage et la mise à jour du toast
  useEffect(() => {
    if (isStarting && !currentToastId) {
      // Démarrage: créer le toast initial
      const id = toast.show({
        type: 'loading',
        title: 'Import en cours...',
        duration: 0,
        dismissible: false,
        custom: <ToastImportProgress jobStatus={{ status: 'processing' }} fileName={fileName} />,
      });
      setCurrentToastId(id);
    }

    if (jobStatus && currentToastId) {
      // Mettre à jour le toast avec le nouveau statut
      toast.dismiss(currentToastId);

      const newId = toast.show({
        type: jobStatus.status === 'completed' ? 'success' :
              jobStatus.status === 'failed' ? 'error' : 'loading',
        title: jobStatus.status === 'completed' ? 'Import terminé !' :
               jobStatus.status === 'failed' ? 'Échec de l\'import' :
               'Import en cours...',
        duration: jobStatus.status === 'completed' || jobStatus.status === 'failed' ? 5000 : 0,
        dismissible: jobStatus.status === 'completed' || jobStatus.status === 'failed',
        custom: <ToastImportProgress jobStatus={jobStatus} fileName={fileName} />,
      });
      setCurrentToastId(newId);

      // Nettoyer après succès ou échec
      if (jobStatus.status === 'completed' || jobStatus.status === 'failed') {
        setTimeout(() => {
          setCurrentToastId(null);
          setFileName(null);
          reset();
        }, 5000);
      }
    }
  }, [isStarting, jobStatus, fileName, currentToastId, toast, reset]);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file) => {
    // Validation du fichier
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];

    if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|docx|txt)$/i)) {
      toast.error('Format non supporté', {
        description: 'Utilisez un fichier PDF, DOCX ou TXT',
      });
      return;
    }

    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      toast.error('Fichier trop volumineux', {
        description: 'Taille maximale: 10MB',
      });
      return;
    }

    // Stocker le nom du fichier et lancer l'import
    setFileName(file.name);
    startJob({
      file,
      marginPercent,
      supplierHint: supplier || null,
      autoConfirm: true,
    });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const isImporting = isStarting || isPolling;

  return (
    <Card className="flex flex-col gap-6">
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400 mb-2">
          Import Zero-Click
        </p>
        <h2 className="text-2xl font-semibold text-slate-900">
          Import automatique de facture
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Un seul clic pour extraire, matcher et importer votre facture.
        </p>
      </div>

      {/* Configuration */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Marge cible */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Marge cible (%)
          </label>
          <input
            type="range"
            min={0}
            max={150}
            value={marginPercent}
            onChange={(e) => setMarginPercent(Number(e.target.value))}
            className="w-full accent-blue-500"
            disabled={isImporting}
          />
          <div className="flex justify-between items-center mt-1">
            <p className="text-sm font-medium text-slate-600">{marginPercent}%</p>
            <p className="text-xs text-slate-400">
              PV = Coût × {(1 + marginPercent / 100).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Fournisseur */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Fournisseur (optionnel)
          </label>
          <input
            type="text"
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
            placeholder="Ex: Metro, Carrefour..."
            className="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
            disabled={isImporting}
          />
          <p className="text-xs text-slate-400 mt-1">
            Améliore la précision du matching
          </p>
        </div>
      </div>

      {/* Dropzone */}
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        animate={{
          borderColor: isDragging ? 'rgb(59 130 246)' : 'rgb(203 213 225)',
          backgroundColor: isDragging ? 'rgb(239 246 255)' : 'rgb(248 250 252)',
          scale: isDragging ? 1.01 : 1,
        }}
        transition={{ duration: 0.2 }}
        className="relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer"
      >
        <input
          type="file"
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isImporting}
        />

        <motion.div
          animate={{
            y: isDragging ? -5 : 0,
            scale: isDragging ? 1.1 : 1,
          }}
          className="flex flex-col items-center gap-4"
        >
          {isDragging ? (
            <FileText className="w-16 h-16 text-blue-500" />
          ) : (
            <Upload className="w-16 h-16 text-slate-400" />
          )}

          <div>
            <p className="text-lg font-medium text-slate-700">
              {isDragging
                ? 'Déposez la facture ici'
                : isImporting
                ? 'Import en cours...'
                : 'Glissez une facture ou cliquez'}
            </p>
            <p className="text-sm text-slate-500 mt-1">
              PDF, DOCX, TXT (max 10MB)
            </p>
          </div>

          {!isImporting && (
            <Button
              variant="brand"
              size="lg"
              onClick={(e) => {
                e.stopPropagation();
                document.querySelector('input[type="file"]').click();
              }}
              className="mt-2"
            >
              Choisir un fichier
            </Button>
          )}
        </motion.div>
      </motion.div>

      {/* Info */}
      <div className="rounded-xl bg-blue-50 border border-blue-100 p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
              <span className="text-white text-sm font-bold">i</span>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-1">
              Import automatisé
            </h4>
            <p className="text-sm text-blue-800 leading-relaxed">
              Le système extrait automatiquement les produits, les matche avec votre catalogue,
              crée les nouveaux produits si nécessaire, et génère les mouvements de stock.
              Une notification vous tiendra informé de la progression.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
