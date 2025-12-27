import { useState, useEffect, useCallback } from 'react';
import { X, Check, Search } from 'lucide-react';
import clsx from 'clsx';
import Button from './Button.jsx';

/**
 * FiltersDrawer - Panneau latéral de filtres
 * Design basé sur mockup drawer-filters.html
 */
export default function FiltersDrawer({
  open,
  onClose,
  title = 'Filtres',
  filters = [],
  activeFilters = {},
  onApply,
  onReset,
  resultCount,
  children,
}) {
  const [internalFilters, setInternalFilters] = useState(activeFilters);

  // Sync with external activeFilters
  useEffect(() => {
    setInternalFilters(activeFilters);
  }, [activeFilters]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  // Lock body scroll
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  const handleFilterChange = useCallback((filterId, value) => {
    setInternalFilters((prev) => ({
      ...prev,
      [filterId]: value,
    }));
  }, []);

  const handleApply = useCallback(() => {
    onApply?.(internalFilters);
    onClose?.();
  }, [internalFilters, onApply, onClose]);

  const handleReset = useCallback(() => {
    setInternalFilters({});
    onReset?.();
  }, [onReset]);

  const removeActiveFilter = useCallback((filterId) => {
    setInternalFilters((prev) => {
      const next = { ...prev };
      delete next[filterId];
      return next;
    });
  }, []);

  // Get active filter tags for display
  const activeFilterTags = Object.entries(internalFilters)
    .filter(([_, value]) => {
      if (Array.isArray(value)) return value.length > 0;
      if (typeof value === 'object' && value !== null) return Object.values(value).some(Boolean);
      return value !== undefined && value !== null && value !== '';
    })
    .map(([key, value]) => {
      const filter = filters.find((f) => f.id === key);
      let label = filter?.label || key;
      if (Array.isArray(value)) {
        label = value.join(', ');
      } else if (typeof value === 'string') {
        label = value;
      }
      return { id: key, label };
    });

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed top-0 right-0 w-[380px] h-screen bg-slate-900/98 border-l border-white/15 flex flex-col z-50 animate-slide-in-right"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white font-['Sora',sans-serif] flex items-center gap-2">
            <Search className="w-5 h-5 text-slate-400" />
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
            aria-label="Fermer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Active Filters Tags */}
        {activeFilterTags.length > 0 && (
          <div className="flex flex-wrap gap-2 px-6 py-4 bg-white/5 border-b border-white/10">
            {activeFilterTags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-md text-xs text-emerald-400"
              >
                {tag.label}
                <button
                  type="button"
                  onClick={() => removeActiveFilter(tag.id)}
                  className="text-emerald-400 hover:text-emerald-300"
                  aria-label={`Supprimer le filtre ${tag.label}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Body - Scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {/* Render filter sections from config */}
          {filters.map((filter) => (
            <FilterSection
              key={filter.id}
              filter={filter}
              value={internalFilters[filter.id]}
              onChange={(value) => handleFilterChange(filter.id, value)}
            />
          ))}

          {/* Or render custom children */}
          {children}
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-5 border-t border-white/10">
          <Button
            variant="subtle"
            onClick={handleReset}
            className="flex-1"
          >
            Réinitialiser
          </Button>
          <Button
            variant="primary"
            onClick={handleApply}
            className="flex-1 bg-emerald-500 hover:bg-emerald-600"
          >
            Appliquer{resultCount !== undefined && ` (${resultCount})`}
          </Button>
        </div>
      </div>

      <style>{`
        @keyframes slide-in-right {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
      `}</style>
    </>
  );
}

/**
 * FilterSection - Section de filtre générique
 */
function FilterSection({ filter, value, onChange }) {
  const { id, type, label, options = [], min, max, placeholder } = filter;

  return (
    <div className="mb-7 last:mb-0">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
        {label}
      </h3>

      {/* Checkbox options */}
      {type === 'checkbox' && (
        <div className="flex flex-col gap-2">
          {options.map((option) => {
            const isSelected = Array.isArray(value)
              ? value.includes(option.value)
              : false;

            return (
              <FilterOption
                key={option.value}
                label={option.label}
                count={option.count}
                selected={isSelected}
                onClick={() => {
                  const currentValues = Array.isArray(value) ? value : [];
                  const newValues = isSelected
                    ? currentValues.filter((v) => v !== option.value)
                    : [...currentValues, option.value];
                  onChange(newValues);
                }}
              />
            );
          })}
        </div>
      )}

      {/* Range slider */}
      {type === 'range' && (
        <RangeFilter
          min={min}
          max={max}
          value={value || { min: min || 0, max: max || 100 }}
          onChange={onChange}
        />
      )}

      {/* Date range */}
      {type === 'dateRange' && (
        <DateRangeFilter
          value={value || {}}
          onChange={onChange}
          quickDates={filter.quickDates}
        />
      )}
    </div>
  );
}

/**
 * FilterOption - Option de filtre checkbox
 */
function FilterOption({ label, count, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-left transition-all',
        selected
          ? 'bg-emerald-500/10 border border-emerald-500/30'
          : 'bg-white/5 border border-transparent hover:bg-white/10'
      )}
    >
      <div
        className={clsx(
          'w-[18px] h-[18px] rounded flex items-center justify-center border-2 transition-all text-xs',
          selected
            ? 'bg-emerald-500 border-emerald-500 text-white'
            : 'border-white/20'
        )}
      >
        {selected && <Check className="w-3 h-3" strokeWidth={3} />}
      </div>
      <span className="flex-1 text-sm text-white">{label}</span>
      {count !== undefined && (
        <span className="text-xs text-slate-400 px-2 py-0.5 bg-white/5 rounded">
          {count}
        </span>
      )}
    </button>
  );
}

/**
 * RangeFilter - Filtre de fourchette numérique
 */
function RangeFilter({ min = 0, max = 100, value, onChange }) {
  const handleMinChange = (e) => {
    const newMin = Number(e.target.value);
    onChange({ ...value, min: newMin });
  };

  const handleMaxChange = (e) => {
    const newMax = Number(e.target.value);
    onChange({ ...value, max: newMax });
  };

  const rangePercent = {
    left: ((value.min - min) / (max - min)) * 100,
    right: ((max - value.max) / (max - min)) * 100,
  };

  return (
    <div className="py-4">
      <div className="flex gap-3 mb-3">
        <input
          type="number"
          value={value.min}
          onChange={handleMinChange}
          placeholder="Min"
          className="flex-1 px-3 py-2.5 bg-white/5 border border-white/15 rounded-lg text-white text-sm text-center focus:outline-none focus:border-emerald-500"
        />
        <input
          type="number"
          value={value.max}
          onChange={handleMaxChange}
          placeholder="Max"
          className="flex-1 px-3 py-2.5 bg-white/5 border border-white/15 rounded-lg text-white text-sm text-center focus:outline-none focus:border-emerald-500"
        />
      </div>
      <div className="h-1.5 bg-white/10 rounded-full relative">
        <div
          className="absolute h-full bg-emerald-500 rounded-full"
          style={{
            left: `${rangePercent.left}%`,
            right: `${rangePercent.right}%`,
          }}
        />
      </div>
    </div>
  );
}

/**
 * DateRangeFilter - Filtre de période
 */
function DateRangeFilter({ value, onChange, quickDates }) {
  const defaultQuickDates = [
    { label: "Aujourd'hui", value: 'today' },
    { label: '7 jours', value: '7d' },
    { label: '30 jours', value: '30d' },
    { label: 'Ce mois', value: 'month' },
    { label: 'Trimestre', value: 'quarter' },
  ];

  const dates = quickDates || defaultQuickDates;

  return (
    <div>
      <div className="flex gap-3 mb-3">
        <input
          type="date"
          value={value.from || ''}
          onChange={(e) => onChange({ ...value, from: e.target.value })}
          className="flex-1 px-3 py-2.5 bg-white/5 border border-white/15 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
        />
        <input
          type="date"
          value={value.to || ''}
          onChange={(e) => onChange({ ...value, to: e.target.value })}
          className="flex-1 px-3 py-2.5 bg-white/5 border border-white/15 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        {dates.map((date) => (
          <button
            key={date.value}
            type="button"
            onClick={() => onChange({ ...value, quick: date.value })}
            className={clsx(
              'px-3 py-1.5 text-xs rounded-md border transition-all',
              value.quick === date.value
                ? 'bg-blue-500/20 border-blue-500 text-blue-400'
                : 'bg-white/5 border-white/15 text-slate-300 hover:bg-white/10'
            )}
          >
            {date.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// Export sub-components for custom usage
export { FilterSection, FilterOption, RangeFilter, DateRangeFilter };
