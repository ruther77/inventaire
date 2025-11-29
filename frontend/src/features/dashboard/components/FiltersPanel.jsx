import React from 'react';
import { Search } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';

const statusOptions = [
  { value: 'all', label: 'Tout statut' },
  { value: 'critical', label: 'Critique' },
  { value: 'warning', label: 'Alerte' },
  { value: 'ok', label: 'OK' },
];

export default function FiltersPanel({
  categories = [],
  filters,
  meta,
  onChange,
  onReset,
}) {
  const { search, category, status } = filters;
  const handleUpdate = (field, value) => {
    if (onChange) {
      onChange(field, value);
    }
  };
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">FILTRES</p>
          <h3 className="text-lg font-semibold text-slate-900">Focus catalogue</h3>
        </div>
        <Button size="xs" variant="ghost" onClick={onReset}>
          Réinitialiser
        </Button>
      </div>
      <div className="mt-4 space-y-4">
        <label className="text-xs uppercase tracking-[0.4em] text-slate-400">Recherche</label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={search}
            placeholder="SKU, fournisseur, famille…"
            className="w-full rounded-2xl border border-slate-200 bg-white px-10 py-3 text-sm text-slate-900 focus:border-brand-500 focus:outline-none"
            onChange={(event) => handleUpdate('search', event.target.value)}
          />
        </div>

        <label className="text-xs uppercase tracking-[0.4em] text-slate-400">Catégorie</label>
        <select
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 focus:border-brand-500 focus:outline-none"
          value={category}
          onChange={(event) => handleUpdate('category', event.target.value)}
        >
          <option value="all">Toutes</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>

        <label className="text-xs uppercase tracking-[0.4em] text-slate-400">Statut</label>
        <div className="flex gap-2">
          {statusOptions.map((item) => (
            <button
              key={item.value}
              className={`flex-1 rounded-2xl border px-3 py-2 text-xs font-semibold transition ${
                status === item.value
                  ? 'border-brand-500 bg-brand-500/10 text-brand-600'
                  : 'border-slate-200 text-slate-600'
              }`}
              onClick={() => handleUpdate('status', item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-6 flex items-center justify-between text-xs text-slate-500">
        <span>
          {meta
            ? `Affiche ${meta.page * meta.per_page - meta.per_page + 1} - ${
                meta.page * meta.per_page < meta.total ? meta.page * meta.per_page : meta.total
              } sur ${meta.total}`
            : 'Chargement...'}
        </span>
        <Button variant="ghost" size="sm">
          Exporter
        </Button>
      </div>
    </div>
  );
}
