/**
 * Module de hooks pour l'administration système (sauvegardes, utilisateurs, diagnostics).
 * @module hooks/useAdmin
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  createBackupRequest,
  deleteBackupRequest,
  fetchAdminOverview,
  fetchAdminUsers,
  fetchBackupSettings,
  fetchIntegrityReport,
  resetAdminUserPassword,
  restoreBackupRequest,
  saveBackupSettingsRequest,
  updateAdminUserRole,
} from '../api/client.js';

/**
 * Hook pour récupérer la vue d'ensemble de l'administration système.
 *
 * Fournit les statistiques globales du système : nombre d'utilisateurs,
 * dernière sauvegarde, espace disque, santé de la base de données, etc.
 *
 * @returns {Object} Query TanStack avec les données d'administration
 * @property {Object} data - Statistiques et état du système
 * @property {boolean} isLoading - État de chargement
 *
 * @example
 * const { data: overview } = useAdminOverview();
 * console.log(overview.lastBackup, overview.systemHealth);
 */
export function useAdminOverview() {
  return useQuery({
    queryKey: ['admin-overview'],
    queryFn: fetchAdminOverview,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook pour récupérer la liste des utilisateurs du système.
 *
 * Liste tous les utilisateurs avec leurs rôles, permissions et statut.
 * Utilisé pour la gestion des accès et des droits.
 *
 * @returns {Object} Query TanStack avec la liste des utilisateurs
 * @property {Array} data - Liste des utilisateurs
 *
 * @example
 * const { data: users } = useAdminUsers();
 */
export function useAdminUsers() {
  return useQuery({
    queryKey: ['admin-users'],
    queryFn: fetchAdminUsers,
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook mutation pour créer une sauvegarde manuelle de la base de données.
 *
 * Déclenche une sauvegarde complète immédiate et affiche une notification.
 * Invalide les caches pour refléter la nouvelle sauvegarde.
 *
 * @returns {Object} Mutation TanStack pour créer une sauvegarde
 * @property {Function} mutate - Fonction pour déclencher la sauvegarde
 *
 * @example
 * const createBackup = useCreateBackup();
 * createBackup.mutate();
 */
export function useCreateBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createBackupRequest,
    onSuccess: () => {
      toast.success('Sauvegarde déclenchée');
      queryClient.invalidateQueries({ queryKey: ['admin-overview'] });
      queryClient.invalidateQueries({ queryKey: ['maintenance-backups'] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail ?? "Impossible de créer la sauvegarde");
    },
  });
}

export function useRestoreBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: restoreBackupRequest,
    onSuccess: () => {
      toast.success('Restauration effectuée');
      queryClient.invalidateQueries({ queryKey: ['admin-overview'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail ?? "Échec de la restauration");
    },
  });
}

export function useDeleteBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteBackupRequest,
    onSuccess: () => {
      toast.success('Sauvegarde supprimée');
      queryClient.invalidateQueries({ queryKey: ['admin-overview'] });
      queryClient.invalidateQueries({ queryKey: ['maintenance-backups'] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail ?? "Suppression impossible");
    },
  });
}

export function useBackupSettings() {
  return useQuery({
    queryKey: ['admin-settings'],
    queryFn: fetchBackupSettings,
  });
}

export function useSaveBackupSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: saveBackupSettingsRequest,
    onSuccess: () => {
      toast.success('Planification enregistrée');
      queryClient.invalidateQueries({ queryKey: ['admin-overview'] });
      queryClient.invalidateQueries({ queryKey: ['admin-settings'] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail ?? "Impossible d'enregistrer la planification");
    },
  });
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateAdminUserRole,
    onSuccess: () => {
      toast.success('Rôle mis à jour');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail ?? 'Opération refusée');
    },
  });
}

export function useResetUserPassword() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: resetAdminUserPassword,
    onSuccess: (data) => {
      toast.success('Mot de passe régénéré');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      return data;
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail ?? 'Impossible de réinitialiser');
    },
  });
}

export function useIntegrityReport() {
  return useMutation({
    mutationFn: fetchIntegrityReport,
    onError: (error) => {
      toast.error(error?.response?.data?.detail ?? 'Diagnostic indisponible');
    },
  });
}
