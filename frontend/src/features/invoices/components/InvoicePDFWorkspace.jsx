/**
 * InvoicePDFWorkspace - Workspace d'édition avec PDF et highlighting
 *
 * Composant qui combine:
 * - Preview PDF avec highlighting
 * - Éditeur de lignes synchronisé
 * - Possibilité de highlight des montants/produits dans le PDF
 * - Sync entre PDF et lignes éditées
 */

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Highlighter, Link2, AlertCircle } from 'lucide-react';
import PDFViewerWrapper, { useHighlights } from '../../../components/pdf/PDFViewerWrapper.jsx';
import InvoiceLinesEditor from './InvoiceLinesEditor.jsx';
import Button from '../../../components/ui/Button.jsx';
import clsx from 'clsx';

/**
 * Mode d'interaction
 */
const MODES = {
  EDIT: 'edit',
  HIGHLIGHT: 'highlight',
  LINK: 'link',
};

/**
 * InvoicePDFWorkspace Component
 */
export default function InvoicePDFWorkspace({
  pdfFile,
  pdfFileName,
  lines = [],
  onLinesChange,
  onDownloadCsv,
  className,
}) {
  const [mode, setMode] = useState(MODES.EDIT);
  const [selectedLineIndex, setSelectedLineIndex] = useState(null);
  const { highlights, addHighlight, removeHighlight, clearHighlights } = useHighlights();

  // Gestion du highlight de texte dans le PDF
  const handleTextHighlight = useCallback(
    (highlightData) => {
      if (mode === MODES.HIGHLIGHT) {
        addHighlight({
          text: highlightData.text,
          timestamp: highlightData.timestamp,
          linkedToLine: selectedLineIndex,
        });
      }
    },
    [mode, selectedLineIndex, addHighlight]
  );

  // Lier un highlight à une ligne
  const handleLinkHighlightToLine = useCallback(
    (lineIndex) => {
      setSelectedLineIndex(lineIndex);
      setMode(MODES.LINK);
    },
    []
  );

  // Toggle mode highlight
  const toggleHighlightMode = () => {
    setMode((prev) => (prev === MODES.HIGHLIGHT ? MODES.EDIT : MODES.HIGHLIGHT));
  };

  return (
    <div className={clsx('grid lg:grid-cols-12 gap-6', className)}>
      {/* PDF Preview - 40% width */}
      <div className="lg:col-span-5">
        <PDFViewerWrapper
          file={pdfFile}
          fileName={pdfFileName}
          enableHighlight={mode === MODES.HIGHLIGHT}
          onTextHighlight={handleTextHighlight}
          highlights={highlights}
          collapsible={true}
          defaultCollapsed={false}
          className="sticky top-6 h-[calc(100vh-200px)]"
        />

        {/* Contrôles du mode */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-4 rounded-2xl border border-slate-200 bg-white"
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div
                className={clsx(
                  'p-2 rounded-lg',
                  mode === MODES.HIGHLIGHT ? 'bg-yellow-100' : 'bg-slate-100'
                )}
              >
                <Highlighter
                  className={clsx('w-4 h-4', mode === MODES.HIGHLIGHT ? 'text-yellow-600' : 'text-slate-400')}
                />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900">
                  {mode === MODES.HIGHLIGHT ? 'Mode Highlight actif' : 'Mode Édition'}
                </p>
                <p className="text-xs text-slate-500">
                  {mode === MODES.HIGHLIGHT
                    ? 'Sélectionnez du texte dans le PDF'
                    : 'Cliquez pour activer le highlighting'}
                </p>
              </div>
            </div>
            <Button
              variant={mode === MODES.HIGHLIGHT ? 'brand' : 'outline'}
              size="sm"
              onClick={toggleHighlightMode}
            >
              {mode === MODES.HIGHLIGHT ? 'Désactiver' : 'Activer'}
            </Button>
          </div>

          {/* Liste des highlights */}
          {highlights.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-200">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                Highlights ({highlights.length})
              </p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {highlights.map((highlight) => (
                  <div
                    key={highlight.id}
                    className="flex items-start gap-2 p-2 rounded-lg bg-yellow-50 border border-yellow-200"
                  >
                    <Highlighter className="w-3 h-3 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-700 truncate">{highlight.text}</p>
                      {highlight.linkedToLine !== null && (
                        <div className="flex items-center gap-1 mt-1">
                          <Link2 className="w-3 h-3 text-blue-500" />
                          <span className="text-[10px] text-blue-600">
                            Lié à la ligne {highlight.linkedToLine + 1}
                          </span>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => removeHighlight(highlight.id)}
                      className="text-xs text-slate-400 hover:text-slate-600"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
              <Button
                variant="ghost"
                size="xs"
                onClick={clearHighlights}
                className="mt-2 w-full"
              >
                Effacer tous les highlights
              </Button>
            </div>
          )}
        </motion.div>
      </div>

      {/* Editor - 60% width */}
      <div className="lg:col-span-7 space-y-6">
        <InvoiceLinesEditor
          lines={lines}
          onLinesChange={onLinesChange}
          onDownloadCsv={onDownloadCsv}
          onLineSelect={handleLinkHighlightToLine}
          selectedLineIndex={selectedLineIndex}
          highlightMode={mode === MODES.LINK}
        />

        {/* Info highlight mode */}
        {mode === MODES.LINK && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-2xl border border-blue-200 bg-blue-50"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900 mb-1">
                  Mode liaison actif
                </p>
                <p className="text-xs text-blue-700">
                  Sélectionnez du texte dans le PDF pour le lier à la ligne sélectionnée.
                  Cliquez sur une autre ligne ou annulez pour sortir de ce mode.
                </p>
              </div>
              <Button
                variant="ghost"
                size="xs"
                onClick={() => {
                  setMode(MODES.EDIT);
                  setSelectedLineIndex(null);
                }}
              >
                Annuler
              </Button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
