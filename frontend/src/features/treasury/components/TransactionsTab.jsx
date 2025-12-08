import React, { useState, useMemo } from 'react';
import { Download, Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import Input from '../../../components/ui/Input.jsx';
import Select from '../../../components/ui/Select.jsx';
import { roundAmount } from '../../../utils/banking.js';

const PAGE_SIZE = 50;

export default function TransactionsTab({
  transactions = [],
  categories = [],
  accounts = [],
  isLoading = false,
  onRefresh,
  onExportCSV,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterAccount, setFilterAccount] = useState('');
  const [filterDirection, setFilterDirection] = useState('');
  const [page, setPage] = useState(1);

  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const matchLabel = (tx.label || tx.libelle || '').toLowerCase().includes(term);
        if (!matchLabel) return false;
      }
      if (filterCategory && tx.category_id !== Number(filterCategory)) return false;
      if (filterAccount && tx.account_id !== Number(filterAccount)) return false;
      if (filterDirection) {
        const dir = tx.direction || (tx.type === 'Entrée' ? 'IN' : 'OUT');
        if (dir !== filterDirection) return false;
      }
      return true;
    });
  }, [transactions, searchTerm, filterCategory, filterAccount, filterDirection]);

  const totalPages = Math.ceil(filteredTransactions.length / PAGE_SIZE);
  const paginatedTransactions = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredTransactions.slice(start, start + PAGE_SIZE);
  }, [filteredTransactions, page]);

  const totalInflow = filteredTransactions
    .filter((tx) => (tx.direction || (tx.type === 'Entrée' ? 'IN' : 'OUT')) === 'IN')
    .reduce((sum, tx) => sum + Math.abs(tx.amount || tx.montant || 0), 0);

  const totalOutflow = filteredTransactions
    .filter((tx) => (tx.direction || (tx.type === 'Entrée' ? 'IN' : 'OUT')) === 'OUT')
    .reduce((sum, tx) => sum + Math.abs(tx.amount || tx.montant || 0), 0);

  const handleExport = () => {
    if (onExportCSV) {
      onExportCSV(filteredTransactions);
    } else {
      const headers = ['Date', 'Libellé', 'Catégorie', 'Montant', 'Direction'];
      const rows = filteredTransactions.map((tx) => [
        tx.date_operation || tx.date,
        tx.label || tx.libelle,
        tx.category_name || tx.categorie || '',
        (tx.amount || tx.montant || 0).toFixed(2),
        tx.direction || tx.type,
      ]);
      const csv = [headers, ...rows].map((row) => row.join(';')).join('\n');
      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `transactions-${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Rechercher..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="pl-10"
            />
          </div>
          <Select
            value={filterCategory}
            onChange={(e) => {
              setFilterCategory(e.target.value);
              setPage(1);
            }}
            className="min-w-[150px]"
          >
            <option value="">Toutes catégories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name || cat.code}
              </option>
            ))}
          </Select>
          <Select
            value={filterAccount}
            onChange={(e) => {
              setFilterAccount(e.target.value);
              setPage(1);
            }}
            className="min-w-[150px]"
          >
            <option value="">Tous comptes</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.label}
              </option>
            ))}
          </Select>
          <Select
            value={filterDirection}
            onChange={(e) => {
              setFilterDirection(e.target.value);
              setPage(1);
            }}
            className="min-w-[120px]"
          >
            <option value="">Tous flux</option>
            <option value="IN">Entrées</option>
            <option value="OUT">Sorties</option>
          </Select>
          <Button variant="ghost" onClick={onRefresh} disabled={isLoading}>
            Rafraîchir
          </Button>
          <Button variant="ghost" onClick={handleExport} className="inline-flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>
        </div>
      </Card>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-3 text-center">
          <p className="text-xs uppercase tracking-widest text-slate-400">Entrées</p>
          <p className="text-lg font-semibold text-emerald-600">{roundAmount(totalInflow)} €</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xs uppercase tracking-widest text-slate-400">Sorties</p>
          <p className="text-lg font-semibold text-rose-600">{roundAmount(totalOutflow)} €</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xs uppercase tracking-widest text-slate-400">Transactions</p>
          <p className="text-lg font-semibold text-slate-900">{filteredTransactions.length}</p>
        </Card>
      </div>

      {/* Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-widest text-slate-500">Date</th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-widest text-slate-500">Libellé</th>
                <th className="px-4 py-3 text-left text-xs uppercase tracking-widest text-slate-500">Catégorie</th>
                <th className="px-4 py-3 text-right text-xs uppercase tracking-widest text-slate-500">Montant</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paginatedTransactions.map((tx, idx) => {
                const isIn = (tx.direction || (tx.type === 'Entrée' ? 'IN' : 'OUT')) === 'IN';
                const amount = Math.abs(tx.amount || tx.montant || 0);
                return (
                  <tr key={tx.id || tx.transaction_id || idx} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-600">{tx.date_operation || tx.date}</td>
                    <td className="px-4 py-3 text-slate-900 font-medium">{tx.label || tx.libelle}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700">
                        {tx.category_name || tx.categorie || 'Non catégorisé'}
                      </span>
                    </td>
                    <td className={`px-4 py-3 text-right font-semibold ${isIn ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {isIn ? '+' : '-'}{roundAmount(amount)} €
                    </td>
                  </tr>
                );
              })}
              {paginatedTransactions.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                    Aucune transaction trouvée
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50">
            <p className="text-sm text-slate-500">
              {(page - 1) * PAGE_SIZE + 1} - {Math.min(page * PAGE_SIZE, filteredTransactions.length)} sur {filteredTransactions.length}
            </p>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="flex items-center text-sm text-slate-600">
                {page} / {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
