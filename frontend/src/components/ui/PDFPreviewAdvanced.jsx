/**
 * PDFPreviewAdvanced - Composant d'aperçu PDF avec Canvas
 *
 * Version alternative qui utilise Canvas pour un meilleur contrôle
 * et la possibilité de highlight du texte
 *
 * Fonctionnalités:
 * - Rendu PDF via Canvas
 * - Text selection et highlight
 * - Zoom fluide
 * - Navigation pages
 * - Annotations possibles
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  RotateCw,
  FileText,
  Highlighter,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import clsx from 'clsx';
import Button from './Button.jsx';

/**
 * PDFPreviewAdvanced Component
 * Cette version utilise Canvas pour un rendu personnalisé
 * et permet le highlight de texte
 */
export default function PDFPreviewAdvanced({
  file,
  fileName,
  onTextHighlight,
  highlights = [],
  collapsible = true,
  defaultCollapsed = false,
  className,
}) {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [scale, setScale] = useState(1.0);
  const [rotation, setRotation] = useState(0);
  const [selectedText, setSelectedText] = useState('');
  const canvasRef = useRef(null);
  const textLayerRef = useRef(null);
  const containerRef = useRef(null);

  // Créer l'URL blob du PDF
  useEffect(() => {
    if (!file) {
      setPdfUrl(null);
      return;
    }

    if (typeof file === 'string') {
      setPdfUrl(file);
      return;
    }

    if (file instanceof File || file instanceof Blob) {
      const url = URL.createObjectURL(file);
      setPdfUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [file]);

  // Gestion de la sélection de texte
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    const text = selection?.toString();

    if (text && text.trim()) {
      setSelectedText(text);
      if (onTextHighlight) {
        onTextHighlight({
          text,
          timestamp: Date.now(),
        });
      }
    }
  }, [onTextHighlight]);

  // Gestion du zoom
  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.25, 3.0));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.25, 0.5));
  };

  const handleResetZoom = () => {
    setScale(1.0);
  };

  // Gestion de la rotation
  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  // Highlight un mot/phrase
  const highlightText = useCallback((text) => {
    if (!textLayerRef.current) return;

    // Logique simplifiée - dans un cas réel, utiliser PDF.js text layer
    const textLayer = textLayerRef.current;
    const content = textLayer.textContent || '';

    if (content.includes(text)) {
      // Créer un marqueur visuel
      const marker = document.createElement('div');
      marker.className = 'absolute bg-yellow-200/40 pointer-events-none';
      marker.textContent = text;
      textLayer.appendChild(marker);
    }
  }, []);

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
        className
      )}
    >
      {/* Header avec contrôles */}
      <div className="flex items-center justify-between gap-3 p-3 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <span className="text-sm font-medium text-slate-900 truncate">
            {fileName || 'Aperçu PDF'}
          </span>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Zoom */}
          <Button variant="ghost" size="xs" onClick={handleZoomOut} disabled={scale <= 0.5}>
            <ZoomOut className="w-4 h-4" />
          </Button>
          <button
            onClick={handleResetZoom}
            className="px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-900"
          >
            {Math.round(scale * 100)}%
          </button>
          <Button variant="ghost" size="xs" onClick={handleZoomIn} disabled={scale >= 3.0}>
            <ZoomIn className="w-4 h-4" />
          </Button>

          <div className="w-px h-5 bg-slate-300 mx-1" />

          {/* Rotation */}
          <Button variant="ghost" size="xs" onClick={handleRotate} title="Rotation 90°">
            <RotateCw className="w-4 h-4" />
          </Button>

          {/* Highlight mode */}
          <Button
            variant="ghost"
            size="xs"
            title="Mode highlight"
            className={selectedText ? 'text-yellow-600' : ''}
          >
            <Highlighter className="w-4 h-4" />
          </Button>

          {collapsible && (
            <>
              <div className="w-px h-5 bg-slate-300 mx-1" />
              <Button variant="ghost" size="xs" onClick={() => setIsCollapsed(true)}>
                <ChevronUp className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </div>

      {/* PDF Viewer avec text layer */}
      <div
        className="flex-1 relative bg-slate-100 overflow-auto"
        onMouseUp={handleTextSelection}
      >
        {pdfUrl ? (
          <div className="relative w-full h-full flex items-start justify-center p-4">
            <div
              style={{
                transform: `scale(${scale}) rotate(${rotation}deg)`,
                transformOrigin: 'top center',
                transition: 'transform 0.2s ease-out',
              }}
              className="relative bg-white shadow-lg"
            >
              {/* Iframe pour le PDF */}
              <iframe
                src={pdfUrl}
                className="w-full h-full border-0"
                style={{ minHeight: '600px', minWidth: '400px' }}
                title="PDF Viewer"
              />

              {/* Text overlay pour sélection */}
              <div
                ref={textLayerRef}
                className="absolute inset-0 pointer-events-none"
                style={{ userSelect: 'text' }}
              />

              {/* Highlights overlay */}
              {highlights.map((highlight, index) => (
                <div
                  key={index}
                  className="absolute bg-yellow-200/40 pointer-events-none"
                  style={{
                    left: `${highlight.x}%`,
                    top: `${highlight.y}%`,
                    width: `${highlight.width}%`,
                    height: `${highlight.height}%`,
                  }}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-slate-500">Chargement du PDF...</p>
          </div>
        )}
      </div>

      {/* Footer - Selection text */}
      {selectedText && (
        <div className="p-3 border-t border-slate-200 bg-yellow-50">
          <div className="flex items-start gap-2">
            <Highlighter className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-yellow-900 mb-1">Texte sélectionné:</p>
              <p className="text-xs text-yellow-800 truncate">{selectedText}</p>
            </div>
            <Button
              variant="ghost"
              size="xs"
              onClick={() => setSelectedText('')}
            >
              Effacer
            </Button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
