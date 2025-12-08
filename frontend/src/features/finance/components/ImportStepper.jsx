import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import Button from '../../../components/ui/Button.jsx';
import { useFinanceImport } from '../../../hooks/useFinance.js';

const STATES = {
  IDLE: 'IDLE',
  UPLOADING: 'UPLOADING',
  PARSING: 'PARSING',
  DONE: 'DONE',
  ERROR: 'ERROR',
};

/**
 * ImportStepper - Composant pour gérer l'import de fichiers CSV bancaires
 */
export default function ImportStepper({ accountId, onComplete }) {
  const [state, setState] = useState(STATES.IDLE);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const importMutation = useFinanceImport();

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
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setSelectedFile(file);
      } else {
        setError('Veuillez sélectionner un fichier CSV');
      }
    }
  }, []);

  const handleFileInput = useCallback((e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setError('');
      } else {
        setError('Veuillez sélectionner un fichier CSV');
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

    // Simulate upload progress
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

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('account_id', accountId);

      const data = await importMutation.mutateAsync(formData);

      clearInterval(progressInterval);
      setResult(data);
      setState(STATES.DONE);

      if (onComplete) {
        onComplete(data);
      }
    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message || 'Erreur lors de l\'import');
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

  return (
    <div className="space-y-4">
      {/* Step 1: IDLE - File Selection */}
      {state === STATES.IDLE && (
        <div
          className={clsx(
            'relative rounded-2xl border-2 border-dashed p-8 transition-colors duration-150',
            dragActive
              ? 'border-brand-500 bg-brand-50'
              : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            className="hidden"
            disabled={!accountId}
          />

          <div className="flex flex-col items-center gap-4 text-center">
            <div className="rounded-full bg-white p-4 shadow-sm">
              {selectedFile ? (
                <FileText className="h-8 w-8 text-brand-600" />
              ) : (
                <Upload className="h-8 w-8 text-slate-400" />
              )}
            </div>

            {selectedFile ? (
              <>
                <div>
                  <p className="text-sm font-medium text-slate-900">{selectedFile.name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={handleReset}>
                    Changer de fichier
                  </Button>
                  <Button variant="primary" size="sm" onClick={handleUpload} disabled={!accountId}>
                    Importer
                  </Button>
                </div>
              </>
            ) : (
              <>
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    Déposez votre fichier CSV ici
                  </p>
                  <p className="mt-1 text-xs text-slate-500">ou cliquez pour parcourir</p>
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
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                <p className="flex items-center gap-2 text-xs text-amber-700">
                  <AlertCircle className="h-4 w-4" />
                  Veuillez d'abord sélectionner un compte
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 2: UPLOADING - Progress Bar */}
      {state === STATES.UPLOADING && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full border-2 border-slate-200 border-t-brand-600 h-8 w-8" />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">Téléchargement en cours...</p>
                <p className="text-xs text-slate-500">{selectedFile?.name}</p>
              </div>
            </div>
            <div className="relative h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="absolute left-0 top-0 h-full bg-brand-600 transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-center text-xs text-slate-500">{uploadProgress}%</p>
          </div>
        </div>
      )}

      {/* Step 3: PARSING */}
      {state === STATES.PARSING && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full border-2 border-slate-200 border-t-brand-600 h-8 w-8" />
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">Analyse du fichier...</p>
              <p className="text-xs text-slate-500">Traitement des transactions</p>
            </div>
          </div>
        </div>
      )}

      {/* Step 4: DONE - Success Summary */}
      {state === STATES.DONE && result && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-6 w-6 text-emerald-600 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-emerald-900">Import réussi</p>
                <div className="mt-2 space-y-1 text-xs text-emerald-700">
                  <p>
                    <strong>{result.inserted || 0}</strong> ligne{result.inserted > 1 ? 's' : ''} importée
                    {result.inserted > 1 ? 's' : ''}
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
                    <p className="text-rose-600">
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
        </div>
      )}

      {/* Step 5: ERROR - Error Message */}
      {state === STATES.ERROR && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6">
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <XCircle className="h-6 w-6 text-rose-600 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-rose-900">Erreur d'import</p>
                <p className="mt-1 text-xs text-rose-700">{error || 'Une erreur est survenue'}</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={handleReset} className="w-full">
              Réessayer
            </Button>
          </div>
        </div>
      )}

      {/* General Error Message (for IDLE state) */}
      {state === STATES.IDLE && error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">
          <p className="flex items-center gap-2 text-xs text-rose-700">
            <XCircle className="h-4 w-4" />
            {error}
          </p>
        </div>
      )}
    </div>
  );
}
