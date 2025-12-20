/**
 * InvoiceZeroClickUpload - Composant d'upload avec notification de progression
 *
 * Exemple d'intégration du système de notification de progression
 * pour l'import zero-click de factures.
 *
 * Fonctionnalités:
 * - Upload drag & drop
 * - Toast de progression automatique
 * - Gestion des succès/erreurs
 * - Configuration de la marge
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText } from 'lucide-react';
import { toast } from 'sonner';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import { useImportProgress } from '../../../hooks/useImportProgress.js';

export default function InvoiceZeroClickUpload({ onImportSuccess }) {
  const [marginPercent, setMarginPercent] = useState(40);
  const [supplier, setSupplier] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const { startImport, isImporting, ToastPortal } = useImportProgress({
    onSuccess: (summary) => {
      // Notification de succès supplémentaire avec détails
      const { movements_created = 0, quantity_total = 0, products_created = 0 } = summary || {};

      // Appeler le callback parent si fourni
      onImportSuccess?.(summary);

      // Toast de confirmation
      toast.success('Import terminé !', {
        description: `${movements_created} mouvements créés pour ${quantity_total} unités${
          products_created ? ` et ${products_created} nouveaux produits` : ''
        }`,
        duration: 5000,
      });
    },
    onError: (error) => {
      toast.error('Échec de l\'import', {
        description: error?.message || 'Une erreur est survenue lors de l\'import',
        duration: 8000,
      });
    },
    onCancel: () => {
      toast.info('Import annulé');
    },
  });

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file) => {
    // Vérifier le type de fichier
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|docx|txt)$/i)) {
      toast.error('Format de fichier non supporté', {
        description: 'Veuillez uploader un fichier PDF, DOCX ou TXT',
      });
      return;
    }

    // Vérifier la taille (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      toast.error('Fichier trop volumineux', {
        description: 'La taille maximale est de 10MB',
      });
      return;
    }

    // Lancer l'import avec le toast de progression
    startImport({
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

  return (
    <>
      <Card className="flex flex-col gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400 mb-2">
            Import Zero-Click
          </p>
          <h2 className="text-2xl font-semibold text-slate-900">
            Import automatique de facture
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Uploadez votre facture et laissez le système gérer l'extraction, le matching et l'import automatiquement.
          </p>
        </div>

        {/* Configuration */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Marge cible */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Marge cible (%)
            </label>
            <input
              type="range"
              min={0}
              max={150}
              value={marginPercent}
              onChange={(e) => setMarginPercent(Number(e.target.value))}
              className="mt-2 w-full accent-blue-500"
              disabled={isImporting}
            />
            <div className="flex justify-between items-center mt-1">
              <p className="text-sm font-medium text-slate-600">{marginPercent}%</p>
              <p className="text-xs text-slate-400">
                Prix de vente = Coût × (1 + {marginPercent}%)
              </p>
            </div>
          </div>

          {/* Fournisseur (optionnel) */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Fournisseur (optionnel)
            </label>
            <input
              type="text"
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
              placeholder="Ex: Metro, Carrefour..."
              className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
              disabled={isImporting}
            />
            <p className="text-xs text-slate-400 mt-1">
              Aide à améliorer la précision du matching
            </p>
          </div>
        </div>

        {/* Dropzone */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <motion.div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            animate={{
              borderColor: isDragging ? 'rgb(59 130 246)' : 'rgb(203 213 225)',
              backgroundColor: isDragging ? 'rgb(239 246 255)' : 'rgb(248 250 252)',
              scale: isDragging ? 1.01 : 1,
            }}
            className="relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all"
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
                    ? 'Déposez votre facture ici'
                    : isImporting
                    ? 'Import en cours...'
                    : 'Glissez une facture ou cliquez pour parcourir'}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  Formats supportés : PDF, DOCX, TXT (max 10MB)
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
                  Parcourir les fichiers
                </Button>
              )}
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Info supplémentaire */}
        <div className="rounded-xl bg-blue-50 border border-blue-200 p-4">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            Comment ça marche ?
          </h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">1.</span>
              <span>Le fichier est analysé pour extraire les lignes de produits</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">2.</span>
              <span>Chaque ligne est automatiquement matchée avec votre catalogue</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">3.</span>
              <span>Les mouvements de stock sont créés et les prix sont mis à jour</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">4.</span>
              <span>Les nouveaux produits sont ajoutés automatiquement au catalogue</span>
            </li>
          </ul>
        </div>
      </Card>

      {/* Rendu du toast de progression */}
      {ToastPortal && <ToastPortal />}
    </>
  );
}
