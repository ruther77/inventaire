import React from 'react';
import { Building2 } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useFinanceAccountsOverviewStats } from '../../hooks/useFinanceCategories.js';
import AccountsTab from '../treasury/components/AccountsTab.jsx';

export default function FinanceAccountsPage() {
  const accountsStatsQuery = useFinanceAccountsOverviewStats({});
  const accounts = accountsStatsQuery.data ?? [];

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-blue-100">
              <Building2 className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Tresorerie HQ</p>
              <h1 className="text-2xl font-semibold text-slate-900">Comptes bancaires</h1>
            </div>
          </div>
          <Button
            variant="ghost"
            onClick={() => accountsStatsQuery.refetch()}
            disabled={accountsStatsQuery.isLoading}
          >
            Rafraichir
          </Button>
        </header>

        {/* Content */}
        <AccountsTab
          accounts={accounts}
          isLoading={accountsStatsQuery.isLoading}
          onRefresh={() => accountsStatsQuery.refetch()}
        />
      </div>
    </div>
  );
}
