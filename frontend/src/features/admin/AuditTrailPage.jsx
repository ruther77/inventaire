import React, { useState, useMemo } from 'react';
import { History, Search, Filter, Download, Shield, User, AlertTriangle, RefreshCw, Eye } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import DataTable from '../../components/ui/DataTable.jsx';
import Modal from '../../components/ui/Modal.jsx';
import { useAuditTrail, useGenerateAuditReport } from '../../hooks/useAuditTrail.js';

const Stat = ({ label, value, hint, icon: Icon, accent = 'text-slate-900' }) => (
  <div className="rounded-2xl border border-slate-200 bg-white p-4 transition-all hover:shadow-md">
    <div className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-[0.3em]">
      {Icon && <Icon className="w-4 h-4" />} {label}
    </div>
    <p className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
  </div>
);

const SeverityBadge = ({ severity }) => {
  const styles = {
    debug: 'bg-slate-100 text-slate-600',
    info: 'bg-blue-100 text-blue-700',
    warning: 'bg-amber-100 text-amber-700',
    error: 'bg-rose-100 text-rose-700',
    critical: 'bg-red-200 text-red-800',
    security: 'bg-purple-100 text-purple-700',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${styles[severity] || styles.info}`}>
      {severity}
    </span>
  );
};

const ActionBadge = ({ action }) => {
  const styles = {
    create: 'bg-emerald-100 text-emerald-700',
    update: 'bg-blue-100 text-blue-700',
    delete: 'bg-rose-100 text-rose-700',
    login: 'bg-purple-100 text-purple-700',
    logout: 'bg-slate-100 text-slate-600',
    login_failed: 'bg-red-100 text-red-700',
    import: 'bg-cyan-100 text-cyan-700',
    export: 'bg-teal-100 text-teal-700',
  };
  const labels = {
    create: 'Création',
    update: 'Modification',
    delete: 'Suppression',
    login: 'Connexion',
    logout: 'Déconnexion',
    login_failed: 'Échec connexion',
    import: 'Import',
    export: 'Export',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${styles[action] || 'bg-slate-100 text-slate-600'}`}>
      {labels[action] || action}
    </span>
  );
};

export default function AuditTrailPage() {
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [filters, setFilters] = useState({
    action: '',
    entity: '',
    severity: '',
    search: '',
    startDate: '',
    endDate: '',
    limit: 100,
  });

  const {
    summary,
    entries,
    securityEvents,
    isLoading,
    generateReport,
    refetchAll,
  } = useAuditTrail(filters);

  const entriesData = entries.data || [];
  const summaryData = summary.data || {};
  const securityEventsData = securityEvents.data || [];

  const handleExportReport = () => {
    const today = new Date().toISOString().split('T')[0];
    const startDate = filters.startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    generateReport.mutate(
      { startDate, endDate: today },
      {
        onSuccess: (report) => {
          const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `audit_report_${today}.json`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        },
      }
    );
  };

  const columns = useMemo(() => [
    {
      key: 'timestamp',
      header: 'Date/Heure',
      sortable: true,
      render: (value) => {
        if (!value) return '—';
        const date = new Date(value);
        return (
          <div className="text-sm">
            <div className="font-medium">{date.toLocaleDateString('fr-FR')}</div>
            <div className="text-slate-500">{date.toLocaleTimeString('fr-FR')}</div>
          </div>
        );
      },
    },
    {
      key: 'action',
      header: 'Action',
      sortable: true,
      render: (value) => <ActionBadge action={value} />,
    },
    {
      key: 'entity',
      header: 'Entité',
      sortable: true,
      render: (value, row) => (
        <div className="text-sm">
          <div className="font-medium capitalize">{value}</div>
          {row.entity_id && <div className="text-slate-500">#{row.entity_id}</div>}
        </div>
      ),
    },
    {
      key: 'username',
      header: 'Utilisateur',
      sortable: true,
      render: (value) => (
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-slate-400" />
          <span className="text-sm">{value || 'Système'}</span>
        </div>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (value) => (
        <span className="text-sm text-slate-600 truncate max-w-xs block">{value || '—'}</span>
      ),
    },
    {
      key: 'severity',
      header: 'Niveau',
      sortable: true,
      render: (value) => <SeverityBadge severity={value} />,
    },
    {
      key: 'actions',
      header: '',
      render: (_, row) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setSelectedEntry(row);
            setDetailModalOpen(true);
          }}
        >
          <Eye className="w-4 h-4" />
        </Button>
      ),
    },
  ], []);

  const actionOptions = [
    { value: '', label: 'Toutes les actions' },
    { value: 'create', label: 'Création' },
    { value: 'update', label: 'Modification' },
    { value: 'delete', label: 'Suppression' },
    { value: 'login', label: 'Connexion' },
    { value: 'import', label: 'Import' },
  ];

  const entityOptions = [
    { value: '', label: 'Toutes les entités' },
    { value: 'product', label: 'Produit' },
    { value: 'invoice', label: 'Facture' },
    { value: 'transaction', label: 'Transaction' },
    { value: 'user', label: 'Utilisateur' },
    { value: 'price', label: 'Prix' },
  ];

  const severityOptions = [
    { value: '', label: 'Tous les niveaux' },
    { value: 'info', label: 'Info' },
    { value: 'warning', label: 'Warning' },
    { value: 'error', label: 'Erreur' },
    { value: 'security', label: 'Sécurité' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Administration</p>
          <h1 className="text-2xl font-semibold text-slate-900">Audit Trail</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={refetchAll} loading={isLoading}>
            <RefreshCw className="h-4 w-4" />
            Actualiser
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportReport}>
            <Download className="h-4 w-4" />
            Exporter
          </Button>
        </div>
      </header>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat
          label="Total Entrées"
          value={summaryData?.total_entries || entriesData.length}
          hint="Période sélectionnée"
          icon={History}
        />
        <Stat
          label="Utilisateurs Actifs"
          value={summaryData?.active_users || Object.keys(summaryData?.users_activity || {}).length}
          hint="7 derniers jours"
          icon={User}
        />
        <Stat
          label="Événements Sécurité"
          value={summaryData?.security_events || securityEventsData.length}
          hint="À surveiller"
          icon={Shield}
          accent={securityEventsData.length > 0 ? 'text-amber-600' : 'text-emerald-600'}
        />
        <Stat
          label="Échecs Connexion"
          value={summaryData?.failed_logins || 0}
          hint="7 derniers jours"
          icon={AlertTriangle}
          accent={summaryData?.failed_logins > 5 ? 'text-rose-600' : 'text-slate-900'}
        />
      </div>

      {/* Événements de sécurité récents */}
      {securityEventsData.length > 0 && (
        <Card className="border-amber-200 bg-amber-50">
          <div className="flex items-start gap-3 p-4">
            <Shield className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-900">Événements de sécurité récents</h3>
              <ul className="mt-2 space-y-1">
                {securityEventsData.slice(0, 5).map((event, i) => (
                  <li key={i} className="text-sm text-amber-800">
                    {event.description || event.action} — {event.username || 'Anonyme'} ({new Date(event.timestamp).toLocaleString('fr-FR')})
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}

      {/* Filtres */}
      <Card>
        <div className="flex flex-wrap items-center gap-4 p-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
          </div>

          <select
            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5"
            value={filters.action}
            onChange={(e) => setFilters((f) => ({ ...f, action: e.target.value }))}
          >
            {actionOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5"
            value={filters.entity}
            onChange={(e) => setFilters((f) => ({ ...f, entity: e.target.value }))}
          >
            {entityOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5"
            value={filters.severity}
            onChange={(e) => setFilters((f) => ({ ...f, severity: e.target.value }))}
          >
            {severityOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <div className="flex items-center gap-2">
            <input
              type="date"
              className="text-sm border border-slate-200 rounded-lg px-3 py-1.5"
              value={filters.startDate}
              onChange={(e) => setFilters((f) => ({ ...f, startDate: e.target.value }))}
            />
            <span className="text-slate-400">→</span>
            <input
              type="date"
              className="text-sm border border-slate-200 rounded-lg px-3 py-1.5"
              value={filters.endDate}
              onChange={(e) => setFilters((f) => ({ ...f, endDate: e.target.value }))}
            />
          </div>

          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Rechercher..."
                className="w-full text-sm border border-slate-200 rounded-lg pl-9 pr-3 py-1.5"
                value={filters.search}
                onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card padding="none">
        <DataTable
          data={entriesData}
          columns={columns}
          loading={isLoading}
          sortable
          pagination
          pageSize={25}
          pageSizeOptions={[25, 50, 100]}
          emptyMessage="Aucune entrée d'audit trouvée"
          getRowId={(row) => row.id}
        />
      </Card>

      {/* Modal détail */}
      <Modal
        isOpen={detailModalOpen}
        onClose={() => {
          setDetailModalOpen(false);
          setSelectedEntry(null);
        }}
        title="Détail de l'entrée d'audit"
        size="lg"
      >
        {selectedEntry && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">Action</p>
                <ActionBadge action={selectedEntry.action} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">Niveau</p>
                <SeverityBadge severity={selectedEntry.severity} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">Entité</p>
                <p className="font-medium capitalize">{selectedEntry.entity} #{selectedEntry.entity_id}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">Date/Heure</p>
                <p className="font-medium">{new Date(selectedEntry.timestamp).toLocaleString('fr-FR')}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">Utilisateur</p>
                <p className="font-medium">{selectedEntry.username || 'Système'}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">IP</p>
                <p className="font-mono text-sm">{selectedEntry.ip_address || '—'}</p>
              </div>
            </div>

            {selectedEntry.description && (
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500 mb-1">Description</p>
                <p className="text-sm bg-slate-50 rounded-lg p-3">{selectedEntry.description}</p>
              </div>
            )}

            {selectedEntry.diff && selectedEntry.diff.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">Modifications</p>
                <div className="bg-slate-50 rounded-lg p-3 space-y-2">
                  {selectedEntry.diff.map((d, i) => (
                    <div key={i} className="text-sm">
                      <span className="font-medium text-slate-700">{d.field}:</span>
                      <span className="text-rose-600 line-through ml-2">{JSON.stringify(d.old_value)}</span>
                      <span className="text-slate-400 mx-2">→</span>
                      <span className="text-emerald-600">{JSON.stringify(d.new_value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(selectedEntry.before_state || selectedEntry.after_state) && (
              <div className="grid grid-cols-2 gap-4">
                {selectedEntry.before_state && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500 mb-1">État avant</p>
                    <pre className="text-xs bg-rose-50 text-rose-800 rounded-lg p-3 overflow-auto max-h-40">
                      {JSON.stringify(selectedEntry.before_state, null, 2)}
                    </pre>
                  </div>
                )}
                {selectedEntry.after_state && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500 mb-1">État après</p>
                    <pre className="text-xs bg-emerald-50 text-emerald-800 rounded-lg p-3 overflow-auto max-h-40">
                      {JSON.stringify(selectedEntry.after_state, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
