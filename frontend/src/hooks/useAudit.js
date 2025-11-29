import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  fetchAuditDiagnostics,
  fetchAuditActions,
  fetchAuditResolutions,
  createAuditAssignment,
  updateAuditActionStatus,
} from '../api/client.js';

export function useAuditDiagnostics(filters) {
  return useQuery({
    queryKey: ['audit-diagnostics', filters],
    queryFn: () => fetchAuditDiagnostics(filters),
    keepPreviousData: true,
  });
}

export function useAuditActions(includeClosed = false) {
  return useQuery({
    queryKey: ['audit-actions', includeClosed],
    queryFn: () => fetchAuditActions(includeClosed),
  });
}

export function useAuditResolutions() {
  return useQuery({
    queryKey: ['audit-resolutions'],
    queryFn: fetchAuditResolutions,
  });
}

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
