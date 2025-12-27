/**
 * Page Transactions Bancaires.
 *
 * Cette page permet de gérer et catégoriser les transactions bancaires.
 * Elle affiche:
 * - Une liste complète des transactions avec pagination infinie
 * - Des statistiques en temps réel (entrées, sorties, solde net, non rapprochées)
 * - Des filtres avancés (entité, compte, catégorie, date, montant)
 * - Un éditeur inline de catégories avec suggestions IA
 * - Des badges de confiance IA pour les suggestions de catégorisation
 * - Mode mobile avec cartes swipables et actions rapides
 *
 * Fonctionnalités principales:
 * - Catégorisation inline avec mise à jour optimiste
 * - Suggestions IA avec niveau de confiance
 * - Filtrage multi-critères avec sauvegarde des préférences
 * - Verrouillage des transactions validées
 * - Export CSV des transactions filtrées
 * - Scroll infini pour charger plus de données
 * - Pull-to-refresh sur mobile
 *
 * @component
 *
 * @example
 * <FinanceTransactionsPage />
 */

import React, { useMemo, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFinanceTransactions, useUpdateFinanceTransaction, useLockFinanceTransaction } from '../../hooks/useFinance.js';
import { useFinanceCategories, useFinanceAccounts, useFinanceTreasury } from '../../hooks/useFinanceCategories.js';
import usePersistedFilters from '../../hooks/usePersistedFilters.js';
import TransactionFilters from './components/TransactionFilters.jsx';
import CategoryInlineEdit from './components/CategoryInlineEdit.jsx';
import SmartTable, { columnHelpers } from '../../components/ui/SmartTable.jsx';
import AIConfidenceBadge from '../../components/ui/AIConfidenceBadge.jsx';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { EmptyTransactions, EmptyFilteredResults } from '../../components/feedback/ActionableEmptyStates.jsx';
import { Download, RefreshCw, Sparkles, Tag, Info, Lock, TrendingUp, TrendingDown, Wallet, AlertCircle } from 'lucide-react';
import PullToRefresh from '../../components/ui/PullToRefresh.jsx';
import { SwipeableRow, SwipeableRowProvider } from '../../components/ui/SwipeableRow.jsx';
import Modal from '../../components/ui/Modal.jsx';
import { TransactionsSkeleton } from '../../components/ui/Skeleton.jsx';
import QueryErrorState from '../../components/feedback/QueryErrorState.jsx';

const defaultFilters = {
  entity_id: undefined,
  account_id: undefined,
  category_id: undefined,
  date_from: undefined,
  date_to: undefined,
  amount_min: undefined,
  amount_max: undefined,
  q: undefined,
};

// Migration: nettoyer les anciens filtres invalides (entity_id=1 n'existe plus)
if (typeof window !== 'undefined') {
  try {
    const saved = localStorage.getItem('filters_finance_transactions');
    if (saved) {
      const parsed = JSON.parse(saved);
      // entity_id=1 n'a pas de transactions finance, on le supprime
      if (parsed.entity_id === 1 || parsed.entity_id === '1') {
        parsed.entity_id = undefined;
        localStorage.setItem('filters_finance_transactions', JSON.stringify(parsed));
      }
    }
  } catch (e) {
    // Ignore errors
  }
}

export default function FinanceTransactionsPage() {
  const navigate = useNavigate();
  const { filters, setFilters, updateFilter, resetFilters } = usePersistedFilters(
    'finance_transactions',
    defaultFilters
  );

  const [selectedRows, setSelectedRows] = useState([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const updateTransaction = useUpdateFinanceTransaction();
  const lockTransaction = useLockFinanceTransaction();

  // Handle window resize for mobile detection
  React.useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Vérifier si des filtres sont actifs
  const hasActiveFilters = useMemo(() => {
    return Object.entries(filters).some(([key, value]) => value !== undefined && value !== null && value !== '');
  }, [filters]);

  // Load data
  const categoriesQuery = useFinanceCategories({});
  const accountsQuery = useFinanceAccounts({});
  const treasuryQuery = useFinanceTreasury({ period: '30d' });

  // Préparer les filtres pour l'API
  const apiFilters = useMemo(() => {
    const params = {};
    if (filters.entity_id) params.entityId = Number(filters.entity_id);
    if (filters.account_id) params.accountId = filters.account_id;
    if (filters.category_id) params.categoryId = Number(filters.category_id);
    if (filters.date_from) params.dateFrom = filters.date_from;
    if (filters.date_to) params.dateTo = filters.date_to;
    if (filters.amount_min) params.amountMin = Number(filters.amount_min);
    if (filters.amount_max) params.amountMax = Number(filters.amount_max);
    if (filters.q) params.q = filters.q;
    return params;
  }, [filters]);

  const transactionsQuery = useFinanceTransactions(apiFilters);

  // Flatten all pages
  const transactions = useMemo(() => {
    const pages = transactionsQuery.data?.pages || [];
    return pages.flatMap((page) => page?.items || []).filter(Boolean);
  }, [transactionsQuery.data]);

  const categories = categoriesQuery.data || [];
  const accounts = accountsQuery.data || [];
  const treasury = treasuryQuery.data || {};

  // Calculer les stats pour les transactions affichées
  const transactionStats = useMemo(() => {
    const incomeTotal = transactions
      .filter(tx => tx.direction === 'IN')
      .reduce((sum, tx) => sum + (Number(tx.amount) || 0), 0);
    const expenseTotal = transactions
      .filter(tx => tx.direction === 'OUT')
      .reduce((sum, tx) => sum + (Number(tx.amount) || 0), 0);
    const netBalance = incomeTotal - expenseTotal;
    const unmatchedCount = transactions.filter(tx => tx.status !== 'matched').length;

    return { incomeTotal, expenseTotal, netBalance, unmatchedCount };
  }, [transactions]);

  // Créer un map pour les catégories
  const categoryById = useMemo(() => {
    const map = new Map();
    categories.forEach((c) => map.set(c.id, c));
    return map;
  }, [categories]);

  // Créer un map pour les comptes
  const accountById = useMemo(() => {
    const map = new Map();
    accounts.forEach((a) => map.set(a.id, a));
    return map;
  }, [accounts]);

  // Mise à jour inline avec mutation optimiste
  // Les changements sont appliqués immédiatement dans l'UI avant la confirmation serveur
  const handleEdit = useCallback((transactionId, field, value) => {
    updateTransaction.mutate({
      transactionId,
      payload: { [field]: value },
    });
  }, [updateTransaction]);

  // Callback pour mise à jour de catégorie inline
  const handleCategoryUpdate = useCallback((transactionId, newCategoryId) => {
    // Le CategoryInlineEdit gère déjà l'invalidation des queries
    // Ce callback peut être utilisé pour des actions supplémentaires si nécessaire
    console.log(`Transaction ${transactionId} catégorisée: ${newCategoryId}`);
  }, []);

  // Callback pour verrouiller une transaction
  const handleLockTransaction = useCallback((transactionId) => {
    if (window.confirm('Voulez-vous vraiment verrouiller cette transaction ? Cette action est irréversible.')) {
      lockTransaction.mutate(transactionId);
    }
  }, [lockTransaction]);

  // Handlers for mobile swipe actions
  const handleOpenCategoryModal = useCallback((transaction) => {
    setSelectedTransaction(transaction);
    setCategoryModalOpen(true);
  }, []);

  const handleOpenDetailModal = useCallback((transaction) => {
    setSelectedTransaction(transaction);
    setDetailModalOpen(true);
  }, []);

  const handleCategoryModalSave = useCallback((newCategoryId) => {
    if (selectedTransaction && newCategoryId) {
      updateTransaction.mutate({
        transactionId: selectedTransaction.id || selectedTransaction.transaction_id,
        payload: { category_id: Number(newCategoryId) },
      });
    }
    setCategoryModalOpen(false);
    setSelectedTransaction(null);
  }, [selectedTransaction, updateTransaction]);

  // Pull to refresh handler
  const handleRefresh = useCallback(async () => {
    await transactionsQuery.refetch();
  }, [transactionsQuery]);

  // Définir les colonnes du tableau avec SmartTable
  const columns = useMemo(
    () => [
      columnHelpers.date('date_operation', 'Date', {
        render: (value) => {
          if (!value) return '—';
          // Parse la date sans conversion timezone (format YYYY-MM-DD)
          const parts = value.split('-');
          if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
          }
          // Fallback pour autres formats
          const date = new Date(value + 'T00:00:00');
          return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
          });
        },
      }),
      {
        key: 'label',
        header: 'Libellé',
        sortable: true,
        editable: true,
        type: 'text',
        render: (value) => (
          <span className="font-medium text-white">{value || ''}</span>
        ),
      },
      {
        key: 'amount',
        header: 'Montant',
        sortable: true,
        type: 'currency',
        render: (value, row) => {
          const amount = Number(value) || 0;
          // Use direction field to determine if it's income (IN) or expense (OUT)
          const isIncome = row.direction === 'IN';
          return (
            <span
              className={`font-semibold ${
                isIncome ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isIncome ? '+' : '-'}
              {amount.toFixed(2)} €
            </span>
          );
        },
      },
      {
        key: 'category_id',
        header: 'Catégorie',
        sortable: true,
        render: (value, row) => {
          const category = categoryById.get(value);
          const hasAIConfidence = row.ai_confidence !== undefined && row.ai_confidence !== null;

          return (
            <div className="flex items-center gap-2">
              <CategoryInlineEdit
                transactionId={row.id || row.transaction_id}
                currentCategoryId={value}
                currentCategoryName={category?.name || category?.label || row.category_code || '—'}
                aiConfidence={row.ai_confidence}
                predictedCategoryId={row.predicted_category_id}
                onUpdate={handleCategoryUpdate}
              />
              {hasAIConfidence && (
                <AIConfidenceBadge
                  confidence={row.ai_confidence}
                  size="sm"
                  variant="compact"
                  showTooltip={true}
                  explanation={row.ai_suggestion_reason}
                />
              )}
            </div>
          );
        },
      },
      {
        key: 'account_id',
        header: 'Compte',
        sortable: true,
        render: (value, row) => {
          const account = accountById.get(value);
          return (
            <span className="text-sm text-slate-400">
              {row.account_label || account?.label || value || '—'}
            </span>
          );
        },
      },
      columnHelpers.status('status', 'Statut', {
        matched: { label: 'Rapproché', color: 'emerald', icon: null },
        pending: { label: 'En attente', color: 'amber', icon: null },
        ignored: { label: 'Ignoré', color: 'slate', icon: null },
      }),
      columnHelpers.actions((row) => {
        if (!row) return null;
        return (
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleLockTransaction(row.id || row.transaction_id)}
              disabled={!!row.locked_at}
              title={row.locked_at ? 'Transaction déjà verrouillée' : 'Verrouiller la transaction'}
            >
              <Lock className={`h-4 w-4 ${row.locked_at ? 'text-slate-500' : ''}`} />
            </Button>
          </div>
        );
      }),
    ],
    [categoryById, accountById, handleCategoryUpdate, handleLockTransaction]
  );

  // Actions en masse
  const bulkActions = [
    {
      id: 'recategorize',
      label: 'Recatégoriser',
      onClick: (selectedData) => {
        console.log('Recatégoriser les transactions sélectionnées:', selectedRows);
        // TODO: Ouvrir modal de recatégorisation
      },
    },
  ];

  const handleFilterChange = (field, value) => {
    updateFilter(field, value);
  };

  const handleExport = useCallback(() => {
    if (!transactions.length) return;

    // Générer le contenu CSV
    const headers = ['Date', 'Libellé', 'Montant', 'Catégorie', 'Compte', 'Statut'];
    const rows = transactions.map((tx) => {
      const category = categoryById.get(tx.category_id);
      const account = accountById.get(tx.account_id);
      return [
        tx.date_operation || '',
        `"${(tx.label || '').replace(/"/g, '""')}"`, // Escape quotes
        tx.amount || 0,
        category?.name || category?.label || tx.category_code || '',
        tx.account_label || account?.label || '',
        tx.status || '',
      ].join(';');
    });

    const csvContent = [headers.join(';'), ...rows].join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' }); // BOM for Excel
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [transactions, categoryById, accountById]);

  // Mobile Transaction Card Component
  const MobileTransactionCard = useCallback(({ transaction }) => {
    const category = categoryById.get(transaction.category_id);
    const account = accountById.get(transaction.account_id);
    const amount = Number(transaction.amount) || 0;
    const isIncome = transaction.direction === 'IN';

    // Format date
    let formattedDate = '—';
    if (transaction.date_operation) {
      const parts = transaction.date_operation.split('-');
      if (parts.length === 3) {
        formattedDate = `${parts[2]}/${parts[1]}/${parts[0]}`;
      }
    }

    return (
      <div className="bg-white/5 rounded-xl p-4 space-y-3">
        {/* Header: Date and Amount */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs text-slate-400">{formattedDate}</p>
            <p className="text-sm font-medium text-white mt-0.5 line-clamp-2">
              {transaction.label || '—'}
            </p>
          </div>
          <div className={`text-lg font-semibold ml-3 ${isIncome ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isIncome ? '+' : '-'}{amount.toFixed(2)} €
          </div>
        </div>

        {/* Category and AI Badge */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <Tag className="h-4 w-4 text-slate-400 flex-shrink-0" />
            <span className="text-sm text-slate-300 truncate">
              {category?.name || category?.label || transaction.category_code || 'Non catégorisé'}
            </span>
          </div>
          {transaction.ai_confidence !== undefined && transaction.ai_confidence !== null && (
            <AIConfidenceBadge
              confidence={transaction.ai_confidence}
              size="sm"
              variant="compact"
              showTooltip={true}
              explanation={transaction.ai_suggestion_reason}
            />
          )}
        </div>

        {/* Account and Status */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">
            {transaction.account_label || account?.label || transaction.account_id || '—'}
          </span>
          <span className={`px-2 py-1 rounded-full ${
            transaction.status === 'matched' ? 'bg-emerald-500/20 text-emerald-400' :
            transaction.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
            'bg-slate-500/20 text-slate-400'
          }`}>
            {transaction.status === 'matched' ? 'Rapproché' :
             transaction.status === 'pending' ? 'En attente' : 'Ignoré'}
          </span>
        </div>
      </div>
    );
  }, [categoryById, accountById]);

  // Erreur sans données de fallback
  if (transactionsQuery.isError && !transactions.length) {
    return (
      <QueryErrorState
        error={transactionsQuery.error}
        onRetry={() => transactionsQuery.refetch()}
        variant="full"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Finance</p>
          <h1 className="text-2xl font-semibold text-white">Transactions bancaires</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => transactionsQuery.refetch()}
            loading={transactionsQuery.isRefetching}
            className="hidden md:flex"
          >
            <RefreshCw className="h-4 w-4" />
            Rafraîchir
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4" />
            <span className="hidden md:inline">Exporter</span>
          </Button>
        </div>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors cursor-pointer">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            <span className="text-xs text-slate-400">Entrées ce mois</span>
          </div>
          <div className="text-xl font-bold text-emerald-400">
            +{transactionStats.incomeTotal.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors cursor-pointer">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown className="h-4 w-4 text-rose-400" />
            <span className="text-xs text-slate-400">Sorties ce mois</span>
          </div>
          <div className="text-xl font-bold text-rose-400">
            -{transactionStats.expenseTotal.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors cursor-pointer">
          <div className="flex items-center gap-2 mb-1">
            <Wallet className="h-4 w-4 text-amber-400" />
            <span className="text-xs text-slate-400">Solde net</span>
          </div>
          <div className={`text-xl font-bold ${transactionStats.netBalance >= 0 ? 'text-amber-400' : 'text-rose-400'}`}>
            {transactionStats.netBalance >= 0 ? '+' : ''}{transactionStats.netBalance.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors cursor-pointer">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-400">Non rapprochées</span>
          </div>
          <div className="text-xl font-bold text-white">
            {transactionStats.unmatchedCount}
          </div>
        </div>
      </div>

      {/* Filtres */}
      <TransactionFilters
        filters={filters}
        onChange={handleFilterChange}
        onReset={resetFilters}
        entities={[
          { id: '1', name: 'Épicerie' },
          { id: '2', name: 'Restaurant' },
        ]}
        accounts={accounts}
        categories={categories}
      />

      {/* Tableau ou état vide */}
      {!transactionsQuery.isLoading && !transactionsQuery.error && transactions.length === 0 ? (
        hasActiveFilters ? (
          <EmptyFilteredResults onReset={resetFilters} />
        ) : (
          <EmptyTransactions
            onImport={() => navigate('/finance/import')}
            onRefresh={() => transactionsQuery.refetch()}
          />
        )
      ) : (
        <>
          {/* Desktop View - Table */}
          {!isMobile && (
            <Card padding="none">
              <SmartTable
                data={transactions}
                columns={columns}
                keyField="id"
                loading={transactionsQuery.isLoading}
                emptyMessage="Aucune transaction trouvée"
                sortable={true}
                filterable={true}
                selectable={true}
                exportable={true}
                editable={true}
                onEdit={handleEdit}
                onSelect={(selectedData) => setSelectedRows(selectedData)}
                paginated={true}
                pageSize={50}
                pageSizeOptions={[25, 50, 100, 200]}
                stickyHeader={true}
                striped={true}
                variant="default"
              />

              {/* Load more button */}
              {transactionsQuery.hasNextPage && (
                <div className="p-4 border-t border-white/10 text-center">
                  <Button
                    variant="ghost"
                    onClick={() => transactionsQuery.fetchNextPage()}
                    loading={transactionsQuery.isFetchingNextPage}
                    disabled={transactionsQuery.isFetchingNextPage}
                  >
                    Charger plus de transactions
                  </Button>
                </div>
              )}
            </Card>
          )}

          {/* Mobile View - Cards with Swipe */}
          {isMobile && (
            <>
              {/* Loading state - ONLY shown before data */}
              {transactionsQuery.isLoading && (
                <div className="py-16 text-center">
                  <div className="w-8 h-8 border-2 border-slate-600 border-t-brand-500 rounded-full animate-spin mx-auto" />
                  <p className="text-sm text-slate-500 mt-3">Chargement...</p>
                </div>
              )}

              {/* Data view - NO animations once loaded */}
              {!transactionsQuery.isLoading && (
                <PullToRefresh onRefresh={handleRefresh}>
                  <SwipeableRowProvider>
                    <div className="space-y-2">
                      {transactions.map((transaction) => (
                        <SwipeableRow
                          key={transaction.id || transaction.transaction_id}
                          id={String(transaction.id || transaction.transaction_id)}
                          leftActions={[
                            {
                              label: 'Catégoriser',
                              icon: Tag,
                              variant: 'primary',
                              onAction: () => handleOpenCategoryModal(transaction),
                            },
                            {
                              label: 'Verrouiller',
                              icon: Lock,
                              variant: 'secondary',
                              onAction: () => handleLockTransaction(transaction.id || transaction.transaction_id),
                              disabled: !!transaction.locked_at,
                            },
                          ]}
                          rightActions={[
                            {
                              label: 'Détails',
                              icon: Info,
                              variant: 'primary',
                              onAction: () => handleOpenDetailModal(transaction),
                            },
                          ]}
                        >
                          <MobileTransactionCard transaction={transaction} />
                        </SwipeableRow>
                      ))}

                      {/* Load more button */}
                      {transactionsQuery.hasNextPage && (
                        <div className="pt-4 text-center">
                          <Button
                            variant="ghost"
                            onClick={() => transactionsQuery.fetchNextPage()}
                            loading={transactionsQuery.isFetchingNextPage}
                            disabled={transactionsQuery.isFetchingNextPage}
                            className="min-h-[44px]"
                          >
                            Charger plus
                          </Button>
                        </div>
                      )}
                    </div>
                  </SwipeableRowProvider>
                </PullToRefresh>
              )}
            </>
          )}
        </>
      )}

      {/* Category Modal for Mobile */}
      <Modal
        isOpen={categoryModalOpen}
        onClose={() => {
          setCategoryModalOpen(false);
          setSelectedTransaction(null);
        }}
        title="Catégoriser la transaction"
        size="sm"
      >
        <div className="space-y-4">
          {selectedTransaction && (
            <>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Transaction</p>
                <p className="text-sm font-medium text-white">{selectedTransaction.label}</p>
                <p className="text-lg font-semibold text-brand-400 mt-1">
                  {Number(selectedTransaction.amount || 0).toFixed(2)} €
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Sélectionner une catégorie
                </label>
                <select
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 min-h-[44px]"
                  defaultValue={selectedTransaction.category_id || ''}
                  onChange={(e) => {
                    if (e.target.value) {
                      handleCategoryModalSave(e.target.value);
                    }
                  }}
                >
                  <option value="">Sélectionner...</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name || cat.code}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* Detail Modal for Mobile */}
      <Modal
        isOpen={detailModalOpen}
        onClose={() => {
          setDetailModalOpen(false);
          setSelectedTransaction(null);
        }}
        title="Détails de la transaction"
        size="md"
      >
        {selectedTransaction && (
          <div className="space-y-4">
            <div className="bg-slate-800/50 rounded-lg p-4 space-y-3">
              <div>
                <p className="text-xs text-slate-400 mb-1">Libellé</p>
                <p className="text-sm font-medium text-white">{selectedTransaction.label || '—'}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-slate-400 mb-1">Date</p>
                  <p className="text-sm text-white">
                    {selectedTransaction.date_operation ?
                      (() => {
                        const parts = selectedTransaction.date_operation.split('-');
                        return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : selectedTransaction.date_operation;
                      })()
                      : '—'
                    }
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-400 mb-1">Montant</p>
                  <p className={`text-lg font-semibold ${
                    selectedTransaction.direction === 'IN' ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {selectedTransaction.direction === 'IN' ? '+' : '-'}
                    {Number(selectedTransaction.amount || 0).toFixed(2)} €
                  </p>
                </div>
              </div>

              <div>
                <p className="text-xs text-slate-400 mb-1">Catégorie</p>
                <div className="flex items-center gap-2">
                  <p className="text-sm text-white">
                    {(() => {
                      const category = categoryById.get(selectedTransaction.category_id);
                      return category?.name || category?.label || selectedTransaction.category_code || 'Non catégorisé';
                    })()}
                  </p>
                  {selectedTransaction.ai_confidence !== undefined && selectedTransaction.ai_confidence !== null && (
                    <AIConfidenceBadge
                      confidence={selectedTransaction.ai_confidence}
                      size="sm"
                      variant="compact"
                      showTooltip={true}
                      explanation={selectedTransaction.ai_suggestion_reason}
                    />
                  )}
                </div>
              </div>

              <div>
                <p className="text-xs text-slate-400 mb-1">Compte</p>
                <p className="text-sm text-white">
                  {(() => {
                    const account = accountById.get(selectedTransaction.account_id);
                    return selectedTransaction.account_label || account?.label || selectedTransaction.account_id || '—';
                  })()}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-400 mb-1">Statut</p>
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                  selectedTransaction.status === 'matched' ? 'bg-emerald-500/20 text-emerald-400' :
                  selectedTransaction.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                  'bg-slate-500/20 text-slate-400'
                }`}>
                  {selectedTransaction.status === 'matched' ? 'Rapproché' :
                   selectedTransaction.status === 'pending' ? 'En attente' : 'Ignoré'}
                </span>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1 min-h-[44px]"
                onClick={() => {
                  setDetailModalOpen(false);
                  handleOpenCategoryModal(selectedTransaction);
                }}
              >
                <Tag className="h-4 w-4" />
                Catégoriser
              </Button>
              <Button
                variant="ghost"
                className="flex-1 min-h-[44px]"
                onClick={() => {
                  setDetailModalOpen(false);
                  setSelectedTransaction(null);
                }}
              >
                Fermer
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
