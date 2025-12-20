/**
 * ImportPage - Orchestrateur de l'import de factures
 *
 * Architecture modulaire:
 * - InvoiceUploadCard: Upload PDF/TXT et extraction
 * - InvoiceDocumentSelector: Selection des sous-documents
 * - InvoiceLinesEditor: Edition des lignes detectees
 * - InvoiceImportActions: Boutons d'import et resultats
 * - InvoiceHistoryPanel: Historique et conflits
 */

import { useEffect, useMemo, useState, Suspense, lazy } from 'react';
import { useSearchParams } from 'react-router-dom';
import Button from '../../components/ui/Button.jsx';
import FiltersDrawer from '../../components/ui/FiltersDrawer.jsx';
import Card from '../../components/ui/Card.jsx';
import PDFPreview from '../../components/ui/PDFPreview.jsx';
import {
  InvoiceUploadCard,
  InvoiceDocumentSelector,
  InvoiceLinesEditor,
  InvoiceImportActions,
  InvoiceHistoryPanel,
} from './components/index.js';
import { InvoiceProcessingCard } from './components/index.js';
import CardExpandable from '../../components/ui/CardExpandable.jsx';
import AIConfidenceBadge from '../../components/ui/AIConfidenceBadge.jsx';
import { useInvoiceZeroClick } from '../../hooks/useInvoiceImport.js';
import { usePDFFileFromUpload } from '../../hooks/usePDFFile.js';
import { InvoiceImportSkeleton, TableSkeleton } from '../../components/ui/PageSkeletons.jsx';

// Lazy load ImportSessionsView (historique rarement utilisé immédiatement)
const ImportSessionsView = lazy(() => import('./components/ImportSessionsView.jsx'));

// ============================================================================
// CONSTANTES
// ============================================================================

const SECTION_DEFINITIONS = [
  {
    id: 'workspace',
    label: 'Preparation',
    groups: [
      {
        title: 'Analyses',
        items: [
          {
            id: 'workspace.intake',
            label: 'Factures & import',
            description: "Selection des documents et parametrage de l'import.",
          },
        ],
      },
    ],
  },
  {
    id: 'history',
    label: 'Historique',
    groups: [
      {
        title: 'Suivi des imports',
        items: [
          {
            id: 'history.list',
            label: 'Factures traitees',
            description: 'Consultez les PDF stockes et rejouez un import facilement.',
          },
          {
            id: 'history.sessions',
            label: 'Historique par session',
            description: 'Voir les imports groupes par session de travail.',
          },
        ],
      },
    ],
  },
];

// ============================================================================
// UTILS
// ============================================================================

const csvEscape = (value) => {
  const text = value === null || value === undefined ? '' : String(value);
  return `"${text.replace(/"/g, '""')}"`;
};

const downloadLinesCsv = (items) => {
  if (!items.length) return;
  const headers = ['Nom', 'EAN', 'Produit_ID', 'Quantite', 'Prix_achat', 'TVA'];
  const rows = items.map((line) => [
    line.nom,
    line.codes ?? '',
    line.produit_id ?? '',
    line.quantite_recue ?? line.qte_init ?? 0,
    line.prix_achat ?? 0,
    line.tva ?? 0,
  ]);
  const body = [headers, ...rows].map((row) => row.map(csvEscape).join(',')).join('\n');
  const blob = new Blob([body], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'facture_preparee.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const normalizeDateForInput = (dateStr) => {
  if (!dateStr) return '';
  const match = dateStr.match(/^(\d{2})[-/](\d{2})[-/](\d{4})/);
  if (match) return `${match[3]}-${match[2]}-${match[1]}`;
  if (/^\d{4}-\d{2}-\d{2}/.test(dateStr)) return dateStr.slice(0, 10);
  return dateStr;
};

const normalizeLineItem = (item) => ({
  ...item,
  prix_vente: Number(item.prix_vente ?? 0),
});

const buildDocumentsFromExtraction = (payload) => {
  if (!payload) return [];
  const hasDocuments = Array.isArray(payload.documents) && payload.documents.length > 0;
  const source = hasDocuments
    ? payload.documents
    : [
        {
          invoice_id: payload.items?.[0]?.invoice_id ?? 'INV-001',
          facture_date: payload.items?.[0]?.facture_date ?? '',
          items: payload.items ?? [],
        },
      ];
  return source
    .filter((entry) => entry && Array.isArray(entry.items))
    .map((entry, index) => {
      const invoiceId = entry.invoice_id || `INV-${String(index + 1).padStart(3, '0')}`;
      return {
        invoice_id: invoiceId,
        facture_date: normalizeDateForInput(entry.facture_date ?? ''),
        items: (entry.items ?? []).map((line) => normalizeLineItem(line)),
        pdf_path: entry.pdf_path ?? '',
      };
    });
};

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

export default function ImportPage() {
  // State: Parametres globaux
  const [marginPercent, setMarginPercent] = useState(40);
  const [supplier, setSupplier] = useState('');
  const [invoiceDate, setInvoiceDate] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);

  // State: Documents et lignes
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);
  const [lines, setLines] = useState([]);
  const [processingSnapshot, setProcessingSnapshot] = useState({
    isProcessing: false,
    fileName: null,
    steps: [],
    attentionItems: [],
    summary: null,
  });

  // State: Resultats d'import (pour transmettre a l'historique)
  const [catalogSummary, setCatalogSummary] = useState(null);
  const zeroClickMutation = useInvoiceZeroClick();

  // State: PDF Preview
  const pdfFile = usePDFFileFromUpload();

  // Navigation par section
  const defaultPanel = SECTION_DEFINITIONS[0]?.groups?.[0]?.items?.[0]?.id ?? 'workspace.intake';
  const [searchParams, setSearchParams] = useSearchParams();
  const sectionParam = searchParams.get('section');
  const [activePanel, setActivePanel] = useState(sectionParam || defaultPanel);

  useEffect(() => {
    if (sectionParam && sectionParam !== activePanel) {
      setActivePanel(sectionParam);
    } else if (!sectionParam && activePanel !== defaultPanel) {
      setActivePanel(defaultPanel);
    }
  }, [sectionParam, activePanel, defaultPanel]);

  const sectionOptions = useMemo(() => {
    const options = [];
    SECTION_DEFINITIONS.forEach((section) => {
      section.groups?.forEach((group) => {
        group.items?.forEach((item) => {
          options.push({
            id: item.id,
            label: `${section.label} - ${item.label}`,
          });
        });
      });
    });
    return options;
  }, []);

  const handlePanelSelect = (panelId) => {
    const params = new URLSearchParams(searchParams);
    if (!panelId || panelId === defaultPanel) {
      params.delete('section');
    } else {
      params.set('section', panelId);
    }
    setSearchParams(params);
  };

  // ============================================================================
  // HANDLERS: Documents
  // ============================================================================

  const selectDocument = (invoiceId, sourceDocs = documents) => {
    const target = sourceDocs.find((doc) => doc.invoice_id === invoiceId);
    if (!target) return;
    setSelectedDocumentId(invoiceId);
    setLines(target.items);
    setInvoiceDate(target.facture_date || '');
  };

  const handleSelectAll = () => {
    const allItems = documents.flatMap((doc) => doc.items || []);
    setLines(allItems);
    setSelectedDocumentId('__all__');
    setInvoiceDate('');
  };

  const handleExtractionSuccess = (payload) => {
    const normalizedDocs = buildDocumentsFromExtraction(payload);
    setDocuments(normalizedDocs);
    const firstInvoice = normalizedDocs[0];
    const itemCount = firstInvoice?.items?.length || 0;
    const anomalies = (firstInvoice?.items || []).filter((item) => item.is_anomaly || item.price_anomaly);
    const newProducts = (firstInvoice?.items || []).filter((item) => !item.produit_id);

    setProcessingSnapshot((prev) => ({
      ...prev,
      isProcessing: true,
      steps: [
        { id: 'ocr', status: 'completed', result: `${itemCount} lignes extraites` },
        { id: 'matching', status: newProducts.length ? 'warning' : 'completed', result: `${itemCount - newProducts.length}/${itemCount} matchés` },
        { id: 'pricing', status: anomalies.length ? 'warning' : 'completed', result: `${anomalies.length} anomalies détectées` },
        { id: 'categorization', status: 'completed', result: 'Catégorisation auto' },
        { id: 'stock', status: 'processing', result: 'Mise à jour stock...' },
      ],
      attentionItems: [
        ...newProducts.slice(0, 1).map((item) => ({
          id: `new-${item.nom || item.codes || Math.random()}`,
          type: 'new_product',
          title: `"${item.nom || 'Produit inconnu'}" → Nouveau produit`,
          suggestion: item.suggestion || 'Similaire détecté dans le catalogue',
          actions: [
            { id: 'link', label: 'Lier à existant' },
            { id: 'create', label: 'Créer nouveau' },
          ],
        })),
        ...anomalies.slice(0, 1).map((item) => ({
          id: `price-${item.nom || Math.random()}`,
          type: 'price_anomaly',
          title: `"${item.nom || 'Ligne'}" → Prix suspect`,
          description: item.description || 'Écart détecté vs dernier achat',
          actions: [
            { id: 'accept', label: 'Accepter' },
            { id: 'reject', label: 'Contester' },
          ],
        })),
      ],
      summary: {
        totalHT: payload?.totaux?.ht || 0,
        tva: payload?.totaux?.tva || 0,
        totalTTC: payload?.totaux?.ttc || 0,
        lineCount: itemCount,
      },
      fileName: payload?.file_name || prev.fileName || 'Facture importée',
    }));
    if (normalizedDocs.length) {
      selectDocument(normalizedDocs[0].invoice_id, normalizedDocs);
    } else {
      setSelectedDocumentId(null);
      setLines([]);
      setInvoiceDate('');
    }
  };

  // ============================================================================
  // HANDLERS: Lines
  // ============================================================================

  const syncDocumentItems = (nextItems) => {
    if (!selectedDocumentId || selectedDocumentId === '__all__') return;
    setDocuments((prevDocs) =>
      prevDocs.map((doc) =>
        doc.invoice_id === selectedDocumentId ? { ...doc, items: nextItems } : doc,
      ),
    );
  };

  const handleLinesChange = (nextLines) => {
    setLines(nextLines);
    syncDocumentItems(nextLines);
  };

  const handleInvoiceDateChange = (value) => {
    setInvoiceDate(value);
    if (!selectedDocumentId || selectedDocumentId === '__all__') return;
    setDocuments((prevDocs) =>
      prevDocs.map((doc) =>
        doc.invoice_id === selectedDocumentId ? { ...doc, facture_date: value } : doc,
      ),
    );
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  const isHistoryPanel = activePanel.startsWith('history.');

    const renderWorkspacePanel = () => (
    <>
      {/* Selection des documents detectes */}
      <InvoiceDocumentSelector
        documents={documents}
        selectedDocumentId={selectedDocumentId}
        onSelectDocument={(id) => selectDocument(id)}
        onSelectAll={handleSelectAll}
      />

      {/* Upload et extraction */}
      <InvoiceUploadCard
        marginPercent={marginPercent}
        onMarginChange={setMarginPercent}
        supplier={supplier}
        onExtractionSuccess={handleExtractionSuccess}
        onProcessingSnapshot={setProcessingSnapshot}
        onFileUpload={(file) => pdfFile.setPDFFile(file)}
      />

      {/* Split View: PDF Preview (left) + Editor (right) */}
      {pdfFile.hasFile && lines.length > 0 && (
        <div className="grid lg:grid-cols-12 gap-6">
          {/* PDF Preview - 40% width on desktop, full width on mobile */}
          <div className="lg:col-span-5">
            <PDFPreview
              file={pdfFile.file}
              fileName={pdfFile.fileMetadata?.name || 'Facture'}
              collapsible={true}
              defaultCollapsed={false}
              className="sticky top-6 h-[calc(100vh-200px)]"
            />
          </div>

          {/* Editor - 60% width on desktop, full width on mobile */}
          <div className="lg:col-span-7 space-y-6">
            {/* Carte de traitement en temps réel */}
            <InvoiceProcessingCard
              isProcessing={processingSnapshot.isProcessing}
              fileName={processingSnapshot.fileName}
              steps={processingSnapshot.steps}
              attentionItems={processingSnapshot.attentionItems}
              summary={processingSnapshot.summary}
              onValidate={() => setProcessingSnapshot((prev) => ({ ...prev, isProcessing: false }))}
              onCancel={() => setProcessingSnapshot((prev) => ({ ...prev, isProcessing: false }))}
            />

            {/* Editeur de lignes */}
            <InvoiceLinesEditor
              lines={lines}
              onLinesChange={handleLinesChange}
              onDownloadCsv={() => downloadLinesCsv(lines)}
            />

            {/* Actions d'import */}
            <InvoiceImportActions
              lines={lines}
              supplier={supplier}
              onSupplierChange={setSupplier}
              invoiceDate={invoiceDate}
              onInvoiceDateChange={handleInvoiceDateChange}
              onImportSuccess={() => setCatalogSummary(null)}
            />
          </div>
        </div>
      )}

      {/* Fallback: Afficher les cartes normalement si pas de PDF ou pas de lignes */}
      {(!pdfFile.hasFile || lines.length === 0) && (
        <>
          {/* Carte de traitement en temps réel */}
          <InvoiceProcessingCard
            isProcessing={processingSnapshot.isProcessing}
            fileName={processingSnapshot.fileName}
            steps={processingSnapshot.steps}
            attentionItems={processingSnapshot.attentionItems}
            summary={processingSnapshot.summary}
            onValidate={() => setProcessingSnapshot((prev) => ({ ...prev, isProcessing: false }))}
            onCancel={() => setProcessingSnapshot((prev) => ({ ...prev, isProcessing: false }))}
          />

          {/* Editeur de lignes */}
          <InvoiceLinesEditor
            lines={lines}
            onLinesChange={handleLinesChange}
            onDownloadCsv={() => downloadLinesCsv(lines)}
          />

          {/* Actions d'import */}
          <InvoiceImportActions
            lines={lines}
            supplier={supplier}
            onSupplierChange={setSupplier}
            invoiceDate={invoiceDate}
            onInvoiceDateChange={handleInvoiceDateChange}
            onImportSuccess={() => setCatalogSummary(null)}
          />
        </>
      )}
    </>
  );

  const renderHistoryPanel = () => (
    <InvoiceHistoryPanel supplier={supplier} catalogSummary={catalogSummary} />
  );

  const renderSessionsPanel = () => (
    <Suspense fallback={<TableSkeleton rows={8} columns={5} />}>
      <ImportSessionsView />
    </Suspense>
  );

  const renderPanel = () => {
    switch (activePanel) {
      case 'workspace.intake':
        return renderWorkspacePanel();
      case 'history.list':
        return renderHistoryPanel();
      case 'history.sessions':
        return renderSessionsPanel();
      default:
        return (
          <Card>
            <p className="text-sm text-slate-500">
              Selectionnez une section pour afficher son contenu.
            </p>
          </Card>
        );
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <CardExpandable
        title="Flux Zero-Click"
        subtitle="Scénario 3.2"
        summary="Extraction → Lignes → Import stock/finance"
        variant="info"
        defaultExpanded
      >
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
          <AIConfidenceBadge
            confidence={0.88}
            label="Auto-extraction"
            variant="pill"
            size="sm"
            explanation="OCR + mapping catalogue"
          />
          <AIConfidenceBadge
            confidence={0.75}
            label="Catégorisation"
            variant="pill"
            size="sm"
            explanation="Keyword analyzer"
          />
          <AIConfidenceBadge
            confidence={0.8}
            label="Stock"
            variant="pill"
            size="sm"
            explanation="Mouvements + prix"
          />
          <div className="ml-auto flex gap-2">
            <Button size="sm" variant="outline" onClick={() => handlePanelSelect('workspace.intake')}>
              Aller à l'import
            </Button>
            <Button size="sm" variant="brand" onClick={() => setDrawerOpen(true)}>
              Vérifier paramètres
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={processingSnapshot.isProcessing || zeroClickMutation.isPending}
              onClick={() => {
                const file = processingSnapshot?.file;
                if (!file) return;
                zeroClickMutation.mutate({
                  file,
                  supplierHint: supplier || undefined,
                  marginPercent,
                  autoConfirm: true,
                });
              }}
            >
              {zeroClickMutation.isPending ? 'Import...' : 'Zero-Click direct'}
            </Button>
          </div>
        </div>
      </CardExpandable>

      {/* Bouton drawer */}
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="outline" size="sm" onClick={() => setDrawerOpen(true)}>
          Ouvrir le panneau avance
        </Button>
      </div>

      {/* Drawer filtres */}
      <FiltersDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} title="Filtres facture">
        <div className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Fournisseur</p>
            <p className="text-lg font-semibold text-slate-900">{supplier || 'non selectionne'}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Date de facture</p>
            <p className="text-lg font-semibold text-slate-900">{invoiceDate || 'non renseignee'}</p>
          </div>
        </div>
      </FiltersDrawer>

      {/* Selecteur mobile */}
      <div className="lg:hidden">
        <label
          className="text-xs uppercase tracking-[0.3em] text-slate-400"
          htmlFor="mobile-import-section"
        >
          Section
        </label>
        <select
          id="mobile-import-section"
          value={activePanel}
          onChange={(event) => handlePanelSelect(event.target.value)}
          className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-brand-400 focus:outline-none"
        >
          {sectionOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Contenu du panel actif */}
      {renderPanel()}
    </div>
  );
}
