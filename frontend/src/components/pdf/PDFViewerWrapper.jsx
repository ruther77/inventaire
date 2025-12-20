/**
 * PDFViewerWrapper - Wrapper intelligent pour le preview PDF
 *
 * Détecte automatiquement la meilleure méthode de rendu:
 * - Navigateur moderne avec support PDF natif → iframe
 * - Besoin de highlighting → Canvas avec text layer
 * - Mobile → Version optimisée
 */

import { useState, useEffect } from 'react';
import PDFPreview from '../ui/PDFPreview.jsx';
import PDFPreviewAdvanced from '../ui/PDFPreviewAdvanced.jsx';

/**
 * Détecte si le navigateur supporte l'affichage PDF natif
 */
function detectPDFSupport() {
  // Chrome, Edge, Safari supportent l'iframe PDF
  const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
  const isEdge = /Edg/.test(navigator.userAgent);
  const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);

  return isChrome || isEdge || isSafari;
}

/**
 * Détecte si on est sur mobile
 */
function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * PDFViewerWrapper Component
 *
 * @param {File|string} file - Fichier PDF ou URL
 * @param {string} fileName - Nom du fichier
 * @param {boolean} enableHighlight - Activer le mode highlight (utilise Canvas)
 * @param {Function} onTextHighlight - Callback quand du texte est sélectionné
 * @param {Array} highlights - Liste des highlights à afficher
 * @param {boolean} collapsible - Permet de réduire
 * @param {boolean} defaultCollapsed - État initial
 * @param {string} className - Classes CSS
 */
export default function PDFViewerWrapper({
  file,
  fileName,
  enableHighlight = false,
  onTextHighlight,
  highlights = [],
  collapsible = true,
  defaultCollapsed = false,
  className,
}) {
  const [renderMode, setRenderMode] = useState('iframe');

  useEffect(() => {
    // Déterminer le meilleur mode de rendu
    const hasNativePDFSupport = detectPDFSupport();
    const needsAdvancedFeatures = enableHighlight || highlights.length > 0;
    const onMobile = isMobile();

    if (onMobile) {
      // Sur mobile, toujours utiliser iframe (plus léger)
      setRenderMode('iframe');
    } else if (needsAdvancedFeatures) {
      // Si besoin de highlighting, utiliser la version avancée
      setRenderMode('canvas');
    } else if (hasNativePDFSupport) {
      // Sinon, utiliser iframe natif
      setRenderMode('iframe');
    } else {
      // Fallback sur canvas
      setRenderMode('canvas');
    }
  }, [enableHighlight, highlights.length]);

  // Rendu conditionnel selon le mode
  if (renderMode === 'canvas') {
    return (
      <PDFPreviewAdvanced
        file={file}
        fileName={fileName}
        onTextHighlight={onTextHighlight}
        highlights={highlights}
        collapsible={collapsible}
        defaultCollapsed={defaultCollapsed}
        className={className}
      />
    );
  }

  // Par défaut, utiliser la version iframe (plus performante)
  return (
    <PDFPreview
      file={file}
      fileName={fileName}
      collapsible={collapsible}
      defaultCollapsed={defaultCollapsed}
      className={className}
    />
  );
}

/**
 * Hook pour gérer les highlights
 */
export function useHighlights() {
  const [highlights, setHighlights] = useState([]);

  const addHighlight = (highlight) => {
    setHighlights((prev) => [...prev, { ...highlight, id: Date.now() }]);
  };

  const removeHighlight = (id) => {
    setHighlights((prev) => prev.filter((h) => h.id !== id));
  };

  const clearHighlights = () => {
    setHighlights([]);
  };

  return {
    highlights,
    addHighlight,
    removeHighlight,
    clearHighlights,
  };
}
