import React, { useState } from 'react';
import { RefreshCw, AlertTriangle, GitCompare } from 'lucide-react';
import clsx from 'clsx';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Select from '../../components/ui/Select.jsx';
import Badge from '../../components/ui/Badge.jsx';
import { useFinanceAnomalies, useFinanceRefreshAnomalies } from '../../hooks/useFinance.js';
import RecoAnomaliesTable from './components/RecoAnomaliesTable.jsx';

const TABS = {
  EXPENSES: 'expenses',
  RECONCILIATION: 'reconciliation',
};

export default function FinanceAnomaliesPage() {
  const [activeTab, setActiveTab] = useState(TABS.EXPENSES);
  const [severity, setSeverity] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const anomalies = useFinanceAnomalies({ severity: severity || undefined });
  const refreshAnomalies = useFinanceRefreshAnomalies();

  const handleRefreshAnomalies = () => {
    refreshAnomalies.mutate(
      { zscore_threshold: 2.5, min_occurrences: 3 },
      { onSuccess: () => anomalies.refetch() }
    );
  };

  const getSeverityBadge = (severity) => {
    const severityConfig = {
      high: { variant: 'error', label: 'Élevée' },
      medium: { variant: 'warning', label: 'Moyenne' },
      low: { variant: 'info', label: 'Faible' },
    };

    const config = severityConfig[severity] || { variant: 'default', label: severity };
    return <Badge variant={config.variant} size="sm">{config.label}</Badge>;
  };

  const formatAmount = (amount) => {
    if (amount === null || amount === undefined) return '—';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Anomalies & Contrôle</p>
          <h1 className="text-2xl font-semibold text-slate-900">Contrôle et validation</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            onClick={handleRefreshAnomalies}
            disabled={refreshAnomalies.isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${refreshAnomalies.isLoading ? 'animate-spin' : ''}`} />
            {refreshAnomalies.isLoading ? 'Actualisation...' : 'Rafraîchir'}
          </Button>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex gap-6" aria-label="Tabs">
          <button
            onClick={() => setActiveTab(TABS.EXPENSES)}
            className={clsx(
              'flex items-center gap-2 border-b-2 px-1 py-4 text-sm font-medium transition-colors',
              activeTab === TABS.EXPENSES
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
            )}
          >
            <AlertTriangle className="h-4 w-4" />
            Anomalies dépenses
            {anomalies.data && anomalies.data.length > 0 && (
              <Badge variant="error-solid" size="xs">
                {anomalies.data.length}
              </Badge>
            )}
          </button>
          <button
            onClick={() => setActiveTab(TABS.RECONCILIATION)}
            className={clsx(
              'flex items-center gap-2 border-b-2 px-1 py-4 text-sm font-medium transition-colors',
              activeTab === TABS.RECONCILIATION
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
            )}
          >
            <GitCompare className="h-4 w-4" />
            Réconciliation
          </button>
        </nav>
      </div>

      {/* Tab Content: Expenses Anomalies */}
      {activeTab === TABS.EXPENSES && (
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Anomalies de dépenses</h3>
                <p className="mt-1 text-sm text-slate-500">
                  Détection automatique des dépenses inhabituelles
                </p>
              </div>
              <Select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                <option value="">Toutes les sévérités</option>
                <option value="high">Élevée</option>
                <option value="medium">Moyenne</option>
                <option value="low">Faible</option>
              </Select>
            </div>

            <div className="space-y-2">
              {anomalies.isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="flex items-center gap-3">
                    <div className="animate-spin rounded-full border-2 border-slate-200 border-t-brand-600 h-6 w-6" />
                    <p className="text-sm text-slate-500">Chargement...</p>
                  </div>
                </div>
              ) : (anomalies.data ?? []).length === 0 ? (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
                  <AlertTriangle className="mx-auto h-12 w-12 text-slate-300" />
                  <p className="mt-3 text-sm font-medium text-slate-900">Aucune anomalie détectée</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Toutes vos dépenses semblent normales
                  </p>
                </div>
              ) : (
                (anomalies.data ?? []).map((anomaly) => (
                  <div
                    key={anomaly.id}
                    className="rounded-lg border border-slate-200 bg-white p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-slate-900">
                            {anomaly.rule || 'Anomalie détectée'}
                          </p>
                          {getSeverityBadge(anomaly.severity)}
                        </div>
                        <div className="mt-2 space-y-1 text-xs text-slate-600">
                          <p>
                            <span className="font-medium">Transaction:</span>{' '}
                            {anomaly.statement_label || '—'}
                          </p>
                          <p>
                            <span className="font-medium">Compte:</span>{' '}
                            {anomaly.statement_account || '—'}
                          </p>
                          <p>
                            <span className="font-medium">Date:</span>{' '}
                            {anomaly.statement_date || '—'}
                          </p>
                        </div>
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <p className="text-sm font-semibold text-slate-900">
                          {formatAmount(anomaly.amount)}
                        </p>
                        {anomaly.expected_amount !== null &&
                         anomaly.expected_amount !== undefined && (
                          <p className="mt-1 text-xs text-slate-500">
                            Attendu: {formatAmount(anomaly.expected_amount)}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Tab Content: Reconciliation Anomalies */}
      {activeTab === TABS.RECONCILIATION && (
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Anomalies de réconciliation</h3>
                <p className="mt-1 text-sm text-slate-500">
                  Correspondances entre relevés bancaires et factures à valider
                </p>
              </div>
              <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="">Tous les statuts</option>
                <option value="pending">En attente</option>
                <option value="auto">Automatique</option>
                <option value="confirmed">Confirmés</option>
                <option value="rejected">Rejetés</option>
              </Select>
            </div>
          </Card>

          <RecoAnomaliesTable status={statusFilter || undefined} />
        </div>
      )}
    </div>
  );
}
