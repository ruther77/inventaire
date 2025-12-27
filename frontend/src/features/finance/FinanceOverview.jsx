/**
 * Page Finance Overview - Dashboard de trésorerie principal.
 *
 * Cette page permet de visualiser et analyser la trésorerie de l'entreprise.
 * Elle affiche:
 * - Un hero avec le solde actuel de trésorerie et la tendance
 * - Des onglets de sélection de période (7j, 30j, 90j, 12m, tout)
 * - Un graphique interactif d'évolution de la trésorerie
 * - Les KPIs principaux (entrées, sorties, solde net, alertes)
 * - Les dernières transactions bancaires
 *
 * Fonctionnalités principales:
 * - Visualisation multi-périodes avec graphique à barres
 * - Calcul automatique des tendances et variations
 * - Affichage des anomalies et rapprochements en attente
 * - Export CSV des données
 * - Rafraîchissement manuel des données
 *
 * @component
 *
 * @example
 * <FinanceOverview />
 */

import React, { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  ArrowDownCircle,
  ArrowUpCircle,
  Activity,
  Download,
  Calendar,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import clsx from 'clsx';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useFinanceMatches, useFinanceAnomalies, useFinanceTransactions } from '../../hooks/useFinance.js';
import {
  useFinanceTimeline,
  useFinanceTreasury,
} from '../../hooks/useFinanceCategories.js';
import { roundAmount } from '../../utils/banking.js';
import QueryErrorState from '../../components/feedback/QueryErrorState.jsx';

// Format currency
const formatCurrency = (val) => {
  if (val === null || val === undefined) return '0,00 €';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
  }).format(val);
};

// Format compact currency
const formatCompact = (val) => {
  if (val === null || val === undefined) return '0 €';
  if (Math.abs(val) >= 1000000) {
    return `${(val / 1000000).toFixed(1)}M €`;
  }
  if (Math.abs(val) >= 1000) {
    return `${(val / 1000).toFixed(1)}k €`;
  }
  return `${val.toFixed(0)} €`;
};

// Period config
const PERIODS = [
  { key: '7d', label: '7 jours', days: 7 },
  { key: '30d', label: '30 jours', days: 30 },
  { key: '90d', label: '90 jours', days: 90 },
  { key: '12m', label: '12 mois', days: 365 },
  { key: 'all', label: 'Tout', days: null },
];

// Period Tabs Component
function PeriodTabs({ value, onChange }) {
  return (
    <div className="flex gap-1 p-1.5 rounded-xl bg-white/5 border border-white/10">
      {PERIODS.map((period) => (
        <button
          key={period.key}
          onClick={() => onChange(period.key)}
          className={clsx(
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            value === period.key
              ? 'bg-amber-500/20 text-amber-400'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          )}
        >
          {period.label}
        </button>
      ))}
    </div>
  );
}

// Custom Tooltip for Bar Chart
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-slate-900/95 border border-white/10 rounded-xl p-4 shadow-xl min-w-[200px]">
      <p className="text-xs text-slate-400 mb-2">{data.period || label}</p>
      <p className="text-2xl font-bold text-amber-400 mb-3">
        {formatCurrency(data.balance || data.cumulative_balance)}
      </p>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-slate-400 flex items-center gap-1">
            <ArrowUpCircle className="w-3 h-3 text-emerald-400" />
            Entrées
          </span>
          <span className="text-emerald-400 font-medium">
            +{formatCurrency(data.inflow)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400 flex items-center gap-1">
            <ArrowDownCircle className="w-3 h-3 text-rose-400" />
            Sorties
          </span>
          <span className="text-rose-400 font-medium">
            -{formatCurrency(data.outflow)}
          </span>
        </div>
      </div>
    </div>
  );
}

// Transaction Row
function TransactionRow({ tx, onClick }) {
  const isPositive = tx.direction === 'IN' || Number(tx.amount) > 0;
  const amount = Math.abs(Number(tx.amount) || 0);

  return (
    <motion.tr
      whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
      onClick={onClick}
      className="cursor-pointer border-b border-white/5"
    >
      <td className="px-4 py-4 text-sm text-slate-400">
        {tx.transaction_date
          ? new Date(tx.transaction_date).toLocaleDateString('fr-FR', {
              day: 'numeric',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
            })
          : '—'}
      </td>
      <td className="px-4 py-4">
        <span className="font-medium text-white">{tx.label || tx.description || '—'}</span>
      </td>
      <td className="px-4 py-4 text-sm text-slate-400">
        {tx.category_name || tx.category || '—'}
      </td>
      <td className="px-4 py-4 text-sm text-slate-400">
        {tx.account_label || tx.account_id || '—'}
      </td>
      <td className={clsx(
        'px-4 py-4 text-sm font-semibold text-right',
        isPositive ? 'text-emerald-400' : 'text-rose-400'
      )}>
        {isPositive ? '+' : '-'}{formatCurrency(amount)}
      </td>
    </motion.tr>
  );
}

export default function FinanceOverview() {
  const [period, setPeriod] = useState('30d');

  // Get days from period
  const periodConfig = PERIODS.find((p) => p.key === period) || PERIODS[1];
  const days = periodConfig.days;

  // Data hooks
  const timelineQuery = useFinanceTimeline({
    days: days,
    granularity: days && days <= 30 ? 'daily' : days <= 90 ? 'weekly' : 'monthly',
  });

  const treasuryQuery = useFinanceTreasury({
    period: period === 'all' ? null : period,
  });

  const transactionsQuery = useFinanceTransactions({
    limit: 5,
    sort_by: 'transaction_date',
    sort_order: 'desc',
  });

  const anomaliesQuery = useFinanceAnomalies({});
  const matchesQuery = useFinanceMatches({ status: 'pending' });

  // Extracted data
  const treasury = treasuryQuery.data ?? {};
  const transactions = Array.isArray(transactionsQuery.data?.items)
    ? transactionsQuery.data.items
    : Array.isArray(transactionsQuery.data)
    ? transactionsQuery.data
    : [];
  const anomalies = Array.isArray(anomaliesQuery.data) ? anomaliesQuery.data : [];
  const pendingMatches = Array.isArray(matchesQuery.data) ? matchesQuery.data : [];

  // Transformation des données timeline pour le graphique
  // Normalise les données en s'assurant que les montants sont positifs
  const chartData = useMemo(() => {
    const data = Array.isArray(timelineQuery.data) ? timelineQuery.data : [];
    return data.map((item) => ({
      ...item,
      balance: item.cumulative_balance || item.balance || 0,
      inflow: item.inflow || 0,
      outflow: Math.abs(item.outflow || 0), // Valeur absolue pour les sorties
    }));
  }, [timelineQuery.data]);

  // Calcul du solde actuel et des tendances
  // Si trend_percent n'est pas fourni par l'API, on le calcule à partir des données du graphique
  const currentBalance = treasury.current_balance || treasury.net_balance || 0;
  const totalInflow = treasury.total_inflow || 0;
  const totalOutflow = treasury.total_outflow || 0;
  const netChange = totalInflow - totalOutflow;
  const trendPercent = treasury.trend_percent || (
    chartData.length >= 2
      ? ((chartData[chartData.length - 1]?.balance - chartData[0]?.balance) / Math.abs(chartData[0]?.balance || 1)) * 100
      : 0
  );

  const hasError = treasuryQuery.isError && !treasuryQuery.data;

  if (hasError) {
    return (
      <QueryErrorState
        error={treasuryQuery.error}
        onRetry={() => treasuryQuery.refetch()}
        variant="full"
      />
    );
  }

  const handleRefresh = () => {
    timelineQuery.refetch();
    treasuryQuery.refetch();
    transactionsQuery.refetch();
  };

  return (
    <div className="space-y-8">
      {/* Hero Header with Balance */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-3xl border border-amber-500/30 bg-gradient-to-br from-amber-500/15 to-amber-500/5 p-12 text-center"
      >
        <p className="text-lg font-semibold text-slate-400 mb-4 uppercase tracking-wider">
          Trésorerie
        </p>
        <div className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-amber-400 to-yellow-300 bg-clip-text text-transparent mb-4">
          {formatCurrency(currentBalance)}
        </div>
        <div className={clsx(
          'inline-flex items-center gap-2 text-lg font-semibold',
          trendPercent >= 0 ? 'text-emerald-400' : 'text-rose-400'
        )}>
          {trendPercent >= 0 ? (
            <TrendingUp className="w-5 h-5" />
          ) : (
            <TrendingDown className="w-5 h-5" />
          )}
          {trendPercent >= 0 ? '+' : ''}{trendPercent.toFixed(1)}% vs période précédente
        </div>
      </motion.div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <PeriodTabs value={period} onChange={setPeriod} />
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            loading={treasuryQuery.isLoading}
          >
            <RefreshCw className="w-4 h-4" />
            Rafraîchir
          </Button>
          <Button variant="outline" size="sm">
            <Calendar className="w-4 h-4" />
            Période personnalisée
          </Button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4"
        >
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <ArrowDownCircle className="w-4 h-4 text-emerald-400" />
            Entrées
          </div>
          <p className="text-2xl font-bold text-emerald-400">
            +{formatCompact(totalInflow)}
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4"
        >
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <ArrowUpCircle className="w-4 h-4 text-rose-400" />
            Sorties
          </div>
          <p className="text-2xl font-bold text-rose-400">
            -{formatCompact(totalOutflow)}
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className={clsx(
            'rounded-xl border p-4',
            netChange >= 0
              ? 'border-amber-500/30 bg-amber-500/10'
              : 'border-rose-500/30 bg-rose-500/10'
          )}
        >
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Wallet className="w-4 h-4 text-amber-400" />
            Solde net
          </div>
          <p className={clsx(
            'text-2xl font-bold',
            netChange >= 0 ? 'text-amber-400' : 'text-rose-400'
          )}>
            {netChange >= 0 ? '+' : ''}{formatCompact(netChange)}
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className={clsx(
            'rounded-xl border p-4',
            anomalies.length > 0
              ? 'border-rose-500/30 bg-rose-500/10'
              : 'border-white/10 bg-white/5'
          )}
        >
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Activity className="w-4 h-4" />
            Alertes
          </div>
          <p className="text-2xl font-bold text-white">
            {anomalies.length} / {pendingMatches.length}
          </p>
          <p className="text-xs text-slate-500">Anomalies / À rapprocher</p>
        </motion.div>
      </div>

      {/* Interactive Chart */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Évolution trésorerie
            </h2>
            <p className="text-sm text-slate-400">
              {periodConfig.label} - {chartData.length} points
            </p>
          </div>
          <Button variant="ghost" size="sm">
            <Download className="w-4 h-4" />
            Exporter CSV
          </Button>
        </div>

        {chartData.length > 0 ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis
                  dataKey="period"
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => formatCompact(v)}
                />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                <Bar dataKey="balance" radius={[4, 4, 0, 0]} maxBarSize={60}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={`rgba(245, 158, 11, ${0.4 + (index / chartData.length) * 0.6})`}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-80 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <p>Aucune donnée disponible</p>
            </div>
          </div>
        )}
      </Card>

      {/* Recent Transactions */}
      <Card className="overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-semibold text-white">
            Dernières transactions
          </h2>
          <Button variant="ghost" size="sm" className="text-blue-400">
            Voir tout
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>

        {transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Description
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Catégorie
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                    Compte
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500">
                    Montant
                  </th>
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 5).map((tx, index) => (
                  <TransactionRow
                    key={tx.id || index}
                    tx={tx}
                    onClick={() => {}}
                  />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-slate-400">
            <Wallet className="w-12 h-12 mx-auto mb-2 opacity-30" />
            <p>Aucune transaction récente</p>
          </div>
        )}
      </Card>
    </div>
  );
}
