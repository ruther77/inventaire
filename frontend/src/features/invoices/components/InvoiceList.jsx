import React from 'react';
import Button from '../../../components/ui/Button.jsx';

export default function InvoiceList({
  documents,
  selectedDocumentIds,
  setSelectedDocumentIds,
  selectedDocumentId,
  setSelectedDocumentId,
  onReset,
}) {
  if (!documents.length) {
    return (
      <p className="text-sm text-slate-500">
        Analysez une facture (PDF/TXT) pour afficher ici les sous-documents détectés.
      </p>
    );
  }

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-brand-500 focus:ring-brand-400"
            checked={selectedDocumentIds.length === documents.length}
            onChange={(event) =>
              setSelectedDocumentIds(event.target.checked ? documents.map((doc) => doc.invoice_id) : [])
            }
          />
          Tout sélectionner
        </label>
        <Button variant="ghost" size="sm" onClick={onReset}>
          Réinitialiser
        </Button>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {documents
          .slice()
          .sort((a, b) => a.invoice_id.localeCompare(b.invoice_id, undefined, { numeric: true }))
          .map((doc) => {
            const isActive = doc.invoice_id === selectedDocumentId;
            const isSelected = selectedDocumentIds.includes(doc.invoice_id);
            return (
              <div
                key={doc.invoice_id}
                className={`flex flex-col gap-2 rounded-2xl border px-4 py-3 text-left transition ${
                  isActive ? 'border-brand-400 bg-brand-50 shadow-sm' : 'border-slate-200 bg-white'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-500 focus:ring-brand-400"
                    checked={isSelected}
                    onChange={(event) => {
                      setSelectedDocumentIds((prev) => {
                        const exists = prev.includes(doc.invoice_id);
                        if (event.target.checked && !exists) {
                          return [...prev, doc.invoice_id];
                        }
                        if (!event.target.checked && exists) {
                          return prev.filter((id) => id !== doc.invoice_id);
                        }
                        return prev;
                      });
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedDocumentId(doc.invoice_id);
                      if (!isSelected) {
                        setSelectedDocumentIds((prev) => [...prev, doc.invoice_id]);
                      }
                    }}
                    className="flex flex-1 flex-col text-left"
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
                </div>
                <p className="text-xs text-slate-500">
                  Cliquez pour éditer · cochez pour inclure dans l&apos;import
                </p>
              </div>
            );
          })}
      </div>
    </>
  );
}
