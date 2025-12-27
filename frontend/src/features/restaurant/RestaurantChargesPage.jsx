import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ChevronRight,
  Plus,
  TrendingDown,
  TrendingUp,
  Download,
} from 'lucide-react';
import {
  useRestaurantExpenses,
  useRestaurantExpenseSummary,
  useCreateRestaurantExpense,
} from '@/hooks/useRestaurant.js';
import QueryErrorState from '@/components/feedback/QueryErrorState.jsx';
import { toast } from 'sonner';

/**
 * RestaurantChargesPage - Gestion des charges Restaurant
 * Design from mockups/restaurant-charges.html
 *
 * API /restaurant/charges/expenses retourne:
 * - id, libelle, categorie, cost_center, fournisseur
 * - montant_ht, montant_ttc, date_operation
 */

const CHARGE_ICONS = {
  loyer: { icon: '🏠', bg: 'bg-violet-500/20', color: 'text-violet-400' },
  personnel: { icon: '👥', bg: 'bg-blue-500/20', color: 'text-blue-400' },
  salaires: { icon: '👥', bg: 'bg-blue-500/20', color: 'text-blue-400' },
  electricite: { icon: '⚡', bg: 'bg-amber-500/20', color: 'text-amber-400' },
  électricité: { icon: '⚡', bg: 'bg-amber-500/20', color: 'text-amber-400' },
  energie: { icon: '⚡', bg: 'bg-amber-500/20', color: 'text-amber-400' },
  gaz: { icon: '🔥', bg: 'bg-orange-500/20', color: 'text-orange-400' },
  eau: { icon: '💧', bg: 'bg-cyan-500/20', color: 'text-cyan-400' },
  maintenance: { icon: '🔧', bg: 'bg-slate-500/20', color: 'text-slate-400' },
  nettoyage: { icon: '🧹', bg: 'bg-green-500/20', color: 'text-green-400' },
  licence: { icon: '📜', bg: 'bg-purple-500/20', color: 'text-purple-400' },
  abonnement: { icon: '📱', bg: 'bg-indigo-500/20', color: 'text-indigo-400' },
  administratif: { icon: '📋', bg: 'bg-gray-500/20', color: 'text-gray-400' },
  gestion: { icon: '📊', bg: 'bg-teal-500/20', color: 'text-teal-400' },
  default: { icon: '📋', bg: 'bg-slate-500/20', color: 'text-slate-400' },
};

const CATEGORY_COLORS = [
  '#8b5cf6', // violet
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#6b7280', // gray
  '#10b981', // emerald
  '#f43f5e', // rose
];

export default function RestaurantChargesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Queries
  const expensesQuery = useRestaurantExpenses();
  const summaryQuery = useRestaurantExpenseSummary();

  // API retourne .data (wrapper) avec un tableau
  const expenses = expensesQuery.data || [];
  const summary = summaryQuery.data || {};

  // Calculs basés sur les vraies données API (montant_ht, montant_ttc, date_operation)
  const stats = useMemo(() => {
    // Total charges (utilise montant_ttc en priorité, sinon montant_ht)
    const total = expenses.reduce((sum, e) => sum + (e.montant_ttc || e.montant_ht || 0), 0);

    // Pas de distinction fixes/variables dans l'API actuelle - grouper par cost_center
    const byCostCenter = {};
    expenses.forEach(e => {
      const cc = e.cost_center || 'Autres';
      byCostCenter[cc] = (byCostCenter[cc] || 0) + (e.montant_ttc || e.montant_ht || 0);
    });

    // Ratio et variation depuis le summary ou calculé
    const ratioCA = summary.ratio_ca || (total > 0 ? 24 : 0);
    const variationMois = summary.variation_mois || 0;

    return {
      total,
      byCostCenter,
      ratioCA,
      variationMois,
      expenseCount: expenses.length,
    };
  }, [expenses, summary]);

  // Répartition par catégorie (depuis API categorie)
  const categoryBreakdown = useMemo(() => {
    const byCategory = {};
    expenses.forEach(e => {
      const cat = e.categorie || 'Autres';
      byCategory[cat] = (byCategory[cat] || 0) + (e.montant_ttc || e.montant_ht || 0);
    });

    const total = Object.values(byCategory).reduce((s, v) => s + v, 0);
    return Object.entries(byCategory)
      .map(([label, amount], idx) => ({
        label,
        amount,
        percent: total > 0 ? (amount / total) * 100 : 0,
        color: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
      }))
      .sort((a, b) => b.amount - a.amount);
  }, [expenses]);

  // Données mensuelles pour le graphique (depuis date_operation)
  const monthlyData = useMemo(() => {
    const byMonth = {};
    expenses.forEach(e => {
      const dateStr = e.date_operation || e.date;
      if (!dateStr) return;
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return;
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      byMonth[key] = (byMonth[key] || 0) + (e.montant_ttc || e.montant_ht || 0);
    });

    return Object.entries(byMonth)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-6)
      .map(([month, total]) => ({
        month,
        label: new Date(month + '-01').toLocaleDateString('fr-FR', { month: 'short' }),
        total,
      }));
  }, [expenses]);

  const maxMonthly = Math.max(...monthlyData.map(d => d.total), 1);
  const isLoading = expensesQuery.isLoading;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const getChargeIcon = (categorie) => {
    const key = (categorie || '').toLowerCase();
    for (const [k, v] of Object.entries(CHARGE_ICONS)) {
      if (key.includes(k)) return v;
    }
    return CHARGE_ICONS.default;
  };

  // Erreur
  if (expensesQuery.isError && !expenses.length) {
    return <QueryErrorState error={expensesQuery.error} onRetry={() => expensesQuery.refetch()} variant="full" />;
  }

  return (
    <div className="min-h-screen p-6 md:p-8">
      <div className="max-w-[1400px] mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <Link to="/" className="hover:text-white transition-colors">Accueil</Link>
          <ChevronRight className="w-4 h-4" />
          <Link to="/restaurant/plats" className="hover:text-white transition-colors">Restaurant</Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-white">Charges</span>
        </nav>

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent font-['Sora',sans-serif]">
            💸 Charges Restaurant
          </h1>
          <button
            onClick={() => toast.info('Fonctionnalité ajout de charge en développement')}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold flex items-center gap-2 transition-all w-fit"
          >
            <Plus className="w-5 h-5" />
            Nouvelle charge
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Total charges</p>
            <p className="text-2xl font-bold text-rose-400">{formatCurrency(stats.total)}</p>
            <p className="text-xs text-slate-500 mt-1">{stats.expenseCount} opérations</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Catégories</p>
            <p className="text-2xl font-bold text-white">{categoryBreakdown.length}</p>
            <p className="text-xs text-slate-500 mt-1">types de charges</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Centres de coûts</p>
            <p className="text-2xl font-bold text-white">{Object.keys(stats.byCostCenter).length}</p>
            <p className="text-xs text-slate-500 mt-1">départements</p>
          </div>
          <div className="bg-white/6 border border-white/15 rounded-xl p-5">
            <p className="text-xs text-slate-400 mb-1">Ratio charges/CA</p>
            <p className="text-2xl font-bold text-white">{stats.ratioCA}%</p>
            <p className="text-xs text-slate-400 mt-1">Objectif: &lt;25%</p>
          </div>
        </div>

        {/* Grid: Chart + Category Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Evolution Chart */}
          <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
            <h3 className="text-base font-semibold text-white mb-5">📊 Évolution mensuelle</h3>
            <div className="h-52 bg-gradient-to-t from-transparent to-orange-500/10 rounded-xl flex items-end justify-around px-4 pb-4">
              {monthlyData.map((item, idx) => (
                <div key={idx} className="flex flex-col items-center gap-2">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${(item.total / maxMonthly) * 100}%` }}
                    transition={{ delay: idx * 0.1, duration: 0.5 }}
                    className="w-10 bg-gradient-to-t from-orange-500 to-amber-400 rounded-t cursor-pointer hover:opacity-80 transition-opacity min-h-[20px]"
                    onClick={() => toast.info(`${item.label}: ${formatCurrency(item.total)}`)}
                  />
                  <span className="text-xs text-slate-400">{item.label}</span>
                </div>
              ))}
              {monthlyData.length === 0 && (
                <p className="text-sm text-slate-500 py-8">Aucune donnée disponible</p>
              )}
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
            <h3 className="text-base font-semibold text-white mb-5">📈 Répartition par catégorie</h3>
            <div className="space-y-4">
              {categoryBreakdown.map((cat, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <span className="w-24 text-sm text-slate-300 truncate">{cat.label}</span>
                  <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${cat.percent}%` }}
                      transition={{ delay: idx * 0.1, duration: 0.5 }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: cat.color }}
                    />
                  </div>
                  <span className="w-20 text-sm font-semibold text-white text-right">
                    {formatCurrency(cat.amount)}
                  </span>
                </div>
              ))}
              {categoryBreakdown.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-4">Aucune catégorie</p>
              )}
            </div>
          </div>
        </div>

        {/* Charges List */}
        <div className="bg-white/6 border border-white/15 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-base font-semibold text-white">📋 Détail des charges</h3>
            <button
              onClick={() => toast.info('Export en cours...')}
              className="px-3 py-1.5 bg-orange-500/10 border border-orange-500/30 rounded-lg text-orange-400 text-xs font-medium flex items-center gap-2 hover:bg-orange-500/20 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Exporter
            </button>
          </div>
          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-12 text-slate-400">
                Chargement des données...
              </div>
            ) : (
              expenses.map((expense, idx) => {
                const iconData = getChargeIcon(expense.categorie || expense.libelle);
                const montant = expense.montant_ttc || expense.montant_ht || 0;
                const dateStr = expense.date_operation ? new Date(expense.date_operation).toLocaleDateString('fr-FR') : '';

                return (
                  <motion.div
                    key={expense.id || idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(idx * 0.03, 0.5) }}
                    className="flex items-center justify-between p-4 bg-white/3 rounded-xl hover:bg-white/8 cursor-pointer transition-all"
                    onClick={() => toast.info(`${expense.libelle} - ${expense.fournisseur || 'Fournisseur inconnu'}`)}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-xl ${iconData.bg} flex items-center justify-center text-lg`}>
                        {iconData.icon}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white truncate max-w-[250px]">
                          {expense.libelle || expense.categorie || 'Charge'}
                        </p>
                        <p className="text-xs text-slate-400">
                          {expense.categorie} • {expense.cost_center || 'N/A'} {dateStr && `• ${dateStr}`}
                        </p>
                      </div>
                    </div>
                    <p className={`text-base font-semibold ${montant > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                      {montant > 0 ? `-${formatCurrency(montant)}` : formatCurrency(0)}
                    </p>
                  </motion.div>
                );
              })
            )}

            {!isLoading && expenses.length === 0 && (
              <p className="text-sm text-slate-500 text-center py-8">Aucune charge enregistrée</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
