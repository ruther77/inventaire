import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import FiltersDrawer from '../../components/ui/FiltersDrawer.jsx';
import {
  useInvoiceExtraction,
  useInvoiceFileExtraction,
  useInvoiceImport,
  useInvoiceCatalogImport,
  useInvoiceHistory,
} from '../../hooks/useInvoiceImport.js';
import { downloadInvoiceFile } from '../../api/client.js';

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

const SECTION_DEFINITIONS = [
  {
    id: 'workspace',
    label: 'Préparation',
    groups: [
      {
        title: 'Analyses',
        items: [
          {
            id: 'workspace.intake',
            label: 'Factures & import',
            description: 'Sélection des documents et paramétrage de l’import.',
          },
        ],
      },
      {
        title: 'Catalogue',
        items: [
          {
            id: 'workspace.catalog',
            label: 'Mises à jour & rejets',
            description: 'Synchronisation catalogue et export des lignes conflictuelles.',
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
            label: 'Factures traitées',
            description: 'Consultez les PDF stockés et rejouez un import facilement.',
          },
        ],
      },
    ],
  },
];

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

const extractErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) return detail.join(', ');
  if (typeof detail === 'string' && detail.trim()) return detail;
  return fallback;
};

export default function ImportPage() {
  const [marginPercent, setMarginPercent] = useState(40);
  const [rawText, setRawText] = useState('');
  const [lines, setLines] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);
  const [supplier, setSupplier] = useState('');
  const [movementType, setMovementType] = useState('ENTREE');
  const [username, setUsername] = useState('');
  const [summary, setSummary] = useState(null);
  const [catalogSummary, setCatalogSummary] = useState(null);
  const [initializeStock, setInitializeStock] = useState(false);
  const [invoiceDate, setInvoiceDate] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [downloadingInvoice, setDownloadingInvoice] = useState(null);
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
            label: `${section.label} · ${item.label}`,
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

  const extractTextMutation = useInvoiceExtraction();
  const extractFileMutation = useInvoiceFileExtraction();
  const importMutation = useInvoiceImport();
  const catalogImportMutation = useInvoiceCatalogImport();
  const historyQuery = useInvoiceHistory({ supplier: supplier || undefined, limit: 25 });
  const historyItems = historyQuery.data ?? [];

  const normalizeLineItem = (item) => ({
    ...item,
    prix_vente: Number(item.prix_vente ?? 0),
  });

  const buildDocumentsFromExtraction = (payload) => {
    if (!payload) {
      return [];
    }
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
          facture_date: entry.facture_date ?? '',
          items: (entry.items ?? []).map((line) => normalizeLineItem(line)),
          pdf_path: entry.pdf_path ?? '',
        };
      });
  };

  const handleDownloadInvoicePdf = async (invoiceId) => {
    if (!invoiceId) return;
    try {
      setDownloadingInvoice(invoiceId);
      const response = await downloadInvoiceFile(invoiceId);
      const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${invoiceId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Téléchargement impossible');
    } finally {
      setDownloadingInvoice(null);
    }
  };

  const selectDocument = (invoiceId, sourceDocs = documents) => {
    const target = sourceDocs.find((doc) => doc.invoice_id === invoiceId);
    if (!target) {
      return;
    }
    setSelectedDocumentId(invoiceId);
    setLines(target.items);
    setInvoiceDate(target.facture_date || '');
  };

  const applyExtractionResult = (payload) => {
    const normalizedDocs = buildDocumentsFromExtraction(payload);
    setDocuments(normalizedDocs);
    if (normalizedDocs.length) {
      selectDocument(normalizedDocs[0].invoice_id, normalizedDocs);
    } else {
      setSelectedDocumentId(null);
      setLines([]);
      setInvoiceDate('');
    }
    setErrorMessage('');
    historyQuery?.refetch?.();
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    extractFileMutation.mutate(
      { file, marginPercent, supplierHint: supplier || null },
      {
        onSuccess: (data) => {
          applyExtractionResult(data);
        },
      },
    );
  };

  const handleTextExtract = () => {
    if (!rawText.trim()) return;
    extractTextMutation.mutate(
      { text: rawText, marginPercent, supplierHint: supplier || null },
      {
        onSuccess: (data) => {
          applyExtractionResult(data);
        },
      },
    );
  };

  const syncDocumentItems = (nextItems) => {
    if (!selectedDocumentId) return;
    setDocuments((prevDocs) =>
      prevDocs.map((doc) => (doc.invoice_id === selectedDocumentId ? { ...doc, items: nextItems } : doc)),
    );
  };

  const handleLineFieldChange = (index, field, value) => {
    setLines((prev) => {
      const next = prev.map((line, idx) =>
        idx === index
          ? {
              ...line,
              [field]: ['prix_achat', 'prix_vente', 'tva', 'qte_init', 'quantite_recue', 'produit_id'].includes(field)
                ? parseFloat(value) || 0
                : value,
            }
          : line,
      );
      syncDocumentItems(next);
      return next;
    });
  };

  const handleRemoveLine = (index) => {
    setLines((prev) => {
      const next = prev.filter((_, idx) => idx !== index);
      syncDocumentItems(next);
      return next;
    });
  };

  const normaliseInvoiceDate = () => (invoiceDate ? invoiceDate : undefined);

  const handleInvoiceDateChange = (value) => {
    setInvoiceDate(value);
    if (!selectedDocumentId) return;
    setDocuments((prevDocs) =>
      prevDocs.map((doc) => (doc.invoice_id === selectedDocumentId ? { ...doc, facture_date: value } : doc)),
    );
  };

  const handleImport = () => {
    if (!lines.length) return;
    importMutation.mutate(
      {
        lines,
        supplier,
        movementType,
        username,
        invoiceDate: normaliseInvoiceDate(),
      },
      {
        onSuccess: (data) => {
          setSummary(data);
          setErrorMessage('');
          historyQuery?.refetch?.();
        },
        onError: (error) => setErrorMessage(extractErrorMessage(error, 'Import impossible')),
      },
    );
  };

  const handleCatalogImport = () => {
    if (!lines.length) return;
    catalogImportMutation.mutate(
      {
        lines,
        supplier,
        username,
        initializeStock,
        invoiceDate: normaliseInvoiceDate(),
      },
      {
        onSuccess: (data) => {
          setCatalogSummary(data);
          setErrorMessage('');
          historyQuery?.refetch?.();
        },
        onError: (error) => setErrorMessage(extractErrorMessage(error, 'Import catalogue impossible')),
      },
    );
  };

  const totals = useMemo(() => {
    if (!lines.length) {
      return { qty: 0, total: 0, catalog: 0, vat: 0 };
    }
    return lines.reduce(
      (acc, line) => {
        const qty = Number(line.quantite_recue ?? line.qte_init ?? 0);
        const purchase = Number(line.prix_achat ?? 0);
        const amount = purchase * qty;
        const catalogUnit = Number(line.prix_achat_catalogue ?? purchase);
        const vatPct = Number(line.tva ?? 0);
        return {
          qty: acc.qty + qty,
          total: acc.total + amount,
          catalog: acc.catalog + catalogUnit * qty,
          vat: acc.vat + amount * (vatPct / 100),
        };
      },
      { qty: 0, total: 0, catalog: 0, vat: 0 },
    );
  }, [lines]);

  const renderPanel = () => {
    switch (activePanel) {


      case 'workspace.intake':
        return (
          <>
            <Card className="flex flex-col gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-slate-400">factures détectées</p>
                <h3 className="text-lg font-semibold text-slate-900">Sélectionnez la facture à traiter</h3>
              </div>
              {documents.length ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {documents.map((doc) => {
                    const isActive = doc.invoice_id === selectedDocumentId;
                    return (
                      <button
                        type="button"
                        key={doc.invoice_id}
                        onClick={() => selectDocument(doc.invoice_id)}
                        className={`flex flex-col rounded-2xl border px-4 py-3 text-left transition ${
                          isActive ? 'border-brand-400 bg-brand-50 shadow-sm' : 'border-slate-200 bg-white'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <p className="font-semibold text-slate-900">Facture {doc.invoice_id}</p>
                          <span className="text-xs text-slate-500">{doc.items.length} lignes</span>
                        </div>
                        <p className="text-sm text-slate-600">Date : {doc.facture_date || 'non renseignée'}</p>
                        {doc.pdf_path && (
                          <p className="text-xs text-slate-500 break-words">Stockée : {doc.pdf_path}</p>
                        )}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-slate-500">
                  Analysez une facture (PDF/TXT) pour afficher ici les sous-documents détectés.
                </p>
              )}
            </Card>

            <Card className="flex flex-col gap-6">
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-slate-400">import facture</p>
                <h2 className="text-2xl font-semibold text-slate-900">Automatiser la réception</h2>
                <p className="text-sm text-slate-500">
                  Téléversez une facture Metro, corrigez les lignes détectées et créez automatiquement les mouvements
                  d&apos;entrée.
                </p>
              </div>
              <div className="grid gap-4 lg:grid-cols-3">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Marge cible (%)
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={150}
                    value={marginPercent}
                    onChange={(event) => setMarginPercent(Number(event.target.value))}
                    className="mt-2 w-full"
                  />
                  <p className="text-sm text-slate-600">{marginPercent}%</p>
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Upload PDF / DOCX / TXT
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleFileChange}
                    className="mt-2 block w-full rounded-2xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-600"
                    disabled={extractFileMutation.isLoading}
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Ou collez le texte détecté
                  </label>
                  <textarea
                    rows={4}
                    value={rawText}
                    onChange={(event) => setRawText(event.target.value)}
                    className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-700 focus:border-brand-400 focus:outline-none"
                    placeholder="Collez la section produits de la facture…"
                  />
                  <Button
                    variant="brand"
                    size="sm"
                    className="mt-2"
                    onClick={handleTextExtract}
                    disabled={extractTextMutation.isLoading}
                  >
                    Analyser ce texte
                  </Button>
                </div>
              </div>
            </Card>

            <Card className="flex flex-col gap-4">
              <div className="grid gap-4 md:grid-cols-4">
                <Metric label="Articles analysés" value={lines.length} />
                <Metric label="Unités" value={numberFormatter.format(totals.qty)} />
                <Metric label="Montant HT" value={`${numberFormatter.format(totals.total)} €`} />
                <Metric label="TVA estimée" value={`${numberFormatter.format(totals.vat)} €`} />
                <Metric
                  label="Valeur catalogue"
                  value={`${numberFormatter.format(totals.catalog)} €`}
                  className="md:col-span-2"
                />
                <Metric
                  label="Écart vs catalogue"
                  value={`${numberFormatter.format(totals.total - totals.catalog)} €`}
                  className="md:col-span-2"
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <Button variant="ghost" size="sm" onClick={() => downloadLinesCsv(lines)} disabled={!lines.length}>
                  Télécharger la sélection
                </Button>
              </div>
            </Card>

            <Card className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] text-slate-400">lignes détectées</p>
                  <h3 className="text-xl font-semibold text-slate-900">{lines.length} articles</h3>
                </div>
                <div className="flex flex-wrap gap-2 text-sm text-slate-600">
                  <p>Unités : {numberFormatter.format(totals.qty)}</p>
                  <p>Montant HT : {numberFormatter.format(totals.total)} €</p>
                </div>
                {lines.length > 0 && (
                  <Button variant="ghost" size="sm" onClick={() => setLines([])}>
                    Effacer
                  </Button>
                )}
              </div>
              {lines.length === 0 ? (
                <p className="text-sm text-slate-500">Analysez une facture pour afficher les lignes ici.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-100 text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                        <th className="px-3 py-2">Produit</th>
                        <th className="px-3 py-2">EAN</th>
                        <th className="px-3 py-2">Qté</th>
                        <th className="px-3 py-2">Reçue</th>
                        <th className="px-3 py-2">Prix achat</th>
                        <th className="px-3 py-2">TVA</th>
                        <th className="px-3 py-2">Produit ID</th>
                        <th className="px-3 py-2" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {lines.map((line, index) => (
                        <tr key={`${line.nom}-${index}`}>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              value={line.nom ?? ''}
                              onChange={(event) => handleLineFieldChange(index, 'nom', event.target.value)}
                              className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              value={line.codes ?? ''}
                              onChange={(event) => handleLineFieldChange(index, 'codes', event.target.value)}
                              className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              value={line.quantite ?? ''}
                              onChange={(event) => handleLineFieldChange(index, 'quantite', event.target.value)}
                              className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              value={line.quantite_recue ?? line.qte_init ?? ''}
                              onChange={(event) => handleLineFieldChange(index, 'quantite_recue', event.target.value)}
                              className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              step="0.01"
                              value={line.prix_achat ?? ''}
                              onChange={(event) => handleLineFieldChange(index, 'prix_achat', event.target.value)}
                              className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="number"
                              step="0.01"
                              value={line.tva ?? ''}
                              onChange={(event) => handleLineFieldChange(index, 'tva', event.target.value)}
                              className="w-full rounded-xl border border-slate-200 px-3 py-1 focus-border-brand-400 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              value={line.produit_id ?? ''}
                              onChange={(event) => handleLineFieldChange(index, 'produit_id', event.target.value)}
                              className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2 text-right">
                            <Button variant="ghost" size="xs" onClick={() => duplicateLine(index)}>
                              Dupliquer
                            </Button>
                            <Button
                              variant="ghost"
                              size="xs"
                              className="text-rose-600"
                              onClick={() => removeLine(index)}
                            >
                              Supprimer
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            <Card className="flex flex-col gap-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-600">
                  Fournisseur
                  <input
                    type="text"
                    value={supplier}
                    onChange={(event) => setSupplier(event.target.value)}
                    className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  />
                </label>
                <label className="text-sm text-slate-600">
                  Date facture
                  <input
                    type="date"
                    value={invoiceDate}
                    onChange={(event) => handleInvoiceDateChange(event.target.value)}
                    className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  />
                </label>
                <label className="text-sm text-slate-600">
                  Type de mouvement
                  <select
                    value={movementType}
                    onChange={(event) => setMovementType(event.target.value)}
                    className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  >
                    <option value="ENTREE">Entrée</option>
                    <option value="TRANSFERT">Transfert</option>
                  </select>
                </label>
                <label className="text-sm text-slate-600">
                  Utilisateur
                  <input
                    type="text"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                    placeholder="opérateur"
                  />
                </label>
              </div>
              <Button
                variant="brand"
                size="lg"
                onClick={handleImport}
                disabled={!lines.length || importMutation.isLoading}
              >
                Créer les mouvements
              </Button>
              {summary && (
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-700">
                  <p>Mouvements créés : {summary.movements_created}</p>
                  <p>Quantité totale : {summary.quantity_total}</p>
                  {summary.errors?.length ? (
                    <ul className="mt-2 list-disc pl-4 text-rose-600">
                      {summary.errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-emerald-600">Import réussi.</p>
                  )}
                </div>
              )}
            </Card>
          </>
        );
      case 'workspace.catalog':
        return (
          <>
            <Card className="flex flex-col gap-4">
              <h3 className="text-lg font-semibold text-slate-900">Mettre à jour le catalogue</h3>
              <p className="text-sm text-slate-600">
                Ajoute ou met à jour les produits existants, initialise le stock et historise les prix d&apos;achat.
              </p>
              <Button
                variant="brand"
                onClick={handleCatalogImport}
                disabled={!lines.length || catalogImportMutation.isLoading}
              >
                Importer dans le catalogue
              </Button>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-brand-500 focus:ring-brand-400"
                  checked={initializeStock}
                  onChange={(event) => setInitializeStock(event.target.checked)}
                />
                Alimenter automatiquement le stock avec les quantités détectées
              </label>
              {catalogSummary && (
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-700">
                  <div className="grid gap-4 md:grid-cols-3">
                    <Metric label="Lignes traitées" value={catalogSummary.rows_processed} />
                    <Metric label="Créées" value={catalogSummary.created} />
                    <Metric label="Mises à jour" value={catalogSummary.updated} />
                  </div>
                  <div className="mt-3 grid gap-4 md:grid-cols-3">
                    <Metric label="Stocks init" value={catalogSummary.stock_initialized} />
                    <Metric label="Codes ajoutés" value={catalogSummary.barcode?.added ?? 0} />
                    <Metric label="Conflits codes" value={catalogSummary.barcode?.conflicts ?? 0} />
                  </div>
                  {catalogSummary.errors?.length ? (
                    <ul className="mt-3 list-disc pl-5 text-rose-600">
                      {catalogSummary.errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-3 text-emerald-600">Catalogue synchronisé.</p>
                  )}
                </div>
              )}
            </Card>

            <Card className="flex flex-col gap-4">
              <h3 className="text-lg font-semibold text-slate-900">Conflits & rejets</h3>
              <p className="text-sm text-slate-600">
                Téléchargez les lignes rejetées pour corriger les anomalies (codes-barres en double, références
                absentes, etc.).
              </p>
              {catalogSummary?.rejected_rows?.length ? (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                  <p className="font-medium">
                    {catalogSummary.rejected_rows.length} ligne(s) rejetée(s). Téléchargez le fichier pour les corriger
                    manuellement.
                  </p>
                  {catalogSummary.rejected_csv && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      onClick={() => {
                        const blob = new Blob([catalogSummary.rejected_csv], { type: 'text/csv;charset=utf-8;' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = 'lignes_rejetees.csv';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                      }}
                    >
                      Télécharger les lignes rejetées
                    </Button>
                  )}
                </div>
              ) : (
                <p className="text-sm text-slate-500">Aucune ligne rejetée pour le moment.</p>
              )}
            </Card>
          </>
        );
      case 'history.list':
        return (
          <Card className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Historique</p>
                <h3 className="text-lg font-semibold text-slate-900">Factures importées</h3>
              </div>
              <Button variant="ghost" size="sm" onClick={() => historyQuery?.refetch?.()}>
                Actualiser
              </Button>
            </div>
            {historyQuery.isLoading ? (
              <p className="text-sm text-slate-500">Chargement…</p>
            ) : historyQuery.isError ? (
              <p className="text-sm text-rose-600">Impossible de charger l'historique.</p>
            ) : historyItems.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-widest text-slate-500">
                    <tr>
                      <th className="px-3 py-2 text-left">Facture</th>
                      <th className="px-3 py-2 text-left">Fournisseur</th>
                      <th className="px-3 py-2 text-left">Date</th>
                      <th className="px-3 py-2 text-right">Lignes</th>
                      <th className="px-3 py-2 text-right">PDF</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {historyItems.map((item) => (
                      <tr key={item.invoice_id}>
                        <td className="px-3 py-2 font-medium text-slate-900">{item.invoice_id}</td>
                        <td className="px-3 py-2 text-slate-600">{item.supplier || '—'}</td>
                        <td className="px-3 py-2 text-slate-600">{item.facture_date || '—'}</td>
                        <td className="px-3 py-2 text-right text-slate-600">{item.line_count}</td>
                        <td className="px-3 py-2 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownloadInvoicePdf(item.invoice_id)}
                            disabled={downloadingInvoice === item.invoice_id}
                          >
                            Télécharger
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Aucune facture importée pour l'instant.</p>
            )}
          </Card>
        );
      default:
        return (
          <Card>
            <p className="text-sm text-slate-500">Sélectionnez une section pour afficher son contenu.</p>
          </Card>
        );
    }
  };

  const isHistoryPanel = activePanel.startsWith('history.');

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="outline" size="sm" onClick={() => setDrawerOpen(true)}>
          Ouvrir le panneau avancé
        </Button>
      </div>
      <FiltersDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} title="Filtres facture">
        <div className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Fournisseur</p>
            <p className="text-lg font-semibold text-slate-900">{supplier || 'non sélectionné'}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Type de mouvement</p>
            <p className="text-lg font-semibold text-slate-900">{movementType}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Date de facture</p>
            <p className="text-lg font-semibold text-slate-900">{invoiceDate || 'non renseignée'}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Utilisateur</p>
            <p className="text-lg font-semibold text-slate-900">{username || 'non défini'}</p>
          </div>
        </div>
      </FiltersDrawer>
      {!isHistoryPanel && errorMessage && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}
      <div className="lg:hidden">
        <label className="text-xs uppercase tracking-[0.3em] text-slate-400" htmlFor="mobile-import-section">
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
      {renderPanel()}
    </div>
  );
}

function Metric({ label, value, className }) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-white p-4 ${className ?? ''}`}>
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
