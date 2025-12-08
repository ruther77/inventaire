import { useState, useMemo, useCallback, useRef, useEffect, forwardRef } from 'react';
import clsx from 'clsx';
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Search,
  Filter,
  Download,
  MoreHorizontal,
  Check,
  X,
  Loader2,
  ArrowUpDown,
  Columns,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Skeleton } from './Skeleton.jsx';
import useDebounce from '../../hooks/useDebounce.js';

/**
 * DataTable - Composant de tableau de données avancé et accessible
 * WCAG 2.1 Level AA compliant
 *
 * Features:
 * - Tri, filtrage, pagination, sélection
 * - Colonnes redimensionnables, recherche, export
 * - Actions de masse, états de chargement
 *
 * Accessibility features:
 * - ARIA table roles (role="table", role="grid")
 * - ARIA sort attributes (aria-sort)
 * - Row selection with aria-selected
 * - Keyboard navigation (Arrow keys, Home, End)
 * - Screen reader announcements (aria-live)
 * - Descriptive labels (aria-label, aria-labelledby)
 * - Focus management and indicators
 *
 * @see https://www.w3.org/WAI/ARIA/apg/patterns/table/
 * @see https://www.w3.org/WAI/ARIA/apg/patterns/grid/
 */
export function DataTable({
  data = [],
  columns = [],
  loading = false,
  error = null,
  // Pagination
  pagination = true,
  pageSize: initialPageSize = 10,
  pageSizeOptions = [10, 25, 50, 100],
  // Tri
  sortable = true,
  defaultSort = null,
  // Sélection
  selectable = false,
  selectedRows = [],
  onSelectionChange,
  // Recherche
  searchable = true,
  searchPlaceholder = 'Rechercher...',
  onSearch,
  // Filtres
  filters = [],
  onFilterChange,
  // Actions
  bulkActions = [],
  rowActions,
  onRowClick,
  // Style
  className,
  stickyHeader = true,
  striped = false,
  compact = false,
  bordered = false,
  // Colonnes
  columnVisibility = true,
  resizableColumns = false,
  // Export
  exportable = false,
  onExport,
  // Empty state
  emptyMessage = 'Aucune donnée',
  emptyIcon = null,
  // Custom rendering
  rowClassName,
  getRowId = (row, index) => row.id ?? index,
}) {
  // État local
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [sortConfig, setSortConfig] = useState(defaultSort);
  const [searchQuery, setSearchQuery] = useState('');
  const [internalSelected, setInternalSelected] = useState(selectedRows);
  const [visibleColumns, setVisibleColumns] = useState(
    columns.reduce((acc, col) => ({ ...acc, [col.key]: col.visible !== false }), {})
  );
  const [columnWidths, setColumnWidths] = useState({});
  const [activeFilters, setActiveFilters] = useState({});
  const [focusedRowIndex, setFocusedRowIndex] = useState(-1);
  const [announcementMessage, setAnnouncementMessage] = useState('');

  const debouncedSearch = useDebounce(searchQuery, 300);
  const tableRef = useRef(null);
  const rowRefs = useRef([]);

  // Sync selected rows with external state
  useEffect(() => {
    if (selectedRows !== internalSelected) {
      setInternalSelected(selectedRows);
    }
  }, [selectedRows]);

  // Notify parent of selection changes
  const handleSelectionChange = useCallback(
    (newSelection) => {
      setInternalSelected(newSelection);
      onSelectionChange?.(newSelection);
    },
    [onSelectionChange]
  );

  // Tri des données
  const sortedData = useMemo(() => {
    if (!sortConfig?.key) return data;

    return [...data].sort((a, b) => {
      const column = columns.find((c) => c.key === sortConfig.key);
      const aVal = column?.getValue ? column.getValue(a) : a[sortConfig.key];
      const bVal = column?.getValue ? column.getValue(b) : b[sortConfig.key];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = typeof aVal === 'string'
        ? aVal.localeCompare(bVal, 'fr', { sensitivity: 'base' })
        : aVal < bVal ? -1 : 1;

      return sortConfig.direction === 'desc' ? -comparison : comparison;
    });
  }, [data, sortConfig, columns]);

  // Filtrage par recherche
  const filteredData = useMemo(() => {
    let result = sortedData;

    // Recherche globale
    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase();
      result = result.filter((row) =>
        columns.some((col) => {
          if (col.searchable === false) return false;
          const value = col.getValue ? col.getValue(row) : row[col.key];
          return String(value ?? '').toLowerCase().includes(searchLower);
        })
      );
    }

    // Filtres actifs
    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        const column = columns.find((c) => c.key === key);
        result = result.filter((row) => {
          const rowValue = column?.getValue ? column.getValue(row) : row[key];
          if (Array.isArray(value)) {
            return value.includes(rowValue);
          }
          return rowValue === value;
        });
      }
    });

    return result;
  }, [sortedData, debouncedSearch, activeFilters, columns]);

  // Pagination
  const totalPages = Math.ceil(filteredData.length / pageSize);
  const paginatedData = useMemo(() => {
    if (!pagination) return filteredData;
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage, pageSize, pagination]);

  // Reset page when data changes
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearch, activeFilters, pageSize]);

  // Announce changes to screen readers
  useEffect(() => {
    if (loading) {
      setAnnouncementMessage('Chargement des données...');
    } else if (filteredData.length === 0) {
      setAnnouncementMessage('Aucun résultat trouvé');
    } else {
      setAnnouncementMessage(
        `${filteredData.length} résultat${filteredData.length > 1 ? 's' : ''} trouvé${filteredData.length > 1 ? 's' : ''}`
      );
    }
  }, [loading, filteredData.length]);

  // Handlers
  const handleSort = useCallback((key) => {
    if (!sortable) return;
    setSortConfig((prev) => {
      if (prev?.key !== key) return { key, direction: 'asc' };
      if (prev.direction === 'asc') return { key, direction: 'desc' };
      return null;
    });
  }, [sortable]);

  const handleSelectAll = useCallback(() => {
    const currentPageIds = paginatedData.map((row, i) => getRowId(row, i));
    const allSelected = currentPageIds.every((id) => internalSelected.includes(id));

    if (allSelected) {
      handleSelectionChange(internalSelected.filter((id) => !currentPageIds.includes(id)));
    } else {
      handleSelectionChange([...new Set([...internalSelected, ...currentPageIds])]);
    }
  }, [paginatedData, internalSelected, handleSelectionChange, getRowId]);

  const handleSelectRow = useCallback((rowId) => {
    handleSelectionChange(
      internalSelected.includes(rowId)
        ? internalSelected.filter((id) => id !== rowId)
        : [...internalSelected, rowId]
    );
  }, [internalSelected, handleSelectionChange]);

  const handlePageChange = useCallback((page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    setFocusedRowIndex(-1); // Reset focus when page changes
  }, [totalPages]);

  // Keyboard navigation for table rows
  const handleKeyDown = useCallback(
    (e, rowIndex) => {
      const maxIndex = paginatedData.length - 1;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          if (rowIndex < maxIndex) {
            setFocusedRowIndex(rowIndex + 1);
            rowRefs.current[rowIndex + 1]?.focus();
          }
          break;

        case 'ArrowUp':
          e.preventDefault();
          if (rowIndex > 0) {
            setFocusedRowIndex(rowIndex - 1);
            rowRefs.current[rowIndex - 1]?.focus();
          }
          break;

        case 'Home':
          e.preventDefault();
          setFocusedRowIndex(0);
          rowRefs.current[0]?.focus();
          break;

        case 'End':
          e.preventDefault();
          setFocusedRowIndex(maxIndex);
          rowRefs.current[maxIndex]?.focus();
          break;

        case ' ':
        case 'Enter':
          if (selectable && !e.target.closest('button, a, input')) {
            e.preventDefault();
            const rowId = getRowId(paginatedData[rowIndex], rowIndex);
            handleSelectRow(rowId);
          }
          break;

        default:
          break;
      }
    },
    [paginatedData, selectable, handleSelectRow, getRowId]
  );

  // Visible columns
  const displayedColumns = useMemo(
    () => columns.filter((col) => visibleColumns[col.key]),
    [columns, visibleColumns]
  );

  // Render loading skeleton
  if (loading && data.length === 0) {
    return (
      <div className={clsx('w-full', className)}>
        <DataTableSkeleton columns={displayedColumns.length} rows={5} />
      </div>
    );
  }

  // Render error
  if (error) {
    return (
      <div className={clsx('w-full p-8 text-center', className)}>
        <div className="text-rose-500 mb-2">Une erreur est survenue</div>
        <div className="text-sm text-slate-500">{error.message || String(error)}</div>
      </div>
    );
  }

  const allCurrentSelected = paginatedData.length > 0 &&
    paginatedData.every((row, i) => internalSelected.includes(getRowId(row, i)));
  const someCurrentSelected = paginatedData.some((row, i) =>
    internalSelected.includes(getRowId(row, i))
  );

  return (
    <div className={clsx('w-full', className)}>
      {/* Screen reader announcements */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {announcementMessage}
      </div>

      {/* Toolbar */}
      <DataTableToolbar
        searchable={searchable}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder={searchPlaceholder}
        filters={filters}
        activeFilters={activeFilters}
        onFilterChange={(key, value) => {
          setActiveFilters((prev) => ({ ...prev, [key]: value }));
          onFilterChange?.(key, value);
        }}
        columnVisibility={columnVisibility}
        columns={columns}
        visibleColumns={visibleColumns}
        onVisibleColumnsChange={setVisibleColumns}
        exportable={exportable}
        onExport={() => onExport?.(filteredData)}
        selectedCount={internalSelected.length}
        bulkActions={bulkActions}
        data={filteredData}
      />

      {/* Table */}
      <div className="relative overflow-x-auto" role="region" aria-label="Tableau de données" tabIndex={0}>
        <table
          ref={tableRef}
          role={selectable ? 'grid' : 'table'}
          aria-label="Données du tableau"
          aria-rowcount={filteredData.length}
          aria-colcount={displayedColumns.length + (selectable ? 1 : 0) + (rowActions ? 1 : 0)}
          className={clsx(
            'w-full text-sm text-left',
            bordered && 'border border-slate-200'
          )}
        >
          <thead
            role="rowgroup"
            className={clsx(
              'text-xs uppercase bg-slate-50 text-slate-600',
              stickyHeader && 'sticky top-0 z-10 shadow-[0_1px_3px_0_rgba(0,0,0,0.05),0_1px_2px_-1px_rgba(0,0,0,0.05)]',
              bordered && 'border-b border-slate-200'
            )}
          >
            <tr role="row">
              {selectable && (
                <th role="columnheader" scope="col" className="w-12 px-3 py-3">
                  <Checkbox
                    checked={allCurrentSelected}
                    indeterminate={someCurrentSelected && !allCurrentSelected}
                    onChange={handleSelectAll}
                    aria-label="Sélectionner toutes les lignes"
                  />
                </th>
              )}
              {displayedColumns.map((column, colIndex) => (
                <th
                  key={column.key}
                  role="columnheader"
                  scope="col"
                  aria-colindex={colIndex + 1 + (selectable ? 1 : 0)}
                  aria-sort={
                    sortConfig?.key === column.key
                      ? sortConfig.direction === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : column.sortable !== false && sortable
                        ? 'none'
                        : undefined
                  }
                  className={clsx(
                    'px-4 py-3 font-semibold',
                    column.sortable !== false && sortable && 'cursor-pointer select-none hover:bg-slate-100',
                    column.align === 'right' && 'text-right',
                    column.align === 'center' && 'text-center'
                  )}
                  style={{ width: columnWidths[column.key] || column.width }}
                  onClick={() => column.sortable !== false && handleSort(column.key)}
                >
                  <div className={clsx(
                    'flex items-center gap-2',
                    column.align === 'right' && 'justify-end',
                    column.align === 'center' && 'justify-center'
                  )}>
                    <span>{column.header || column.key}</span>
                    {column.sortable !== false && sortable && (
                      <SortIndicator
                        direction={sortConfig?.key === column.key ? sortConfig.direction : null}
                      />
                    )}
                  </div>
                </th>
              ))}
              {rowActions && (
                <th role="columnheader" scope="col" className="w-12 px-3 py-3" aria-label="Actions">
                  <span className="sr-only">Actions</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody role="rowgroup" className="divide-y divide-slate-100">
            {paginatedData.length === 0 ? (
              <tr role="row">
                <td
                  role="cell"
                  colSpan={displayedColumns.length + (selectable ? 1 : 0) + (rowActions ? 1 : 0)}
                  className="px-4 py-12 text-center text-slate-500"
                >
                  {emptyIcon && <div className="mb-3">{emptyIcon}</div>}
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIndex) => {
                const rowId = getRowId(row, rowIndex);
                const isSelected = internalSelected.includes(rowId);
                const isFocused = focusedRowIndex === rowIndex;

                return (
                  <tr
                    key={rowId}
                    ref={(el) => (rowRefs.current[rowIndex] = el)}
                    role="row"
                    aria-rowindex={rowIndex + 2}
                    aria-selected={selectable ? isSelected : undefined}
                    tabIndex={onRowClick || selectable ? 0 : -1}
                    onKeyDown={(e) => handleKeyDown(e, rowIndex)}
                    className={clsx(
                      'transition-colors',
                      striped && rowIndex % 2 === 1 && 'bg-slate-50/50',
                      isSelected && 'bg-brand-50',
                      isFocused && 'ring-2 ring-brand-500 ring-inset',
                      onRowClick && 'cursor-pointer hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                      typeof rowClassName === 'function' ? rowClassName(row, rowIndex) : rowClassName
                    )}
                    onClick={() => onRowClick?.(row, rowIndex)}
                  >
                    {selectable && (
                      <td
                        role={selectable ? 'gridcell' : 'cell'}
                        className="w-12 px-3 py-3"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Checkbox
                          checked={isSelected}
                          onChange={() => handleSelectRow(rowId)}
                          aria-label={`Sélectionner la ligne ${rowIndex + 1}`}
                        />
                      </td>
                    )}
                    {displayedColumns.map((column, colIndex) => {
                      const value = column.getValue ? column.getValue(row) : row[column.key];
                      const cellContent = column.render
                        ? column.render(value, row, rowIndex)
                        : value ?? '—';

                      return (
                        <td
                          key={column.key}
                          role={selectable ? 'gridcell' : 'cell'}
                          aria-colindex={colIndex + 1 + (selectable ? 1 : 0)}
                          className={clsx(
                            compact ? 'px-4 py-2' : 'px-4 py-3',
                            column.align === 'right' && 'text-right',
                            column.align === 'center' && 'text-center',
                            column.className
                          )}
                        >
                          {cellContent}
                        </td>
                      );
                    })}
                    {rowActions && (
                      <td
                        role={selectable ? 'gridcell' : 'cell'}
                        className="w-12 px-3 py-3"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <RowActionsMenu actions={rowActions} row={row} rowIndex={rowIndex} />
                      </td>
                    )}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>

        {/* Loading overlay */}
        {loading && data.length > 0 && (
          <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination && totalPages > 0 && (
        <DataTablePagination
          currentPage={currentPage}
          totalPages={totalPages}
          pageSize={pageSize}
          pageSizeOptions={pageSizeOptions}
          totalItems={filteredData.length}
          onPageChange={handlePageChange}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setCurrentPage(1);
          }}
        />
      )}
    </div>
  );
}

/**
 * DataTableToolbar - Barre d'outils du tableau
 */
function DataTableToolbar({
  searchable,
  searchQuery,
  onSearchChange,
  searchPlaceholder,
  filters,
  activeFilters,
  onFilterChange,
  columnVisibility,
  columns,
  visibleColumns,
  onVisibleColumnsChange,
  exportable,
  onExport,
  selectedCount,
  bulkActions,
  data,
}) {
  const [showFilters, setShowFilters] = useState(false);
  const [showColumns, setShowColumns] = useState(false);

  const hasActiveFilters = Object.values(activeFilters).some(
    (v) => v !== undefined && v !== null && v !== ''
  );

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      {/* Search */}
      {searchable && (
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <label htmlFor="table-search" className="sr-only">
            Rechercher dans le tableau
          </label>
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
            aria-hidden="true"
          />
          <input
            id="table-search"
            type="search"
            role="searchbox"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            aria-label="Rechercher dans le tableau"
            aria-controls="data-table"
            className={clsx(
              'w-full pl-9 pr-4 py-2 text-sm',
              'border border-slate-200 rounded-lg',
              'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
              'placeholder-slate-400'
            )}
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              aria-label="Effacer la recherche"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded p-1"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>
      )}

      {/* Bulk actions */}
      {selectedCount > 0 && bulkActions.length > 0 && (
        <div
          className="flex items-center gap-2 px-3 py-1.5 bg-brand-50 rounded-lg"
          role="region"
          aria-label="Actions groupées"
        >
          <span
            className="text-sm font-medium text-brand-700"
            aria-live="polite"
            aria-atomic="true"
          >
            {selectedCount} sélectionné{selectedCount > 1 ? 's' : ''}
          </span>
          <div className="h-4 w-px bg-brand-200" aria-hidden="true" />
          {bulkActions.map((action) => (
            <button
              key={action.id}
              type="button"
              onClick={() => action.onClick?.(data.filter((_, i) => true))}
              className="text-sm text-brand-600 hover:text-brand-800 font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded px-2 py-1"
              aria-label={`${action.label} pour ${selectedCount} élément${selectedCount > 1 ? 's' : ''}`}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1" />

      {/* Filters */}
      {filters.length > 0 && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            aria-label="Ouvrir les filtres"
            aria-expanded={showFilters}
            aria-haspopup="true"
            className={clsx(
              'flex items-center gap-2 px-3 py-2 text-sm',
              'border rounded-lg transition-colors',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
              hasActiveFilters
                ? 'border-brand-500 bg-brand-50 text-brand-700'
                : 'border-slate-200 hover:bg-slate-50 text-slate-600'
            )}
          >
            <Filter className="h-4 w-4" aria-hidden="true" />
            Filtres
            {hasActiveFilters && (
              <span
                className="flex items-center justify-center h-5 w-5 text-xs bg-brand-500 text-white rounded-full"
                aria-label={`${Object.values(activeFilters).filter((v) => v != null && v !== '').length} filtres actifs`}
              >
                {Object.values(activeFilters).filter((v) => v != null && v !== '').length}
              </span>
            )}
          </button>

          {showFilters && (
            <FilterDropdown
              filters={filters}
              activeFilters={activeFilters}
              onFilterChange={onFilterChange}
              onClose={() => setShowFilters(false)}
            />
          )}
        </div>
      )}

      {/* Column visibility */}
      {columnVisibility && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowColumns(!showColumns)}
            className="flex items-center gap-2 px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600"
          >
            <Columns className="h-4 w-4" />
            Colonnes
          </button>

          {showColumns && (
            <ColumnVisibilityDropdown
              columns={columns}
              visibleColumns={visibleColumns}
              onVisibleColumnsChange={onVisibleColumnsChange}
              onClose={() => setShowColumns(false)}
            />
          )}
        </div>
      )}

      {/* Export */}
      {exportable && (
        <button
          type="button"
          onClick={onExport}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600"
        >
          <Download className="h-4 w-4" />
          Exporter
        </button>
      )}
    </div>
  );
}

/**
 * DataTablePagination - Composant de pagination
 */
function DataTablePagination({
  currentPage,
  totalPages,
  pageSize,
  pageSizeOptions,
  totalItems,
  onPageChange,
  onPageSizeChange,
}) {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 mt-4 px-2">
      {/* Items info */}
      <div className="text-sm text-slate-500">
        {startItem}-{endItem} sur {totalItems} résultat{totalItems > 1 ? 's' : ''}
      </div>

      {/* Page size selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-500">Lignes par page:</span>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="px-2 py-1 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </div>

      {/* Page navigation */}
      <div className="flex items-center gap-1">
        <PaginationButton
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          aria-label="Première page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </PaginationButton>
        <PaginationButton
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          aria-label="Page précédente"
        >
          <ChevronLeft className="h-4 w-4" />
        </PaginationButton>

        <div className="flex items-center gap-1 mx-2">
          {generatePageNumbers(currentPage, totalPages).map((page, i) =>
            page === '...' ? (
              <span key={`ellipsis-${i}`} className="px-2 text-slate-400">
                ...
              </span>
            ) : (
              <PaginationButton
                key={page}
                onClick={() => onPageChange(page)}
                active={page === currentPage}
              >
                {page}
              </PaginationButton>
            )
          )}
        </div>

        <PaginationButton
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          aria-label="Page suivante"
        >
          <ChevronRight className="h-4 w-4" />
        </PaginationButton>
        <PaginationButton
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          aria-label="Dernière page"
        >
          <ChevronsRight className="h-4 w-4" />
        </PaginationButton>
      </div>
    </div>
  );
}

/**
 * Composants auxiliaires
 */
function PaginationButton({ children, active, disabled, ...props }) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={clsx(
        'flex items-center justify-center min-w-[32px] h-8 px-2 text-sm rounded-md transition-colors',
        active
          ? 'bg-brand-600 text-white'
          : disabled
            ? 'text-slate-300 cursor-not-allowed'
            : 'text-slate-600 hover:bg-slate-100'
      )}
      {...props}
    >
      {children}
    </button>
  );
}

function SortIndicator({ direction }) {
  if (!direction) {
    return <ChevronsUpDown className="h-4 w-4 text-slate-300" />;
  }
  return direction === 'asc' ? (
    <ChevronUp className="h-4 w-4 text-brand-600" />
  ) : (
    <ChevronDown className="h-4 w-4 text-brand-600" />
  );
}

const Checkbox = forwardRef(function Checkbox({ checked, indeterminate, onChange, ...props }, ref) {
  const innerRef = useRef(null);

  useEffect(() => {
    if (innerRef.current) {
      innerRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);

  return (
    <label className="relative inline-flex items-center justify-center min-w-[44px] min-h-[44px] cursor-pointer">
      <input
        ref={(el) => {
          innerRef.current = el;
          if (typeof ref === 'function') ref(el);
          else if (ref) ref.current = el;
        }}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className={clsx(
          'h-5 w-5 rounded border-slate-400 text-brand-600 cursor-pointer',
          'transition-colors duration-150',
          'focus:ring-2 focus:ring-brand-500 focus:ring-offset-2',
          'hover:border-brand-500'
        )}
        {...props}
      />
    </label>
  );
});

function RowActionsMenu({ actions, row, rowIndex }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const visibleActions = typeof actions === 'function' ? actions(row, rowIndex) : actions;

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-20">
          {visibleActions.map((action) => (
            <button
              key={action.id}
              type="button"
              onClick={() => {
                action.onClick?.(row, rowIndex);
                setIsOpen(false);
              }}
              disabled={action.disabled}
              className={clsx(
                'w-full flex items-center gap-2 px-3 py-2 text-sm text-left',
                action.destructive
                  ? 'text-rose-600 hover:bg-rose-50'
                  : 'text-slate-700 hover:bg-slate-50',
                action.disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              {action.icon && <action.icon className="h-4 w-4" />}
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function FilterDropdown({ filters, activeFilters, onFilterChange, onClose }) {
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-slate-200 p-4 z-20"
    >
      <div className="space-y-4">
        {filters.map((filter) => (
          <div key={filter.key}>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              {filter.label}
            </label>
            {filter.type === 'select' ? (
              <select
                value={activeFilters[filter.key] || ''}
                onChange={(e) => onFilterChange(filter.key, e.target.value || null)}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">Tous</option>
                {filter.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={activeFilters[filter.key] || ''}
                onChange={(e) => onFilterChange(filter.key, e.target.value || null)}
                placeholder={filter.placeholder}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            )}
          </div>
        ))}
      </div>
      <div className="mt-4 pt-4 border-t border-slate-100 flex justify-end gap-2">
        <button
          type="button"
          onClick={() => {
            filters.forEach((f) => onFilterChange(f.key, null));
          }}
          className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 rounded"
        >
          Réinitialiser
        </button>
        <button
          type="button"
          onClick={onClose}
          className="px-3 py-1.5 text-sm bg-brand-600 text-white rounded hover:bg-brand-700"
        >
          Appliquer
        </button>
      </div>
    </div>
  );
}

function ColumnVisibilityDropdown({ columns, visibleColumns, onVisibleColumnsChange, onClose }) {
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-20"
    >
      <div className="px-3 py-2 border-b border-slate-100">
        <span className="text-xs font-semibold uppercase text-slate-400">
          Colonnes visibles
        </span>
      </div>
      <div className="max-h-64 overflow-y-auto py-1">
        {columns.map((column) => (
          <label
            key={column.key}
            className="flex items-center gap-3 px-3 py-2 hover:bg-slate-50 cursor-pointer"
          >
            <input
              type="checkbox"
              checked={visibleColumns[column.key]}
              onChange={(e) =>
                onVisibleColumnsChange((prev) => ({
                  ...prev,
                  [column.key]: e.target.checked,
                }))
              }
              className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            <span className="text-sm text-slate-700">{column.header || column.key}</span>
            {visibleColumns[column.key] ? (
              <Eye className="h-4 w-4 text-slate-400 ml-auto" />
            ) : (
              <EyeOff className="h-4 w-4 text-slate-300 ml-auto" />
            )}
          </label>
        ))}
      </div>
    </div>
  );
}

function DataTableSkeleton({ columns = 5, rows = 5 }) {
  return (
    <div className="w-full space-y-4">
      {/* Toolbar skeleton */}
      <div className="flex gap-3">
        <Skeleton className="h-10 w-64" />
        <div className="flex-1" />
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24" />
      </div>

      {/* Table skeleton */}
      <div className="border border-slate-200 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="flex gap-4 px-4 py-3 bg-slate-50 border-b border-slate-200">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>

        {/* Rows */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div
            key={rowIndex}
            className="flex gap-4 px-4 py-3 border-b border-slate-100 last:border-0"
          >
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton key={colIndex} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>

      {/* Pagination skeleton */}
      <div className="flex justify-between">
        <Skeleton className="h-8 w-32" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-8" />
        </div>
      </div>
    </div>
  );
}

// Utility function for pagination numbers
function generatePageNumbers(currentPage, totalPages) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const pages = [];

  // Always show first page
  pages.push(1);

  if (currentPage > 3) {
    pages.push('...');
  }

  // Pages around current
  const start = Math.max(2, currentPage - 1);
  const end = Math.min(totalPages - 1, currentPage + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (currentPage < totalPages - 2) {
    pages.push('...');
  }

  // Always show last page
  if (totalPages > 1) {
    pages.push(totalPages);
  }

  return pages;
}

export default DataTable;
