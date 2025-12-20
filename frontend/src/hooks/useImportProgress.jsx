/**
 * useImportProgress - Hook pour gérer l'import de factures avec notification de progression
 *
 * Combine:
 * - Le polling du job zero-click (useZeroClickJob)
 * - L'affichage du toast de progression (ImportProgressToast)
 * - La gestion automatique du cycle de vie de la notification
 *
 * Usage:
 * const { startImport, isImporting } = useImportProgress({
 *   onSuccess: (summary) => { ... },
 *   onError: (error) => { ... }
 * });
 *
 * startImport({ file, marginPercent, supplierHint });
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { zeroClickInvoiceJob, fetchZeroClickJobStatus } from '../api/client.js';
import ImportProgressToast from '../components/ui/ImportProgressToast.jsx';

export function useImportProgress({ onSuccess, onError, onCancel } = {}) {
  const [jobId, setJobId] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [fileName, setFileName] = useState(null);
  const pollingIntervalRef = useRef(null);

  // Mutation pour lancer le job
  const startJobMutation = useMutation({
    mutationFn: zeroClickInvoiceJob,
    onSuccess: (data) => {
      setJobId(data.job_id);
      setIsPolling(true);
      setShowToast(true);
    },
    onError: (error) => {
      setIsPolling(false);
      setShowToast(false);
      onError?.(error);
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
      // Garder le toast visible pendant 5 secondes après le succès
      setTimeout(() => {
        setShowToast(false);
        setJobId(null);
        setFileName(null);
      }, 5000);

      onSuccess?.(jobStatus.summary);
    } else if (jobStatus.status === 'failed') {
      setIsPolling(false);
      // Garder le toast visible jusqu'à ce que l'utilisateur le ferme
      onError?.(jobStatus.error);
    }
  }, [jobStatus, isPolling, onSuccess, onError]);

  // Fonction pour démarrer un import
  const startImport = useCallback(
    ({ file, marginPercent = 40, supplierHint = null, autoConfirm = true }) => {
      setFileName(file.name);
      startJobMutation.mutate({ file, marginPercent, supplierHint, autoConfirm });
    },
    [startJobMutation]
  );

  // Fonction pour annuler l'import
  const handleCancel = useCallback(() => {
    setIsPolling(false);
    setShowToast(false);
    setJobId(null);
    setFileName(null);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    onCancel?.();
  }, [onCancel]);

  // Fonction pour fermer manuellement le toast
  const handleDismiss = useCallback(() => {
    setShowToast(false);
    setJobId(null);
    setFileName(null);
  }, []);

  // Reset complet
  const reset = useCallback(() => {
    setJobId(null);
    setIsPolling(false);
    setShowToast(false);
    setFileName(null);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  return {
    startImport,
    isImporting: isPolling || startJobMutation.isPending,
    jobId,
    jobStatus,
    reset,
    // Composant toast à rendre
    ToastPortal: showToast
      ? () =>
          createPortal(
            <div className="fixed bottom-4 right-4 z-[200]">
              <ImportProgressToast
                jobStatus={jobStatus}
                fileName={fileName}
                onCancel={handleCancel}
                onDismiss={handleDismiss}
                canCancel={isPolling}
              />
            </div>,
            document.body
          )
      : null,
  };
}

/**
 * Hook simplifié qui retourne uniquement les fonctions essentielles
 * sans le portail de toast (pour une utilisation avec le système de toast existant)
 */
export function useZeroClickJobWithProgress({ onSuccess, onError } = {}) {
  const [jobId, setJobId] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const pollingIntervalRef = useRef(null);

  // Mutation pour lancer le job
  const startJobMutation = useMutation({
    mutationFn: zeroClickInvoiceJob,
    onSuccess: (data) => {
      setJobId(data.job_id);
      setIsPolling(true);
    },
    onError: (error) => {
      setIsPolling(false);
      onError?.(error);
    },
  });

  // Query pour le polling du statut
  const { data: jobStatus, refetch } = useQuery({
    queryKey: ['zero-click-job-progress', jobId],
    queryFn: () => fetchZeroClickJobStatus(jobId),
    enabled: Boolean(jobId && isPolling),
    refetchInterval: false,
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
      onSuccess?.(jobStatus);
    } else if (jobStatus.status === 'failed') {
      setIsPolling(false);
      onError?.(jobStatus);
    }
  }, [jobStatus, isPolling, onSuccess, onError]);

  const startJob = useCallback(
    ({ file, marginPercent = 40, supplierHint = null, autoConfirm = true }) => {
      startJobMutation.mutate({ file, marginPercent, supplierHint, autoConfirm });
    },
    [startJobMutation]
  );

  const reset = useCallback(() => {
    setJobId(null);
    setIsPolling(false);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  return {
    startJob,
    isStarting: startJobMutation.isPending,
    isPolling,
    jobId,
    jobStatus,
    reset,
  };
}
