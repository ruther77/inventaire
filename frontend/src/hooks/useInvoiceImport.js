import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useEffect, useRef, useState } from 'react';
import {
  extractInvoiceFromText,
  extractInvoiceFromFile,
  importInvoiceLines,
  importInvoiceToCatalog,
  linkInvoiceLine,
  createProductFromLine,
  confirmInvoiceStock,
  zeroClickInvoiceImport,
  zeroClickInvoiceJob,
  fetchZeroClickJobStatus,
  fetchZeroClickJobs,
  fetchInvoiceHistory,
  fetchProductMatchSuggestions,
  fetchImportSessions,
  fetchImportSessionDetails,
} from '../api/client.js';
import { getSessionId } from '../utils/sessionManager.js';

const getErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.join(', ');
  }
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  return fallback;
};

export function useInvoiceExtraction() {
  return useMutation({
    mutationFn: extractInvoiceFromText,
    onError: () => toast.error("Impossible d'analyser le texte"),
  });
}

export function useInvoiceFileExtraction() {
  return useMutation({
    mutationFn: extractInvoiceFromFile,
    onError: () => toast.error("Impossible de lire la facture"),
  });
}

export function useInvoiceImport() {
  return useMutation({
    mutationFn: importInvoiceLines,
    onSuccess: () => toast.success('Mouvements créés'),
    onError: (error) => toast.error(getErrorMessage(error, 'Import impossible')),
  });
}

export function useInvoiceCatalogImport() {
  return useMutation({
    mutationFn: importInvoiceToCatalog,
    onSuccess: () => toast.success('Catalogue mis à jour'),
    onError: (error) => toast.error(getErrorMessage(error, 'Import catalogue impossible')),
  });
}

export function useInvoiceHistory(filters = {}) {
  return useQuery({
    queryKey: ['invoice-history', filters],
    queryFn: () => fetchInvoiceHistory(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useInvoiceZeroClick() {
  return useMutation({
    mutationFn: zeroClickInvoiceImport,
    onSuccess: () => toast.success('Import zero-click en cours'),
    onError: (error) => toast.error(getErrorMessage(error, 'Zero-click impossible')),
  });
}

export function useLinkInvoiceLine() {
  return useMutation({
    mutationFn: linkInvoiceLine,
    onSuccess: () => toast.success('Ligne liée au produit'),
    onError: (error) => toast.error(getErrorMessage(error, 'Liaison impossible')),
  });
}

export function useCreateProductFromLine() {
  return useMutation({
    mutationFn: createProductFromLine,
    onSuccess: () => toast.success('Produit créé depuis la facture'),
    onError: (error) => toast.error(getErrorMessage(error, 'Création produit impossible')),
  });
}

export function useConfirmInvoiceStock() {
  return useMutation({
    mutationFn: confirmInvoiceStock,
    onSuccess: () => toast.success('Mouvements stock validés'),
    onError: (error) => toast.error(getErrorMessage(error, 'Validation stock impossible')),
  });
}

// Hook pour lancer un job zero-click avec polling automatique
export function useZeroClickJob() {
  const [jobId, setJobId] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const pollingIntervalRef = useRef(null);

  // Mutation pour lancer le job
  const startJobMutation = useMutation({
    mutationFn: (params) => {
      // Ajouter automatiquement le session_id
      const sessionId = getSessionId();
      return zeroClickInvoiceJob({ ...params, sessionId });
    },
    onSuccess: (data) => {
      setJobId(data.job_id);
      setIsPolling(true);
      toast.info('Import en cours...', { id: 'zero-click-job' });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Impossible de lancer l\'import'));
      setIsPolling(false);
    },
  });

  // Query pour le polling du statut
  const { data: jobStatus, refetch } = useQuery({
    queryKey: ['zero-click-job', jobId],
    queryFn: () => fetchZeroClickJobStatus(jobId),
    enabled: Boolean(jobId && isPolling),
    refetchInterval: false, // Contrôlé manuellement
    retry: 3,
  });

  // Effet de polling
  useEffect(() => {
    if (!isPolling || !jobId) {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      return;
    }

    // Poll toutes les 2 secondes
    pollingIntervalRef.current = setInterval(() => {
      refetch();
    }, 2000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [isPolling, jobId, refetch]);

  // Effet pour gérer la fin du job
  useEffect(() => {
    if (!jobStatus || !isPolling) return;

    if (jobStatus.status === 'completed') {
      setIsPolling(false);
      toast.success('Import terminé avec succès !', { id: 'zero-click-job' });

      // Afficher le résumé
      if (jobStatus.summary) {
        const { movements_created, quantity_total, products_created } = jobStatus.summary;
        toast.success(
          `${movements_created || 0} mouvements créés, ${quantity_total || 0} unités ajoutées${
            products_created ? `, ${products_created} produits créés` : ''
          }`,
          { duration: 5000 }
        );
      }
    } else if (jobStatus.status === 'failed') {
      setIsPolling(false);
      toast.error(jobStatus.error || 'Import échoué', { id: 'zero-click-job' });
    }
  }, [jobStatus, isPolling]);

  const reset = () => {
    setJobId(null);
    setIsPolling(false);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  return {
    startJob: startJobMutation.mutate,
    isStarting: startJobMutation.isPending,
    jobId,
    jobStatus,
    isPolling,
    reset,
  };
}

// Hook pour lister les jobs zero-click récents
export function useZeroClickJobs(filters = {}) {
  return useQuery({
    queryKey: ['zero-click-jobs', filters],
    queryFn: () => fetchZeroClickJobs(filters),
    staleTime: 10_000,
    refetchInterval: 30_000, // Rafraîchir toutes les 30s
  });
}

// Hook pour obtenir des suggestions de matching fuzzy pour un produit
export function useProductMatchSuggestions(query, options = {}) {
  const { enabled = true, maxResults = 5, minScore = 60.0 } = options;

  return useQuery({
    queryKey: ['product-match-suggestions', query, maxResults, minScore],
    queryFn: () => fetchProductMatchSuggestions({ query, maxResults, minScore }),
    enabled: enabled && Boolean(query && query.trim()),
    staleTime: 60_000, // Cache 1 minute
    retry: 1,
  });
}

// Hook pour lister les sessions d'import
export function useImportSessions(filters = {}) {
  return useQuery({
    queryKey: ['import-sessions', filters],
    queryFn: () => fetchImportSessions(filters),
    staleTime: 30_000,
    refetchInterval: 60_000, // Rafraîchir toutes les 60s
  });
}

// Hook pour récupérer les détails d'une session
export function useImportSessionDetails(sessionId) {
  return useQuery({
    queryKey: ['import-session-details', sessionId],
    queryFn: () => fetchImportSessionDetails(sessionId),
    enabled: Boolean(sessionId),
    staleTime: 10_000,
  });
}
