import { useEffect, useMemo, useState } from 'react';
import { Download, RefreshCw, ShieldCheck, Trash2, RotateCw, AlertTriangle } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import MetricCard from '../../components/ui/MetricCard.jsx';
import api from '../../api/client.js';
import {
  useAdminOverview,
  useAdminUsers,
  useCreateBackup,
  useDeleteBackup,
  useIntegrityReport,
  useResetUserPassword,
  useRestoreBackup,
  useSaveBackupSettings,
  useUpdateUserRole,
} from '../../hooks/useAdmin.js';

const frequencyLabels = {
  manual: 'Manuel',
  daily: 'Quotidien',
  weekly: 'Hebdomadaire',
};

const weekdays = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

export default function AdminPage() {
  const overviewQuery = useAdminOverview();
  const usersQuery = useAdminUsers();

  const createBackup = useCreateBackup();
  const restoreBackup = useRestoreBackup();
  const deleteBackup = useDeleteBackup();
  const saveSettings = useSaveBackupSettings();
  const updateRole = useUpdateUserRole();
  const resetPassword = useResetUserPassword();
  const integrityMutation = useIntegrityReport();

  const [backupLabel, setBackupLabel] = useState('');
  const [settingsForm, setSettingsForm] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState('');
  const [passwordUser, setPasswordUser] = useState(null);
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [integrityReport, setIntegrityReport] = useState([]);

  const overview = overviewQuery.data;
  const backups = overview?.backups?.recent ?? [];
  const backupSummary = overview?.backups?.summary;
  const tableCounts = overview?.table_counts ?? [];
  const diagnostics = overview?.diagnostics ?? [];
  const recentMovements = overview?.recent_movements ?? [];
  const backupSettings = overview?.backups?.settings ?? null;
  const toolStatus = overview?.backups?.tool_status ?? [];
  const cleanupList = overview?.backups?.suggested_cleanup ?? [];

  useEffect(() => {
    if (backupSettings) {
      setSettingsForm(backupSettings);
    }
  }, [backupSettings]);

  useEffect(() => {
    if (usersQuery.data?.users?.length && selectedUser === null) {
      setSelectedUser(usersQuery.data.users[0]?.id ?? null);
      setPasswordUser(usersQuery.data.users[0]?.id ?? null);
      setSelectedRole(usersQuery.data.users[0]?.role ?? '');
    }
  }, [usersQuery.data, selectedUser]);

  const handleCreateBackup = () => {
    createBackup.mutate(
      { label: backupLabel || undefined },
      {
        onSuccess: () => setBackupLabel(''),
      },
    );
  };

  const handleRestore = (name) => {
    if (!name) return;
    if (!window.confirm(`Restaurer ${name} ? Cette opération est irréversible.`)) return;
    restoreBackup.mutate(name);
  };

  const handleDelete = (name) => {
    if (!name) return;
    if (!window.confirm(`Supprimer définitivement ${name} ?`)) return;
    deleteBackup.mutate(name);
  };

  const handleSettingsSubmit = (event) => {
    event.preventDefault();
    if (!settingsForm) return;
    saveSettings.mutate(settingsForm, {
      onSuccess: () => overviewQuery.refetch(),
    });
  };

  const handleRoleSubmit = (event) => {
    event.preventDefault();
    if (!selectedUser || !selectedRole) return;
    updateRole.mutate(
      { userId: selectedUser, role: selectedRole },
      { onSuccess: () => usersQuery.refetch() },
    );
  };

  const handlePasswordReset = async (event) => {
    event.preventDefault();
    if (!passwordUser) return;
    try {
      const result = await resetPassword.mutateAsync({ userId: passwordUser });
      setGeneratedPassword(result?.password ?? '');
    } catch {
      setGeneratedPassword('');
    }
  };

  const handleIntegrity = async () => {
    try {
      const report = await integrityMutation.mutateAsync();
      setIntegrityReport(report ?? []);
    } catch {
      setIntegrityReport([]);
    }
  };

  const baseDownloadUrl = api.defaults.baseURL ?? '';

  const backupMetrics = useMemo(
    () => [
      {
        label: 'Backups suivis',
        value: backupSummary?.count?.toLocaleString('fr-FR') ?? '0',
        hint: 'Total fichiers',
      },
      {
        label: 'Prochaine exécution',
        value: backupSummary?.next_run
          ? new Date(backupSummary.next_run).toLocaleString('fr-FR')
          : 'Non planifiée',
        hint: backupSettings ? frequencyLabels[backupSettings.frequency] : '—',
      },
      {
        label: 'Volume cumulé',
        value: `${backupSummary?.stats?.total_size_mb?.toFixed(1) ?? '0.0'} Mo`,
        hint: `${backupSummary?.stats?.average_size_mb?.toFixed(1) ?? '0.0'} Mo / backup`,
      },
    ],
    [backupSummary, backupSettings],
  );

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">admin & outils</p>
            <h1 className="text-2xl font-semibold text-slate-900">Sauvegardes, diagnostics, rôles</h1>
            <p className="text-sm text-slate-500">
              Cette page remplace les panneaux Streamlit historiques : déclenchez les sauvegardes,
              surveillez l&apos;intégrité des tables et pilotez les comptes applicatifs.
            </p>
          </div>
          <Button
            variant="ghost"
            iconOnly
            aria-label="Actualiser la vue"
            onClick={() => overviewQuery.refetch()}
          >
            <RefreshCw className={overviewQuery.isFetching ? 'animate-spin' : ''} />
          </Button>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {backupMetrics.map((metric) => (
          <MetricCard key={metric.label} label={metric.label} value={metric.value} hint={metric.hint} />
        ))}
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">plan de reprise</p>
            <h3 className="text-lg font-semibold text-slate-900">Gouvernance des sauvegardes</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              type="text"
              value={backupLabel}
              onChange={(event) => setBackupLabel(event.target.value)}
              placeholder="Étiquette optionnelle"
              className="rounded-2xl border border-slate-200 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
            />
            <Button onClick={handleCreateBackup} disabled={createBackup.isLoading}>
              <ShieldCheck className="h-4 w-4" />
              Sauvegarder maintenant
            </Button>
            <Button variant="ghost" onClick={handleIntegrity} disabled={integrityMutation.isLoading}>
              <RotateCw className="h-4 w-4" />
              Vérifier intégrité
            </Button>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">outils système</p>
            <ul className="mt-2 space-y-2">
              {toolStatus.map((status) => (
                <li
                  key={status.name}
                  className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{status.name}</p>
                    <p className="text-xs text-slate-500">
                      Résolu via {status.source} — {status.resolved ?? 'non trouvé'}
                    </p>
                  </div>
                  <span
                    className={`text-sm font-semibold ${
                      status.available ? 'text-emerald-600' : 'text-rose-600'
                    }`}
                  >
                    {status.available ? 'OK' : 'Manquant'}
                  </span>
                </li>
              ))}
              {!toolStatus.length && <p className="text-sm text-slate-500">En attente de diagnostic.</p>}
            </ul>
          </div>

          <div>
            <form className="space-y-3" onSubmit={handleSettingsSubmit}>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">planification</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1 text-sm text-slate-600">
                  Fréquence
                  <select
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                    value={settingsForm?.frequency ?? 'manual'}
                    onChange={(event) =>
                      setSettingsForm((prev) => ({ ...prev, frequency: event.target.value }))
                    }
                  >
                    {Object.entries(frequencyLabels).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-1 text-sm text-slate-600">
                  Heure
                  <input
                    type="time"
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                    value={settingsForm?.time ?? '02:00'}
                    onChange={(event) =>
                      setSettingsForm((prev) => ({ ...prev, time: event.target.value }))
                    }
                  />
                </label>
              </div>
              {settingsForm?.frequency === 'weekly' && (
                <label className="flex flex-col gap-1 text-sm text-slate-600">
                  Jour
                  <select
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                    value={settingsForm?.weekday ?? 0}
                    onChange={(event) =>
                      setSettingsForm((prev) => ({ ...prev, weekday: Number(event.target.value) }))
                    }
                  >
                    {weekdays.map((day, index) => (
                      <option key={day} value={index}>
                        {day}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1 text-sm text-slate-600">
                  Rétention (jours)
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={settingsForm?.retention_days ?? 30}
                    onChange={(event) =>
                      setSettingsForm((prev) => ({
                        ...prev,
                        retention_days: Number(event.target.value),
                      }))
                    }
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </label>
                <label className="flex flex-col gap-1 text-sm text-slate-600">
                  Backups max
                  <input
                    type="number"
                    min="1"
                    max="500"
                    value={settingsForm?.max_backups ?? 20}
                    onChange={(event) =>
                      setSettingsForm((prev) => ({
                        ...prev,
                        max_backups: Number(event.target.value),
                      }))
                    }
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </label>
              </div>
              <Button type="submit" disabled={saveSettings.isLoading}>
                Sauvegarder la planification
              </Button>
            </form>
          </div>
        </div>

        {cleanupList.length > 0 && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            <p className="font-semibold">Rétention à épurer</p>
            <p className="text-amber-800">
              {cleanupList.length} fichier(s) dépassent la politique : {cleanupList.join(', ')}.
            </p>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                <th className="px-3 py-2">Sauvegarde</th>
                <th className="px-3 py-2">Créée le</th>
                <th className="px-3 py-2">Taille</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {backups.map((backup) => (
                <tr key={backup.name}>
                  <td className="px-3 py-2 font-medium text-slate-900">{backup.name}</td>
                  <td className="px-3 py-2 text-slate-500">
                    {new Date(backup.created_at).toLocaleString('fr-FR')}
                  </td>
                  <td className="px-3 py-2 text-slate-500">
                    {(backup.size_bytes / 1024 / 1024).toFixed(2)} Mo
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        as="a"
                        variant="ghost"
                        size="sm"
                        href={`${baseDownloadUrl}/maintenance/backups/${encodeURIComponent(backup.name)}`}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRestore(backup.name)}
                      >
                        <ShieldCheck className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(backup.name)}>
                        <Trash2 className="h-4 w-4 text-rose-500" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {!backups.length && (
                <tr>
                  <td colSpan={4} className="px-3 py-2 text-sm text-slate-500">
                    Aucune sauvegarde détectée.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {integrityReport.length > 0 && (
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">rapport intégrité</p>
            <div className="mt-2 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Sauvegarde</th>
                    <th className="px-3 py-2">Statut</th>
                    <th className="px-3 py-2">Détails</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {integrityReport.map((row) => (
                    <tr key={row.name}>
                      <td className="px-3 py-2 text-slate-900">{row.name}</td>
                      <td className="px-3 py-2">{row.status}</td>
                      <td className="px-3 py-2 text-slate-500">{row.details}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">structure bdd</p>
            <h3 className="text-lg font-semibold text-slate-900">Diagnostics tables</h3>
          </div>
          <div className="flex flex-wrap gap-3">
            {tableCounts.map((row) => (
              <div
                key={row.table}
                className="flex flex-col rounded-2xl border border-slate-100 px-4 py-3"
              >
                <span className="text-xs uppercase tracking-[0.3em] text-slate-400">{row.table}</span>
                <span className="text-lg font-semibold text-slate-900">
                  {Number(row.lignes).toLocaleString('fr-FR')}
                </span>
              </div>
            ))}
            {!tableCounts.length && (
              <p className="text-sm text-slate-500">Statistiques indisponibles.</p>
            )}
          </div>
          <div className="rounded-2xl border border-slate-100">
            <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3 text-sm font-semibold text-slate-900">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Écarts stock / mouvements
            </div>
            <div className="max-h-72 overflow-auto">
              <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Produit</th>
                    <th className="px-3 py-2">Stock</th>
                    <th className="px-3 py-2">Calculé</th>
                    <th className="px-3 py-2">Écart</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {diagnostics.map((row) => (
                    <tr key={row.id}>
                      <td className="px-3 py-2 text-slate-900">{row.nom}</td>
                      <td className="px-3 py-2 text-slate-500">{row.stock_actuel}</td>
                      <td className="px-3 py-2 text-slate-500">{row.stock_calcule}</td>
                      <td className="px-3 py-2 font-semibold text-rose-600">{row.ecart}</td>
                    </tr>
                  ))}
                  {!diagnostics.length && (
                    <tr>
                      <td className="px-3 py-2 text-sm text-slate-500" colSpan={4}>
                        Aucun écart détecté.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </Card>

        <Card className="flex flex-col gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">flux récents</p>
            <h3 className="text-lg font-semibold text-slate-900">20 derniers mouvements</h3>
          </div>
          <div className="max-h-96 overflow-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Produit</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Quantité</th>
                  <th className="px-3 py-2">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {recentMovements.map((row, index) => (
                  <tr key={`${row.produit}-${index}`}>
                    <td className="px-3 py-2 text-slate-500">
                      {new Date(row.date_mvt).toLocaleString('fr-FR')}
                    </td>
                    <td className="px-3 py-2 text-slate-900">{row.produit}</td>
                    <td className="px-3 py-2">{row.type}</td>
                    <td className="px-3 py-2">{row.quantite}</td>
                    <td className="px-3 py-2 text-slate-500">{row.source ?? '—'}</td>
                  </tr>
                ))}
                {!recentMovements.length && (
                  <tr>
                    <td className="px-3 py-2 text-sm text-slate-500" colSpan={5}>
                      Aucun mouvement enregistré.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">comptes applicatifs</p>
            <h3 className="text-lg font-semibold text-slate-900">Gestion des rôles</h3>
          </div>
          <Button variant="ghost" onClick={() => usersQuery.refetch()}>
            <RefreshCw className={usersQuery.isFetching ? 'animate-spin' : 'h-4 w-4'} />
            Actualiser
          </Button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                <th className="px-3 py-2">Utilisateur</th>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Rôle</th>
                <th className="px-3 py-2">Créé le</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {(usersQuery.data?.users ?? []).map((user) => (
                <tr key={user.id}>
                  <td className="px-3 py-2 text-slate-900">{user.username}</td>
                  <td className="px-3 py-2 text-slate-500">{user.email}</td>
                  <td className="px-3 py-2">{user.role}</td>
                  <td className="px-3 py-2 text-slate-500">
                    {new Date(user.created_at).toLocaleDateString('fr-FR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <form className="space-y-3 rounded-2xl border border-slate-100 p-4" onSubmit={handleRoleSubmit}>
            <p className="text-sm font-semibold text-slate-900">Mettre à jour un rôle</p>
            <select
              className="w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm"
              value={selectedUser ?? ''}
              onChange={(event) => {
                const userId = Number(event.target.value);
                setSelectedUser(userId);
                const user = usersQuery.data?.users?.find((u) => u.id === userId);
                setSelectedRole(user?.role ?? '');
              }}
            >
              {(usersQuery.data?.users ?? []).map((user) => (
                <option key={user.id} value={user.id}>
                  {user.username} — {user.email}
                </option>
              ))}
            </select>
            <select
              className="w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm"
              value={selectedRole}
              onChange={(event) => setSelectedRole(event.target.value)}
            >
              {(usersQuery.data?.roles ?? ['admin', 'manager', 'standard']).map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
            <Button type="submit" disabled={updateRole.isLoading}>
              Mettre à jour
            </Button>
          </form>

          <form
            className="space-y-3 rounded-2xl border border-slate-100 p-4"
            onSubmit={handlePasswordReset}
          >
            <p className="text-sm font-semibold text-slate-900">Réinitialiser un mot de passe</p>
            <select
              className="w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm"
              value={passwordUser ?? ''}
              onChange={(event) => setPasswordUser(Number(event.target.value))}
            >
              {(usersQuery.data?.users ?? []).map((user) => (
                <option key={user.id} value={user.id}>
                  {user.username} — {user.email}
                </option>
              ))}
            </select>
            <Button type="submit" disabled={resetPassword.isLoading}>
              Générer un nouveau mot de passe
            </Button>
            {generatedPassword && (
              <div className="rounded-2xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                Nouveau mot de passe : <code className="font-semibold">{generatedPassword}</code>
              </div>
            )}
          </form>
        </div>
      </Card>
    </div>
  );
}
