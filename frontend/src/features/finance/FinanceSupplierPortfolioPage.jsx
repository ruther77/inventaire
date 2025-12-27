/**
 * FinanceSupplierPortfolioPage - Portefeuille Fournisseurs
 * Design: finance-portefeuille.html mockup
 */

import React from 'react';
import { motion } from 'framer-motion';
import {
  Store,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  FileText,
  ShoppingCart,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import clsx from 'clsx';
import Button from '../../components/ui/Button.jsx';
import { useSuppliersPaginated, useSupplierScoringOverview } from '../../hooks/useSupplierScoring.js';

// Format currency
const formatCurrency = (val) => {
  if (val === null || val === undefined) return '0 €';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(val);
};

// Get score badge config
const getScoreConfig = (score) => {
  if (score >= 80) return { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Excellent' };
  if (score >= 60) return { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'Correct' };
  return { bg: 'bg-rose-500/20', text: 'text-rose-400', label: 'À surveiller' };
};

// Summary Card Component
function SummaryCard({ label, value, detail, valueColor = 'text-white', icon: Icon }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="rounded-2xl border border-white/10 bg-white/5 p-6"
    >
      <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
        {Icon && <Icon className="w-4 h-4" />}
        {label}
      </div>
      <div className={clsx('text-3xl font-bold', valueColor)}>
        {value}
      </div>
      {detail && (
        <p className="text-sm text-slate-500 mt-2">{detail}</p>
      )}
    </motion.div>
  );
}

// Supplier Card Component
function SupplierCard({ supplier, onClick }) {
  const score = Number(supplier.overall_score || supplier.score || 0);
  const scoreConfig = getScoreConfig(score);
  const encours = Number(supplier.outstanding_amount || supplier.encours || 0);
  const achats12m = Number(supplier.total_purchases_12m || supplier.total_purchases || 0);
  const delaiPaiement = supplier.payment_delay_days || supplier.payment_terms || 30;
  const nextDueDate = supplier.next_due_date;

  // Calculate if overdue
  const isOverdue = nextDueDate && new Date(nextDueDate) < new Date();

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      onClick={onClick}
      className="rounded-2xl border border-white/10 bg-white/5 p-6 cursor-pointer hover:bg-white/10 transition-all"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center text-xl font-bold text-blue-400">
          {(supplier.name || 'F')[0].toUpperCase()}
        </div>
        <span className={clsx(
          'px-3 py-1 rounded-lg text-xs font-semibold',
          scoreConfig.bg,
          scoreConfig.text
        )}>
          Score: {score}/100
        </span>
      </div>

      {/* Name & Category */}
      <h3 className="text-lg font-semibold text-white mb-1">
        {supplier.name || 'Fournisseur'}
      </h3>
      <p className="text-sm text-slate-400 mb-4">
        {supplier.category || 'Fournisseur'}
      </p>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 py-4 border-t border-b border-white/10">
        <div>
          <p className="text-xs text-slate-500 mb-1">Encours</p>
          <p className={clsx(
            'text-base font-semibold',
            encours > 0 ? 'text-rose-400' : 'text-slate-400'
          )}>
            {formatCurrency(encours)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500 mb-1">Achats (12m)</p>
          <p className="text-base font-semibold text-white">
            {formatCurrency(achats12m)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500 mb-1">Délai paiement</p>
          <p className="text-base font-semibold text-white">
            {delaiPaiement} jours
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500 mb-1">Prochaine échéance</p>
          <p className={clsx(
            'text-base font-semibold',
            isOverdue ? 'text-rose-400' : 'text-amber-400'
          )}>
            {isOverdue
              ? 'Dépassée'
              : nextDueDate
              ? new Date(nextDueDate).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
              : '—'}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 mt-4">
        <button
          onClick={(e) => { e.stopPropagation(); alert('Voir factures'); }}
          className="flex-1 px-4 py-2.5 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-400 text-sm font-medium hover:bg-amber-500/30 transition-colors"
        >
          Voir factures
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); alert('Commander'); }}
          className="flex-1 px-4 py-2.5 rounded-lg border border-white/10 text-slate-300 text-sm font-medium hover:bg-white/5 transition-colors"
        >
          Commander
        </button>
      </div>
    </motion.div>
  );
}

export default function FinanceSupplierPortfolioPage() {
  const overviewQuery = useSupplierScoringOverview({});
  const suppliersQuery = useSuppliersPaginated({ page: 1, per_page: 50 });

  const overview = overviewQuery.data ?? {};
  const suppliersData = suppliersQuery.data;

  // Handle both array and paginated response
  const suppliers = Array.isArray(suppliersData)
    ? suppliersData
    : suppliersData?.items || suppliersData?.suppliers || [];

  // Calculate totals from overview or suppliers
  const totalEncours = overview.total_outstanding || suppliers.reduce(
    (sum, s) => sum + (Number(s.outstanding_amount) || 0), 0
  );
  const dueWithin7Days = overview.due_within_7_days || 0;
  const monthlyPurchases = overview.monthly_purchases || overview.total_purchases_30d || 0;
  const pendingInvoices = overview.pending_invoices || 0;
  const upcomingInvoices = overview.upcoming_invoices || 0;

  const handleSupplierClick = (supplier) => {
    alert(`Détail fournisseur: ${supplier.name}`);
  };

  const handleRefresh = () => {
    overviewQuery.refetch();
    suppliersQuery.refetch();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-amber-500/20">
            <Store className="w-8 h-8 text-amber-400" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Finance</p>
            <h1 className="text-2xl font-semibold text-white">Portefeuille Fournisseurs</h1>
          </div>
        </div>
        <Button
          variant="ghost"
          onClick={handleRefresh}
          loading={overviewQuery.isLoading || suppliersQuery.isLoading}
        >
          <RefreshCw className="w-4 h-4" />
          Rafraîchir
        </Button>
      </header>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard
          label="Encours total fournisseurs"
          value={formatCurrency(totalEncours)}
          detail={`${pendingInvoices} factures en attente`}
          valueColor="text-rose-400"
          icon={AlertTriangle}
        />
        <SummaryCard
          label="Échéances < 7 jours"
          value={formatCurrency(dueWithin7Days)}
          detail={`${upcomingInvoices} factures à payer`}
          valueColor="text-amber-400"
          icon={Clock}
        />
        <SummaryCard
          label="Achats ce mois"
          value={formatCurrency(monthlyPurchases)}
          detail={
            overview.monthly_trend >= 0
              ? `+${overview.monthly_trend?.toFixed(0) || 0}% vs mois dernier`
              : `${overview.monthly_trend?.toFixed(0) || 0}% vs mois dernier`
          }
          valueColor="text-white"
          icon={ShoppingCart}
        />
      </div>

      {/* Suppliers Grid */}
      {suppliersQuery.isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="rounded-2xl border border-white/10 bg-white/5 p-6 animate-pulse"
            >
              <div className="flex justify-between mb-5">
                <div className="w-12 h-12 rounded-xl bg-white/10" />
                <div className="w-24 h-6 rounded-lg bg-white/10" />
              </div>
              <div className="h-5 w-32 bg-white/10 rounded mb-2" />
              <div className="h-4 w-24 bg-white/10 rounded mb-4" />
              <div className="grid grid-cols-2 gap-4 py-4">
                {[1, 2, 3, 4].map((j) => (
                  <div key={j}>
                    <div className="h-3 w-16 bg-white/10 rounded mb-2" />
                    <div className="h-5 w-20 bg-white/10 rounded" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : suppliers.length > 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {suppliers.map((supplier) => (
            <SupplierCard
              key={supplier.id || supplier.name}
              supplier={supplier}
              onClick={() => handleSupplierClick(supplier)}
            />
          ))}
        </motion.div>
      ) : (
        <div className="text-center py-12">
          <div className="p-4 rounded-full bg-slate-500/10 w-fit mx-auto mb-4">
            <Store className="w-8 h-8 text-slate-500" />
          </div>
          <p className="text-slate-400">Aucun fournisseur trouvé</p>
          <p className="text-sm text-slate-500 mt-1">
            Les fournisseurs apparaîtront après l'import de factures
          </p>
        </div>
      )}
    </div>
  );
}
