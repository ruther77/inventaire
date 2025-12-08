import React, { useState, useMemo } from 'react';
import { Landmark, LayoutList, Building2, Upload, Tag, TrendingUp } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';

import TreasurySummary from './components/TreasurySummary.jsx';
import TransactionsTab from './components/TransactionsTab.jsx';
import AccountsTab from './components/AccountsTab.jsx';
import ImportsTab from './components/ImportsTab.jsx';
import RulesTab from './components/RulesTab.jsx';

import { useFinanceTransactions, useFinanceAnomalies, useFinanceMatches } from '../../hooks/useFinance.js';
import {
  useFinanceCategories,
  useFinanceAccounts,
  useFinanceRules,
  useFinanceAccountsOverviewStats,
  useFinanceTreasury,
  useFinanceRuleMutations,
} from '../../hooks/useFinanceCategories.js';
import { useFinanceImports, useFinanceImportMutation } from '../../hooks/useFinanceImports.js';

const TABS = [
  { id: 'transactions', label: 'Transactions', icon: LayoutList },
  { id: 'accounts', label: 'Comptes', icon: Building2 },
  { id: 'imports', label: 'Imports', icon: Upload },
  { id: 'rules', label: 'Règles', icon: Tag },
];

export default function BankStatementPage() {
  const [activeTab, setActiveTab] = useState('transactions');

  // Data hooks
  const transactionsQuery = useFinanceTransactions({ size: 200, sort: '-date_operation' });
  const categoriesQuery = useFinanceCategories({});
  const accountsQuery = useFinanceAccounts({});
  const accountsStatsQuery = useFinanceAccountsOverviewStats({});
  const rulesQuery = useFinanceRules({});
  const treasuryQuery = useFinanceTreasury({});
  const anomaliesQuery = useFinanceAnomalies({});
  const matchesQuery = useFinanceMatches({ status: 'pending' });
  const importsQuery = useFinanceImports();
  const importMutation = useFinanceImportMutation();
  const ruleMutations = useFinanceRuleMutations();

  // Flatten paginated transactions
  const transactions = useMemo(() => {
    if (!transactionsQuery.data?.pages) return [];
    return transactionsQuery.data.pages.flatMap((page) => page.items || []);
  }, [transactionsQuery.data]);

  const categories = categoriesQuery.data ?? [];
  const accounts = accountsQuery.data ?? [];
  const accountsStats = accountsStatsQuery.data ?? [];
  const rules = rulesQuery.data ?? [];
  const treasury = treasuryQuery.data ?? {};
  const anomalies = anomaliesQuery.data ?? [];
  const pendingMatches = matchesQuery.data ?? [];
  const imports = importsQuery.data ?? [];

  // Handlers
  const handleImport = async ({ accountId, file }) => {
    return importMutation.mutateAsync({ accountId, file });
  };

  const handleCreateRule = async (payload) => {
    return ruleMutations.create.mutateAsync(payload);
  };

  const handleUpdateRule = async (id, payload) => {
    return ruleMutations.update.mutateAsync({ id, payload });
  };

  const handleDeleteRule = async (id) => {
    return ruleMutations.remove.mutateAsync(id);
  };

  const renderTab = () => {
    switch (activeTab) {
      case 'transactions':
        return (
          <TransactionsTab
            transactions={transactions}
            categories={categories}
            accounts={accounts}
            isLoading={transactionsQuery.isLoading || transactionsQuery.isFetching}
            onRefresh={() => transactionsQuery.refetch()}
          />
        );
      case 'accounts':
        return (
          <AccountsTab
            accounts={accountsStats}
            isLoading={accountsStatsQuery.isLoading}
            onRefresh={() => accountsStatsQuery.refetch()}
          />
        );
      case 'imports':
        return (
          <ImportsTab
            accounts={accounts}
            imports={imports}
            onImport={handleImport}
            onRefresh={() => importsQuery.refetch()}
            isLoading={importMutation.isPending}
          />
        );
      case 'rules':
        return (
          <RulesTab
            rules={rules}
            categories={categories}
            onCreate={handleCreateRule}
            onUpdate={handleUpdateRule}
            onDelete={handleDeleteRule}
            onRefresh={() => rulesQuery.refetch()}
            isLoading={rulesQuery.isLoading}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-blue-100">
              <Landmark className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Trésorerie HQ</p>
              <h1 className="text-2xl font-semibold text-slate-900">Relevés bancaires</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              onClick={() => {
                transactionsQuery.refetch();
                treasuryQuery.refetch();
                accountsStatsQuery.refetch();
              }}
            >
              Rafraîchir tout
            </Button>
          </div>
        </header>

        {/* Summary KPIs */}
        <TreasurySummary
          treasury={treasury}
          anomaliesCount={anomalies.length}
          pendingMatchesCount={pendingMatches.length}
        />

        {/* Tabs Navigation */}
        <Card className="p-1">
          <nav className="flex gap-1">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </Card>

        {/* Tab Content */}
        <div>{renderTab()}</div>
      </div>
    </div>
  );
}
