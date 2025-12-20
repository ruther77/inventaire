/**
 * SmartTable - Table intelligente avec tri, filtres, export
 * Phase 4 - UX_NEXT_GEN_2025.md
 *
 * Dark Theme Design System (2025 Next-Gen)
 *
 * Features:
 * - Tri multi-colonnes
 * - Filtres inline
 * - Export CSV/JSON
 * - Sélection bulk
 * - Édition inline
 * - Virtualisation (grandes listes)
 * - Responsive
 */

import { useState, useMemo, useCallback, useRef, forwardRef, useImperativeHandle } from 'react';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Filter,
  Download,
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  Check,
  Loader2,
  Settings2,
} from 'lucide-react';
import clsx from 'clsx';
import EditableCell from './InlineEditor.jsx';

// ============================================================================
// SMART TABLE COMPONENT
// ============================================================================

const SmartTable = forwardRef(function SmartTable(
  {
    // Data
    data = [],
    columns = [],
    keyField = 'id',

    // Features
    sortable = true,
    filterable = true,
    selectable = false,
    exportable = true,
    editable = false,

    // Pagination
    paginated = true,
    pageSize = 25,
    pageSizeOptions = [10, 25, 50, 100],

    // Callbacks
    onSort,
    onFilter,
    onSelect,
    onEdit,
    onRowClick,
    onExport,

    // State
    loading = false,
    emptyMessage = 'Aucune donnée',

    // Style
    className,
    stickyHeader = true,
    striped = true,
    compact = false,
    variant = 'default', // default, bordered, minimal

    // External control
    initialSort,
    initialFilters,
  },
  ref
) {
  // State
  const [sortConfig, setSortConfig] = useState(initialSort || { key: null, direction: 'asc' });
  const [filters, setFilters] = useState(initialFilters || {});
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [localPageSize, setLocalPageSize] = useState(pageSize);
  const [showFilters, setShowFilters] = useState(false);
  const [showColumnSettings, setShowColumnSettings] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState(
    columns.map((col) => col.key)
  );

  const tableRef = useRef(null);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    getSelectedRows: () => Array.from(selectedRows).map((key) =>
      data.find((row) => row[keyField] === key)
    ),
    clearSelection: () => setSelectedRows(new Set()),
    resetFilters: () => setFilters({}),
    exportData: (format) => handleExport(format),
    getData: () => processedData,
  }));

  // Process data: filter, sort
  const processedData = useMemo(() => {
    let result = [...data];

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (!value) return;
      const column = columns.find((col) => col.key === key);
      if (column?.filterFn) {
        result = result.filter((row) => column.filterFn(row[key], value, row));
      } else {
        result = result.filter((row) =>
          String(row[key] ?? '')
            .toLowerCase()
            .includes(String(value).toLowerCase())
        );
      }
    });

    // Apply sort
    if (sortConfig.key) {
      const column = columns.find((col) => col.key === sortConfig.key);
      result.sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];

        if (column?.sortFn) {
          return column.sortFn(aVal, bVal) * (sortConfig.direction === 'asc' ? 1 : -1);
        }

        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;

        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return (aVal - bVal) * (sortConfig.direction === 'asc' ? 1 : -1);
        }

        return String(aVal).localeCompare(String(bVal)) *
          (sortConfig.direction === 'asc' ? 1 : -1);
      });
    }

    return result;
  }, [data, filters, sortConfig, columns]);

  // Pagination
  const paginatedData = useMemo(() => {
    if (!paginated) return processedData;
    const start = (currentPage - 1) * localPageSize;
    return processedData.slice(start, start + localPageSize);
  }, [processedData, currentPage, localPageSize, paginated]);

  const totalPages = Math.ceil(processedData.length / localPageSize);

  // Handlers
  const handleSort = useCallback((key) => {
    if (!sortable) return;

    setSortConfig((prev) => {
      const newConfig = {
        key,
        direction:
          prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
      };
      onSort?.(newConfig);
      return newConfig;
    });
  }, [sortable, onSort]);

  const handleFilterChange = useCallback((key, value) => {
    setFilters((prev) => {
      const newFilters = { ...prev, [key]: value };
      if (!value) delete newFilters[key];
      onFilter?.(newFilters);
      return newFilters;
    });
    setCurrentPage(1);
  }, [onFilter]);

  const handleSelectAll = useCallback(() => {
    if (selectedRows.size === paginatedData.length) {
      setSelectedRows(new Set());
      onSelect?.([]);
    } else {
      const allKeys = new Set(paginatedData.map((row) => row[keyField]));
      setSelectedRows(allKeys);
      onSelect?.(paginatedData);
    }
  }, [paginatedData, selectedRows, keyField, onSelect]);

  const handleSelectRow = useCallback((key) => {
    setSelectedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      onSelect?.(
        Array.from(newSet).map((k) => data.find((row) => row[keyField] === k))
      );
      return newSet;
    });
  }, [data, keyField, onSelect]);

  const handleExport = useCallback((format = 'csv') => {
    const exportData = processedData.map((row) => {
      const exportRow = {};
      columns.forEach((col) => {
        if (col.exportable !== false) {
          exportRow[col.header || col.key] = col.exportFn
            ? col.exportFn(row[col.key], row)
            : row[col.key];
        }
      });
      return exportRow;
    });

    if (format === 'csv') {
      const headers = Object.keys(exportData[0] || {});
      const csvContent = [
        headers.join(','),
        ...exportData.map((row) =>
          headers.map((h) => {
            const val = row[h];
            if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
              return `"${val.replace(/"/g, '""')}"`;
            }
            return val ?? '';
          }).join(',')
        ),
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `export_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } else if (format === 'json') {
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `export_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
    }

    onExport?.(format, exportData);
  }, [processedData, columns, onExport]);

  // Visible columns
  const displayColumns = columns.filter((col) => visibleColumns.includes(col.key));

  // Variant styles - Dark Theme
  const variantStyles = {
    default: 'border border-white/10 rounded-xl overflow-hidden',
    bordered: 'border border-white/20 rounded-xl overflow-hidden [&_td]:border-white/10 [&_th]:border-white/10',
    minimal: 'overflow-hidden',
  };

  return (
    <div className={clsx('relative', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4 mb-3">
        <div className="flex items-center gap-2">
          {filterable && (
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border transition-colors',
                showFilters || Object.keys(filters).length > 0
                  ? 'bg-blue-500/20 border-blue-500/30 text-blue-400'
                  : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
              )}
            >
              <Filter className="w-4 h-4" />
              Filtres
              {Object.keys(filters).length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-500 text-white rounded-full">
                  {Object.keys(filters).length}
                </span>
              )}
            </button>
          )}

          {selectable && selectedRows.size > 0 && (
            <span className="text-sm text-slate-400">
              {selectedRows.size} sélectionné{selectedRows.size > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Column visibility */}
          <div className="relative">
            <button
              onClick={() => setShowColumnSettings(!showColumnSettings)}
              className="p-2 rounded-lg border border-white/10 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
              title="Colonnes"
            >
              <Settings2 className="w-4 h-4" />
            </button>
            {showColumnSettings && (
              <div className="absolute right-0 top-full mt-1 z-20 bg-slate-800 border border-white/10 rounded-xl shadow-xl p-2 min-w-[200px]">
                {columns.map((col) => (
                  <label
                    key={col.key}
                    className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded-lg cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={visibleColumns.includes(col.key)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setVisibleColumns([...visibleColumns, col.key]);
                        } else {
                          setVisibleColumns(visibleColumns.filter((k) => k !== col.key));
                        }
                      }}
                      className="rounded bg-white/10 border-white/20 text-blue-500 focus:ring-blue-500/50"
                    />
                    <span className="text-sm text-slate-300">{col.header || col.key}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Export */}
          {exportable && (
            <div className="relative group">
              <button
                onClick={() => handleExport('csv')}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-white/10 text-slate-300 hover:bg-white/10 transition-colors"
              >
                <Download className="w-4 h-4" />
                Exporter
              </button>
            </div>
          )}

          {/* Results count */}
          <span className="text-sm text-slate-500">
            {processedData.length} résultat{processedData.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Filters row */}
      {showFilters && (
        <div className="flex flex-wrap gap-2 mb-3 p-3 bg-white/5 rounded-xl border border-white/10">
          {displayColumns
            .filter((col) => col.filterable !== false)
            .map((col) => (
              <div key={col.key} className="flex items-center gap-1">
                <span className="text-xs text-slate-500">{col.header || col.key}:</span>
                {col.filterType === 'select' ? (
                  <select
                    value={filters[col.key] || ''}
                    onChange={(e) => handleFilterChange(col.key, e.target.value)}
                    className="text-sm px-2 py-1 rounded-lg border border-white/20 bg-white/5 text-white"
                  >
                    <option value="">Tous</option>
                    {col.filterOptions?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500" />
                    <input
                      type="text"
                      value={filters[col.key] || ''}
                      onChange={(e) => handleFilterChange(col.key, e.target.value)}
                      placeholder="Filtrer..."
                      className="text-sm pl-6 pr-2 py-1 w-32 rounded-lg border border-white/20 bg-white/5 text-white placeholder-slate-500"
                    />
                  </div>
                )}
              </div>
            ))}
          {Object.keys(filters).length > 0 && (
            <button
              onClick={() => {
                setFilters({});
                onFilter?.({});
              }}
              className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1"
            >
              <X className="w-3 h-3" />
              Effacer tout
            </button>
          )}
        </div>
      )}

      {/* Table */}
      <div
        ref={tableRef}
        className={clsx(variantStyles[variant], 'overflow-x-auto')}
      >
        <table className="w-full">
          <thead
            className={clsx(
              'bg-white/5 text-left text-sm font-medium text-slate-400',
              stickyHeader && 'sticky top-0 z-10'
            )}
          >
            <tr>
              {selectable && (
                <th className="w-10 px-3 py-3">
                  <input
                    type="checkbox"
                    checked={
                      paginatedData.length > 0 &&
                      selectedRows.size === paginatedData.length
                    }
                    onChange={handleSelectAll}
                    className="rounded bg-white/10 border-white/20 text-blue-500"
                  />
                </th>
              )}
              {displayColumns.map((col) => (
                <th
                  key={col.key}
                  className={clsx(
                    'px-3',
                    compact ? 'py-2' : 'py-3',
                    col.width && `w-[${col.width}]`,
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    sortable && col.sortable !== false && 'cursor-pointer hover:bg-white/5 transition-colors'
                  )}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    <span>{col.header || col.key}</span>
                    {sortable && col.sortable !== false && (
                      <span className="text-slate-500">
                        {sortConfig.key === col.key ? (
                          sortConfig.direction === 'asc' ? (
                            <ArrowUp className="w-4 h-4 text-blue-400" />
                          ) : (
                            <ArrowDown className="w-4 h-4 text-blue-400" />
                          )
                        ) : (
                          <ArrowUpDown className="w-4 h-4 opacity-30" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-white/5">
            {loading ? (
              <tr>
                <td
                  colSpan={displayColumns.length + (selectable ? 1 : 0)}
                  className="px-3 py-12 text-center"
                >
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-500" />
                  <p className="text-sm text-slate-500 mt-2">Chargement...</p>
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={displayColumns.length + (selectable ? 1 : 0)}
                  className="px-3 py-12 text-center text-slate-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIndex) => {
                const rowKey = row[keyField];
                const isSelected = selectedRows.has(rowKey);

                return (
                  <tr
                    key={rowKey}
                    className={clsx(
                      'transition-colors',
                      striped && rowIndex % 2 === 1 && 'bg-white/[0.02]',
                      isSelected && 'bg-blue-500/10',
                      onRowClick && 'cursor-pointer hover:bg-white/5'
                    )}
                    onClick={() => onRowClick?.(row)}
                  >
                    {selectable && (
                      <td className="w-10 px-3 py-2">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleSelectRow(rowKey);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="rounded bg-white/10 border-white/20 text-blue-500"
                        />
                      </td>
                    )}
                    {displayColumns.map((col) => (
                      <td
                        key={col.key}
                        className={clsx(
                          'px-3',
                          compact ? 'py-2' : 'py-3',
                          'text-sm text-slate-300',
                          col.align === 'right' && 'text-right',
                          col.align === 'center' && 'text-center'
                        )}
                      >
                        {editable && col.editable ? (
                          <EditableCell
                            value={row[col.key]}
                            displayValue={
                              col.render
                                ? col.render(row[col.key], row)
                                : row[col.key]
                            }
                            type={col.type || 'text'}
                            options={col.options}
                            onSave={(value) => onEdit?.(rowKey, col.key, value)}
                            formatDisplay={col.formatDisplay}
                          />
                        ) : col.render ? (
                          col.render(row[col.key], row)
                        ) : (
                          row[col.key] ?? '-'
                        )}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {paginated && totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Lignes par page:</span>
            <select
              value={localPageSize}
              onChange={(e) => {
                setLocalPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="px-2 py-1 rounded-lg border border-white/20 bg-white/5 text-white"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500">
              {(currentPage - 1) * localPageSize + 1}-
              {Math.min(currentPage * localPageSize, processedData.length)} sur{' '}
              {processedData.length}
            </span>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              {/* Page numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={clsx(
                      'w-8 h-8 rounded-lg text-sm transition-colors',
                      currentPage === pageNum
                        ? 'bg-blue-500 text-white'
                        : 'text-slate-400 hover:bg-white/10'
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

export default SmartTable;

// ============================================================================
// COLUMN HELPERS
// ============================================================================

export const columnHelpers = {
  // Nombre formaté
  number: (key, header, options = {}) => ({
    key,
    header,
    align: 'right',
    render: (val) =>
      val !== null && val !== undefined
        ? Number(val).toLocaleString('fr-FR', options)
        : '-',
    sortFn: (a, b) => (a || 0) - (b || 0),
    ...options,
  }),

  // Prix en euros
  currency: (key, header, options = {}) => ({
    key,
    header,
    align: 'right',
    render: (val) => {
      if (val === null || val === undefined) return '-';
      const num = Number(val);
      const formatted = num.toLocaleString('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      const isNegative = num < 0;
      return (
        <span className={isNegative ? 'text-rose-400' : 'text-emerald-400'}>
          {formatted}€
        </span>
      );
    },
    sortFn: (a, b) => (a || 0) - (b || 0),
    ...options,
  }),

  // Pourcentage
  percentage: (key, header, options = {}) => ({
    key,
    header,
    align: 'right',
    render: (val) =>
      val !== null && val !== undefined
        ? `${Number(val).toFixed(1)}%`
        : '-',
    sortFn: (a, b) => (a || 0) - (b || 0),
    ...options,
  }),

  // Date
  date: (key, header, options = {}) => ({
    key,
    header,
    render: (val) =>
      val
        ? new Date(val).toLocaleDateString('fr-FR')
        : '-',
    sortFn: (a, b) => new Date(a || 0) - new Date(b || 0),
    ...options,
  }),

  // Date et heure
  datetime: (key, header, options = {}) => ({
    key,
    header,
    render: (val) =>
      val
        ? new Date(val).toLocaleString('fr-FR')
        : '-',
    sortFn: (a, b) => new Date(a || 0) - new Date(b || 0),
    ...options,
  }),

  // Badge/Status - Dark theme
  status: (key, header, statusConfig = {}, options = {}) => ({
    key,
    header,
    render: (val) => {
      const config = statusConfig[val] || { label: val, color: 'slate' };
      const colorMap = {
        emerald: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        green: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        yellow: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        rose: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
        red: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
        blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        purple: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
        slate: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
        gray: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
      };
      return (
        <span
          className={clsx(
            'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
            colorMap[config.color] || colorMap.slate
          )}
        >
          {config.icon && <span className="mr-1">{config.icon}</span>}
          {config.label}
        </span>
      );
    },
    filterType: 'select',
    filterOptions: Object.entries(statusConfig).map(([value, cfg]) => ({
      value,
      label: cfg.label,
    })),
    ...options,
  }),

  // Boolean
  boolean: (key, header, options = {}) => ({
    key,
    header,
    align: 'center',
    render: (val) =>
      val ? (
        <Check className="w-4 h-4 text-emerald-400 mx-auto" />
      ) : (
        <X className="w-4 h-4 text-slate-600 mx-auto" />
      ),
    filterType: 'select',
    filterOptions: [
      { value: 'true', label: 'Oui' },
      { value: 'false', label: 'Non' },
    ],
    filterFn: (val, filter) =>
      filter === 'true' ? Boolean(val) : !Boolean(val),
    ...options,
  }),

  // Actions
  actions: (render, options = {}) => ({
    key: '_actions',
    header: '',
    sortable: false,
    filterable: false,
    exportable: false,
    render,
    ...options,
  }),
};
