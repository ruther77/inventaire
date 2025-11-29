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

export function useAdminOverview() {
  return useQuery({
    queryKey: ['admin-overview'],
    queryFn: fetchAdminOverview,
    refetchOnWindowFocus: false,
  });
}

export function useAdminUsers() {
  return useQuery({
    queryKey: ['admin-users'],
    queryFn: fetchAdminUsers,
    refetchOnWindowFocus: false,
  });
}

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
