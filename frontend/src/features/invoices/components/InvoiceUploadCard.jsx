/**
 * InvoiceUploadCard - Composant d'upload et extraction de factures
 *
 * Responsabilites:
 * - Upload de fichiers PDF/DOCX/TXT
 * - Extraction de texte colle
 * - Configuration de la marge cible
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, CheckCircle } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import {
  useInvoiceExtraction,
  useInvoiceFileExtraction,
} from '../../../hooks/useInvoiceImport.js';

const dropzoneVariants = {
  idle: {
    scale: 1,
    borderColor: 'rgb(203 213 225)',
    backgroundColor: 'rgb(248 250 252)',
  },
  hover: {
    scale: 1.01,
    borderColor: 'rgb(59 130 246)',
    backgroundColor: 'rgb(239 246 255)',
    transition: { duration: 0.2 },
  },
  active: {
    scale: 0.99,
    borderColor: 'rgb(37 99 235)',
    backgroundColor: 'rgb(219 234 254)',
    transition: { duration: 0.1 },
  },
};

export default function InvoiceUploadCard({
  marginPercent,
  onMarginChange,
  supplier,
  onExtractionSuccess,
  onProcessingSnapshot,
  onFileUpload,
}) {
  const [rawText, setRawText] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const extractTextMutation = useInvoiceExtraction();
  const extractFileMutation = useInvoiceFileExtraction();

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    processFile(file);
  };

  const processFile = (file) => {
    // Notifier le parent qu'un fichier a été uploadé (pour le preview PDF)
    if (onFileUpload) {
      onFileUpload(file);
    }

    if (onProcessingSnapshot) {
      onProcessingSnapshot({
        isProcessing: true,
        fileName: file.name,
        steps: [
          { id: 'ocr', status: 'processing', result: 'Analyse en cours' },
          { id: 'matching', status: 'pending' },
          { id: 'pricing', status: 'pending' },
          { id: 'categorization', status: 'pending' },
          { id: 'stock', status: 'pending' },
        ],
      });
    }

    // Simulate progress
    setUploadProgress(0);
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 100);

    extractFileMutation.mutate(
      { file, marginPercent, supplierHint: supplier || null },
      {
        onSuccess: (data) => {
          setUploadProgress(100);
          setTimeout(() => {
            onExtractionSuccess(data);
            if (onProcessingSnapshot) {
              onProcessingSnapshot({
                isProcessing: true,
                fileName: file.name,
                steps: [
                  { id: 'ocr', status: 'completed', result: `${data?.items?.length || 0} lignes extraites` },
                  { id: 'matching', status: 'processing', result: 'Matching catalogue...' },
                  { id: 'pricing', status: 'pending' },
                  { id: 'categorization', status: 'pending' },
                  { id: 'stock', status: 'pending' },
                ],
              });
            }
            setUploadProgress(0);
          }, 500);
        },
        onError: () => {
          clearInterval(interval);
          setUploadProgress(0);
          if (onProcessingSnapshot) {
            onProcessingSnapshot({
              isProcessing: false,
              steps: [
                { id: 'ocr', status: 'error', result: 'Erreur extraction' },
                { id: 'matching', status: 'pending' },
                { id: 'pricing', status: 'pending' },
                { id: 'categorization', status: 'pending' },
                { id: 'stock', status: 'pending' },
              ],
            });
          }
        },
      },
    );
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

  const handleTextExtract = () => {
    if (!rawText.trim()) return;
    if (onProcessingSnapshot) {
      onProcessingSnapshot({
        isProcessing: true,
        fileName: 'Texte collé',
        steps: [
          { id: 'ocr', status: 'completed', result: 'Texte fourni' },
          { id: 'matching', status: 'processing', result: 'Matching catalogue...' },
          { id: 'pricing', status: 'pending' },
          { id: 'categorization', status: 'pending' },
          { id: 'stock', status: 'pending' },
        ],
      });
    }
    extractTextMutation.mutate(
      { text: rawText, marginPercent, supplierHint: supplier || null },
      {
        onSuccess: (data) => {
          onExtractionSuccess(data);
          if (onProcessingSnapshot) {
            onProcessingSnapshot({
              isProcessing: true,
              fileName: 'Texte collé',
              steps: [
                { id: 'ocr', status: 'completed', result: `${data?.items?.length || 0} lignes extraites` },
                { id: 'matching', status: 'processing', result: 'Matching catalogue...' },
                { id: 'pricing', status: 'pending' },
                { id: 'categorization', status: 'pending' },
                { id: 'stock', status: 'pending' },
              ],
            });
          }
          setRawText('');
        },
      },
    );
  };

  const isLoading = extractTextMutation.isPending || extractFileMutation.isPending;

  return (
    <Card className="flex flex-col gap-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400">import facture</p>
        <h2 className="text-2xl font-semibold text-slate-900">Automatiser la reception</h2>
        <p className="text-sm text-slate-500">
          Televersez une facture Metro, corrigez les lignes detectees et creez automatiquement les mouvements
          d&apos;entree.
        </p>
      </motion.div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Marge cible */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Marge cible (%)
          </label>
          <input
            type="range"
            min={0}
            max={150}
            value={marginPercent}
            onChange={(event) => onMarginChange(Number(event.target.value))}
            className="mt-2 w-full accent-blue-500"
          />
          <p className="text-sm text-slate-600">{marginPercent}%</p>
        </motion.div>

        {/* Upload fichier avec Dropzone animée */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Upload PDF / DOCX / TXT
          </label>
          <motion.div
            variants={dropzoneVariants}
            initial="idle"
            animate={isDragging ? 'active' : isLoading ? 'active' : 'idle'}
            whileHover={!isLoading ? 'hover' : undefined}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className="relative mt-2 rounded-2xl border-2 border-dashed p-6 text-center cursor-pointer overflow-hidden"
          >
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={isLoading}
            />

            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex flex-col items-center gap-2"
                >
                  <motion.div
                    className="w-10 h-10 rounded-full border-3 border-blue-200 border-t-blue-500"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                  <p className="text-sm text-blue-600">Analyse en cours...</p>
                  {/* Progress bar */}
                  <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden mt-2">
                    <motion.div
                      className="h-full bg-blue-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      transition={{ duration: 0.3, ease: 'easeOut' }}
                    />
                  </div>
                  <p className="text-xs text-slate-500">{uploadProgress}%</p>
                </motion.div>
              ) : uploadProgress === 100 ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-2"
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                  >
                    <CheckCircle className="w-10 h-10 text-emerald-500" />
                  </motion.div>
                  <p className="text-sm text-emerald-600">Fichier traite!</p>
                </motion.div>
              ) : (
                <motion.div
                  key="idle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-2"
                >
                  <motion.div
                    animate={isDragging ? { scale: 1.1, y: -5 } : { scale: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Upload className="w-8 h-8 text-slate-400" />
                  </motion.div>
                  <p className="text-sm text-slate-600">
                    {isDragging ? 'Deposez le fichier ici' : 'Glissez un fichier ou cliquez'}
                  </p>
                  <p className="text-xs text-slate-400">PDF, DOCX, TXT</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>

        {/* Texte colle */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Ou collez le texte detecte
          </label>
          <textarea
            rows={4}
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all"
            placeholder="Collez la section produits de la facture..."
          />
          <Button
            variant="brand"
            size="sm"
            className="mt-2"
            onClick={handleTextExtract}
            disabled={isLoading || !rawText.trim()}
          >
            {extractTextMutation.isPending ? 'Analyse...' : 'Analyser ce texte'}
          </Button>
        </motion.div>
      </div>

      {/* Erreurs */}
      <AnimatePresence>
        {(extractTextMutation.isError || extractFileMutation.isError) && (
          <motion.div
            initial={{ opacity: 0, y: 10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -10, height: 0 }}
            className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"
          >
            Erreur lors de l'extraction. Verifiez le format du fichier.
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
