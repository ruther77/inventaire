import React from 'react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import Input from '../../../components/ui/Input.jsx';
import Select from '../../../components/ui/Select.jsx';
import { X } from 'lucide-react';

export default function TransactionFilters({
  filters,
  onChange,
  onReset,
  entities = [],
  accounts = [],
  categories = [],
}) {
  const handleChange = (field, value) => {
    onChange(field, value || undefined);
  };

  const hasActiveFilters = Object.values(filters).some(
    (v) => v !== undefined && v !== null && v !== ''
  );

  return (
    <Card className="p-4">
      <div className="space-y-4">
        {/* Row 1: Entity, Account, Category */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Entité
            </label>
            <Select
              value={filters.entity_id || ''}
              onChange={(e) => handleChange('entity_id', e.target.value)}
              className="w-full"
            >
              <option value="">Toutes les entités</option>
              <option value="1">Épicerie</option>
              <option value="2">Restaurant</option>
            </Select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Compte bancaire
            </label>
            <Select
              value={filters.account_id || ''}
              onChange={(e) => handleChange('account_id', e.target.value)}
              className="w-full"
            >
              <option value="">Tous les comptes</option>
              {accounts.map((acc) => (
                <option key={acc.id} value={acc.id}>
                  {acc.label || acc.name || acc.id}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Catégorie
            </label>
            <Select
              value={filters.category_id || ''}
              onChange={(e) => handleChange('category_id', e.target.value)}
              className="w-full"
            >
              <option value="">Toutes les catégories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name || cat.code}
                </option>
              ))}
            </Select>
          </div>
        </div>

        {/* Row 2: Dates */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Date de début
            </label>
            <input
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => handleChange('date_from', e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200 min-h-[44px]"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Date de fin
            </label>
            <input
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => handleChange('date_to', e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200 min-h-[44px]"
            />
          </div>
        </div>

        {/* Row 3: Amount range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Montant minimum (€)
            </label>
            <Input
              type="number"
              step="0.01"
              value={filters.amount_min || ''}
              onChange={(e) => handleChange('amount_min', e.target.value)}
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1.5">
              Montant maximum (€)
            </label>
            <Input
              type="number"
              step="0.01"
              value={filters.amount_max || ''}
              onChange={(e) => handleChange('amount_max', e.target.value)}
              placeholder="0.00"
            />
          </div>
        </div>

        {/* Row 4: Search text */}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1.5">
            Recherche dans le libellé
          </label>
          <Input
            type="text"
            value={filters.q || ''}
            onChange={(e) => handleChange('q', e.target.value)}
            placeholder="Rechercher dans les libellés..."
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 pt-2">
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={onReset}>
              <X className="h-4 w-4" />
              Réinitialiser
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
