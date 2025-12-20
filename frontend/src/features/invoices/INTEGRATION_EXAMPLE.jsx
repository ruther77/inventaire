/**
 * INTEGRATION_EXAMPLE.jsx
 *
 * Exemples d'intégration de la fonctionnalité PDF Preview
 * Ce fichier n'est pas utilisé dans l'app, c'est juste pour référence
 */

import { useState } from 'react';
import PDFPreview from '../../components/ui/PDFPreview.jsx';
import PDFPreviewAdvanced from '../../components/ui/PDFPreviewAdvanced.jsx';
import PDFViewerWrapper, { useHighlights } from '../../components/pdf/PDFViewerWrapper.jsx';
import InvoicePDFWorkspace from './components/InvoicePDFWorkspace.jsx';
import { usePDFFile, usePDFFileFromUpload } from '../../hooks/usePDFFile.js';

// ============================================================================
// EXEMPLE 1: Usage basique avec iframe
// ============================================================================

function Example1_BasicUsage() {
  const pdfFile = usePDFFile();

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      pdfFile.setPDFFile(file);
    }
  };

  return (
    <div className="p-6">
      <input type="file" accept=".pdf" onChange={handleFileSelect} />

      {pdfFile.hasFile && (
        <PDFPreview
          file={pdfFile.file}
          fileName={pdfFile.fileMetadata?.name || 'Document'}
          collapsible={true}
          defaultCollapsed={false}
          className="mt-4 h-[600px]"
        />
      )}
    </div>
  );
}

// ============================================================================
// EXEMPLE 2: Split-view avec éditeur
// ============================================================================

function Example2_SplitView() {
  const pdfFile = usePDFFile();
  const [lines, setLines] = useState([]);

  return (
    <div className="grid lg:grid-cols-12 gap-6 p-6">
      {/* PDF à gauche - 40% */}
      <div className="lg:col-span-5">
        <PDFPreview
          file={pdfFile.file}
          fileName="Facture.pdf"
          className="sticky top-6 h-[calc(100vh-200px)]"
        />
      </div>

      {/* Éditeur à droite - 60% */}
      <div className="lg:col-span-7">
        <div className="space-y-4">
          <h2 className="text-xl font-bold">Lignes de facture</h2>
          {lines.map((line, index) => (
            <div key={index} className="p-4 border rounded">
              <p>{line.nom}</p>
              <p>Prix: {line.prix_achat}€</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// EXEMPLE 3: Mode highlighting avancé
// ============================================================================

function Example3_AdvancedHighlighting() {
  const pdfFile = usePDFFile();
  const { highlights, addHighlight, removeHighlight, clearHighlights } = useHighlights();
  const [enableHighlight, setEnableHighlight] = useState(false);

  const handleTextHighlight = (highlightData) => {
    console.log('Text highlighted:', highlightData);
    addHighlight({
      text: highlightData.text,
      timestamp: highlightData.timestamp,
      color: 'yellow',
    });
  };

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center gap-4">
        <button
          onClick={() => setEnableHighlight(!enableHighlight)}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          {enableHighlight ? 'Désactiver' : 'Activer'} Highlighting
        </button>
        <button
          onClick={clearHighlights}
          className="px-4 py-2 bg-gray-500 text-white rounded"
        >
          Effacer highlights ({highlights.length})
        </button>
      </div>

      <PDFViewerWrapper
        file={pdfFile.file}
        fileName="Document.pdf"
        enableHighlight={enableHighlight}
        onTextHighlight={handleTextHighlight}
        highlights={highlights}
        className="h-[600px]"
      />

      {/* Liste des highlights */}
      <div className="mt-4 space-y-2">
        {highlights.map((highlight) => (
          <div
            key={highlight.id}
            className="p-3 border rounded bg-yellow-50 flex justify-between items-center"
          >
            <span className="text-sm">{highlight.text}</span>
            <button
              onClick={() => removeHighlight(highlight.id)}
              className="text-red-500 hover:text-red-700"
            >
              Supprimer
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// EXEMPLE 4: Workspace complet avec linking
// ============================================================================

function Example4_FullWorkspace() {
  const pdfFile = usePDFFileFromUpload();
  const [lines, setLines] = useState([
    { nom: 'Tomates cerises', prix_achat: 3.5, quantite: 10 },
    { nom: 'Salade verte', prix_achat: 1.2, quantite: 5 },
    { nom: 'Carottes bio', prix_achat: 2.8, quantite: 8 },
  ]);

  return (
    <div className="p-6">
      <InvoicePDFWorkspace
        pdfFile={pdfFile.file}
        pdfFileName={pdfFile.fileMetadata?.name || 'Facture'}
        lines={lines}
        onLinesChange={setLines}
        onDownloadCsv={() => console.log('Download CSV', lines)}
      />
    </div>
  );
}

// ============================================================================
// EXEMPLE 5: Détection automatique du mode de rendu
// ============================================================================

function Example5_AutoDetection() {
  const pdfFile = usePDFFile();

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-bold">Détection automatique</h2>
      <p className="text-gray-600">
        Le wrapper choisit automatiquement entre iframe et Canvas selon:
        - Le navigateur (support PDF natif)
        - Le device (mobile vs desktop)
        - Les fonctionnalités demandées (highlighting)
      </p>

      <PDFViewerWrapper
        file={pdfFile.file}
        fileName="Auto-detect.pdf"
        enableHighlight={false}  // Force iframe si supporté
        className="h-[600px]"
      />
    </div>
  );
}

// ============================================================================
// EXEMPLE 6: Gestion des métadonnées du fichier
// ============================================================================

function Example6_FileMetadata() {
  const pdfFile = usePDFFile();

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      pdfFile.setPDFFile(file);
    }
  };

  return (
    <div className="p-6">
      <input type="file" accept=".pdf" onChange={handleFileSelect} />

      {pdfFile.hasFile && (
        <div className="mt-4 p-4 border rounded">
          <h3 className="font-bold mb-2">Métadonnées du fichier</h3>
          <ul className="space-y-1 text-sm">
            <li>Nom: {pdfFile.fileMetadata?.name}</li>
            <li>Taille: {pdfFile.formatFileSize(pdfFile.fileMetadata?.size)}</li>
            <li>Type: {pdfFile.fileMetadata?.type}</li>
            <li>
              Modifié: {pdfFile.fileMetadata?.lastModified?.toLocaleDateString()}
            </li>
            <li>URL Blob: {pdfFile.fileUrl?.substring(0, 50)}...</li>
          </ul>

          <button
            onClick={pdfFile.clearPDFFile}
            className="mt-3 px-3 py-1 bg-red-500 text-white rounded text-sm"
          >
            Supprimer le fichier
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// EXEMPLE 7: Responsive behavior
// ============================================================================

function Example7_ResponsiveDesign() {
  const pdfFile = usePDFFile();
  const [lines, setLines] = useState([]);

  return (
    <div className="p-6">
      {/* Desktop: Split-view, Mobile: Stack vertical */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* PDF Preview */}
        <div className="lg:col-span-5">
          <PDFPreview
            file={pdfFile.file}
            fileName="Responsive.pdf"
            collapsible={true}           // Collapsible sur mobile
            defaultCollapsed={false}     // Expanded par défaut sur desktop
            className="lg:sticky lg:top-6 h-auto lg:h-[calc(100vh-200px)]"
          />
        </div>

        {/* Editor */}
        <div className="lg:col-span-7">
          <div className="p-4 border rounded">
            <h3 className="font-bold mb-3">Éditeur de lignes</h3>
            {/* Contenu de l'éditeur */}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// EXEMPLE 8: Contrôles personnalisés
// ============================================================================

function Example8_CustomControls() {
  const pdfFile = usePDFFile();
  const [zoom, setZoom] = useState(100);
  const [page, setPage] = useState(1);

  return (
    <div className="p-6 space-y-4">
      {/* Contrôles externes */}
      <div className="flex items-center gap-4 p-4 border rounded">
        <button
          onClick={() => setZoom(Math.max(50, zoom - 25))}
          className="px-3 py-1 bg-gray-200 rounded"
        >
          Zoom -
        </button>
        <span className="font-mono">{zoom}%</span>
        <button
          onClick={() => setZoom(Math.min(200, zoom + 25))}
          className="px-3 py-1 bg-gray-200 rounded"
        >
          Zoom +
        </button>

        <div className="w-px h-6 bg-gray-300 mx-2" />

        <button
          onClick={() => setPage(Math.max(1, page - 1))}
          className="px-3 py-1 bg-gray-200 rounded"
        >
          Page précédente
        </button>
        <span>Page {page}</span>
        <button
          onClick={() => setPage(page + 1)}
          className="px-3 py-1 bg-gray-200 rounded"
        >
          Page suivante
        </button>
      </div>

      {/* Le zoom et page sont gérés par le composant */}
      <PDFPreview
        file={pdfFile.file}
        fileName="Custom.pdf"
        className="h-[600px]"
      />
    </div>
  );
}

// ============================================================================
// EXPORTS (pour référence uniquement)
// ============================================================================

export {
  Example1_BasicUsage,
  Example2_SplitView,
  Example3_AdvancedHighlighting,
  Example4_FullWorkspace,
  Example5_AutoDetection,
  Example6_FileMetadata,
  Example7_ResponsiveDesign,
  Example8_CustomControls,
};
