import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import { formatDateTime } from '../../../utils/dateUtils.js';
import { fetchImportSessions, fetchImportSessionDetails } from '../../../api/client.js';

/**
 * ImportSessionsView - Affichage des sessions d'import groupées
 *
 * Features:
 * - Liste des sessions avec statistiques agrégées
 * - Expansion pour voir les détails de chaque session
 * - Filtres: Cette session / Aujourd'hui / Cette semaine
 * - Groupement par jour
 */

const FILTER_OPTIONS = [
  { id: 'current', label: 'Cette session', description: 'Imports de la session courante' },
  { id: 'today', label: "Aujourd'hui", description: "Tous les imports d'aujourd'hui" },
  { id: 'week', label: 'Cette semaine', description: 'Imports des 7 derniers jours' },
  { id: 'all', label: 'Tout', description: 'Tous les imports' },
];

const STATUS_LABELS = {
  pending: { label: 'En attente', color: 'text-slate-500' },
  processing: { label: 'En cours', color: 'text-blue-500' },
  completed: { label: 'Terminé', color: 'text-green-600' },
  failed: { label: 'Échoué', color: 'text-red-600' },
};

function formatDuration(dateDebut, dateFin) {
  if (!dateDebut || !dateFin) return '—';
  const debut = new Date(dateDebut);
  const fin = new Date(dateFin);
  const diffMs = fin - debut;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return '< 1 min';
  if (diffMin < 60) return `${diffMin} min`;
  const hours = Math.floor(diffMin / 60);
  const mins = diffMin % 60;
  return `${hours}h ${mins}min`;
}

function formatDateGroup(dateStr) {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return "Aujourd'hui";
  }
  if (date.toDateString() === yesterday.toDateString()) {
    return 'Hier';
  }
  return date.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
}

function groupSessionsByDay(sessions) {
  const groups = {};
  sessions.forEach((session) => {
    const dateKey = new Date(session.date_debut).toDateString();
    if (!groups[dateKey]) {
      groups[dateKey] = {
        label: formatDateGroup(session.date_debut),
        date: session.date_debut,
        sessions: [],
      };
    }
    groups[dateKey].sessions.push(session);
  });
  return Object.values(groups).sort((a, b) => new Date(b.date) - new Date(a.date));
}

function SessionCard({ session, onExpand, isExpanded }) {
  const successRate = session.nb_imports > 0
    ? Math.round((session.nb_completed / session.nb_imports) * 100)
    : 0;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 transition-all hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h3 className="text-sm font-semibold text-slate-900">
              Session {session.session_id.slice(0, 8)}
            </h3>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
              {session.nb_imports} import{session.nb_imports > 1 ? 's' : ''}
            </span>
            {successRate === 100 && (
              <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
                ✓ Succès
              </span>
            )}
            {session.nb_failed > 0 && (
              <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">
                {session.nb_failed} échec{session.nb_failed > 1 ? 's' : ''}
              </span>
            )}
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-1">
              <span className="font-medium">Début:</span>
              <span>{formatDateTime(session.date_debut)}</span>
            </div>
            {session.date_fin && (
              <div className="flex items-center gap-1">
                <span className="font-medium">Durée:</span>
                <span>{formatDuration(session.date_debut, session.date_fin)}</span>
              </div>
            )}
            {session.fournisseurs && (
              <div className="flex items-center gap-1">
                <span className="font-medium">Fournisseurs:</span>
                <span>{session.fournisseurs}</span>
              </div>
            )}
          </div>

          <div className="mt-3 grid grid-cols-3 gap-4 rounded-lg bg-slate-50 p-3">
            <div>
              <div className="text-xs text-slate-500">Lignes</div>
              <div className="text-lg font-semibold text-slate-900">{session.total_lignes}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Mouvements</div>
              <div className="text-lg font-semibold text-slate-900">{session.total_mouvements}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Produits créés</div>
              <div className="text-lg font-semibold text-slate-900">{session.total_produits_crees}</div>
            </div>
          </div>
        </div>

        <Button
          size="sm"
          variant="ghost"
          onClick={() => onExpand(session.session_id)}
        >
          {isExpanded ? 'Réduire' : 'Détails'}
        </Button>
      </div>
    </div>
  );
}

function SessionDetailsPanel({ sessionId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['import-session-details', sessionId],
    queryFn: () => fetchImportSessionDetails(sessionId),
    enabled: Boolean(sessionId),
    staleTime: 10_000,
  });

  if (isLoading) {
    return (
      <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-slate-500">Chargement des détails...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="text-sm text-red-600">Erreur: {error.message}</p>
      </div>
    );
  }

  if (!data || !data.imports || data.imports.length === 0) {
    return (
      <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-slate-500">Aucun import dans cette session</p>
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-2">
      {data.imports.map((job) => {
        const statusInfo = STATUS_LABELS[job.status] || STATUS_LABELS.pending;
        return (
          <div
            key={job.job_id}
            className="rounded-lg border border-slate-200 bg-white p-3"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-900">
                    {job.filename || 'Sans nom'}
                  </span>
                  <span className={`text-xs font-medium ${statusInfo.color}`}>
                    {statusInfo.label}
                  </span>
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {formatDateTime(job.created_at)}
                </div>
                {job.summary && (
                  <div className="mt-2 flex gap-4 text-xs text-slate-600">
                    <span>{job.summary.rows_received || 0} lignes</span>
                    <span>{job.summary.movements_created || 0} mouvements</span>
                    {job.summary.products_created > 0 && (
                      <span className="font-medium text-green-600">
                        +{job.summary.products_created} produits
                      </span>
                    )}
                  </div>
                )}
                {job.error && (
                  <div className="mt-2 rounded bg-red-50 p-2 text-xs text-red-600">
                    {job.error}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function ImportSessionsView() {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [expandedSessionId, setExpandedSessionId] = useState(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['import-sessions', selectedFilter],
    queryFn: () => fetchImportSessions({ limit: 100 }),
    staleTime: 30_000,
    refetchInterval: 60_000, // Rafraîchir toutes les minutes
  });

  const handleExpand = (sessionId) => {
    setExpandedSessionId((prev) => (prev === sessionId ? null : sessionId));
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <p className="text-sm text-slate-500">Chargement des sessions...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <p className="text-sm text-red-600">Erreur: {error.message}</p>
        </div>
      </Card>
    );
  }

  const sessions = data?.items || [];
  const groupedSessions = groupSessionsByDay(sessions);

  return (
    <div className="space-y-6">
      {/* Filtres */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Historique par session</h2>
            <p className="mt-1 text-sm text-slate-500">
              {data?.total || 0} session{data?.total > 1 ? 's' : ''} trouvée{data?.total > 1 ? 's' : ''}
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={() => refetch()}>
            Actualiser
          </Button>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((filter) => (
            <button
              key={filter.id}
              onClick={() => setSelectedFilter(filter.id)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                selectedFilter === filter.id
                  ? 'bg-brand-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Liste des sessions groupées par jour */}
      {groupedSessions.length === 0 ? (
        <Card>
          <div className="py-8 text-center">
            <p className="text-sm text-slate-500">Aucune session d'import trouvée</p>
            <p className="mt-1 text-xs text-slate-400">
              Les imports seront automatiquement groupés par session browser
            </p>
          </div>
        </Card>
      ) : (
        groupedSessions.map((group) => (
          <div key={group.label} className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
              {group.label}
            </h3>
            <div className="space-y-3">
              {group.sessions.map((session) => (
                <div key={session.session_id}>
                  <SessionCard
                    session={session}
                    onExpand={handleExpand}
                    isExpanded={expandedSessionId === session.session_id}
                  />
                  {expandedSessionId === session.session_id && (
                    <SessionDetailsPanel sessionId={session.session_id} />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
