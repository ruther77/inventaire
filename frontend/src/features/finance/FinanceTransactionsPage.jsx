import React, { useMemo, useState, useCallback } from 'react';
import { useFinanceTransactions } from '../../hooks/useFinance.js';
import { useFinanceCategories, useFinanceAccounts } from '../../hooks/useFinanceCategories.js';
import usePersistedFilters from '../../hooks/usePersistedFilters.js';
import TransactionFilters from './components/TransactionFilters.jsx';
import CategoryInlineEdit from './components/CategoryInlineEdit.jsx';
import DataTable from '../../components/ui/DataTable.jsx';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { Download, RefreshCw } from 'lucide-react';

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

export default function FinanceTransactionsPage() {
  const { filters, setFilters, updateFilter, resetFilters } = usePersistedFilters(
    'finance_transactions',
    defaultFilters
  );

  const [selectedRows, setSelectedRows] = useState([]);

  // Load data
  const categoriesQuery = useFinanceCategories({});
  const accountsQuery = useFinanceAccounts({});

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
    return transactionsQuery.data?.pages?.flatMap((page) => page.items || []) || [];
  }, [transactionsQuery.data]);

  const categories = categoriesQuery.data || [];
  const accounts = accountsQuery.data || [];

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

  // Callback pour mise à jour de catégorie inline
  const handleCategoryUpdate = useCallback((transactionId, newCategoryId) => {
    // Le CategoryInlineEdit gère déjà l'invalidation des queries
    // Ce callback peut être utilisé pour des actions supplémentaires si nécessaire
    console.log(`Transaction ${transactionId} catégorisée: ${newCategoryId}`);
  }, []);

  // Définir les colonnes du tableau
  const columns = useMemo(
    () => [
      {
        key: 'date_operation',
        header: 'Date',
        sortable: true,
        render: (value) => {
          if (!value) return '—';
          const date = new Date(value);
          return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
          });
        },
      },
      {
        key: 'label',
        header: 'Libellé',
        sortable: true,
        render: (value) => (
          <span className="font-medium text-slate-900">{value || '—'}</span>
        ),
      },
      {
        key: 'amount',
        header: 'Montant',
        align: 'right',
        sortable: true,
        render: (value, row) => {
          const amount = Number(value) || 0;
          const isPositive = amount >= 0;
          return (
            <span
              className={`font-semibold ${
                isPositive ? 'text-emerald-600' : 'text-rose-600'
              }`}
            >
              {isPositive ? '+' : ''}
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
          return (
            <CategoryInlineEdit
              transactionId={row.id || row.transaction_id}
              currentCategoryId={value}
              currentCategoryName={category?.name || category?.label || row.category_code || '—'}
              onUpdate={handleCategoryUpdate}
            />
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
            <span className="text-sm text-slate-600">
              {row.account_label || account?.label || value || '—'}
            </span>
          );
        },
      },
      {
        key: 'status',
        header: 'Statut',
        sortable: true,
        render: (value) => {
          const statusColors = {
            matched: 'bg-emerald-100 text-emerald-700',
            pending: 'bg-amber-100 text-amber-700',
            ignored: 'bg-slate-100 text-slate-600',
          };
          const statusLabels = {
            matched: 'Rapproché',
            pending: 'En attente',
            ignored: 'Ignoré',
          };
          return (
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                statusColors[value] || 'bg-slate-100 text-slate-600'
              }`}
            >
              {statusLabels[value] || value || 'Inconnu'}
            </span>
          );
        },
      },
    ],
    [categoryById, accountById, handleCategoryUpdate]
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Finance</p>
          <h1 className="text-2xl font-semibold text-slate-900">Transactions bancaires</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => transactionsQuery.refetch()}
            loading={transactionsQuery.isRefetching}
          >
            <RefreshCw className="h-4 w-4" />
            Rafraîchir
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4" />
            Exporter
          </Button>
        </div>
      </header>

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

      {/* Tableau */}
      <Card padding="none">
        <DataTable
          data={transactions}
          columns={columns}
          loading={transactionsQuery.isLoading}
          error={transactionsQuery.error}
          selectable={true}
          selectedRows={selectedRows}
          onSelectionChange={setSelectedRows}
          bulkActions={bulkActions}
          sortable={true}
          pagination={true}
          pageSize={50}
          pageSizeOptions={[25, 50, 100, 200]}
          searchable={false}
          emptyMessage="Aucune transaction trouvée"
          getRowId={(row) => row.id || row.transaction_id}
        />

        {/* Load more button */}
        {transactionsQuery.hasNextPage && (
          <div className="p-4 border-t border-slate-100 text-center">
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
    </div>
  );
}
