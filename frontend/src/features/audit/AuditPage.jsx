import { useEffect, useMemo, useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import {
  useAuditDiagnostics,
  useAuditActions,
  useAuditResolutions,
  useCreateAuditAssignment,
  useUpdateAuditStatus,
} from '../../hooks/useAudit.js';

const severityOptions = ['Critique', 'Modéré', 'Mineur'];

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

export default function AuditPage() {
  const [filters, setFilters] = useState({
    categories: [],
    levels: severityOptions,
    minAbs: 0,
    maxAbs: 10,
  });
  const [categoriesInitialized, setCategoriesInitialized] = useState(false);

  const diagnosticsQuery = useAuditDiagnostics({
    categories: filters.categories,
    levels: filters.levels,
    minAbs: filters.minAbs,
    maxAbs: filters.maxAbs,
  });
  const actionsQuery = useAuditActions(false);
  const resolutionsQuery = useAuditResolutions();
  const createAssignment = useCreateAuditAssignment();
  const updateStatus = useUpdateAuditStatus();

  const diagnostics = diagnosticsQuery.data ?? {
    available_categories: [],
    summary: { anomalies: 0, delta: 0, assigned: 0, open_tasks: 0 },
    items: [],
  };

  useEffect(() => {
    if (!categoriesInitialized && diagnostics.available_categories.length) {
      setFilters((prev) => ({ ...prev, categories: diagnostics.available_categories }));
      setCategoriesInitialized(true);
    }
  }, [diagnostics.available_categories, categoriesInitialized]);

  const maxObserved = useMemo(() => {
    if (!diagnostics.items.length) return 1;
    return Math.max(1, Math.ceil(Math.max(...diagnostics.items.map((item) => item.ecart_abs))));
  }, [diagnostics.items]);

  useEffect(() => {
    setFilters((prev) => ({
      ...prev,
      maxAbs: Math.max(prev.maxAbs, maxObserved),
    }));
  }, [maxObserved]);

  const [assignmentForm, setAssignmentForm] = useState({
    productId: null,
    responsable: '',
    note: '',
    dueDate: '',
    createTask: true,
  });
  const [resolutionForm, setResolutionForm] = useState({
    actionId: null,
    status: 'En cours',
    note: '',
  });

  const handleCategoryToggle = (category) => {
    setFilters((prev) => {
      const exists = prev.categories.includes(category);
      if (exists) {
        return { ...prev, categories: prev.categories.filter((cat) => cat !== category) };
      }
      return { ...prev, categories: [...prev.categories, category] };
    });
  };

  const handleSeverityToggle = (level) => {
    setFilters((prev) => {
      const exists = prev.levels.includes(level);
      if (exists) {
        return { ...prev, levels: prev.levels.filter((item) => item !== level) };
      }
      return { ...prev, levels: [...prev.levels, level] };
    });
  };

  const handleResetFilters = () => {
    setFilters({
      categories: diagnostics.available_categories,
      levels: severityOptions,
      minAbs: 0,
      maxAbs: maxObserved,
    });
  };

  const handleAssignmentSubmit = (event) => {
    event.preventDefault();
    if (!assignmentForm.productId || !assignmentForm.responsable) return;
    createAssignment.mutate({
      product_id: assignmentForm.productId,
      responsable: assignmentForm.responsable,
      note: assignmentForm.note || undefined,
      due_date: assignmentForm.dueDate || undefined,
      create_task: assignmentForm.createTask,
    });
  };

  const handleResolutionSubmit = (event) => {
    event.preventDefault();
    if (!resolutionForm.actionId) return;
    updateStatus.mutate({
      actionId: resolutionForm.actionId,
      status: resolutionForm.status,
      note: resolutionForm.note || undefined,
    });
  };

  const isLoading = diagnosticsQuery.isLoading;

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">audit</p>
          <h2 className="text-2xl font-semibold text-slate-900">Résolution d&apos;écarts</h2>
          <p className="text-sm text-slate-500">
            Identifiez les écarts entre stock théorique et mouvements, assignez les comptages correctifs et suivez la
            clôture des actions.
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Catégories</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {diagnostics.available_categories.map((category) => (
                <button
                  key={category}
                  type="button"
                  onClick={() => handleCategoryToggle(category)}
                  className={`rounded-full px-3 py-1 text-sm ${
                    filters.categories.includes(category)
                      ? 'bg-brand-50 text-brand-700 border border-brand-200'
                      : 'bg-slate-100 text-slate-600 border border-transparent'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Niveaux</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {severityOptions.map((level) => (
                <label key={level} className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={filters.levels.includes(level)}
                    onChange={() => handleSeverityToggle(level)}
                  />
                  {level}
                </label>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Amplitude de l&apos;écart</p>
            <div className="mt-3 flex gap-3">
              <input
                type="number"
                min={0}
                max={filters.maxAbs}
                value={filters.minAbs}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, minAbs: Math.max(0, Number(event.target.value)) }))
                }
                className="w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              />
              <input
                type="number"
                min={filters.minAbs}
                value={filters.maxAbs}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, maxAbs: Math.max(prev.minAbs, Number(event.target.value)) }))
                }
                className="w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              />
            </div>
            <p className="mt-1 text-xs text-slate-500">Max observé : {maxObserved}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="ghost" onClick={handleResetFilters}>
            Réinitialiser
          </Button>
        </div>
      </Card>

      <Card className="flex flex-col gap-4">
        {isLoading && <p className="text-sm text-slate-500">Chargement des diagnostics…</p>}
        {!isLoading && (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Metric label="Anomalies ouvertes" value={diagnostics.summary.anomalies} />
              <Metric label="Écart cumulé" value={`${numberFormatter.format(diagnostics.summary.delta)} u`} />
              <Metric label="Assignées" value={diagnostics.summary.assigned} />
              <Metric label="Tâches actives" value={diagnostics.summary.open_tasks} />
            </div>
            {diagnostics.items.length === 0 ? (
              <p className="text-sm text-slate-500">Aucune anomalie ne correspond aux filtres sélectionnés.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                      <th className="px-4 py-3">Produit</th>
                      <th className="px-4 py-3">Catégorie</th>
                      <th className="px-4 py-3">Stock système</th>
                      <th className="px-4 py-3">Stock calculé</th>
                      <th className="px-4 py-3">Écart</th>
                      <th className="px-4 py-3">Niveau</th>
                      <th className="px-4 py-3">Responsable</th>
                      <th className="px-4 py-3">Statut</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {diagnostics.items.map((item) => (
                      <tr key={item.product_id}>
                        <td className="px-4 py-3 font-medium text-slate-900">{item.nom}</td>
                        <td className="px-4 py-3 text-slate-600">{item.categorie ?? 'Non renseigné'}</td>
                        <td className="px-4 py-3">{item.stock_actuel.toFixed(2)}</td>
                        <td className="px-4 py-3">{item.stock_calcule.toFixed(2)}</td>
                        <td className="px-4 py-3">{item.ecart.toFixed(2)}</td>
                        <td className="px-4 py-3">{item.niveau_ecart}</td>
                        <td className="px-4 py-3">{item.responsable ?? '—'}</td>
                        <td className="px-4 py-3">{item.action_status ?? 'À investiguer'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <h3 className="text-lg font-semibold text-slate-900">Assigner un audit</h3>
          {diagnostics.items.length === 0 ? (
            <p className="text-sm text-slate-500">Aucune ligne disponible.</p>
          ) : (
            <form className="flex flex-col gap-4" onSubmit={handleAssignmentSubmit}>
              <select
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
                value={assignmentForm.productId ?? ''}
                onChange={(event) =>
                  setAssignmentForm((prev) => ({ ...prev, productId: Number(event.target.value) || null }))
                }
                required
              >
                <option value="">Sélectionner un produit</option>
                {diagnostics.items.map((item) => (
                  <option key={item.product_id} value={item.product_id}>
                    {item.nom} ({item.ecart.toFixed(2)})
                  </option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Responsable"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
                value={assignmentForm.responsable}
                onChange={(event) => setAssignmentForm((prev) => ({ ...prev, responsable: event.target.value }))}
                required
              />
              <textarea
                placeholder="Notes"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
                value={assignmentForm.note}
                onChange={(event) => setAssignmentForm((prev) => ({ ...prev, note: event.target.value }))}
              />
              <label className="text-sm text-slate-600">
                Date de comptage
                <input
                  type="date"
                  className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
                  value={assignmentForm.dueDate}
                  onChange={(event) => setAssignmentForm((prev) => ({ ...prev, dueDate: event.target.value }))}
                />
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={assignmentForm.createTask}
                  onChange={(event) =>
                    setAssignmentForm((prev) => ({ ...prev, createTask: event.target.checked }))
                  }
                />
                Générer une tâche de comptage correctif
              </label>
              <Button type="submit" variant="brand" disabled={createAssignment.isLoading}>
                Enregistrer
              </Button>
            </form>
          )}
        </Card>

        <Card className="flex flex-col gap-4">
          <h3 className="text-lg font-semibold text-slate-900">Clôturer / journaliser</h3>
          {actionsQuery.data?.items?.length ? (
            <form className="flex flex-col gap-4" onSubmit={handleResolutionSubmit}>
              <select
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
                value={resolutionForm.actionId ?? ''}
                onChange={(event) =>
                  setResolutionForm((prev) => ({ ...prev, actionId: Number(event.target.value) || null }))
                }
                required
              >
                <option value="">Sélectionner une action</option>
                {actionsQuery.data.items.map((action) => (
                  <option key={action.id} value={action.id}>
                    {action.produit} · {action.status}
                  </option>
                ))}
              </select>
              <select
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
                value={resolutionForm.status}
                onChange={(event) =>
                  setResolutionForm((prev) => ({ ...prev, status: event.target.value }))
                }
              >
                <option value="En cours">En cours</option>
                <option value="Résolu">Résolu</option>
              </select>
              <textarea
                placeholder="Commentaire / actions réalisées"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-400 focus:outline-none"
                value={resolutionForm.note}
                onChange={(event) => setResolutionForm((prev) => ({ ...prev, note: event.target.value }))}
              />
              <Button type="submit" variant="brand" disabled={updateStatus.isLoading}>
                Mettre à jour
              </Button>
            </form>
          ) : (
            <p className="text-sm text-slate-500">Aucune action ouverte.</p>
          )}
        </Card>
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">tâches</p>
            <h3 className="text-xl font-semibold text-slate-900">Comptages planifiés</h3>
          </div>
        </div>
        {actionsQuery.data?.items?.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                  <th className="px-4 py-3">Produit</th>
                  <th className="px-4 py-3">Responsable</th>
                  <th className="px-4 py-3">Statut</th>
                  <th className="px-4 py-3">Échéance</th>
                  <th className="px-4 py-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {actionsQuery.data.items.map((task) => (
                  <tr key={task.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{task.produit}</td>
                    <td className="px-4 py-3 text-slate-600">{task.responsable}</td>
                    <td className="px-4 py-3">{task.status}</td>
                    <td className="px-4 py-3">{task.due_date ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{task.note ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Aucune tâche planifiée.</p>
        )}
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">journal</p>
          <h3 className="text-xl font-semibold text-slate-900">Historique des résolutions</h3>
        </div>
        {resolutionsQuery.data?.items?.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Produit</th>
                  <th className="px-4 py-3">Statut</th>
                  <th className="px-4 py-3">Responsable</th>
                  <th className="px-4 py-3">Note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {resolutionsQuery.data.items.map((entry) => (
                  <tr key={entry.id}>
                    <td className="px-4 py-3 text-slate-600">
                      {new Date(entry.created_at).toLocaleString('fr-FR')}
                    </td>
                    <td className="px-4 py-3">#{entry.product_id}</td>
                    <td className="px-4 py-3">{entry.statut}</td>
                    <td className="px-4 py-3">{entry.responsable ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{entry.note ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Le journal est vide pour le moment.</p>
        )}
      </Card>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
