/**
 * Module de hooks pour l'audit et le diagnostic de la qualité des données.
 * @module hooks/useAudit
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  fetchAuditDiagnostics,
  fetchAuditActions,
  fetchAuditResolutions,
  createAuditAssignment,
  updateAuditActionStatus,
} from '../api/client.js';

/**
 * Hook pour récupérer les diagnostics d'audit avec filtres.
 *
 * Permet d'identifier les problèmes de qualité des données (données manquantes,
 * incohérences, doublons, etc.) avec possibilité de filtrage.
 * Conserve les données précédentes pendant le chargement.
 *
 * @param {Object} filters - Filtres de diagnostic
 * @param {string} [filters.severity] - Gravité (critical, warning, info)
 * @param {string} [filters.status] - Statut (pending, in_progress, resolved)
 * @param {string} [filters.category] - Catégorie de diagnostic
 *
 * @returns {Object} Query TanStack avec les diagnostics
 * @property {Array} data - Liste des problèmes détectés
 *
 * @example
 * const { data: diagnostics } = useAuditDiagnostics({
 *   severity: 'critical',
 *   status: 'pending'
 * });
 */
export function useAuditDiagnostics(filters) {
  return useQuery({
    queryKey: ['audit-diagnostics', filters],
    queryFn: () => fetchAuditDiagnostics(filters),
    keepPreviousData: true,
  });
}

/**
 * Hook pour récupérer les actions d'audit en cours ou terminées.
 *
 * Liste les tâches de correction assignées aux utilisateurs pour résoudre
 * les problèmes identifiés par l'audit.
 *
 * @param {boolean} includeClosed - Inclure les actions terminées (défaut: false)
 *
 * @returns {Object} Query TanStack avec les actions d'audit
 * @property {Array} data - Liste des actions à effectuer
 *
 * @example
 * const { data: actions } = useAuditActions(false);
 * // Affiche uniquement les actions en cours
 */
export function useAuditActions(includeClosed = false) {
  return useQuery({
    queryKey: ['audit-actions', includeClosed],
    queryFn: () => fetchAuditActions(includeClosed),
  });
}

/**
 * Hook pour récupérer l'historique des résolutions d'audit.
 *
 * Permet de consulter les problèmes qui ont été résolus avec les détails
 * des corrections apportées.
 *
 * @returns {Object} Query TanStack avec les résolutions
 * @property {Array} data - Liste des problèmes résolus
 *
 * @example
 * const { data: resolutions } = useAuditResolutions();
 */
export function useAuditResolutions() {
  return useQuery({
    queryKey: ['audit-resolutions'],
    queryFn: fetchAuditResolutions,
  });
}

/**
 * Hook mutation pour créer une assignation d'audit.
 *
 * Permet d'assigner une tâche de correction à un utilisateur pour résoudre
 * un problème identifié. Affiche une notification et invalide les caches.
 *
 * @returns {Object} Mutation TanStack pour créer une assignation
 * @property {Function} mutate - Fonction pour créer l'assignation
 *
 * @example
 * const createAssignment = useCreateAuditAssignment();
 * createAssignment.mutate({
 *   diagnosticId: 123,
 *   assignedTo: 'user@example.com',
 *   priority: 'high'
 * });
 */
export function useCreateAuditAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAuditAssignment,
    onSuccess: () => {
      toast.success('Assignation créée');
      queryClient.invalidateQueries({ queryKey: ['audit-diagnostics'] });
      queryClient.invalidateQueries({ queryKey: ['audit-actions'] });
    },
    onError: () => toast.error("Impossible d'enregistrer l'assignation"),
  });
}

/**
 * Hook mutation pour mettre à jour le statut d'une action d'audit.
 *
 * Permet de marquer une action comme en cours, terminée ou annulée.
 * Affiche une notification et rafraîchit les données.
 *
 * @returns {Object} Mutation TanStack pour mettre à jour le statut
 * @property {Function} mutate - Fonction pour changer le statut
 *
 * @example
 * const updateStatus = useUpdateAuditStatus();
 * updateStatus.mutate({
 *   actionId: 456,
 *   status: 'resolved',
 *   resolution: 'Données corrigées manuellement'
 * });
 */
export function useUpdateAuditStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateAuditActionStatus,
    onSuccess: () => {
      toast.success('Journal mis à jour');
      queryClient.invalidateQueries({ queryKey: ['audit-diagnostics'] });
      queryClient.invalidateQueries({ queryKey: ['audit-actions'] });
      queryClient.invalidateQueries({ queryKey: ['audit-resolutions'] });
    },
    onError: () => toast.error('Mise à jour impossible'),
  });
}
