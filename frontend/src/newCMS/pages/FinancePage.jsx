/**
 * Finance Page - Rapprochement Assisté par IA (Scénario 3.4)
 * Vue unifiée : Transactions | Rapprochement | Comptes | Règles
 */

import { useMemo, useState } from 'react';
import {
  Wallet,
  Activity,
  Link2,
  Landmark,
  Settings,
  CheckCircle2,
  Bot,
  HelpCircle,
  Download,
  Search,
  Filter,
  ChevronRight,
  FileText,
  CreditCard,
  ArrowLeftRight,
  Lightbulb,
  X,
  Check,
  AlertTriangle,
  RefreshCw,
  Tag,
} from 'lucide-react';
import { useNewCMSQuery } from '../hooks/useNewCMSQuery.js';
import {
  fetchFinanceOverview,
  fetchFinanceTransactions,
} from '../../api/newcms.js';

const formatCurrency = (value) => {
  if (typeof value !== 'number') return value ?? '—';
  return value.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
};

// Tab Navigation
function TabNav({ tabs, activeTab, onTabChange }) {
  return (
    <div className="flex gap-1 p-1 rounded-xl bg-slate-800/50 border border-white/10">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === tab.id
              ? 'bg-blue-500 text-white'
              : 'text-slate-400 hover:text-white hover:bg-white/10'
          }`}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
}

// Reconciliation Stats Component
function ReconciliationStats({ stats }) {
  const fallback = [
    { label: 'Rapprochées', value: '847', percent: '89%', amount: '124 350€', icon: CheckCircle2, color: 'emerald' },
    { label: 'Suggestions', value: '67', percent: '7%', amount: '8 720€', icon: Bot, color: 'blue' },
    { label: 'Non matchées', value: '38', percent: '4%', amount: '4 230€', icon: HelpCircle, color: 'amber' },
  ];

  const display = stats?.length ? stats : fallback;

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <Link2 className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">État du Rapprochement</h3>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        {display.map((stat, idx) => (
          <div key={idx} className={`p-4 rounded-xl bg-${stat.color}-500/10 border border-${stat.color}-500/20`}>
            <div className="flex items-center gap-2 mb-2">
              <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
              <span className="text-sm text-slate-400">{stat.label}</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">{stat.value} <span className="text-sm text-slate-400">({stat.percent})</span></div>
            <div className="text-sm text-slate-400">{stat.amount}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <button className="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium flex items-center gap-2">
          <Bot className="w-4 h-4" /> Appliquer toutes les suggestions (67)
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          <Download className="w-4 h-4" /> Importer relevé
        </button>
      </div>
    </div>
  );
}

// Match Card Component
function MatchCard({ match }) {
  const getConfidenceColor = (confidence) => {
    if (confidence >= 90) return 'text-emerald-400 bg-emerald-500/20';
    if (confidence >= 70) return 'text-amber-400 bg-amber-500/20';
    return 'text-rose-400 bg-rose-500/20';
  };

  return (
    <div className="p-4 rounded-xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-slate-400">Match #{match.id}</span>
        <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(match.confidence)}`}>
          Confiance: {match.confidence}%
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 items-center">
        {/* Bank Statement */}
        <div className="p-3 rounded-lg bg-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <CreditCard className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-slate-400 uppercase">Relevé Bancaire</span>
          </div>
          <p className="text-sm text-white font-medium">{match.bankLabel}</p>
          <p className="text-sm text-slate-400">{match.bankDate}</p>
          <p className={`text-lg font-bold ${match.bankAmount < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {match.bankAmount.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
          </p>
        </div>

        {/* Link Icon */}
        <div className="flex justify-center">
          <div className="p-3 rounded-full bg-blue-500/20">
            <ArrowLeftRight className="w-6 h-6 text-blue-400" />
          </div>
        </div>

        {/* Invoice(s) */}
        <div className="p-3 rounded-lg bg-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-purple-400" />
            <span className="text-xs text-slate-400 uppercase">Facture{match.invoices.length > 1 ? 's' : ''}</span>
          </div>
          {match.invoices.map((invoice, idx) => (
            <div key={idx} className="mb-1">
              <p className="text-sm text-white font-medium">{invoice.ref}</p>
              <p className="text-sm text-slate-400">{invoice.amount.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</p>
            </div>
          ))}
          {match.invoices.length > 1 && (
            <p className="text-xs text-emerald-400 mt-1">
              Total: {match.invoices.reduce((sum, i) => sum + i.amount, 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })} ✓
            </p>
          )}
        </div>
      </div>

      {/* Suggestion */}
      <div className="flex items-start gap-2 mt-4 p-3 rounded-lg bg-blue-500/10">
        <Lightbulb className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
        <span className="text-sm text-slate-300">{match.suggestion}</span>
      </div>

      {/* Actions */}
      <div className="flex gap-2 mt-4">
        <button className="px-4 py-2 rounded-lg bg-emerald-500 text-white text-sm font-medium flex items-center gap-2">
          <Check className="w-4 h-4" /> Valider
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          👁️ Détails
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          <X className="w-4 h-4" /> Rejeter
        </button>
      </div>
    </div>
  );
}

// AI Suggestions Section
function AISuggestions({ matches }) {
  const display = matches?.length
    ? matches
    : [
        {
          id: 1,
          confidence: 98,
          bankLabel: 'METRO CASH',
          bankDate: '10/12',
          bankAmount: -847.32,
          invoices: [{ ref: 'Metro #F2025-4521', amount: 847.32 }],
          suggestion: 'Match exact: même montant, même date, nom fournisseur reconnu',
        },
        {
          id: 2,
          confidence: 87,
          bankLabel: 'VIR BRAKE',
          bankDate: '08/12',
          bankAmount: -1523.40,
          invoices: [
            { ref: 'Brake #B-7842', amount: 987.20 },
            { ref: 'Brake #B-7901', amount: 536.20 },
          ],
          suggestion: 'Paiement groupé détecté (2 factures = 1 virement)',
        },
      ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-white">Suggestions IA</h3>
          <span className="text-sm text-slate-400">({display.length} matchs proposés)</span>
        </div>
        <button className="px-4 py-2 rounded-lg bg-emerald-500 text-white text-sm font-medium flex items-center gap-2">
          <Check className="w-4 h-4" /> Tout valider
        </button>
      </div>

      <div className="space-y-4">
        {display.map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>

      <button className="w-full mt-4 py-3 text-center text-sm text-blue-400 hover:text-blue-300">
        Voir les 65 autres suggestions...
      </button>
    </div>
  );
}

// Unmatched Transactions
function UnmatchedTransactions({ transactions }) {
  const display = transactions?.length
    ? transactions
    : [
        { date: '05/12', label: 'CB AMAZON 45.99', amount: -45.99 },
        { date: '03/12', label: 'VIR LOYER LOCAL', amount: -1200 },
        { date: '01/12', label: 'PRLV ASSURANCE', amount: -234.5 },
      ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-white">Non Matchées</h3>
          <span className="text-sm text-slate-400">({display.length} transactions)</span>
        </div>
        <button className="p-2 rounded-lg bg-white/10 text-slate-300">
          <Search className="w-4 h-4" />
        </button>
      </div>

      <table className="w-full">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-2 text-xs text-slate-400">Date</th>
            <th className="text-left py-2 text-xs text-slate-400">Libellé</th>
            <th className="text-right py-2 text-xs text-slate-400">Montant</th>
            <th className="text-right py-2 text-xs text-slate-400">Actions</th>
          </tr>
        </thead>
        <tbody>
          {display.map((tx, idx) => (
            <tr key={idx} className="border-b border-white/5">
              <td className="py-3 text-sm text-slate-400">{tx.date}</td>
              <td className="py-3 text-sm text-white">{tx.label}</td>
              <td className="py-3 text-sm text-right text-rose-400">
                {tx.amount.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
              </td>
              <td className="py-3 text-right">
                <div className="flex justify-end gap-1">
                  <button className="px-2 py-1 rounded text-xs bg-white/10 text-slate-300 flex items-center gap-1">
                    <Tag className="w-3 h-3" /> Catégoriser
                  </button>
                  <button className="px-2 py-1 rounded text-xs bg-white/10 text-slate-300 flex items-center gap-1">
                    <Link2 className="w-3 h-3" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Transactions List View
function TransactionsView({ transactions }) {
  const display = transactions?.length
    ? transactions
    : [
        { date: '11/12', label: 'METRO CASH', amount: -847.32, category: 'Achats', status: 'matched' },
        { date: '10/12', label: 'CB CLIENT 127', amount: 2847.0, category: 'Ventes', status: 'matched' },
        { date: '08/12', label: 'VIR BRAKE', amount: -1523.4, category: 'Achats', status: 'matched' },
        { date: '05/12', label: 'CB AMAZON', amount: -45.99, category: null, status: 'pending' },
        { date: '03/12', label: 'VIR LOYER', amount: -1200.0, category: 'Loyer', status: 'recurrent' },
      ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'matched':
        return <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-400">Rapproché</span>;
      case 'pending':
        return <span className="px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-400">En attente</span>;
      case 'recurrent':
        return <span className="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400">Récurrent</span>;
      default:
        return null;
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      {/* Filters */}
      <div className="flex items-center gap-4 mb-4 p-4 rounded-xl bg-slate-700/30">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Rechercher une transaction..."
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-slate-800 border border-white/10 text-white placeholder-slate-500"
            />
          </div>
        </div>
        <button className="px-3 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          <Filter className="w-4 h-4" /> Filtres
        </button>
        <button className="px-3 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          📅 Période ▼
        </button>
      </div>

      {/* Table */}
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-3 text-xs text-slate-400">Date</th>
            <th className="text-left py-3 text-xs text-slate-400">Libellé</th>
            <th className="text-right py-3 text-xs text-slate-400">Montant</th>
            <th className="text-left py-3 text-xs text-slate-400">Catégorie</th>
            <th className="text-left py-3 text-xs text-slate-400">Statut</th>
            <th className="text-right py-3 text-xs text-slate-400">Actions</th>
          </tr>
        </thead>
        <tbody>
          {display.map((tx, idx) => (
            <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
              <td className="py-3 text-sm text-slate-400">{tx.date}</td>
              <td className="py-3 text-sm text-white">{tx.label}</td>
              <td className={`py-3 text-sm text-right font-medium ${tx.amount < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {tx.amount.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
              </td>
              <td className="py-3 text-sm text-slate-400">{tx.category || '—'}</td>
              <td className="py-3">{getStatusBadge(tx.status)}</td>
              <td className="py-3 text-right">
                <button className="p-1.5 rounded hover:bg-white/10 text-slate-400">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Accounts Overview
function AccountsView() {
  const accounts = [
    { name: 'Compte Courant Pro', bank: 'LCL', balance: 24567.89, trend: 'up' },
    { name: 'Livret Pro', bank: 'LCL', balance: 15000.00, trend: 'stable' },
    { name: 'Compte Épargne', bank: 'BNP', balance: 8234.50, trend: 'up' },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {accounts.map((account, idx) => (
          <div key={idx} className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-xl bg-blue-500/20">
                <Landmark className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h4 className="font-medium text-white">{account.name}</h4>
                <p className="text-sm text-slate-400">{account.bank}</p>
              </div>
            </div>
            <div className="text-2xl font-bold text-white">
              {account.balance.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Main Component
export default function FinancePage() {
  const [activeTab, setActiveTab] = useState('rapprochement');
  const overviewQuery = useNewCMSQuery(['newcms-finance-overview'], () => fetchFinanceOverview());
  const transactionsQuery = useNewCMSQuery(['newcms-finance-transactions'], () => fetchFinanceTransactions({ page: 1, size: 20 }));
  const isLoading = overviewQuery.isLoading || transactionsQuery.isLoading;
  const isError = overviewQuery.isError || transactionsQuery.isError;

  const reconciliationStats = useMemo(() => {
    const stats = overviewQuery.data?.reconciliation_stats;
    if (!stats) return null;
    return [
      {
        label: 'Rapprochées',
        value: String(stats.matched_count ?? 0),
        percent: `${Math.round(stats.matched_percentage ?? 0)}%`,
        amount: formatCurrency(stats.total_amount_matched ?? 0),
        icon: CheckCircle2,
        color: 'emerald',
      },
      {
        label: 'Suggestions',
        value: String(stats.pending_count ?? 0),
        percent: `${Math.round(stats.pending_percentage ?? 0)}%`,
        amount: formatCurrency(stats.total_amount_pending ?? 0),
        icon: Bot,
        color: 'blue',
      },
      {
        label: 'Non matchées',
        value: String(stats.unmatched_count ?? 0),
        percent: `${Math.round(stats.unmatched_percentage ?? 0)}%`,
        amount: formatCurrency(stats.total_amount_unmatched ?? stats.total_amount_pending ?? 0),
        icon: HelpCircle,
        color: 'amber',
      },
    ];
  }, [overviewQuery.data]);

  const aiSuggestions = useMemo(() => {
    if (!overviewQuery.data?.ai_suggestions) return null;
    return overviewQuery.data.ai_suggestions.map((sugg, idx) => ({
      id: sugg.suggestion_id || idx,
      confidence: Math.round((sugg.confidence ?? 0) * 100) || sugg.confidence || 0,
      bankLabel: sugg.transaction_label || sugg.label || 'Transaction',
      bankDate: sugg.transaction_date,
      bankAmount: sugg.transaction_amount ?? 0,
      invoices: (sugg.matched_invoices_info || []).map((inv) => ({
        ref: inv.invoice_number || inv.supplier_name || inv.id,
        amount: inv.amount ?? 0,
      })),
      suggestion: sugg.explanation || 'Suggestion IA',
    }));
  }, [overviewQuery.data]);

  const recentUnmatched = useMemo(() => {
    const tx = transactionsQuery.data?.transactions;
    if (!tx) return null;
    return tx.filter((t) => t.reconciled === false).map((t) => ({
      date: t.date,
      label: t.label,
      amount: t.amount,
    }));
  }, [transactionsQuery.data]);

  const recentTransactions = useMemo(() => {
    const tx = transactionsQuery.data?.transactions;
    if (!tx) return null;
    return tx.map((t) => ({
      date: t.date,
      label: t.label,
      amount: t.amount,
      category: t.category,
      status: t.reconciled ? 'matched' : 'pending',
    }));
  }, [transactionsQuery.data]);

  const tabs = [
    { id: 'transactions', label: 'Transactions', icon: <Activity className="w-4 h-4" /> },
    { id: 'rapprochement', label: 'Rapprochement', icon: <Link2 className="w-4 h-4" /> },
    { id: 'comptes', label: 'Comptes', icon: <Landmark className="w-4 h-4" /> },
    { id: 'regles', label: 'Règles', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {isError && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          Impossible de charger les données Finance (API newCMS). Affichage du fallback démo.
        </div>
      )}
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Wallet className="w-7 h-7 text-purple-400" />
            Finance
          </h1>
          <p className="text-slate-400">Trésorerie & Rapprochement</p>
        </div>
        <TabNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      </div>

      {/* Content based on active tab */}
      {activeTab === 'rapprochement' && (
        <div className="space-y-6">
          <ReconciliationStats stats={reconciliationStats} />
          <AISuggestions matches={aiSuggestions} />
          <UnmatchedTransactions transactions={recentUnmatched} />
        </div>
      )}

      {activeTab === 'transactions' && <TransactionsView transactions={recentTransactions} />}

      {activeTab === 'comptes' && <AccountsView />}

      {activeTab === 'regles' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <Settings className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Règles de Catégorisation</h3>
          <p className="text-slate-400">Automatisez le traitement de vos transactions</p>
        </div>
      )}
    </div>
  );
}
