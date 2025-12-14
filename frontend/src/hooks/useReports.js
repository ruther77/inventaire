import { useQuery, useMutation } from '@tanstack/react-query';
import { fetchReportsOverview, exportReport } from '../api/client.js';

export function useReportsOverview() {
  return useQuery({
    queryKey: ['reports-overview'],
    queryFn: fetchReportsOverview,
    staleTime: 60_000,
  });
}

/**
 * Hook pour exporter un rapport CSV.
 * Gère le téléchargement automatique du fichier.
 */
export function useExportReport() {
  return useMutation({
    mutationFn: async (type) => {
      const response = await exportReport(type);

      // Extraire le nom du fichier depuis le header
      const contentDisposition = response.headers?.['content-disposition'];
      let filename = `rapport_${type}.csv`;
      if (contentDisposition) {
        const match = /filename="?([^"]+)"?/i.exec(contentDisposition);
        if (match?.[1]) {
          filename = match[1];
        }
      }

      // Créer et télécharger le blob
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      return { filename };
    },
  });
}
