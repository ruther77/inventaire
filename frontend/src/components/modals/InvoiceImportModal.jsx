import { useState, useCallback } from 'react';
import { X, Upload, FileText, Trash2, Check, Loader2 } from 'lucide-react';
import { useInvoiceZeroClick } from '@/hooks/useInvoiceImport.js';
import Button from '@/components/ui/Button.jsx';
import { toast } from 'sonner';

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      className={`relative w-11 h-6 rounded-full transition-colors ${
        checked ? 'bg-emerald-500' : 'bg-white/10'
      }`}
      onClick={() => onChange(!checked)}
    >
      <span
        className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  );
}

function FileItem({ file, onRemove }) {
  const statusConfig = {
    ready: { label: 'Prêt', icon: Check, bg: 'bg-emerald-500/20', color: 'text-emerald-400' },
    processing: { label: 'Analyse...', icon: Loader2, bg: 'bg-blue-500/20', color: 'text-blue-400', spin: true },
    error: { label: 'Erreur', icon: X, bg: 'bg-rose-500/20', color: 'text-rose-400' },
  };

  const status = statusConfig[file.status] || statusConfig.ready;
  const StatusIcon = status.icon;

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
      <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
        <FileText className="w-5 h-5 text-amber-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{file.name}</p>
        <p className="text-xs text-slate-500">
          {formatSize(file.size)} - {file.type?.split('/')[1]?.toUpperCase() || 'PDF'}
        </p>
      </div>
      <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold ${status.bg} ${status.color}`}>
        <StatusIcon className={`w-3.5 h-3.5 ${status.spin ? 'animate-spin' : ''}`} />
        {status.label}
      </span>
      <button
        type="button"
        className="p-1.5 rounded-md bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
        onClick={() => onRemove(file)}
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

export default function InvoiceImportModal({ open, onClose, onSuccess }) {
  const [files, setFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [options, setOptions] = useState({
    updatePrices: true,
    autoCreateProducts: false,
    alertPriceVariation: true,
  });

  const { mutate: importInvoice, isPending } = useInvoiceZeroClick();

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  }, []);

  const handleFileSelect = useCallback((e) => {
    const selectedFiles = Array.from(e.target.files || []);
    addFiles(selectedFiles);
  }, []);

  const addFiles = (newFiles) => {
    const validFiles = newFiles.filter((f) =>
      ['application/pdf', 'image/jpeg', 'image/png', 'text/csv'].includes(f.type) ||
      f.name.endsWith('.pdf') || f.name.endsWith('.csv')
    );

    const fileItems = validFiles.map((f) => ({
      id: `${f.name}-${Date.now()}`,
      name: f.name,
      size: f.size,
      type: f.type,
      file: f,
      status: 'ready',
    }));

    setFiles((prev) => [...prev, ...fileItems]);
  };

  const removeFile = (fileToRemove) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileToRemove.id));
  };

  const handleImport = async () => {
    if (files.length === 0) {
      toast.error('Veuillez ajouter au moins un fichier');
      return;
    }

    // Mark files as processing
    setFiles((prev) => prev.map((f) => ({ ...f, status: 'processing' })));

    try {
      for (const fileItem of files) {
        await importInvoice({
          file: fileItem.file,
          options,
        });
      }

      toast.success(`${files.length} facture(s) importée(s) avec succès`);
      setFiles([]);
      onSuccess?.();
      onClose();
    } catch (error) {
      setFiles((prev) => prev.map((f) => ({ ...f, status: 'error' })));
      toast.error("Erreur lors de l'import");
    }
  };

  const totalSize = files.reduce((sum, f) => sum + f.size, 0);
  const formatTotalSize = (bytes) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-xl bg-slate-900/95 border border-white/10 rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-gradient-to-r from-amber-500/10 to-transparent">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-amber-400" />
            Import de factures
          </h2>
          <button
            type="button"
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
            onClick={onClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Dropzone */}
          <label
            className={`block border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              dragOver
                ? 'border-amber-500 bg-amber-500/10'
                : 'border-white/20 hover:border-amber-500/50 hover:bg-white/5'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              className="hidden"
              multiple
              accept=".pdf,.jpg,.jpeg,.png,.csv"
              onChange={handleFileSelect}
            />
            <Upload className="w-12 h-12 mx-auto mb-3 text-slate-400" />
            <p className="text-base font-medium text-white mb-1">
              Déposez vos factures ici
            </p>
            <p className="text-sm text-slate-400 mb-4">
              ou cliquez pour parcourir vos fichiers
            </p>
            <div className="flex justify-center gap-2">
              {['PDF', 'JPG', 'PNG', 'CSV'].map((format) => (
                <span
                  key={format}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-white/5 text-slate-400"
                >
                  {format}
                </span>
              ))}
            </div>
          </label>

          {/* Files List */}
          {files.length > 0 && (
            <div className="space-y-2 p-4 bg-white/5 rounded-xl">
              {files.map((file) => (
                <FileItem key={file.id} file={file} onRemove={removeFile} />
              ))}
            </div>
          )}

          {/* Options */}
          <div className="p-4 bg-white/5 rounded-xl space-y-4">
            <p className="text-sm font-semibold text-white flex items-center gap-2">
              Options d'import
            </p>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">
                Mise à jour automatique des prix
              </span>
              <Toggle
                checked={options.updatePrices}
                onChange={(v) => setOptions({ ...options, updatePrices: v })}
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">
                Création automatique des produits
              </span>
              <Toggle
                checked={options.autoCreateProducts}
                onChange={(v) => setOptions({ ...options, autoCreateProducts: v })}
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">
                Alerter si écart de prix &gt; 20%
              </span>
              <Toggle
                checked={options.alertPriceVariation}
                onChange={(v) => setOptions({ ...options, alertPriceVariation: v })}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/10">
          <span className="text-sm text-slate-400">
            {files.length > 0
              ? `${files.length} fichier(s) - ${formatTotalSize(totalSize)}`
              : 'Aucun fichier sélectionné'}
          </span>
          <div className="flex gap-3">
            <Button variant="ghost" onClick={onClose}>
              Annuler
            </Button>
            <Button
              variant="brand"
              onClick={handleImport}
              disabled={files.length === 0 || isPending}
              className="bg-amber-500 hover:bg-amber-600"
            >
              {isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Import en cours...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Importer les factures
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
