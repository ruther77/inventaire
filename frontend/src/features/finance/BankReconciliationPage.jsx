import React, { useState, useMemo } from 'react';
import { Link2, AlertTriangle, CheckCircle, Clock, RefreshCw, Filter, LayoutGrid, List } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import DataTable from '../../components/ui/DataTable.jsx';
import Modal from '../../components/ui/Modal.jsx';
import { ReconciliationSuggestionList } from '../../components/ai';
import CardExpandable from '../../components/ui/CardExpandable.jsx';
import AIConfidenceBadge from '../../components/ui/AIConfidenceBadge.jsx';
import { useBankReconciliation } from '../../hooks/useBankReconciliation.js';
import { staggerContainer, staggerItem, kpiCard, tabContent, modalScale, overlayFade } from '../../ui/motion.js';
import ReconciliationSplitView from './components/ReconciliationSplitView.jsx';
import { DashboardSkeleton } from '../../components/ui/PageSkeletons.jsx';
import QueryErrorState from '../../components/feedback/QueryErrorState.jsx';

const Stat = ({ label, value, hint, icon: Icon, accent = 'text-white' }) => (
  <motion.div
    className="rounded-2xl border border-white/10 bg-white/5 p-4 cursor-pointer"
    variants={staggerItem}
    whileHover={kpiCard.hover}
    whileTap={kpiCard.tap}
  >
    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-[0.3em]">
      {Icon && <Icon className="w-4 h-4" />} {label}
    </div>
    <p className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
  </motion.div>
);

const StatusBadge = ({ status }) => {
  const styles = {
    matched: 'bg-emerald-500/20 text-emerald-400',
    pending: 'bg-amber-500/20 text-amber-400',
    unmatched: 'bg-rose-500/20 text-rose-400',
    partial: 'bg-blue-500/20 text-blue-400',
  };
  const labels = {
    matched: 'Rapproché',
    pending: 'En attente',
    unmatched: 'Non rapproché',
    partial: 'Partiel',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {labels[status] || status}
    </span>
  );
};

export default function BankReconciliationPage() {
  const [activeTab, setActiveTab] = useState('transactions');
  const [viewMode, setViewMode] = useState('split'); // 'split' or 'list'
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [matchModalOpen, setMatchModalOpen] = useState(false);
  const [filters, setFilters] = useState({ daysBack: 365, minAmount: 0 });

  const {
    summary,
    transactions,
    invoices,
    isLoading,
    runReconciliation,
    createMatch,
    refetchAll,
  } = useBankReconciliation(filters);

  const hasError = summary.isError || transactions.isError || invoices.isError;

  // Gestion des erreurs
  if (hasError) {
    return (
      <QueryErrorState
        error={summary.error || transactions.error || invoices.error}
        onRetry={refetchAll}
        title="Erreur de chargement"
        description="Impossible de charger les données de rapprochement bancaire."
      />
    );
  }

  const unmatchedTransactions = transactions.data || [];
  const unmatchedInvoices = invoices.data || [];
  const suggestions = useMemo(() => {
    if (!unmatchedTransactions.length || !unmatchedInvoices.length) return [];
    return unmatchedTransactions.slice(0, 3).map((tx, idx) => {
      const inv = unmatchedInvoices[idx] || unmatchedInvoices[0];
      return {
        id: tx.transaction_id || tx.id || `sug-${idx}`,
        txId: tx.transaction_id || tx.id,
        invoiceId: inv?.invoice_id || inv?.id,
        transaction: {
          label: tx.label || 'Transaction',
          date: tx.date || '',
          amount: Number(tx.amount) || 0,
          bank_account: tx.bank_account || '',
        },
        invoice: {
          supplier: inv?.supplier_name || 'Fournisseur',
          reference: inv?.invoice_number || '',
          date: inv?.date || '',
          amount: Number(inv?.amount || 0),
          line_count: inv?.line_count || 0,
        },
        confidence: 0.92,
      };
    });
  }, [unmatchedTransactions, unmatchedInvoices]);

  const handleRunReconciliation = () => {
    runReconciliation.mutate({ daysBack: filters.daysBack, autoConfirmThreshold: 0.95 });
  };

  const handleManualMatch = () => {
    if (!selectedTransaction || !selectedInvoice) return;
    createMatch.mutate(
      {
        transaction_id: selectedTransaction.id,
        invoice_id: selectedInvoice.id,
        match_type: 'manual',
      },
      {
        onSuccess: () => {
          setMatchModalOpen(false);
          setSelectedTransaction(null);
          setSelectedInvoice(null);
        },
      }
    );
  };

  const transactionColumns = useMemo(() => [
    {
      key: 'date',
      header: 'Date',
      sortable: true,
      render: (value) => {
        if (!value) return '—';
        const dateStr = typeof value === 'string' ? value : value.toString();
        const parts = dateStr.split('-');
        return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateStr;
      },
    },
    {
      key: 'label',
      header: 'Libellé',
      sortable: true,
      render: (value) => <span className="font-medium text-white truncate max-w-xs block">{value || '—'}</span>,
    },
    {
      key: 'amount',
      header: 'Montant',
      align: 'right',
      sortable: true,
      render: (value) => {
        const amount = Number(value) || 0;
        return (
          <span className={`font-semibold ${amount >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
            {amount >= 0 ? '+' : ''}{amount.toFixed(2)} €
          </span>
        );
      },
    },
    {
      key: 'match_status',
      header: 'Statut',
      render: (value) => <StatusBadge status={value || 'unmatched'} />,
    },
    {
      key: 'actions',
      header: '',
      render: (_, row) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setSelectedTransaction(row);
            setMatchModalOpen(true);
          }}
        >
          <Link2 className="w-4 h-4" />
        </Button>
      ),
    },
  ], []);

  const invoiceColumns = useMemo(() => [
    {
      key: 'date',
      header: 'Date',
      sortable: true,
      render: (value) => {
        if (!value) return '—';
        const dateStr = typeof value === 'string' ? value : value.toString();
        const parts = dateStr.split('-');
        return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateStr;
      },
    },
    {
      key: 'supplier_name',
      header: 'Fournisseur',
      sortable: true,
      render: (value) => <span className="font-medium text-white">{value || '—'}</span>,
    },
    {
      key: 'invoice_number',
      header: 'N° Facture',
      render: (value) => <span className="text-sm text-slate-300">{value || '—'}</span>,
    },
    {
      key: 'amount',
      header: 'Montant TTC',
      align: 'right',
      sortable: true,
      render: (value) => {
        const amount = Number(value) || 0;
        return <span className="font-semibold text-rose-400">-{amount.toFixed(2)} €</span>;
      },
    },
    {
      key: 'match_status',
      header: 'Statut',
      render: (value) => <StatusBadge status={value || 'unmatched'} />,
    },
    {
      key: 'actions',
      header: '',
      render: (_, row) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setSelectedInvoice(row);
            if (selectedTransaction) setMatchModalOpen(true);
          }}
        >
          <Link2 className="w-4 h-4" />
        </Button>
      ),
    },
  ], [selectedTransaction]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Finance</p>
          <h1 className="text-2xl font-semibold text-orange-400">Rapprochement Bancaire</h1>
        </div>
        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex bg-white/5 rounded-lg p-1">
            <button
              onClick={() => setViewMode('split')}
              className={`p-2 rounded transition ${viewMode === 'split' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`}
              title="Vue split"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded transition ${viewMode === 'list' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`}
              title="Vue liste"
            >
              <List className="h-4 w-4" />
            </button>
          </div>
          <Button variant="ghost" size="sm" onClick={refetchAll} loading={isLoading}>
            <RefreshCw className="h-4 w-4" />
            Actualiser
          </Button>
          <Button variant="primary" size="sm" onClick={handleRunReconciliation} loading={runReconciliation.isPending}>
            <CheckCircle className="h-4 w-4" />
            Rapprochement Auto
          </Button>
        </div>
      </header>

      {/* KPIs */}
      <motion.div
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <Stat
          label="Transactions"
          value={summary.data?.total_transactions || 0}
          hint="Total période"
          icon={Activity}
        />
        <Stat
          label="Rapprochées"
          value={summary.data?.matched_count || 0}
          hint={`${summary.data?.match_rate ? (summary.data.match_rate * 100).toFixed(0) : 0}%`}
          icon={CheckCircle}
          accent="text-emerald-600"
        />
        <Stat
          label="En attente"
          value={unmatchedTransactions.length}
          hint="À rapprocher"
          icon={Clock}
          accent="text-amber-600"
        />
        <Stat
          label="Écart total"
          value={`${(summary.data?.total_unmatched_amount || 0).toFixed(2)} €`}
          hint="Non rapproché"
          icon={AlertTriangle}
          accent="text-rose-600"
        />
      </motion.div>

      {/* Filtres */}
      <Card>
        <div className="flex flex-wrap items-center gap-4 p-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-300">Période:</span>
            <select
              className="text-sm border border-white/10 bg-white/5 text-white rounded-lg px-3 py-1.5"
              value={filters.daysBack}
              onChange={(e) => setFilters((f) => ({ ...f, daysBack: Number(e.target.value) }))}
            >
              <option value={30} className="bg-slate-800">30 jours</option>
              <option value={60} className="bg-slate-800">60 jours</option>
              <option value={90} className="bg-slate-800">90 jours</option>
              <option value={180} className="bg-slate-800">6 mois</option>
              <option value={365} className="bg-slate-800">1 an</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-300">Montant min:</span>
            <input
              type="number"
              className="text-sm border border-white/10 bg-white/5 text-white rounded-lg px-3 py-1.5 w-24"
              value={filters.minAmount}
              onChange={(e) => setFilters((f) => ({ ...f, minAmount: Number(e.target.value) }))}
              placeholder="0"
            />
            <span className="text-sm text-slate-400">€</span>
          </div>
        </div>
      </Card>

      {/* Split View Mode */}
      {viewMode === 'split' ? (
        <ReconciliationSplitView
          transactions={unmatchedTransactions}
          invoices={unmatchedInvoices}
          suggestions={suggestions}
          onMatchCreated={refetchAll}
          isLoading={isLoading}
        />
      ) : (
        <>
          {/* Suggestions IA */}
          <CardExpandable
            title="Suggestions IA"
            subtitle="Rapprochement assisté"
            summary={`${suggestions.length || 0} propositions`}
            variant="info"
            defaultExpanded
            className="border-white/10 bg-white/5"
          >
            <div className="flex items-center gap-2 mb-3">
              <AIConfidenceBadge confidence={0.9} label="Auto-match" variant="pill" size="sm" />
              <p className="text-xs text-slate-500">Basé sur montant/date/fournisseur</p>
            </div>
            <ReconciliationSuggestionList
              title="Suggestions IA"
              suggestions={suggestions}
              onValidate={(id) => {
                const target = suggestions.find((s) => s.id === id);
                if (target) {
                  createMatch.mutate({
                    transaction_id: target.txId || target.transaction?.id || target.id,
                    invoice_id: target.invoiceId || target.invoice?.id || target.id,
                    match_type: 'ai',
                  });
                }
              }}
              onReject={() => {}}
              className="bg-white/5 border border-white/10 rounded-2xl p-4"
            />
          </CardExpandable>

          {/* Tabs */}
          <div className="flex gap-2 bg-white/5 p-1 rounded-xl w-fit">
            <button
              onClick={() => setActiveTab('transactions')}
              className="relative px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              {activeTab === 'transactions' && (
                <motion.span
                  layoutId="reco-tab"
                  className="absolute inset-0 bg-orange-500 rounded-lg"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
              <span className={`relative z-10 ${activeTab === 'transactions' ? 'text-white' : 'text-slate-400'}`}>
                Transactions ({unmatchedTransactions.length})
              </span>
            </button>
            <button
              onClick={() => setActiveTab('invoices')}
              className="relative px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              {activeTab === 'invoices' && (
                <motion.span
                  layoutId="reco-tab"
                  className="absolute inset-0 bg-orange-500 rounded-lg"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
              <span className={`relative z-10 ${activeTab === 'invoices' ? 'text-white' : 'text-slate-400'}`}>
                Factures ({unmatchedInvoices.length})
              </span>
            </button>
          </div>

          {/* Tables */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              variants={tabContent}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Card padding="none">
                {activeTab === 'transactions' ? (
                  <DataTable
                    data={unmatchedTransactions}
                    columns={transactionColumns}
                    loading={isLoading}
                    sortable
                    pagination
                    pageSize={25}
                    emptyMessage="Toutes les transactions sont rapprochées"
                    getRowId={(row) => row.id}
                  />
                ) : (
                  <DataTable
                    data={unmatchedInvoices}
                    columns={invoiceColumns}
                    loading={isLoading}
                    sortable
                    pagination
                    pageSize={25}
                    emptyMessage="Toutes les factures sont rapprochées"
                    getRowId={(row) => row.id}
                  />
                )}
              </Card>
            </motion.div>
          </AnimatePresence>
        </>
      )}

      {/* Modal rapprochement manuel */}
      <Modal
        isOpen={matchModalOpen}
        onClose={() => {
          setMatchModalOpen(false);
          setSelectedTransaction(null);
          setSelectedInvoice(null);
        }}
        title="Rapprochement Manuel"
        size="lg"
      >
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            {/* Transaction sélectionnée */}
            <div className="border border-slate-200 rounded-lg p-4">
              <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">Transaction Bancaire</p>
              {selectedTransaction ? (
                <div className="space-y-2">
                  <p className="font-medium">{selectedTransaction.label}</p>
                  <p className="text-lg font-semibold text-rose-600">
                    {Number(selectedTransaction.amount).toFixed(2)} €
                  </p>
                  <p className="text-sm text-slate-500">{selectedTransaction.date_operation}</p>
                </div>
              ) : (
                <p className="text-slate-400 text-sm">Sélectionnez une transaction</p>
              )}
            </div>

            {/* Facture sélectionnée */}
            <div className="border border-slate-200 rounded-lg p-4">
              <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">Facture</p>
              {selectedInvoice ? (
                <div className="space-y-2">
                  <p className="font-medium">{selectedInvoice.supplier}</p>
                  <p className="text-lg font-semibold text-rose-600">
                    -{Number(selectedInvoice.total_ttc).toFixed(2)} €
                  </p>
                  <p className="text-sm text-slate-500">
                    {selectedInvoice.invoice_number} - {selectedInvoice.invoice_date}
                  </p>
                </div>
              ) : (
                <p className="text-slate-400 text-sm">Sélectionnez une facture</p>
              )}
            </div>
          </div>

          {/* Différence */}
          {selectedTransaction && selectedInvoice && (
            <div className="border-t border-slate-200 pt-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Différence:</span>
                <span className={`font-semibold ${
                  Math.abs(Number(selectedTransaction.amount) + Number(selectedInvoice.total_ttc)) < 0.01
                    ? 'text-emerald-600'
                    : 'text-amber-600'
                }`}>
                  {(Number(selectedTransaction.amount) + Number(selectedInvoice.total_ttc)).toFixed(2)} €
                </span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t border-slate-200">
            <Button
              variant="ghost"
              onClick={() => {
                setMatchModalOpen(false);
                setSelectedTransaction(null);
                setSelectedInvoice(null);
              }}
            >
              Annuler
            </Button>
            <Button
              variant="primary"
              onClick={handleManualMatch}
              disabled={!selectedTransaction || !selectedInvoice}
            >
              <Link2 className="w-4 h-4" />
              Rapprocher
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// Icon placeholder (utilisé dans Stat)
const Activity = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12" />
  </svg>
);
