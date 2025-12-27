/**
 * SuppliersListPage - Liste paginée des fournisseurs avec filtres
 *
 * Implémentation exacte selon SUPPLIER_SCORING_FRONTEND_INTEGRATION.md
 * Affiche la liste paginée avec filtres, tri et actions.
 */

import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  BarChart3,
  RefreshCw,
  Download,
  Eye,
  Plus,
  Pencil,
} from 'lucide-react';
import clsx from 'clsx';
import { useSuppliersPaginated } from '@/hooks/useSupplierScoring.js';
import Card, { CardHeader, CardContent } from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Badge from '@/components/ui/Badge.jsx';
import { Skeleton } from '@/components/ui/Skeleton.jsx';
import { SupplierModal, AddSupplierModal } from '@/components/modals/index.js';

// ============================================================================
// GRADE CONFIG
// ============================================================================

const GRADE_CONFIG = {
  A: { color: 'emerald', label: 'Excellent', bg: 'bg-emerald-500', text: 'text-emerald-400', badgeVariant: 'success' },
  B: { color: 'blue', label: 'Bon', bg: 'bg-blue-500', text: 'text-blue-400', badgeVariant: 'info' },
  C: { color: 'amber', label: 'Moyen', bg: 'bg-amber-500', text: 'text-amber-400', badgeVariant: 'warning' },
  D: { color: 'orange', label: 'Faible', bg: 'bg-orange-500', text: 'text-orange-400', badgeVariant: 'warning' },
  F: { color: 'rose', label: 'Critique', bg: 'bg-rose-500', text: 'text-rose-400', badgeVariant: 'danger' },
};

const TREND_ICONS = {
  improving: { icon: TrendingUp, color: 'text-emerald-400' },
  stable: { icon: BarChart3, color: 'text-slate-400' },
  declining: { icon: TrendingDown, color: 'text-rose-400' },
  up: { icon: TrendingUp, color: 'text-emerald-400' },
  down: { icon: TrendingDown, color: 'text-rose-400' },
};

// ============================================================================
// FILTER COMPONENT
// ============================================================================

function FiltersPanel({ filters, onFiltersChange, onReset }) {
  return (
    <Card padding="md">
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher un fournisseur..."
            value={filters.search || ''}
            onChange={(e) => onFiltersChange({ ...filters, search: e.target.value, page: 1 })}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Min Score */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Score min:</label>
          <input
            type="number"
            min="0"
            max="100"
            value={filters.minScore || ''}
            onChange={(e) => onFiltersChange({ ...filters, minScore: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
            className="w-20 px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Grade Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Grade:</label>
          <select
            value={filters.gradeFilter || ''}
            onChange={(e) => onFiltersChange({ ...filters, gradeFilter: e.target.value || undefined, page: 1 })}
            className="px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Tous</option>
            <option value="A">Grade A</option>
            <option value="B">Grade B</option>
            <option value="C">Grade C</option>
            <option value="D">Grade D</option>
            <option value="F">Grade F</option>
          </select>
        </div>

        {/* Sort By */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Trier par:</label>
          <select
            value={filters.sortBy || 'score'}
            onChange={(e) => onFiltersChange({ ...filters, sortBy: e.target.value, page: 1 })}
            className="px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="score">Score</option>
            <option value="name">Nom</option>
            <option value="grade">Grade</option>
          </select>
        </div>

        {/* Sort Order */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Ordre:</label>
          <select
            value={filters.sortOrder || 'desc'}
            onChange={(e) => onFiltersChange({ ...filters, sortOrder: e.target.value, page: 1 })}
            className="px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="desc">Décroissant</option>
            <option value="asc">Croissant</option>
          </select>
        </div>

        {/* Reset Button */}
        <Button variant="ghost" size="sm" onClick={onReset}>
          <Filter className="w-4 h-4 mr-1" />
          Réinitialiser
        </Button>
      </div>
    </Card>
  );
}

// ============================================================================
// TABLE ROW COMPONENT
// ============================================================================

function SupplierRow({ supplier, rank, onClick }) {
  const config = GRADE_CONFIG[supplier.grade] || GRADE_CONFIG.C;
  const TrendIcon = supplier.trend ? TREND_ICONS[supplier.trend]?.icon : null;
  const trendColor = supplier.trend ? TREND_ICONS[supplier.trend]?.color : '';

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return '-';
    }
  };

  return (
    <motion.tr
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
      onClick={() => onClick(supplier)}
    >
      {/* Rank */}
      <td className="px-4 py-3">
        <span className="text-sm font-medium text-slate-400">#{rank}</span>
      </td>

      {/* Supplier Name */}
      <td className="px-4 py-3">
        <p className="font-medium text-white">{supplier.supplier_name}</p>
      </td>

      {/* Score */}
      <td className="px-4 py-3 text-right">
        <span className={clsx('text-lg font-bold', config.text)}>
          {(supplier.score || 0).toFixed(0)}
        </span>
      </td>

      {/* Grade */}
      <td className="px-4 py-3 text-center">
        <Badge variant={config.badgeVariant || 'default'}>{supplier.grade}</Badge>
      </td>

      {/* Trend */}
      <td className="px-4 py-3 text-center">
        {TrendIcon ? (
          <span className={clsx('flex items-center justify-center gap-1', trendColor)}>
            <TrendIcon className="w-4 h-4" />
          </span>
        ) : (
          <span className="text-slate-500">-</span>
        )}
      </td>

      {/* Last Updated */}
      <td className="px-4 py-3 text-right">
        <span className="text-sm text-slate-400">{formatDate(supplier.last_updated)}</span>
      </td>

      {/* Actions */}
      <td className="px-4 py-3 text-center">
        <Button variant="ghost" size="sm" iconOnly onClick={(e) => { e.stopPropagation(); onClick(supplier); }}>
          <Eye className="w-4 h-4" />
        </Button>
      </td>
    </motion.tr>
  );
}

// ============================================================================
// PAGINATION COMPONENT
// ============================================================================

function Pagination({ page, totalPages, totalCount, perPage, onPageChange }) {
  const start = (page - 1) * perPage + 1;
  const end = Math.min(page * perPage, totalCount);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-white/10">
      <span className="text-sm text-slate-400">
        Affichage {start} - {end} sur {totalCount} fournisseurs
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft className="w-4 h-4" />
          Précédent
        </Button>
        <span className="px-3 py-1 bg-slate-800 rounded text-sm text-white">
          Page {page} / {totalPages}
        </span>
        <Button
          variant="ghost"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Suivant
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function SuppliersListPage() {
  const navigate = useNavigate();

  // Modal state for supplier preview
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierModalOpen, setSupplierModalOpen] = useState(false);

  // Modal state for add/edit supplier
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);

  // Filters state
  const [filters, setFilters] = useState({
    page: 1,
    perPage: 20,
    search: '',
    minScore: undefined,
    gradeFilter: undefined,
    sortBy: 'score',
    sortOrder: 'desc',
  });

  // Query
  const suppliersQuery = useSuppliersPaginated({
    page: filters.page,
    perPage: filters.perPage,
    minScore: filters.minScore,
    search: filters.search,
    sortBy: filters.sortBy,
    sortOrder: filters.sortOrder,
  });

  // L'intercepteur axios désenveloppe déjà la réponse, donc data contient directement { suppliers, total_count, ... }
  const data = suppliersQuery.data || {};
  const suppliers = data.suppliers || [];
  const totalCount = data.total_count || 0;
  const totalPages = data.total_pages || Math.ceil(totalCount / filters.perPage) || 1;

  const handleSupplierClick = (supplier) => {
    // Ouvrir la modal de prévisualisation
    setSelectedSupplier({
      id: supplier.supplier_id ?? supplier.id,
      name: supplier.supplier_name,
      type: 'Fournisseur',
      score: Math.round(supplier.score || 0),
      contactName: supplier.contact_name,
      phone: supplier.phone,
      email: supplier.email,
      address: supplier.address,
      paymentTerms: supplier.payment_terms || '30 jours',
      totalPurchases: supplier.total_purchases,
      orderCount: supplier.order_count,
      deliveryDelay: supplier.avg_delivery_days,
      partnerSince: supplier.partner_since,
      products: supplier.products || [],
    });
    setSupplierModalOpen(true);
  };

  const handleViewDetails = (supplier) => {
    const id = supplier.id;
    if (id) {
      navigate(`/intelligence/scoring/suppliers/${id}`);
    }
  };

  const handleReset = () => {
    setFilters({
      page: 1,
      perPage: 20,
      search: '',
      minScore: undefined,
      gradeFilter: undefined,
      sortBy: 'score',
      sortOrder: 'desc',
    });
  };

  const handleExport = () => {
    const csvContent = [
      ['Rang', 'Fournisseur', 'Score', 'Grade', 'Tendance', 'Dernière MAJ'],
      ...suppliers.map((s, idx) => [
        idx + 1 + (filters.page - 1) * filters.perPage,
        s.supplier_name,
        (s.score || 0).toFixed(0),
        s.grade,
        s.trend || 'stable',
        s.last_updated || '-',
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `supplier-ranking-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
          <h1 className="text-2xl font-semibold text-white">Liste des Fournisseurs</h1>
          <p className="text-sm text-slate-400">
            {totalCount} fournisseur{totalCount > 1 ? 's' : ''} évalué{totalCount > 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => suppliersQuery.refetch()}
            loading={suppliersQuery.isFetching}
            iconOnly
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-1" />
            Exporter
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigate('/intelligence/scoring')}>
            Retour à l'overview
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setEditingSupplier(null);
              setAddModalOpen(true);
            }}
            className="bg-cyan-500 hover:bg-cyan-600"
          >
            <Plus className="h-4 w-4 mr-1" />
            Ajouter
          </Button>
        </div>
      </div>

      {/* Filters */}
      <FiltersPanel
        filters={filters}
        onFiltersChange={setFilters}
        onReset={handleReset}
      />

      {/* Table */}
      <Card padding="none">
        {suppliersQuery.isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        ) : suppliers.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-slate-400">Aucun fournisseur trouvé</p>
            <Button variant="ghost" size="sm" className="mt-4" onClick={handleReset}>
              Réinitialiser les filtres
            </Button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-800/50">
                  <tr className="border-b border-white/10">
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Rang
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Fournisseur
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Grade
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Tendance
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Mis à jour
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {suppliers.map((supplier, idx) => (
                    <SupplierRow
                      key={supplier.supplier_id || supplier.id || idx}
                      supplier={supplier}
                      rank={supplier.rank || idx + 1 + (filters.page - 1) * filters.perPage}
                      onClick={handleSupplierClick}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <Pagination
              page={filters.page}
              totalPages={totalPages}
              totalCount={totalCount}
              perPage={filters.perPage}
              onPageChange={(newPage) => setFilters({ ...filters, page: newPage })}
            />
          </>
        )}
      </Card>

      {/* Supplier Preview Modal */}
      <SupplierModal
        open={supplierModalOpen}
        onClose={() => setSupplierModalOpen(false)}
        supplier={selectedSupplier}
        onContact={(s) => {
          window.location.href = `mailto:${s.email || ''}`;
        }}
        onNewOrder={(s) => {
          handleViewDetails(s);
        }}
      />

      {/* Add/Edit Supplier Modal */}
      <AddSupplierModal
        open={addModalOpen}
        onClose={() => {
          setAddModalOpen(false);
          setEditingSupplier(null);
        }}
        onSuccess={() => {
          suppliersQuery.refetch();
        }}
        supplier={editingSupplier}
      />
    </div>
  );
}
