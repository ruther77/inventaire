/**
 * Module de hooks pour la génération et l'export de rapports.
 * @module hooks/useReports
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { fetchReportsOverview, exportReport } from '../api/client.js';

/**
 * Hook pour récupérer la vue d'ensemble des rapports disponibles.
 *
 * Fournit la liste de tous les types de rapports générables avec leurs métadonnées
 * (dernière génération, nombre d'enregistrements, etc.).
 *
 * @returns {Object} Query TanStack avec la vue d'ensemble des rapports
 * @property {Object} data - Métadonnées des rapports disponibles
 * @property {boolean} isLoading - État de chargement
 *
 * @example
 * const { data: overview } = useReportsOverview();
 * console.log(overview.availableReports);
 */
export function useReportsOverview() {
  return useQuery({
    queryKey: ['reports-overview'],
    queryFn: fetchReportsOverview,
    staleTime: 60_000,
  });
}

/**
 * Hook mutation pour exporter un rapport au format CSV.
 *
 * Gère automatiquement le téléchargement du fichier CSV dans le navigateur
 * en extrayant le nom du fichier depuis les headers HTTP (Content-Disposition).
 * Supporte différents types de rapports (ventes, stock, finances, etc.).
 *
 * @returns {Object} Mutation TanStack pour l'export de rapport
 * @property {Function} mutateAsync - Fonction async pour exporter (type de rapport)
 * @property {boolean} isLoading - Indique si l'export est en cours
 *
 * @example
 * const exportReport = useExportReport();
 * const handleExport = async () => {
 *   const { filename } = await exportReport.mutateAsync('ventes');
 *   console.log(`Rapport exporté: ${filename}`);
 * };
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
