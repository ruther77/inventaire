import { useMemo, useState } from 'react';
import { Download } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useBackups } from '../../hooks/useMaintenance.js';
import api from '../../api/client.js';

const sizeFormatter = (size) => {
  if (size === 0) return '0 o';
  const units = ['o', 'Ko', 'Mo', 'Go', 'To'];
  const index = Math.floor(Math.log(size) / Math.log(1024));
  const normalized = size / 1024 ** index;
  return `${normalized.toFixed(1)} ${units[index]}`;
};

export default function MaintenancePage() {
  const [limit, setLimit] = useState(50);
  const backupsQuery = useBackups(limit);

  const lastBackup = useMemo(() => {
    const entries = backupsQuery.data ?? [];
    return entries.length ? entries[0] : null;
  }, [backupsQuery.data]);

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-3">
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400">maintenance</p>
        <h2 className="text-2xl font-semibold text-slate-900">Sauvegardes & reprise</h2>
        <p className="text-sm text-slate-500">
          Surveillez les exports PostgreSQL générés automatiquement et téléchargez-les en cas de besoin.
        </p>
      </Card>

      <Card className="grid gap-4 md:grid-cols-3">
        <Metric label="Dernier backup" value={lastBackup ? new Date(lastBackup.created_at).toLocaleString('fr-FR') : '—'} />
        <Metric label="Taille" value={lastBackup ? sizeFormatter(lastBackup.size_bytes) : '—'} />
        <Metric label="Backups suivis" value={backupsQuery.data?.length ?? 0} />
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-slate-900">Historique des sauvegardes</h3>
          <select
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
            className="rounded-2xl border border-slate-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
          >
            {[25, 50, 100, 200].map((value) => (
              <option key={value} value={value}>
                {value} entrées
              </option>
            ))}
          </select>
        </div>
        {backupsQuery.isLoading ? (
          <p className="text-sm text-slate-500">Chargement…</p>
        ) : (backupsQuery.data ?? []).length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                  <th className="px-3 py-2">Nom</th>
                  <th className="px-3 py-2">Créé le</th>
                  <th className="px-3 py-2">Taille</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {backupsQuery.data.map((backup) => (
                  <tr key={backup.name}>
                    <td className="px-3 py-2 text-slate-900">{backup.name}</td>
                    <td className="px-3 py-2 text-slate-600">
                      {new Date(backup.created_at).toLocaleString('fr-FR')}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{sizeFormatter(backup.size_bytes)}</td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        as="a"
                        href={`${api.defaults.baseURL ?? ''}/maintenance/backups/${encodeURIComponent(backup.name)}`}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Aucune sauvegarde détectée dans /backups.</p>
        )}
      </Card>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
