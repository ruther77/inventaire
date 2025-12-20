/**
 * ImportStepper - Composant pour gérer l'import de fichiers bancaires (CSV et PDF)
 *
 * Supporte:
 * - CSV: Format standard avec colonnes date, libelle, montant
 * - PDF: Relevés LCL, BNP, SumUp (parsing automatique via orchestrator)
 *
 * Design: Standards Morning Brief (dark mode, glass-morphism, Framer Motion)
 */

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, Loader2, X } from 'lucide-react';
import clsx from 'clsx';
import Button from '../../../components/ui/Button.jsx';
import { useFinanceImport, useFinanceImportPDF } from '../../../hooks/useFinance.js';

const STATES = {
  IDLE: 'IDLE',
  UPLOADING: 'UPLOADING',
  PARSING: 'PARSING',
  DONE: 'DONE',
  ERROR: 'ERROR',
};

const ALLOWED_EXTENSIONS = ['.csv', '.pdf'];
const ALLOWED_TYPES = ['text/csv', 'application/pdf'];

const isValidFile = (file) => {
  const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
  return ALLOWED_EXTENSIONS.includes(ext) || ALLOWED_TYPES.includes(file.type);
};

const isPDFFile = (file) => {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
};

export default function ImportStepper({ accountId, onComplete }) {
  const [state, setState] = useState(STATES.IDLE);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const importCSVMutation = useFinanceImport();
  const importPDFMutation = useFinanceImportPDF();

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (isValidFile(file)) {
        setSelectedFile(file);
        setError('');
      } else {
        setError('Veuillez sélectionner un fichier CSV ou PDF');
      }
    }
  }, []);

  const handleFileInput = useCallback((e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (isValidFile(file)) {
        setSelectedFile(file);
        setError('');
      } else {
        setError('Veuillez sélectionner un fichier CSV ou PDF');
      }
    }
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Aucun fichier sélectionné');
      return;
    }

    if (!accountId) {
      setError('Aucun compte sélectionné');
      return;
    }

    setState(STATES.UPLOADING);
    setError('');
    setUploadProgress(0);

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 100);

    try {
      setState(STATES.PARSING);
      setUploadProgress(100);

      // Choisir le bon endpoint selon le type de fichier
      const isPDF = isPDFFile(selectedFile);
      const mutation = isPDF ? importPDFMutation : importCSVMutation;

      const data = await mutation.mutateAsync({
        accountId,
        file: selectedFile,
      });

      clearInterval(progressInterval);
      setResult(data);
      setState(STATES.DONE);

      if (onComplete) {
        onComplete(data);
      }
    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message || "Erreur lors de l'import");
      setState(STATES.ERROR);
    }
  };

  const handleReset = () => {
    setState(STATES.IDLE);
    setSelectedFile(null);
    setError('');
    setResult(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* IDLE - File Selection */}
      <AnimatePresence mode="wait">
        {state === STATES.IDLE && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={clsx(
              'relative rounded-2xl border-2 border-dashed p-8 transition-all duration-200',
              dragActive
                ? 'border-blue-500/50 bg-blue-500/10'
                : 'border-white/20 bg-white/5 hover:border-white/30 hover:bg-white/10'
            )}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.pdf,text/csv,application/pdf"
              onChange={handleFileInput}
              className="hidden"
              disabled={!accountId}
            />

            <div className="flex flex-col items-center gap-4 text-center">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className={clsx(
                  'rounded-full p-4',
                  selectedFile ? 'bg-blue-500/20' : 'bg-white/10'
                )}
              >
                {selectedFile ? (
                  <FileText className="h-8 w-8 text-blue-400" />
                ) : (
                  <Upload className="h-8 w-8 text-slate-400" />
                )}
              </motion.div>

              {selectedFile ? (
                <>
                  <div>
                    <p className="text-sm font-medium text-white">{selectedFile.name}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm" onClick={handleReset}>
                      Changer
                    </Button>
                    <Button variant="primary" size="sm" onClick={handleUpload} disabled={!accountId}>
                      Importer
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <p className="text-sm font-medium text-white">
                      Déposez votre fichier CSV ou PDF ici
                    </p>
                    <p className="mt-1 text-xs text-slate-500">ou cliquez pour parcourir (relevés LCL, BNP, SumUp)</p>
                  </div>
                  <Button
                    variant="subtle"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={!accountId}
                  >
                    Sélectionner un fichier
                  </Button>
                </>
              )}

              {!accountId && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2"
                >
                  <p className="flex items-center gap-2 text-xs text-amber-400">
                    <AlertCircle className="h-4 w-4" />
                    Veuillez d'abord sélectionner un compte
                  </p>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* UPLOADING - Progress */}
        {state === STATES.UPLOADING && (
          <motion.div
            key="uploading"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="rounded-2xl border border-white/10 bg-white/5 p-6"
          >
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Loader2 className="h-8 w-8 text-blue-400 animate-spin" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">Téléchargement en cours...</p>
                  <p className="text-xs text-slate-500">{selectedFile?.name}</p>
                </div>
              </div>
              <div className="relative h-2 overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <p className="text-center text-xs text-slate-500">{uploadProgress}%</p>
            </div>
          </motion.div>
        )}

        {/* PARSING */}
        {state === STATES.PARSING && (
          <motion.div
            key="parsing"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="rounded-2xl border border-white/10 bg-white/5 p-6"
          >
            <div className="flex items-center gap-3">
              <Loader2 className="h-8 w-8 text-violet-400 animate-spin" />
              <div className="flex-1">
                <p className="text-sm font-medium text-white">Analyse du fichier...</p>
                <p className="text-xs text-slate-500">Traitement des transactions</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* DONE - Success */}
        {state === STATES.DONE && result && (
          <motion.div
            key="done"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6"
          >
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-full bg-emerald-500/20">
                  <CheckCircle className="h-6 w-6 text-emerald-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-emerald-400">Import réussi</p>
                  <div className="mt-2 space-y-1 text-xs text-emerald-300/80">
                    <p>
                      <strong className="text-emerald-400">{result.inserted || 0}</strong> ligne
                      {(result.inserted || 0) > 1 ? 's' : ''} importée
                      {(result.inserted || 0) > 1 ? 's' : ''}
                    </p>
                    {result.total && result.total !== result.inserted && (
                      <p>
                        <strong>{result.total - result.inserted}</strong> ligne
                        {result.total - result.inserted > 1 ? 's' : ''} ignorée
                        {result.total - result.inserted > 1 ? 's' : ''} (doublon
                        {result.total - result.inserted > 1 ? 's' : ''})
                      </p>
                    )}
                    {result.errors && result.errors > 0 && (
                      <p className="text-rose-400">
                        <strong>{result.errors}</strong> erreur{result.errors > 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReset} className="w-full">
                Importer un autre fichier
              </Button>
            </div>
          </motion.div>
        )}

        {/* ERROR */}
        {state === STATES.ERROR && (
          <motion.div
            key="error"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6"
          >
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-full bg-rose-500/20">
                  <XCircle className="h-6 w-6 text-rose-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-rose-400">Erreur d'import</p>
                  <p className="mt-1 text-xs text-rose-300/80">{error || 'Une erreur est survenue'}</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReset} className="w-full">
                Réessayer
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* General Error (IDLE state) */}
      <AnimatePresence>
        {state === STATES.IDLE && error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-2"
          >
            <p className="flex items-center gap-2 text-xs text-rose-400">
              <XCircle className="h-4 w-4" />
              {error}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
