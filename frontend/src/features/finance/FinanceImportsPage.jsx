/**
 * FinanceImportsPage - Import de relevés bancaires
 *
 * Design: Standards Morning Brief (dark mode, glass-morphism, Framer Motion)
 */

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RefreshCw,
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Building2,
  TrendingUp,
  Loader2,
  Copy,
  BarChart3,
} from 'lucide-react';
import clsx from 'clsx';

import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useFinanceImports } from '../../hooks/useFinanceImports.js';
import { useFinanceAccountsOverviewStats } from '../../hooks/useFinanceCategories.js';
import { useDeduplicateTransactions, useRefreshFinanceStats } from '../../hooks/useFinance.js';
import ImportStepper from './components/ImportStepper.jsx';

// ============================================================================
// UTILITIES
// ============================================================================

const formatCurrency = (val) => {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
  }).format(val);
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

// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * KPI Card avec style glass-morphism
 */
function KPICard({ label, value, icon: Icon, status = 'neutral', subtitle }) {
  const statusColors = {
    success: 'border-emerald-500/30 bg-emerald-500/10',
    warning: 'border-amber-500/30 bg-amber-500/10',
    error: 'border-rose-500/30 bg-rose-500/10',
    neutral: 'border-white/10 bg-white/5',
  };

  const iconColors = {
    success: 'text-emerald-400',
    warning: 'text-amber-400',
    error: 'text-rose-400',
    neutral: 'text-slate-400',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      className={clsx(
        'relative p-4 rounded-xl border',
        'transition-all duration-200',
        statusColors[status]
      )}
    >
      <div className="flex items-center gap-3">
        <div className={clsx('p-2 rounded-lg bg-white/5', iconColors[status])}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
    </motion.div>
  );
}

/**
 * Status Badge avec style dark mode
 */
function StatusBadge({ status }) {
  const config = {
    success: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Réussi' },
    completed: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Terminé' },
    pending: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'En cours' },
    error: { bg: 'bg-rose-500/20', text: 'text-rose-400', label: 'Erreur' },
  };

  const { bg, text, label } = config[status] || { bg: 'bg-slate-500/20', text: 'text-slate-400', label: status };

  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium', bg, text)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', text.replace('text-', 'bg-'))} />
      {label}
    </span>
  );
}

/**
 * Ligne d'historique d'import
 */
function ImportRow({ imp, index }) {
  const statusIcon = {
    success: CheckCircle,
    completed: CheckCircle,
    pending: Clock,
    error: XCircle,
  };
  const Icon = statusIcon[imp.status] || Clock;

  return (
    <motion.tr
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="group hover:bg-white/5 transition-colors"
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className={clsx(
            'p-2 rounded-lg',
            imp.status === 'error' ? 'bg-rose-500/10' : 'bg-blue-500/10'
          )}>
            <FileText className={clsx(
              'w-4 h-4',
              imp.status === 'error' ? 'text-rose-400' : 'text-blue-400'
            )} />
          </div>
          <div>
            <p className="font-medium text-white">{imp.file_name || 'fichier.csv'}</p>
            <p className="text-xs text-slate-500">{formatDate(imp.created_at)}</p>
          </div>
        </div>
      </td>

      <td className="px-4 py-3">
        <span className="text-white">{imp.account_label || imp.account_id || '—'}</span>
      </td>

      <td className="px-4 py-3 text-center">
        <span className="font-semibold text-white">{imp.inserted ?? 0}</span>
        <span className="text-slate-500">/{imp.total ?? '?'}</span>
      </td>

      <td className="px-4 py-3 text-center">
        <StatusBadge status={imp.status} />
      </td>

      <td className="px-4 py-3">
        {imp.error && (
          <span className="text-sm text-rose-400">{imp.error}</span>
        )}
      </td>
    </motion.tr>
  );
}

/**
 * Select compte avec style dark mode
 */
function AccountSelect({ value, accounts, onChange, disabled }) {
  return (
    <select
      className={clsx(
        'w-full rounded-xl px-4 py-3 text-sm',
        'bg-white/5 border border-white/10',
        'text-white',
        'focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50',
        'transition-all duration-200',
        '[&>option]:bg-slate-800 [&>option]:text-white'
      )}
      value={value}
      onChange={onChange}
      disabled={disabled}
    >
      <option value="">Sélectionnez un compte</option>
      {accounts.map((account) => (
        <option key={account.id} value={account.id}>
          {account.label || account.name || `Compte ${account.id}`}
          {account.balance !== undefined && ` (${formatCurrency(account.balance)})`}
        </option>
      ))}
    </select>
  );
}

/**
 * État vide
 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="p-4 rounded-full bg-slate-500/10 mb-4">
        <FileText className="w-8 h-8 text-slate-500" />
      </div>
      <p className="text-slate-400">Aucun import effectué</p>
      <p className="text-sm text-slate-500 mt-1">
        Importez votre premier relevé bancaire ci-dessus
      </p>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function FinanceImportsPage() {
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const imports = useFinanceImports();
  const { data: accountsData } = useFinanceAccountsOverviewStats();
  const deduplicateMutation = useDeduplicateTransactions();
  const refreshStatsMutation = useRefreshFinanceStats();

  const accounts = accountsData?.accounts || [];

  // Stats calculées
  const stats = useMemo(() => {
    const data = imports.data ?? [];
    const total = data.length;
    const success = data.filter((i) => i.status === 'success' || i.status === 'completed').length;
    const pending = data.filter((i) => i.status === 'pending').length;
    const errors = data.filter((i) => i.status === 'error').length;
    const totalLines = data.reduce((acc, i) => acc + (i.inserted || 0), 0);

    return { total, success, pending, errors, totalLines };
  }, [imports.data]);

  const handleImportComplete = () => {
    imports.refetch();
  };

  const handleDeduplicate = async () => {
    try {
      const result = await deduplicateMutation.mutateAsync();
      alert(`Déduplication terminée:\n- Transactions supprimées: ${result.transactions_deleted}\n- Lignes de relevés supprimées: ${result.statement_lines_deleted}`);
      imports.refetch();
    } catch (error) {
      console.error('Erreur lors de la déduplication:', error);
      alert('Erreur lors de la déduplication');
    }
  };

  const handleRefreshStats = async () => {
    try {
      const result = await refreshStatsMutation.mutateAsync();
      alert(`Stats rafraîchies avec succès:\n${result.refreshed?.join('\n') || 'Vues matérialisées mises à jour'}`);
    } catch (error) {
      console.error('Erreur lors du rafraîchissement:', error);
      alert('Erreur lors du rafraîchissement des stats');
    }
  };

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20">
              <Upload className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">imports</p>
              <h1 className="text-2xl font-bold text-white">Relevés bancaires</h1>
              <p className="text-sm text-slate-400 mt-1">
                Importez vos fichiers CSV pour alimenter la trésorerie
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="subtle"
              onClick={handleDeduplicate}
              disabled={deduplicateMutation.isPending}
              className="flex items-center gap-2"
            >
              {deduplicateMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
              Dédupliquer
            </Button>

            <Button
              variant="subtle"
              onClick={handleRefreshStats}
              disabled={refreshStatsMutation.isPending}
              className="flex items-center gap-2"
            >
              {refreshStatsMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <BarChart3 className="w-4 h-4" />
              )}
              Rafraîchir stats
            </Button>

            <Button
              variant="subtle"
              onClick={() => imports.refetch()}
              disabled={imports.isLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={clsx('w-4 h-4', imports.isLoading && 'animate-spin')} />
              Rafraîchir
            </Button>
          </div>
        </motion.div>

        {/* KPIs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <KPICard
            label="Total imports"
            value={stats.total}
            icon={FileText}
            status="neutral"
          />
          <KPICard
            label="Réussis"
            value={stats.success}
            icon={CheckCircle}
            status="success"
          />
          <KPICard
            label="Lignes importées"
            value={stats.totalLines.toLocaleString('fr-FR')}
            icon={TrendingUp}
            status="neutral"
            subtitle="Transactions"
          />
          <KPICard
            label="Erreurs"
            value={stats.errors}
            icon={AlertTriangle}
            status={stats.errors > 0 ? 'error' : 'success'}
          />
        </motion.div>

        {/* Section Import */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10 p-6"
        >
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Upload className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-semibold text-white">Nouvel import</h2>
            </div>
            <p className="text-sm text-slate-400">
              Importez un fichier CSV de relevé bancaire pour un compte
            </p>
          </div>

          {/* Account Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-400 mb-2">
              Compte bancaire <span className="text-rose-400">*</span>
            </label>
            <AccountSelect
              value={selectedAccountId}
              accounts={accounts}
              onChange={(e) => setSelectedAccountId(e.target.value)}
            />
          </div>

          {/* Import Stepper */}
          <ImportStepper
            accountId={selectedAccountId ? parseInt(selectedAccountId, 10) : null}
            onComplete={handleImportComplete}
          />
        </motion.div>

        {/* Historique */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10 overflow-hidden"
        >
          <div className="p-4 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-violet-400" />
              <h2 className="text-lg font-semibold text-white">Historique des imports</h2>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Liste de tous les imports effectués
            </p>
          </div>

          {imports.isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-4" />
              <p className="text-slate-400">Chargement...</p>
            </div>
          ) : (imports.data ?? []).length === 0 ? (
            <EmptyState />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Fichier
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Compte
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">
                      Importées/Total
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">
                      Statut
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                      Erreur
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <AnimatePresence mode="popLayout">
                    {(imports.data ?? []).map((imp, index) => (
                      <ImportRow key={imp.id} imp={imp} index={index} />
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          )}

          {/* Footer */}
          {(imports.data ?? []).length > 0 && (
            <div className="px-4 py-3 border-t border-white/10">
              <p className="text-sm text-slate-500">
                {(imports.data ?? []).length} import{(imports.data ?? []).length > 1 ? 's' : ''} au total
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
