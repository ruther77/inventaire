/**
 * InvoiceDocumentSelector - Selection des documents detectes
 *
 * Responsabilites:
 * - Affichage des sous-documents detectes dans une facture multi-pages
 * - Selection d'un document pour edition
 * - Selection de tous les documents
 */

import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';

export default function InvoiceDocumentSelector({
  documents,
  selectedDocumentId,
  onSelectDocument,
  onSelectAll,
}) {
  const totalLines = documents.reduce((sum, doc) => sum + (doc.items?.length || 0), 0);

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">factures detectees</p>
          <h3 className="text-lg font-semibold text-slate-900">Selectionnez la facture a traiter</h3>
        </div>
        {documents.length > 0 && (
          <Button variant="brand" size="sm" onClick={onSelectAll}>
            Tout selectionner ({totalLines} lignes)
          </Button>
        )}
      </div>

      {documents.length ? (
        <div className="grid gap-3 md:grid-cols-2">
          {documents.map((doc) => {
            const isActive = doc.invoice_id === selectedDocumentId;
            return (
              <button
                type="button"
                key={doc.invoice_id}
                onClick={() => onSelectDocument(doc.invoice_id)}
                className={`flex flex-col rounded-2xl border px-4 py-3 text-left transition ${
                  isActive ? 'border-brand-400 bg-brand-50 shadow-sm' : 'border-slate-200 bg-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-slate-900">Facture {doc.invoice_id}</p>
                  <span className="text-xs text-slate-500">{doc.items.length} lignes</span>
                </div>
                <p className="text-sm text-slate-600">Date : {doc.facture_date || 'non renseignee'}</p>
                {doc.pdf_path && (
                  <p className="text-xs text-slate-500 break-words">Stockee : {doc.pdf_path}</p>
                )}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-slate-500">
          Analysez une facture (PDF/TXT) pour afficher ici les sous-documents detectes.
        </p>
      )}
    </Card>
  );
}
