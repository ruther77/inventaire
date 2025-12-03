import React from 'react';
import Button from '../../../components/ui/Button.jsx';

export default function InvoiceHistoryTable({ items, onRefresh, onDownload, downloadingId }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">Aucune facture importée pour l'instant.</p>;
  }

  const sorted = items
    .slice()
    .sort((a, b) => b.invoice_id.localeCompare(a.invoice_id, undefined, { numeric: true, sensitivity: 'base' }));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Historique</p>
          <h3 className="text-lg font-semibold text-slate-900">Factures importées</h3>
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh}>
          Actualiser
        </Button>
      </div>
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
            {sorted.map((item) => (
              <tr key={item.invoice_id}>
                <td className="px-3 py-2 font-medium text-slate-900">{item.invoice_id}</td>
                <td className="px-3 py-2 text-slate-600">{item.supplier || '—'}</td>
                <td className="px-3 py-2 text-slate-600">{item.facture_date || '—'}</td>
                <td className="px-3 py-2 text-right text-slate-600">{item.line_count}</td>
                <td className="px-3 py-2 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDownload?.(item.invoice_id)}
                    disabled={downloadingId === item.invoice_id}
                  >
                    Télécharger
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
