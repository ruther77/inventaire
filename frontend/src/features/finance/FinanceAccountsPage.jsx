/**
 * FinanceAccountsPage - Gestion des comptes bancaires
 * Design: Finance-comptes.html mockup
 */

import React from 'react';
import { motion } from 'framer-motion';
import {
  Building2,
  Banknote,
  PiggyBank,
  RefreshCw,
  Plus,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  AlertCircle,
} from 'lucide-react';
import clsx from 'clsx';
import Button from '../../components/ui/Button.jsx';
import { useFinanceAccountsOverviewStats } from '../../hooks/useFinanceCategories.js';

// Format currency
const formatCurrency = (val) => {
  if (val === null || val === undefined) return '0,00 €';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
  }).format(val);
};

// Account type config
const accountTypeConfig = {
  bank: { icon: Building2, bg: 'bg-blue-500/20', text: 'text-blue-400' },
  cash: { icon: Banknote, bg: 'bg-emerald-500/20', text: 'text-emerald-400' },
  savings: { icon: PiggyBank, bg: 'bg-violet-500/20', text: 'text-violet-400' },
  default: { icon: Building2, bg: 'bg-slate-500/20', text: 'text-slate-400' },
};

// Get account type from label
const getAccountType = (label) => {
  const l = (label || '').toLowerCase();
  if (l.includes('caisse') || l.includes('espèces') || l.includes('cash')) return 'cash';
  if (l.includes('livret') || l.includes('épargne') || l.includes('savings')) return 'savings';
  return 'bank';
};

// Account Card Component
function AccountCard({ account, onClick }) {
  const type = getAccountType(account.label);
  const config = accountTypeConfig[type] || accountTypeConfig.default;
  const Icon = config.icon;

  const balance = Number(account.balance) || 0;
  const incomeTotal = Number(account.income_total) || 0;
  const expenseTotal = Number(account.expense_total) || 0;
  const transactionCount = Number(account.transaction_count) || 0;
  const unmatchedCount = Number(account.unmatched_count) || 0;

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      onClick={onClick}
      className="rounded-2xl border border-white/10 bg-white/5 p-6 cursor-pointer hover:bg-white/10 transition-all"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className={clsx('p-3 rounded-xl', config.bg)}>
          <Icon className={clsx('w-6 h-6', config.text)} />
        </div>
        <span className="px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-400 text-xs font-medium">
          Actif
        </span>
      </div>

      {/* Account Info */}
      <h3 className="text-lg font-semibold text-white mb-1">
        {account.label || 'Compte'}
      </h3>
      <p className="text-sm text-slate-400 mb-4">
        {account.account_number || account.iban || '—'}
      </p>

      {/* Balance */}
      <div className={clsx(
        'text-3xl font-bold mb-5',
        balance >= 0 ? 'text-emerald-400' : 'text-rose-400'
      )}>
        {formatCurrency(balance)}
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/10">
        <div>
          <p className="text-xs text-slate-500">Entrées (30j)</p>
          <p className="text-sm font-semibold text-emerald-400 flex items-center gap-1">
            <ArrowUpRight className="w-3 h-3" />
            +{formatCurrency(incomeTotal)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Sorties (30j)</p>
          <p className="text-sm font-semibold text-rose-400 flex items-center gap-1">
            <ArrowDownRight className="w-3 h-3" />
            -{formatCurrency(expenseTotal)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Transactions</p>
          <p className="text-sm font-semibold text-white">{transactionCount}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Non rapprochées</p>
          <p className={clsx(
            'text-sm font-semibold',
            unmatchedCount > 0 ? 'text-amber-400' : 'text-slate-400'
          )}>
            {unmatchedCount}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

// Add Account Card
function AddAccountCard({ onClick }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      onClick={onClick}
      className="rounded-2xl border-2 border-dashed border-white/10 bg-white/[0.02] p-12 cursor-pointer hover:border-amber-500/50 hover:bg-white/5 transition-all flex flex-col items-center justify-center"
    >
      <div className="p-4 rounded-full bg-white/5 mb-4">
        <Plus className="w-8 h-8 text-slate-400" />
      </div>
      <p className="text-slate-400 text-sm">Ajouter un compte</p>
    </motion.div>
  );
}

export default function FinanceAccountsPage() {
  const accountsStatsQuery = useFinanceAccountsOverviewStats({});
  const accountsData = accountsStatsQuery.data;

  // Handle both array and object responses
  const accounts = Array.isArray(accountsData)
    ? accountsData
    : accountsData?.accounts || [];

  // Calculate totals
  const totalBalance = accounts.reduce((sum, acc) => sum + (Number(acc.balance) || 0), 0);
  const totalIncome = accounts.reduce((sum, acc) => sum + (Number(acc.income_total) || 0), 0);
  const totalExpense = accounts.reduce((sum, acc) => sum + (Number(acc.expense_total) || 0), 0);
  const netChange = totalIncome - totalExpense;

  const handleAddAccount = () => {
    alert('Ajouter un compte - Fonctionnalité à venir');
  };

  const handleAccountClick = (account) => {
    alert(`Détail du compte: ${account.label}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-amber-500/20">
            <Building2 className="w-8 h-8 text-amber-400" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Finance</p>
            <h1 className="text-2xl font-semibold text-white">Comptes bancaires</h1>
          </div>
        </div>
        <Button
          variant="ghost"
          onClick={() => accountsStatsQuery.refetch()}
          loading={accountsStatsQuery.isLoading}
        >
          <RefreshCw className="w-4 h-4" />
          Rafraîchir
        </Button>
      </header>

      {/* Total Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/20 to-amber-500/5 p-8"
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <p className="text-sm text-slate-400 mb-2">Solde total consolidé</p>
            <div className="text-4xl md:text-5xl font-bold text-amber-400">
              {formatCurrency(totalBalance)}
            </div>
            <div className={clsx(
              'flex items-center gap-1 mt-2 text-sm',
              netChange >= 0 ? 'text-emerald-400' : 'text-rose-400'
            )}>
              {netChange >= 0 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span>
                {netChange >= 0 ? '+' : ''}{formatCurrency(netChange)} ce mois
              </span>
            </div>
          </div>

          <div className="text-right">
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-3">
              <Clock className="w-4 h-4" />
              Dernière synchronisation: maintenant
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => accountsStatsQuery.refetch()}
              loading={accountsStatsQuery.isLoading}
              className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
            >
              <RefreshCw className="w-4 h-4" />
              Synchroniser
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Loading State */}
      {accountsStatsQuery.isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-2xl border border-white/10 bg-white/5 p-6 animate-pulse"
            >
              <div className="w-12 h-12 rounded-xl bg-white/10 mb-4" />
              <div className="h-5 w-32 bg-white/10 rounded mb-2" />
              <div className="h-4 w-24 bg-white/10 rounded mb-4" />
              <div className="h-8 w-40 bg-white/10 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Accounts Grid */}
      {!accountsStatsQuery.isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {accounts.map((account) => (
            <AccountCard
              key={account.id}
              account={account}
              onClick={() => handleAccountClick(account)}
            />
          ))}
          <AddAccountCard onClick={handleAddAccount} />
        </motion.div>
      )}

      {/* Empty State */}
      {!accountsStatsQuery.isLoading && accounts.length === 0 && (
        <div className="text-center py-12">
          <div className="p-4 rounded-full bg-slate-500/10 w-fit mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-slate-500" />
          </div>
          <p className="text-slate-400">Aucun compte configuré</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={handleAddAccount}
          >
            <Plus className="w-4 h-4" />
            Ajouter votre premier compte
          </Button>
        </div>
      )}
    </div>
  );
}
