/**
 * PDFPreview - Composant d'aperçu PDF inline
 *
 * Fonctionnalités:
 * - Affichage PDF via iframe avec PDF.js natif du navigateur
 * - Zoom in/out avec contrôles
 * - Navigation entre pages
 * - Mode plein écran
 * - Responsive (collapse sur mobile)
 * - Support text selection et highlight
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  Download,
  X,
  FileText,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import clsx from 'clsx';
import Button from './Button.jsx';

/**
 * PDFPreview Component
 * @param {File|string} file - Fichier PDF ou URL blob
 * @param {string} fileName - Nom du fichier pour affichage
 * @param {boolean} collapsible - Permet de réduire le preview (défaut: true)
 * @param {boolean} defaultCollapsed - État initial (défaut: false)
 * @param {string} className - Classes CSS supplémentaires
 */
export default function PDFPreview({
  file,
  fileName,
  collapsible = true,
  defaultCollapsed = false,
  className,
}) {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const iframeRef = useRef(null);
  const containerRef = useRef(null);

  // Créer l'URL blob du PDF
  useEffect(() => {
    if (!file) {
      setPdfUrl(null);
      return;
    }

    setIsLoading(true);

    // Si c'est déjà une URL
    if (typeof file === 'string') {
      setPdfUrl(file);
      setIsLoading(false);
      return;
    }

    // Si c'est un File object
    if (file instanceof File || file instanceof Blob) {
      const url = URL.createObjectURL(file);
      setPdfUrl(url);
      setIsLoading(false);

      // Cleanup
      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [file]);

  // Gestion du zoom
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 25, 50));
  };

  const handleResetZoom = () => {
    setZoom(100);
  };

  // Gestion du plein écran
  const toggleFullscreen = () => {
    if (!isFullscreen) {
      containerRef.current?.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  // Download PDF
  const handleDownload = () => {
    if (!pdfUrl) return;

    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = fileName || 'facture.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Navigation pages (simulée - dans un vrai cas il faudrait PDF.js)
  const handlePrevPage = () => {
    setCurrentPage((prev) => Math.max(prev - 1, 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(prev + 1, totalPages || prev));
  };

  if (!file) {
    return (
      <div className={clsx('rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-8', className)}>
        <div className="flex flex-col items-center justify-center text-center">
          <FileText className="w-12 h-12 text-slate-300 mb-4" />
          <p className="text-sm text-slate-500">Aucun PDF sélectionné</p>
          <p className="text-xs text-slate-400 mt-1">
            Importez une facture pour afficher l'aperçu ici
          </p>
        </div>
      </div>
    );
  }

  if (isCollapsed && collapsible) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={clsx('rounded-2xl border border-slate-200 bg-white shadow-sm', className)}
      >
        <button
          onClick={() => setIsCollapsed(false)}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-50 transition-colors rounded-2xl"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-slate-900">
                {fileName || 'Aperçu PDF'}
              </p>
              <p className="text-xs text-slate-500">Cliquez pour afficher</p>
            </div>
          </div>
          <ChevronDown className="w-5 h-5 text-slate-400" />
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden flex flex-col',
        isFullscreen && 'fixed inset-0 z-50 rounded-none',
        className
      )}
    >
      {/* Header avec contrôles */}
      <div className="flex items-center justify-between gap-3 p-3 border-b border-slate-200 bg-slate-50">
        {/* Titre */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <span className="text-sm font-medium text-slate-900 truncate">
            {fileName || 'Aperçu PDF'}
          </span>
        </div>

        {/* Contrôles */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Zoom */}
          <Button
            variant="ghost"
            size="xs"
            onClick={handleZoomOut}
            disabled={zoom <= 50}
            title="Zoom arrière"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <button
            onClick={handleResetZoom}
            className="px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
            title="Réinitialiser zoom"
          >
            {zoom}%
          </button>
          <Button
            variant="ghost"
            size="xs"
            onClick={handleZoomIn}
            disabled={zoom >= 200}
            title="Zoom avant"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>

          <div className="w-px h-5 bg-slate-300 mx-1" />

          {/* Download */}
          <Button
            variant="ghost"
            size="xs"
            onClick={handleDownload}
            title="Télécharger"
          >
            <Download className="w-4 h-4" />
          </Button>

          {/* Fullscreen */}
          <Button
            variant="ghost"
            size="xs"
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Quitter plein écran' : 'Plein écran'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </Button>

          {/* Collapse */}
          {collapsible && (
            <>
              <div className="w-px h-5 bg-slate-300 mx-1" />
              <Button
                variant="ghost"
                size="xs"
                onClick={() => setIsCollapsed(true)}
                title="Réduire"
              >
                <ChevronUp className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 relative bg-slate-100 overflow-hidden">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <motion.div
                className="w-12 h-12 mx-auto mb-3 rounded-full border-4 border-slate-200 border-t-blue-500"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
              <p className="text-sm text-slate-600">Chargement du PDF...</p>
            </div>
          </div>
        ) : pdfUrl ? (
          <iframe
            ref={iframeRef}
            src={`${pdfUrl}#zoom=${zoom}&page=${currentPage}`}
            className="w-full h-full border-0"
            title="PDF Preview"
            style={{
              transform: `scale(${zoom / 100})`,
              transformOrigin: 'top left',
              width: `${(100 / zoom) * 100}%`,
              height: `${(100 / zoom) * 100}%`,
            }}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-slate-500">Impossible de charger le PDF</p>
          </div>
        )}
      </div>

      {/* Footer - Navigation pages (optionnel) */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 p-3 border-t border-slate-200 bg-slate-50">
          <Button
            variant="ghost"
            size="xs"
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-xs text-slate-600">
            Page {currentPage} / {totalPages}
          </span>
          <Button
            variant="ghost"
            size="xs"
            onClick={handleNextPage}
            disabled={currentPage >= totalPages}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </motion.div>
  );
}

/**
 * PDFPreviewSkeleton - Composant de chargement
 */
export function PDFPreviewSkeleton({ className }) {
  return (
    <div
      className={clsx(
        'rounded-2xl border border-slate-200 bg-white overflow-hidden animate-pulse',
        className
      )}
    >
      <div className="h-12 bg-slate-100 border-b border-slate-200" />
      <div className="h-96 bg-slate-50 flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border-4 border-slate-200 border-t-blue-500 animate-spin" />
      </div>
    </div>
  );
}
