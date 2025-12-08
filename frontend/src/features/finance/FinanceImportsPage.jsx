import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Select from '../../components/ui/Select.jsx';
import Badge from '../../components/ui/Badge.jsx';
import { useFinanceImports } from '../../hooks/useFinanceImports.js';
import { useFinanceAccountsOverviewStats } from '../../hooks/useFinanceCategories.js';
import ImportStepper from './components/ImportStepper.jsx';

export default function FinanceImportsPage() {
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const imports = useFinanceImports();
  const { data: accountsData } = useFinanceAccountsOverviewStats();

  const accounts = accountsData?.accounts || [];

  const handleImportComplete = (result) => {
    // Refresh imports list after successful import
    imports.refetch();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      success: { variant: 'success', label: 'Réussi' },
      pending: { variant: 'warning', label: 'En cours' },
      error: { variant: 'error', label: 'Erreur' },
      completed: { variant: 'success', label: 'Terminé' },
    };

    const config = statusConfig[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant} size="sm" dot>{config.label}</Badge>;
  };

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Imports</p>
          <h1 className="text-2xl font-semibold text-slate-900">Import de relevés bancaires</h1>
        </div>
        <Button
          variant="ghost"
          onClick={() => imports.refetch()}
          disabled={imports.isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${imports.isLoading ? 'animate-spin' : ''}`} />
          Rafraîchir
        </Button>
      </header>

      {/* Import Section */}
      <Card>
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Nouvel import</h2>
            <p className="mt-1 text-sm text-slate-500">
              Importez un fichier CSV de relevé bancaire pour un compte
            </p>
          </div>

          {/* Account Selection */}
          <div>
            <label htmlFor="account-select" className="block text-sm font-medium text-slate-700 mb-1.5">
              Compte bancaire <span className="text-rose-500">*</span>
            </label>
            <Select
              id="account-select"
              value={selectedAccountId}
              onChange={(e) => setSelectedAccountId(e.target.value)}
            >
              <option value="">Sélectionnez un compte</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.label || account.name || `Compte ${account.id}`}
                  {account.balance !== undefined && ` (${new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: 'EUR',
                  }).format(account.balance)})`}
                </option>
              ))}
            </Select>
          </div>

          {/* Import Stepper */}
          <ImportStepper
            accountId={selectedAccountId ? parseInt(selectedAccountId, 10) : null}
            onComplete={handleImportComplete}
          />
        </div>
      </Card>

      {/* Import History */}
      <Card>
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Historique des imports</h2>
            <p className="mt-1 text-sm text-slate-500">
              Liste de tous les imports effectués
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Fichier
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Compte
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Importées/Total
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Statut
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Erreur
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {imports.isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center">
                      <div className="flex items-center justify-center gap-3">
                        <div className="animate-spin rounded-full border-2 border-slate-200 border-t-brand-600 h-5 w-5" />
                        <p className="text-sm text-slate-500">Chargement...</p>
                      </div>
                    </td>
                  </tr>
                ) : (imports.data ?? []).length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-500">
                      Aucun import effectué
                    </td>
                  </tr>
                ) : (
                  (imports.data ?? []).map((imp) => (
                    <tr key={imp.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 text-sm text-slate-900">
                        {imp.file_name || 'fichier.csv'}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-900">
                        {imp.account_label || imp.account_id || '—'}
                      </td>
                      <td className="px-4 py-3 text-center text-sm">
                        <span className="font-medium text-slate-900">{imp.inserted ?? 0}</span>
                        <span className="text-slate-500">/{imp.total ?? '?'}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {getStatusBadge(imp.status)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {imp.error && (
                          <span className="text-rose-600">{imp.error}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {formatDate(imp.created_at)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  );
}
