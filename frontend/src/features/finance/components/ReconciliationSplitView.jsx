/**
 * ReconciliationSplitView - Split view rapprochement (S4 - Rapprochement)
 *
 * Vue split pour le rapprochement bancaire:
 * - Liste transactions a gauche
 * - Detail/match a droite
 * - Drag & drop pour matcher
 * - Validation rapide
 */

import { useState, useMemo, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Link2,
  Unlink,
  Check,
  X,
  ChevronRight,
  Search,
  Filter,
  FileText,
  CreditCard,
  Calendar,
  DollarSign,
  Building,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowRight,
  Sparkles,
  RefreshCw,
  Info,
} from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import Card from '../../../components/ui/Card.jsx';
import AIConfidenceBadge from '../../../components/ui/AIConfidenceBadge.jsx';
import api from '../../../api/client.js';

// ===========================================================================
// API Functions
// ===========================================================================

const createMatch = async (transactionId, invoiceId, matchType = 'manual') => {
  const { data } = await api.post('/bank-reconciliation/matches', {
    transaction_id: transactionId,
    invoice_id: invoiceId,
    match_type: matchType,
  });
  return data;
};

const confirmMatch = async (matchId) => {
  const { data } = await api.post(`/bank-reconciliation/matches/${matchId}/confirm`);
  return data;
};

const rejectMatch = async (matchId) => {
  const { data } = await api.post(`/bank-reconciliation/matches/${matchId}/reject`);
  return data;
};

// ===========================================================================
// Sub-components
// ===========================================================================

function TransactionCard({ transaction, selected, onSelect, suggestion }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  };

  const amount = Number(transaction.amount || transaction.montant || 0);

  return (
    <motion.div
      onClick={() => onSelect(transaction)}
      className={`p-4 rounded-xl border cursor-pointer transition-all ${
        selected
          ? 'border-cyan-500 bg-cyan-500/10'
          : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
      }`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      layout
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <p className="font-medium text-white truncate">
              {transaction.label || transaction.libelle || 'Transaction'}
            </p>
          </div>
          <p className="text-sm text-slate-400 mt-1 truncate">
            {transaction.bank_account || transaction.compte || ''}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {formatDate(transaction.date_operation || transaction.date)}
          </p>
        </div>

        <div className="text-right flex-shrink-0">
          <p className={`font-semibold ${amount >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {amount >= 0 ? '+' : ''}{amount.toFixed(2)} EUR
          </p>
          {suggestion && (
            <div className="mt-2">
              <AIConfidenceBadge
                confidence={suggestion.confidence}
                variant="pill"
                size="sm"
              />
            </div>
          )}
        </div>
      </div>

      {/* Match suggestion preview */}
      {suggestion && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-3 pt-3 border-t border-white/10"
        >
          <div className="flex items-center gap-2 text-xs text-cyan-400">
            <Sparkles className="w-3 h-3" />
            <span>Suggestion: {suggestion.invoice?.supplier || 'Facture'}</span>
            <span className="text-slate-500">|</span>
            <span>{suggestion.invoice?.amount?.toFixed(2) || 0} EUR</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

function InvoiceCard({ invoice, selected, onSelect, matchedTo }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  };

  const amount = Number(invoice.total_ttc || invoice.amount || 0);

  return (
    <motion.div
      onClick={() => onSelect(invoice)}
      className={`p-4 rounded-xl border cursor-pointer transition-all ${
        selected
          ? 'border-cyan-500 bg-cyan-500/10'
          : matchedTo
          ? 'border-emerald-500/30 bg-emerald-500/10'
          : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
      }`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      layout
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <p className="font-medium text-white truncate">
              {invoice.supplier || invoice.fournisseur || 'Fournisseur'}
            </p>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            {invoice.invoice_number || invoice.numero || 'N/A'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {formatDate(invoice.invoice_date || invoice.date)}
          </p>
        </div>

        <div className="text-right flex-shrink-0">
          <p className="font-semibold text-rose-400">-{amount.toFixed(2)} EUR</p>
          {matchedTo && (
            <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-full text-xs bg-emerald-500/20 text-emerald-400">
              <CheckCircle className="w-3 h-3" />
              Rapproche
            </span>
          )}
        </div>
      </div>

      {invoice.line_count > 0 && (
        <p className="text-xs text-slate-500 mt-2">
          {invoice.line_count} ligne{invoice.line_count > 1 ? 's' : ''}
        </p>
      )}
    </motion.div>
  );
}

function MatchPreview({ transaction, invoice, confidence, onConfirm, onReject, loading }) {
  if (!transaction || !invoice) return null;

  const txAmount = Math.abs(Number(transaction.amount || transaction.montant || 0));
  const invAmount = Number(invoice.total_ttc || invoice.amount || 0);
  const diff = Math.abs(txAmount - invAmount);
  const diffPct = invAmount > 0 ? (diff / invAmount) * 100 : 0;
  const isExact = diffPct < 0.1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="p-6 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-white">Apercu du rapprochement</h3>
        {confidence && (
          <AIConfidenceBadge confidence={confidence} variant="pill" />
        )}
      </div>

      {/* Visual match */}
      <div className="flex items-center gap-4 mb-6">
        {/* Transaction */}
        <div className="flex-1 p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <CreditCard className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-400">Transaction</span>
          </div>
          <p className="font-medium text-white truncate">
            {transaction.label || transaction.libelle}
          </p>
          <p className="text-lg font-semibold text-rose-400 mt-2">
            -{txAmount.toFixed(2)} EUR
          </p>
        </div>

        {/* Arrow */}
        <div className="flex-shrink-0">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
            isExact ? 'bg-emerald-500/20' : 'bg-amber-500/20'
          }`}>
            <Link2 className={`w-6 h-6 ${isExact ? 'text-emerald-400' : 'text-amber-400'}`} />
          </div>
        </div>

        {/* Invoice */}
        <div className="flex-1 p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-400">Facture</span>
          </div>
          <p className="font-medium text-white truncate">
            {invoice.supplier || invoice.fournisseur}
          </p>
          <p className="text-lg font-semibold text-rose-400 mt-2">
            -{invAmount.toFixed(2)} EUR
          </p>
        </div>
      </div>

      {/* Difference */}
      <div className={`p-4 rounded-xl mb-6 ${
        isExact ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-amber-500/10 border border-amber-500/20'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isExact ? (
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            )}
            <span className={isExact ? 'text-emerald-400' : 'text-amber-400'}>
              {isExact ? 'Montants identiques' : 'Ecart detecte'}
            </span>
          </div>
          <span className={`font-semibold ${isExact ? 'text-emerald-400' : 'text-amber-400'}`}>
            {diff.toFixed(2)} EUR ({diffPct.toFixed(1)}%)
          </span>
        </div>
      </div>

      {/* Details */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-3 rounded-lg bg-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Calendar className="w-3 h-3" />
            Date transaction
          </div>
          <p className="text-sm text-white">
            {transaction.date_operation || transaction.date || 'N/A'}
          </p>
        </div>
        <div className="p-3 rounded-lg bg-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Calendar className="w-3 h-3" />
            Date facture
          </div>
          <p className="text-sm text-white">
            {invoice.invoice_date || invoice.date || 'N/A'}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          variant="ghost"
          className="flex-1"
          onClick={onReject}
          disabled={loading}
        >
          <X className="w-4 h-4" />
          Annuler
        </Button>
        <Button
          variant="primary"
          className="flex-1"
          onClick={onConfirm}
          loading={loading}
        >
          <Check className="w-4 h-4" />
          Confirmer le match
        </Button>
      </div>
    </motion.div>
  );
}

function EmptyState({ type }) {
  const config = {
    transaction: {
      icon: CreditCard,
      title: 'Selectionnez une transaction',
      message: 'Cliquez sur une transaction a gauche pour voir les details et suggestions de match.',
    },
    invoice: {
      icon: FileText,
      title: 'Selectionnez une facture',
      message: 'Cliquez sur une facture pour la matcher avec la transaction selectionnee.',
    },
  };

  const { icon: Icon, title, message } = config[type] || config.transaction;

  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-slate-500" />
      </div>
      <h3 className="font-medium text-white mb-2">{title}</h3>
      <p className="text-sm text-slate-400 max-w-xs">{message}</p>
    </div>
  );
}

// ===========================================================================
// Main Component
// ===========================================================================

export default function ReconciliationSplitView({
  transactions = [],
  invoices = [],
  suggestions = [],
  onMatchCreated,
  isLoading,
}) {
  const queryClient = useQueryClient();

  // State
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [searchTx, setSearchTx] = useState('');
  const [searchInv, setSearchInv] = useState('');

  // Mutations
  const matchMutation = useMutation({
    mutationFn: ({ transactionId, invoiceId }) => createMatch(transactionId, invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries(['reconciliation']);
      setSelectedTransaction(null);
      setSelectedInvoice(null);
      onMatchCreated?.();
    },
  });

  // Filtered lists
  const filteredTransactions = useMemo(() => {
    if (!searchTx) return transactions;
    const lower = searchTx.toLowerCase();
    return transactions.filter(tx =>
      (tx.label || tx.libelle || '').toLowerCase().includes(lower) ||
      String(tx.amount || tx.montant || '').includes(lower)
    );
  }, [transactions, searchTx]);

  const filteredInvoices = useMemo(() => {
    if (!searchInv) return invoices;
    const lower = searchInv.toLowerCase();
    return invoices.filter(inv =>
      (inv.supplier || inv.fournisseur || '').toLowerCase().includes(lower) ||
      (inv.invoice_number || inv.numero || '').toLowerCase().includes(lower)
    );
  }, [invoices, searchInv]);

  // Get suggestion for selected transaction
  const currentSuggestion = useMemo(() => {
    if (!selectedTransaction) return null;
    return suggestions.find(s => s.txId === selectedTransaction.id);
  }, [selectedTransaction, suggestions]);

  // Handlers
  const handleSelectTransaction = useCallback((tx) => {
    setSelectedTransaction(tx);
    setSelectedInvoice(null);

    // Auto-select suggested invoice
    const suggestion = suggestions.find(s => s.txId === tx.id);
    if (suggestion) {
      const suggestedInvoice = invoices.find(inv => inv.id === suggestion.invoiceId);
      if (suggestedInvoice) {
        setSelectedInvoice(suggestedInvoice);
      }
    }
  }, [suggestions, invoices]);

  const handleConfirmMatch = () => {
    if (!selectedTransaction || !selectedInvoice) return;
    matchMutation.mutate({
      transactionId: selectedTransaction.id,
      invoiceId: selectedInvoice.id,
    });
  };

  const handleRejectMatch = () => {
    setSelectedInvoice(null);
  };

  return (
    <div className="flex h-[calc(100vh-200px)] gap-6">
      {/* Left panel - Transactions */}
      <div className="w-1/3 flex flex-col rounded-2xl bg-white/5 border border-white/10 overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <CreditCard className="w-5 h-5 text-slate-400" />
            <h3 className="font-semibold text-white">Transactions</h3>
            <span className="ml-auto px-2 py-0.5 rounded-full text-xs bg-white/10 text-slate-400">
              {filteredTransactions.length}
            </span>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchTx}
              onChange={(e) => setSearchTx(e.target.value)}
              placeholder="Rechercher..."
              className="w-full pl-9 pr-4 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {filteredTransactions.map((tx) => (
            <TransactionCard
              key={tx.id}
              transaction={tx}
              selected={selectedTransaction?.id === tx.id}
              onSelect={handleSelectTransaction}
              suggestion={suggestions.find(s => s.txId === tx.id)}
            />
          ))}
          {filteredTransactions.length === 0 && (
            <p className="text-center text-slate-500 py-8">Aucune transaction</p>
          )}
        </div>
      </div>

      {/* Middle panel - Match preview */}
      <div className="w-1/3 flex flex-col">
        <AnimatePresence mode="wait">
          {selectedTransaction && selectedInvoice ? (
            <MatchPreview
              key="preview"
              transaction={selectedTransaction}
              invoice={selectedInvoice}
              confidence={currentSuggestion?.confidence}
              onConfirm={handleConfirmMatch}
              onReject={handleRejectMatch}
              loading={matchMutation.isPending}
            />
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 rounded-2xl bg-white/5 border border-white/10"
            >
              <EmptyState type={selectedTransaction ? 'invoice' : 'transaction'} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Suggestions AI */}
        {selectedTransaction && currentSuggestion && !selectedInvoice && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20"
          >
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-medium text-cyan-400">Suggestion IA</span>
              <AIConfidenceBadge confidence={currentSuggestion.confidence} size="sm" />
            </div>
            <p className="text-sm text-slate-300">
              Match suggere avec la facture <strong>{currentSuggestion.invoice?.supplier}</strong>
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => {
                const inv = invoices.find(i => i.id === currentSuggestion.invoiceId);
                if (inv) setSelectedInvoice(inv);
              }}
            >
              Voir la suggestion
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </motion.div>
        )}
      </div>

      {/* Right panel - Invoices */}
      <div className="w-1/3 flex flex-col rounded-2xl bg-white/5 border border-white/10 overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-5 h-5 text-slate-400" />
            <h3 className="font-semibold text-white">Factures</h3>
            <span className="ml-auto px-2 py-0.5 rounded-full text-xs bg-white/10 text-slate-400">
              {filteredInvoices.length}
            </span>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchInv}
              onChange={(e) => setSearchInv(e.target.value)}
              placeholder="Rechercher..."
              className="w-full pl-9 pr-4 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {filteredInvoices.map((inv) => (
            <InvoiceCard
              key={inv.id}
              invoice={inv}
              selected={selectedInvoice?.id === inv.id}
              onSelect={(i) => selectedTransaction && setSelectedInvoice(i)}
              matchedTo={inv.match_status === 'matched'}
            />
          ))}
          {filteredInvoices.length === 0 && (
            <p className="text-center text-slate-500 py-8">Aucune facture</p>
          )}
        </div>
      </div>
    </div>
  );
}
