/**
 * InvoiceHistoryPanel - Historique des factures importees
 *
 * Responsabilites:
 * - Affichage tableau des factures importees
 * - Telechargement PDF des factures
 * - Affichage des lignes rejetees/conflits
 */

import { useState } from 'react';
import { toast } from 'sonner';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import { useInvoiceHistory } from '../../../hooks/useInvoiceImport.js';
import { downloadInvoiceFile } from '../../../api/client.js';

export default function InvoiceHistoryPanel({ supplier, catalogSummary }) {
  const [downloadingInvoice, setDownloadingInvoice] = useState(null);

  const historyQuery = useInvoiceHistory({ supplier: supplier || undefined, limit: 500 });
  const historyItems = historyQuery.data ?? [];

  const handleDownloadInvoicePdf = async (invoiceId) => {
    if (!invoiceId) return;
    try {
      setDownloadingInvoice(invoiceId);
      const response = await downloadInvoiceFile(invoiceId);
      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/pdf',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${invoiceId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Telechargement impossible');
    } finally {
      setDownloadingInvoice(null);
    }
  };

  const handleDownloadRejectedCsv = () => {
    if (!catalogSummary?.rejected_csv) return;
    const blob = new Blob([catalogSummary.rejected_csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'lignes_rejetees.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      {/* Tableau historique */}
      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Historique</p>
            <h3 className="text-lg font-semibold text-slate-900">Factures importees</h3>
          </div>
          <Button variant="ghost" size="sm" onClick={() => historyQuery?.refetch?.()}>
            Actualiser
          </Button>
        </div>

        {historyQuery.isLoading ? (
          <p className="text-sm text-slate-500">Chargement...</p>
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
                        Telecharger
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Aucune facture importee pour l'instant.</p>
        )}
      </Card>

      {/* Conflits et rejets */}
      <Card className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-slate-900">Conflits & rejets</h3>
        <p className="text-sm text-slate-600">
          Telechargez les lignes rejetees pour corriger les anomalies (codes-barres en double,
          references absentes, etc.).
        </p>

        {catalogSummary?.rejected_rows?.length ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-medium">
              {catalogSummary.rejected_rows.length} ligne(s) rejetee(s). Telechargez le fichier pour
              les corriger manuellement.
            </p>
            {catalogSummary.rejected_csv && (
              <Button variant="ghost" size="sm" className="mt-2" onClick={handleDownloadRejectedCsv}>
                Telecharger les lignes rejetees
              </Button>
            )}
          </div>
        ) : (
          <p className="text-sm text-slate-500">Aucune ligne rejetee pour le moment.</p>
        )}
      </Card>
    </>
  );
}
