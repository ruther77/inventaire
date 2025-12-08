import { useMemo } from 'react';
import { CheckCircle, XCircle, EyeOff } from 'lucide-react';
import clsx from 'clsx';
import Button from '../../../components/ui/Button.jsx';
import Badge from '../../../components/ui/Badge.jsx';
import { useFinanceMatches, useFinanceMatchStatus } from '../../../hooks/useFinance.js';

/**
 * RecoAnomaliesTable - Table des anomalies de réconciliation
 */
export default function RecoAnomaliesTable({ status }) {
  const { data: matches = [], isLoading, refetch } = useFinanceMatches({ status });
  const matchStatus = useFinanceMatchStatus();

  const sortedMatches = useMemo(() => {
    return [...matches].sort((a, b) => {
      // Sort by confidence/score descending
      const scoreA = a.score || a.confidence || 0;
      const scoreB = b.score || b.confidence || 0;
      return scoreB - scoreA;
    });
  }, [matches]);

  const handleAction = async (matchId, newStatus) => {
    try {
      await matchStatus.mutateAsync({ matchId, status: newStatus });
      refetch();
    } catch (err) {
      console.error('Error updating match status:', err);
    }
  };

  const getConfidenceBadge = (confidence) => {
    const score = confidence || 0;
    if (score >= 0.8) {
      return <Badge variant="success" size="sm">{(score * 100).toFixed(0)}%</Badge>;
    } else if (score >= 0.5) {
      return <Badge variant="warning" size="sm">{(score * 100).toFixed(0)}%</Badge>;
    } else {
      return <Badge variant="error" size="sm">{(score * 100).toFixed(0)}%</Badge>;
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'warning', label: 'En attente' },
      auto: { variant: 'info', label: 'Automatique' },
      confirmed: { variant: 'success', label: 'Confirmé' },
      rejected: { variant: 'error', label: 'Rejeté' },
    };

    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant} size="sm" dot>{config.label}</Badge>;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const formatAmount = (amount) => {
    if (amount === null || amount === undefined) return '—';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8">
        <div className="flex items-center justify-center gap-3">
          <div className="animate-spin rounded-full border-2 border-slate-200 border-t-brand-600 h-6 w-6" />
          <p className="text-sm text-slate-500">Chargement des anomalies...</p>
        </div>
      </div>
    );
  }

  if (sortedMatches.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8">
        <div className="text-center">
          <CheckCircle className="mx-auto h-12 w-12 text-slate-300" />
          <p className="mt-3 text-sm font-medium text-slate-900">Aucune anomalie</p>
          <p className="mt-1 text-xs text-slate-500">
            {status
              ? `Aucune anomalie avec le statut "${status}"`
              : 'Toutes les transactions sont réconciliées'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
              >
                Date
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
              >
                Libellé banque
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-600"
              >
                Montant
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
              >
                Raison
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-600"
              >
                Confiance
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-600"
              >
                Statut
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-600"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {sortedMatches.map((match) => {
              const confidence = match.score || match.confidence || 0;
              const bankData = match.bank || {};
              const invoiceData = match.invoice || {};
              const isActionDisabled = matchStatus.isLoading;

              return (
                <tr
                  key={match.id}
                  className={clsx(
                    'transition-colors hover:bg-slate-50',
                    match.status === 'rejected' && 'opacity-60'
                  )}
                >
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900">
                    {formatDate(bankData.date || bankData.statement_date)}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-900">
                    <div className="max-w-xs">
                      <p className="truncate font-medium">
                        {bankData.label || bankData.description || '—'}
                      </p>
                      {invoiceData.supplier_name && (
                        <p className="mt-0.5 truncate text-xs text-slate-500">
                          Facture: {invoiceData.supplier_name}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                    <div>
                      <p className="font-medium text-slate-900">
                        {formatAmount(bankData.amount)}
                      </p>
                      {invoiceData.total_incl_tax &&
                       invoiceData.total_incl_tax !== bankData.amount && (
                        <p className="text-xs text-slate-500">
                          Fact: {formatAmount(invoiceData.total_incl_tax)}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    <p className="max-w-xs truncate">
                      {match.reason || match.matching_reason || 'Correspondance automatique'}
                    </p>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center">
                    {getConfidenceBadge(confidence)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center">
                    {getStatusBadge(match.status)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {match.status !== 'confirmed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAction(match.id, 'confirmed')}
                          disabled={isActionDisabled}
                          className="text-emerald-600 hover:bg-emerald-50 hover:text-emerald-700"
                        >
                          <CheckCircle className="h-4 w-4" />
                          <span className="ml-1">Valider</span>
                        </Button>
                      )}
                      {match.status !== 'rejected' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAction(match.id, 'rejected')}
                          disabled={isActionDisabled}
                          className="text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                        >
                          <XCircle className="h-4 w-4" />
                          <span className="ml-1">Rejeter</span>
                        </Button>
                      )}
                      {match.status === 'pending' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAction(match.id, 'ignored')}
                          disabled={isActionDisabled}
                          className="text-slate-600 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <EyeOff className="h-4 w-4" />
                          <span className="ml-1">Ignorer</span>
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer with count */}
      <div className="border-t border-slate-200 bg-slate-50 px-4 py-3">
        <p className="text-xs text-slate-500">
          {sortedMatches.length} anomalie{sortedMatches.length > 1 ? 's' : ''} trouvée
          {sortedMatches.length > 1 ? 's' : ''}
        </p>
      </div>
    </div>
  );
}
