/**
 * MobileDataTable - Version mobile-optimisée du DataTable avec support des gestes
 *
 * Features:
 * - Vue cards sur mobile avec gestes swipe
 * - Vue tableau sur desktop (réutilise DataTable)
 * - Swipe left/right pour actions rapides
 * - Long press pour menu contextuel
 * - Responsive automatique
 *
 * @example
 * <MobileDataTable
 *   data={data}
 *   columns={columns}
 *   mobileCardRenderer={(row) => <div>{row.name}</div>}
 *   swipeActions={{
 *     left: [{ label: 'Supprimer', icon: Trash, variant: 'danger', onAction: handleDelete }],
 *     right: [{ label: 'Éditer', icon: Edit, variant: 'primary', onAction: handleEdit }],
 *   }}
 * />
 */

import { useState, useMemo } from 'react';
import clsx from 'clsx';
import { Search, X } from 'lucide-react';
import { DataTable } from './DataTable.jsx';
import { SwipeableRow } from './SwipeableRow.jsx';
import useMediaQuery from '../../hooks/useMediaQuery.js';
import useDebounce from '../../hooks/useDebounce.js';

export function MobileDataTable({
  data = [],
  columns = [],
  loading = false,
  error = null,
  // Mobile-specific
  mobileCardRenderer,
  swipeActions = {},
  longPressActions = [],
  // Search
  searchable = true,
  searchPlaceholder = 'Rechercher...',
  onSearch,
  // Callbacks
  onRowClick,
  // Style
  className,
  cardClassName,
  // Empty state
  emptyMessage = 'Aucune donnée',
  emptyIcon = null,
  // Passthrough for desktop table
  ...tableProps
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebounce(searchQuery, 300);
  const isMobile = useMediaQuery('(max-width: 768px)');

  // Filter data based on search
  const filteredData = useMemo(() => {
    if (!debouncedSearch) return data;

    const searchLower = debouncedSearch.toLowerCase();
    return data.filter((row) =>
      columns.some((col) => {
        if (col.searchable === false) return false;
        const value = col.getValue ? col.getValue(row) : row[col.key];
        return String(value ?? '').toLowerCase().includes(searchLower);
      })
    );
  }, [data, debouncedSearch, columns]);

  // Desktop: use standard DataTable
  if (!isMobile) {
    return (
      <DataTable
        data={filteredData}
        columns={columns}
        loading={loading}
        error={error}
        searchable={searchable}
        searchPlaceholder={searchPlaceholder}
        onSearch={onSearch}
        onRowClick={onRowClick}
        className={className}
        emptyMessage={emptyMessage}
        emptyIcon={emptyIcon}
        {...tableProps}
      />
    );
  }

  // Mobile: use card view with gestures
  return (
    <div className={clsx('w-full', className)}>
      {/* Mobile search */}
      {searchable && (
        <div className="mb-4">
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 pointer-events-none"
              aria-hidden="true"
            />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                onSearch?.(e.target.value);
              }}
              placeholder={searchPlaceholder}
              className={clsx(
                'w-full pl-10 pr-4 py-3 text-base text-slate-900',
                'border border-slate-300 bg-white rounded-lg',
                'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
                'placeholder-slate-400'
              )}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                aria-label="Effacer la recherche"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && filteredData.length === 0 && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-24 bg-slate-200 rounded-lg animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-8 text-center">
          <div className="text-rose-500 mb-2">
            <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <div className="text-rose-600 font-semibold mb-1">Une erreur est survenue</div>
          <div className="text-sm text-slate-600">{error.message || String(error)}</div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filteredData.length === 0 && (
        <div className="p-8 text-center">
          {emptyIcon && <div className="mb-3 text-slate-400">{emptyIcon}</div>}
          <div className="text-slate-600">{emptyMessage}</div>
        </div>
      )}

      {/* Mobile cards with swipe */}
      {!loading && !error && filteredData.length > 0 && (
        <div className="space-y-3">
          {filteredData.map((row, index) => {
            const leftActionsWithData = swipeActions.left?.map((action) => ({
              ...action,
              onAction: () => action.onAction?.(row, index),
            }));

            const rightActionsWithData = swipeActions.right?.map((action) => ({
              ...action,
              onAction: () => action.onAction?.(row, index),
            }));

            const longPressActionsWithData = longPressActions.map((action) => ({
              ...action,
              onAction: () => action.onAction?.(row, index),
            }));

            return (
              <SwipeableRow
                key={row.id ?? index}
                leftActions={leftActionsWithData}
                rightActions={rightActionsWithData}
                longPressActions={longPressActionsWithData}
                className={cardClassName}
              >
                <div
                  onClick={() => onRowClick?.(row, index)}
                  className={clsx(
                    'bg-white rounded-lg border border-slate-200 shadow-sm',
                    'p-4 transition-shadow',
                    onRowClick && 'active:shadow-md cursor-pointer'
                  )}
                >
                  {mobileCardRenderer ? (
                    mobileCardRenderer(row, index)
                  ) : (
                    <DefaultMobileCard row={row} columns={columns} />
                  )}
                </div>
              </SwipeableRow>
            );
          })}
        </div>
      )}

      {/* Loading overlay for refresh */}
      {loading && filteredData.length > 0 && (
        <div className="fixed inset-0 bg-slate-900/20 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-4 shadow-lg">
            <div className="animate-spin h-8 w-8 border-3 border-brand-500 border-t-transparent rounded-full" />
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * DefaultMobileCard - Carte par défaut si aucun renderer custom n'est fourni
 */
function DefaultMobileCard({ row, columns }) {
  const visibleColumns = columns.filter((col) => col.mobileVisible !== false);

  return (
    <div className="space-y-2">
      {visibleColumns.map((column) => {
        const value = column.getValue ? column.getValue(row) : row[column.key];
        const cellContent = column.render
          ? column.render(value, row)
          : value ?? '—';

        return (
          <div key={column.key} className="flex justify-between items-start gap-2">
            <span className="text-sm font-medium text-slate-500 flex-shrink-0">
              {column.header || column.key}:
            </span>
            <span className="text-sm text-slate-900 text-right">
              {cellContent}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default MobileDataTable;
