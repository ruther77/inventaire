import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  extractInvoiceFromText,
  extractInvoiceFromFile,
  importInvoiceLines,
  importInvoiceToCatalog,
  fetchInvoiceHistory,
} from '../api/client.js';

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
