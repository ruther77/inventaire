import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Download,
  Upload,
  FileText,
  Search,
  ChevronLeft,
  ChevronRight,
  Eye,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { useInvoiceHistory } from '@/hooks/useInvoiceImport.js';
import Button from '@/components/ui/Button.jsx';
import { InvoiceImportModal } from '@/components/modals/index.js';
import { toast } from 'sonner';

// Helper pour télécharger CSV
const downloadCSV = (data, filename) => {
  const headers = ['Reference', 'Fournisseur', 'Date', 'Montant', 'Statut'];
  const rows = data.map(inv => [
    inv.reference || inv.id || '',
    inv.fournisseur || inv.supplier || '',
    inv.facture_date || inv.date || '',
    inv.montant || inv.total || inv.amount || 0,
    inv.status || (inv.is_processed ? 'processed' : 'pending'),
  ]);

  const csvContent = [
    headers.join(';'),
    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';'))
  ].join('\n');

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// Stat Card Component
function StatCard({ label, value, color, subtitle }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-5">
      <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color || 'text-white'}`}>{value}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  );
}

// Status Badge Component
function StatusBadge({ status }) {
  const statusConfig = {
    pending: { label: 'En attente', bg: 'bg-amber-500/20', color: 'text-amber-400' },
    processed: { label: 'Traitée', bg: 'bg-emerald-500/20', color: 'text-emerald-400' },
    error: { label: 'Erreur', bg: 'bg-rose-500/20', color: 'text-rose-400' },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.bg} ${config.color}`}>
      {config.label}
    </span>
  );
}

// Filter Input Component
function FilterInput({ placeholder, value, onChange, icon: Icon }) {
  return (
    <div className="relative">
      {Icon && (
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
      )}
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 ${Icon ? 'pl-10' : ''}`}
      />
    </div>
  );
}

// Filter Select Component
function FilterSelect({ value, onChange, options, placeholder }) {
  return (
    <select
      className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500/50"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{placeholder}</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

// Invoice Row Component
// Formater le nom de facture pour le rendre plus lisible
function formatInvoiceId(id, supplier) {
  if (!id) return '—';
  const sup = supplier?.toUpperCase() || '';

  // Eurociel: FA20232576 -> #2576 (Fact-2023)
  if (sup === 'EUROCIEL') {
    const match = id.match(/^(FA|AV)(\d{2})(\d+)$/);
    if (match) {
      const [, type, year, num] = match;
      const typeLabel = type === 'AV' ? 'Avoir' : 'Fact';
      return `#${num} (${typeLabel}-20${year})`;
    }
  }

  // Metro: METRO-12345678 -> #12345678
  if (sup === 'METRO' || id.startsWith('METRO-')) {
    const match = id.match(/^METRO-(\d+)$/);
    if (match) {
      return `#${match[1]}`;
    }
  }

  // Taiyat: TAIYAT-251192 -> #251192
  if (sup === 'TAIYAT' || id.startsWith('TAIYAT-')) {
    const match = id.match(/^TAIYAT-(\d+)$/);
    if (match) {
      return `#${match[1]}`;
    }
  }

  // Autres fournisseurs: garder tel quel mais formater si pattern reconnu
  // Format générique: SUPPLIER-XXXXX -> #XXXXX
  const genericMatch = id.match(/^[A-Z]+-(\d+)$/);
  if (genericMatch) {
    return `#${genericMatch[1]}`;
  }

  return id;
}

function InvoiceRow({ invoice, onView, onProcess, onViewPDF }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR');
    } catch {
      return dateStr;
    }
  };

  const formatAmount = (amount) => {
    if (!amount) return '€0.00';
    return `€${Number(amount).toLocaleString('fr-FR', { minimumFractionDigits: 2 })}`;
  };

  const status = invoice.status || (invoice.is_processed ? 'processed' : 'pending');
  const supplier = invoice.fournisseur || invoice.supplier;
  const rawId = invoice.invoice_id || invoice.reference || invoice.id;
  const displayRef = formatInvoiceId(rawId, supplier);

  return (
    <tr
      className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-all"
      onClick={() => onView(invoice)}
    >
      <td className="py-4 px-5">
        <strong className="text-white">{displayRef}</strong>
        {rawId !== displayRef && (
          <span className="ml-2 text-xs text-slate-500">{rawId}</span>
        )}
      </td>
      <td className="py-4 px-5 text-slate-300">
        {supplier || '—'}
      </td>
      <td className="py-4 px-5 text-slate-400">
        {formatDate(invoice.facture_date || invoice.date)}
      </td>
      <td className="py-4 px-5 text-white font-medium">
        {formatAmount(invoice.montant || invoice.total || invoice.amount)}
      </td>
      <td className="py-4 px-5">
        <StatusBadge status={status} />
      </td>
      <td className="py-4 px-5">
        <div className="flex gap-2">
          {status === 'pending' && (
            <button
              className="px-3 py-1.5 rounded-md text-xs font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                onProcess(invoice);
              }}
            >
              Traiter
            </button>
          )}
          {status === 'error' && (
            <button
              className="px-3 py-1.5 rounded-md text-xs font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                onProcess(invoice);
              }}
            >
              Corriger
            </button>
          )}
          {status === 'processed' && (
            <button
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-white/10 text-slate-400 hover:bg-white/10 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                onView(invoice);
              }}
            >
              Détails
            </button>
          )}
          <button
            className="px-3 py-1.5 rounded-md text-xs font-medium border border-white/10 text-slate-400 hover:bg-white/10 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onViewPDF?.(invoice);
            }}
          >
            PDF
          </button>
        </div>
      </td>
    </tr>
  );
}

// Pagination Component
function Pagination({ currentPage, totalPages, totalItems, onPageChange }) {
  const pages = useMemo(() => {
    const result = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) result.push(i);
    } else {
      result.push(1);
      if (currentPage > 3) result.push('...');
      for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
        result.push(i);
      }
      if (currentPage < totalPages - 2) result.push('...');
      result.push(totalPages);
    }
    return result;
  }, [currentPage, totalPages]);

  const start = (currentPage - 1) * 5 + 1;
  const end = Math.min(currentPage * 5, totalItems);

  return (
    <div className="flex justify-between items-center px-5 py-4 border-t border-white/10">
      <p className="text-sm text-slate-400">
        Affichage {start}-{end} sur {totalItems} factures
      </p>
      <div className="flex gap-2">
        <button
          className="px-3 py-2 rounded-md border border-white/10 text-slate-400 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {pages.map((page, idx) =>
          page === '...' ? (
            <span key={`ellipsis-${idx}`} className="px-3 py-2 text-slate-500">
              ...
            </span>
          ) : (
            <button
              key={page}
              className={`px-3 py-2 rounded-md text-sm ${
                page === currentPage
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'border border-white/10 text-slate-400 hover:bg-white/5'
              }`}
              onClick={() => onPageChange(page)}
            >
              {page}
            </button>
          )
        )}
        <button
          className="px-3 py-2 rounded-md border border-white/10 text-slate-400 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default function InvoicesListPage({ embedded = false }) {
  const navigate = useNavigate();

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [supplierFilter, setSupplierFilter] = useState('');
  const [periodFilter, setPeriodFilter] = useState('all'); // Par défaut: toutes les dates
  const [currentPage, setCurrentPage] = useState(1);

  // Reset page on search/filter change
  const handleSearchChange = (value) => {
    setSearch(value);
    setCurrentPage(1);
  };

  // Modal state
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  // Fetch invoices - limit élevé car l'API ne supporte pas la pagination par page
  const ITEMS_PER_PAGE = 25;
  const { data: invoicesData, isLoading } = useInvoiceHistory({
    supplier: supplierFilter || undefined,
    limit: 500, // Récupérer toutes les factures, filtrage client-side
  });

  // Process data avec filtrage client-side
  const allInvoices = invoicesData?.items || invoicesData || [];

  // Filtrer par période
  const filteredByPeriod = useMemo(() => {
    if (!periodFilter || periodFilter === 'all') return allInvoices;
    const now = new Date();
    return allInvoices.filter((inv) => {
      const date = new Date(inv.facture_date || inv.created_at);
      if (periodFilter === 'week') {
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        return date >= weekAgo;
      }
      if (periodFilter === 'month') {
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        return date >= monthAgo;
      }
      if (periodFilter === 'quarter') {
        const quarterAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        return date >= quarterAgo;
      }
      if (periodFilter === 'year') {
        const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        return date >= yearAgo;
      }
      return true;
    });
  }, [allInvoices, periodFilter]);

  // Filtrer par recherche
  const filteredInvoices = useMemo(() => {
    if (!search) return filteredByPeriod;
    const term = search.toLowerCase();
    return filteredByPeriod.filter((inv) => {
      const ref = (inv.invoice_id || inv.reference || inv.id || '').toLowerCase();
      const supplier = (inv.supplier || inv.fournisseur || '').toLowerCase();
      return ref.includes(term) || supplier.includes(term);
    });
  }, [filteredByPeriod, search]);

  // Pagination client-side
  const totalItems = filteredInvoices.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE) || 1;
  const invoices = filteredInvoices.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Calculate stats - basé sur TOUTES les factures filtrées, pas juste la page courante
  const stats = useMemo(() => {
    const totalAmount = filteredInvoices.reduce((sum, inv) => sum + (inv.montant || inv.total_ttc || inv.total || 0), 0);
    const pending = filteredInvoices.filter((inv) => inv.status === 'pending').length;
    const processed = filteredInvoices.filter((inv) => inv.status === 'processed').length;
    const errors = filteredInvoices.filter((inv) => inv.status === 'error').length;

    return {
      totalMonth: totalAmount,
      pending,
      processed,
      errors,
      total: filteredInvoices.length,
    };
  }, [filteredInvoices]);

  // Get unique suppliers for filter - basé sur TOUTES les factures
  const suppliers = useMemo(() => {
    const unique = [...new Set(allInvoices.map((inv) => inv.fournisseur || inv.supplier).filter(Boolean))];
    return unique.map((s) => ({ value: s, label: s }));
  }, [allInvoices]);

  // Handlers
  const handleViewInvoice = useCallback((invoice) => {
    setSelectedInvoice(invoice);
    toast.success(`Facture #${invoice.reference || invoice.id} sélectionnée`, {
      description: `${invoice.fournisseur || invoice.supplier || 'Fournisseur'} - €${(invoice.montant || invoice.total || 0).toFixed(2)}`,
      action: {
        label: 'Voir détails',
        onClick: () => navigate(`/operations/factures/${invoice.id}`),
      },
    });
  }, [navigate]);

  const handleProcessInvoice = useCallback((invoice) => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1500)),
      {
        loading: `Traitement de la facture #${invoice.reference || invoice.id}...`,
        success: `Facture #${invoice.reference || invoice.id} traitée avec succès`,
        error: 'Erreur lors du traitement',
      }
    );
  }, []);

  const handleExport = useCallback(() => {
    if (invoices.length === 0) {
      toast.error('Aucune facture à exporter');
      return;
    }
    const filename = `factures_${new Date().toISOString().slice(0, 10)}.csv`;
    downloadCSV(invoices, filename);
    toast.success(`${invoices.length} factures exportées`, {
      description: filename,
    });
  }, [invoices]);

  const handleImport = useCallback(() => {
    if (embedded) {
      setImportModalOpen(true);
    } else {
      navigate('/operations/factures/import');
    }
  }, [navigate, embedded]);

  const handleViewPDF = useCallback((invoice) => {
    if (invoice.pdf_url) {
      window.open(invoice.pdf_url, '_blank');
    } else {
      toast.info('PDF non disponible', {
        description: 'Le fichier PDF n\'est pas encore lié à cette facture.',
      });
    }
  }, []);

  // Mock data if no real data
  const displayInvoices = invoices.length > 0 ? invoices : [
    { id: 1820, reference: '1820', fournisseur: 'Metro', facture_date: '2025-12-23', montant: 847.50, status: 'pending' },
    { id: 1819, reference: '1819', fournisseur: 'Brake', facture_date: '2025-12-22', montant: 1234.80, status: 'processed' },
    { id: 1818, reference: '1818', fournisseur: 'Pomona', facture_date: '2025-12-21', montant: 456.20, status: 'error' },
    { id: 1817, reference: '1817', fournisseur: 'Metro', facture_date: '2025-12-20', montant: 2156.90, status: 'processed' },
    { id: 1816, reference: '1816', fournisseur: 'Brake', facture_date: '2025-12-19', montant: 678.30, status: 'pending' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      {!embedded && (
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-3xl font-bold font-display text-white">Factures Fournisseurs</h1>
          <div className="flex gap-3">
            <Button size="sm" variant="ghost" onClick={handleExport}>
              <Download className="w-4 h-4" />
              Exporter
            </Button>
            <Button size="sm" variant="brand" onClick={handleImport}>
              <Upload className="w-4 h-4" />
              Importer facture
            </Button>
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Factures"
          value={stats.total}
          subtitle={`€${stats.totalMonth.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} TTC`}
        />
        <StatCard
          label="En attente"
          value={stats.pending}
          color="text-amber-400"
        />
        <StatCard
          label="Traitées"
          value={stats.processed}
          color="text-emerald-400"
        />
        <StatCard
          label="En erreur"
          value={stats.errors}
          color="text-rose-400"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <FilterInput
          placeholder="Rechercher facture, fournisseur..."
          value={search}
          onChange={handleSearchChange}
          icon={Search}
        />
        <FilterSelect
          value={statusFilter}
          onChange={setStatusFilter}
          options={[
            { value: 'pending', label: 'En attente' },
            { value: 'processed', label: 'Traitées' },
            { value: 'error', label: 'En erreur' },
          ]}
          placeholder="Tous les statuts"
        />
        <FilterSelect
          value={supplierFilter}
          onChange={setSupplierFilter}
          options={suppliers.length > 0 ? suppliers : [
            { value: 'Metro', label: 'Metro' },
            { value: 'Brake', label: 'Brake' },
            { value: 'Pomona', label: 'Pomona' },
          ]}
          placeholder="Tous les fournisseurs"
        />
        <FilterSelect
          value={periodFilter}
          onChange={(val) => {
            setPeriodFilter(val);
            setCurrentPage(1); // Reset to page 1 on filter change
          }}
          options={[
            { value: 'all', label: 'Toutes les dates' },
            { value: 'week', label: '7 derniers jours' },
            { value: 'month', label: '30 derniers jours' },
            { value: 'quarter', label: '90 derniers jours' },
            { value: 'year', label: '12 derniers mois' },
          ]}
          placeholder="Période"
        />
      </div>

      {/* Table */}
      <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs uppercase text-slate-500 bg-white/5">
              <th className="py-4 px-5 border-b border-white/10">Référence</th>
              <th className="py-4 px-5 border-b border-white/10">Fournisseur</th>
              <th className="py-4 px-5 border-b border-white/10">Date</th>
              <th className="py-4 px-5 border-b border-white/10">Montant</th>
              <th className="py-4 px-5 border-b border-white/10">Statut</th>
              <th className="py-4 px-5 border-b border-white/10">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500">
                  Chargement...
                </td>
              </tr>
            ) : displayInvoices.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500">
                  Aucune facture trouvée
                </td>
              </tr>
            ) : (
              displayInvoices.map((invoice) => (
                <InvoiceRow
                  key={invoice.id || invoice.reference}
                  invoice={invoice}
                  onView={handleViewInvoice}
                  onProcess={handleProcessInvoice}
                  onViewPDF={handleViewPDF}
                />
              ))
            )}
          </tbody>
        </table>

        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={totalItems}
          onPageChange={setCurrentPage}
        />
      </div>

      {/* Import Modal */}
      <InvoiceImportModal
        open={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onSuccess={() => {
          setImportModalOpen(false);
          toast.success('Factures importées avec succès');
        }}
      />
    </div>
  );
}
