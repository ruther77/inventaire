/**
 * Module de hooks pour l'import et l'extraction de factures fournisseurs.
 *
 * Ce module gère:
 * - L'extraction OCR de factures (PDF, images, texte)
 * - L'import des lignes de facture dans le stock
 * - La création/liaison de produits depuis les factures
 * - Le système zero-click (import automatique complet)
 * - Le suivi des jobs d'import asynchrones
 * - L'historique des factures importées
 * - Les suggestions de matching produits
 *
 * @module hooks/useInvoiceImport
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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

/**
 * Extrait un message d'erreur lisible depuis une réponse d'erreur API.
 *
 * @param {Object} error - L'erreur retournée par l'API
 * @param {string} fallback - Message par défaut si extraction impossible
 * @returns {string} Message d'erreur formaté
 */
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

/**
 * Hook d'extraction de facture depuis du texte brut.
 *
 * Parse un texte copié-collé pour en extraire les lignes de produits,
 * quantités, prix, fournisseur, etc.
 *
 * @returns {Object} Mutation d'extraction
 *
 * @example
 * const { mutate: extractFromText } = useInvoiceExtraction();
 *
 * extractFromText({
 *   text: "TOMATES 5kg 12.50€\nOIGNONS 2kg 4.80€",
 *   supplierId: 42
 * });
 */
export function useInvoiceExtraction() {
  return useMutation({
    mutationFn: extractInvoiceFromText,
    onError: () => toast.error("Impossible d'analyser le texte"),
  });
}

/**
 * Hook d'extraction de facture depuis un fichier (PDF, image).
 *
 * Utilise l'OCR pour extraire automatiquement les lignes de produits
 * depuis une photo ou un PDF de facture.
 *
 * @returns {Object} Mutation d'extraction
 *
 * @example
 * const { mutate: extractFromFile, isPending } = useInvoiceFileExtraction();
 *
 * extractFromFile({
 *   file: pdfFile,
 *   supplierId: 42
 * });
 */
export function useInvoiceFileExtraction() {
  return useMutation({
    mutationFn: extractInvoiceFromFile,
    onError: () => toast.error("Impossible de lire la facture"),
  });
}

/**
 * Hook d'import des lignes de facture dans le stock.
 *
 * Crée les mouvements de stock pour les produits déjà existants
 * dans le catalogue. Les produits inconnus doivent être créés
 * ou liés manuellement avant.
 *
 * @returns {Object} Mutation d'import
 *
 * @example
 * const { mutate: importLines } = useInvoiceImport();
 *
 * importLines({
 *   lines: [
 *     { product_id: 10, quantity: 5, unit_price: 12.5 },
 *     { product_id: 20, quantity: 2, unit_price: 4.8 }
 *   ],
 *   invoiceDate: '2025-01-15',
 *   supplierId: 42
 * });
 */
export function useInvoiceImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importInvoiceLines,
    onSuccess: () => {
      toast.success('Mouvements créés');
      // Invalider les données impactées par l'import
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['stock'] });
      queryClient.invalidateQueries({ queryKey: ['invoice-history'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Import impossible')),
  });
}

/**
 * Hook d'import des lignes dans le catalogue produits.
 *
 * Met à jour les prix et informations produits du catalogue
 * à partir des lignes de facture, sans créer de mouvements de stock.
 *
 * @returns {Object} Mutation d'import catalogue
 *
 * @example
 * const { mutate: importToCatalog } = useInvoiceCatalogImport();
 *
 * importToCatalog({
 *   lines: [...],
 *   updatePrices: true
 * });
 */
export function useInvoiceCatalogImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importInvoiceToCatalog,
    onSuccess: () => {
      toast.success('Catalogue mis à jour');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['invoice-history'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Import catalogue impossible')),
  });
}

/**
 * Hook pour récupérer l'historique des factures importées.
 *
 * @param {Object} filters - Filtres de recherche
 * @param {number} [filters.supplierId] - Filtrer par fournisseur
 * @param {string} [filters.dateFrom] - Date de début
 * @param {string} [filters.dateTo] - Date de fin
 *
 * @returns {Object} Query avec l'historique
 *
 * @example
 * const { data: history } = useInvoiceHistory({ supplierId: 42 });
 */
export function useInvoiceHistory(filters = {}) {
  return useQuery({
    queryKey: ['invoice-history', filters],
    queryFn: () => fetchInvoiceHistory(filters),
    staleTime: 30_000, // 30 secondes
    refetchOnWindowFocus: false,
  });
}

/**
 * Hook d'import zero-click (import automatique complet).
 *
 * Lance un import entièrement automatisé: extraction OCR, matching produits,
 * création de produits manquants, et import stock en une seule opération.
 *
 * @returns {Object} Mutation zero-click
 *
 * @example
 * const { mutate: zeroClick } = useInvoiceZeroClick();
 *
 * zeroClick({
 *   file: invoiceFile,
 *   supplierId: 42,
 *   autoCreateProducts: true
 * });
 */
export function useInvoiceZeroClick() {
  return useMutation({
    mutationFn: zeroClickInvoiceImport,
    onSuccess: () => toast.success('Import zero-click en cours'),
    onError: (error) => toast.error(getErrorMessage(error, 'Zero-click impossible')),
  });
}

/**
 * Hook pour lier une ligne de facture à un produit existant.
 *
 * Associe manuellement une ligne extraite (non reconnue automatiquement)
 * à un produit du catalogue.
 *
 * @returns {Object} Mutation de liaison
 *
 * @example
 * const { mutate: linkLine } = useLinkInvoiceLine();
 *
 * linkLine({
 *   lineId: 123,
 *   productId: 456
 * });
 */
export function useLinkInvoiceLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: linkInvoiceLine,
    onSuccess: () => {
      toast.success('Ligne liée au produit');
      queryClient.invalidateQueries({ queryKey: ['invoice-history'] });
      queryClient.invalidateQueries({ queryKey: ['product-match-suggestions'] });
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Liaison impossible')),
  });
}

/**
 * Hook pour créer un nouveau produit depuis une ligne de facture.
 *
 * Crée automatiquement un produit dans le catalogue à partir
 * des informations d'une ligne de facture non reconnue.
 *
 * @returns {Object} Mutation de création
 *
 * @example
 * const { mutate: createProduct } = useCreateProductFromLine();
 *
 * createProduct({
 *   lineId: 123,
 *   productData: {
 *     name: 'Tomates cerises BIO',
 *     category: 'Fruits & Légumes'
 *   }
 * });
 */
export function useCreateProductFromLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProductFromLine,
    onSuccess: () => {
      toast.success('Produit créé depuis la facture');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['invoice-history'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Création produit impossible')),
  });
}

/**
 * Hook pour confirmer et valider les mouvements de stock d'une facture.
 *
 * Valide définitivement les mouvements de stock après vérification.
 * Une fois confirmés, ils ne peuvent plus être modifiés.
 *
 * @returns {Object} Mutation de confirmation
 *
 * @example
 * const { mutate: confirmStock } = useConfirmInvoiceStock();
 *
 * confirmStock({
 *   invoiceId: 789
 * });
 */
export function useConfirmInvoiceStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: confirmInvoiceStock,
    onSuccess: () => {
      toast.success('Mouvements stock validés');
      queryClient.invalidateQueries({ queryKey: ['stock'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['invoice-history'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Validation stock impossible')),
  });
}

/**
 * Hook pour lancer un job zero-click avec suivi en temps réel (polling).
 *
 * Ce hook gère tout le cycle de vie d'un import zero-click asynchrone:
 * 1. Lancement du job d'import
 * 2. Polling automatique du statut toutes les 2 secondes
 * 3. Détection de la fin (succès ou échec)
 * 4. Invalidation des caches et affichage du résumé
 *
 * @returns {Object} État et contrôles du job
 * @property {Function} startJob - Lance un nouveau job zero-click
 * @property {boolean} isStarting - Indique si le job démarre
 * @property {string|null} jobId - ID du job en cours
 * @property {Object|null} jobStatus - Statut actuel du job (status, progress, summary)
 * @property {boolean} isPolling - Indique si le polling est actif
 * @property {Function} reset - Réinitialise le hook pour un nouveau job
 *
 * @example
 * const { startJob, jobStatus, isPolling, reset } = useZeroClickJob();
 *
 * // Lancer un job
 * startJob({
 *   file: invoiceFile,
 *   supplierId: 42,
 *   autoCreateProducts: true
 * });
 *
 * // Suivre la progression
 * if (jobStatus?.status === 'processing') {
 *   console.log(`Progression: ${jobStatus.progress}%`);
 * }
 *
 * // Réinitialiser après succès
 * if (jobStatus?.status === 'completed') {
 *   reset();
 * }
 */
export function useZeroClickJob() {
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const pollingIntervalRef = useRef(null);

  // Mutation pour lancer le job
  const startJobMutation = useMutation({
    mutationFn: (params) => {
      // Ajouter automatiquement le session_id pour tracer l'import
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
    refetchInterval: false, // Contrôlé manuellement via setInterval ci-dessous
    retry: 3,
  });

  // Effet de polling: interroge le serveur toutes les 2 secondes
  useEffect(() => {
    if (!isPolling || !jobId) {
      // Arrêter le polling si plus actif
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      return;
    }

    // Lancer le polling toutes les 2 secondes
    pollingIntervalRef.current = setInterval(() => {
      refetch();
    }, 2000);

    // Cleanup: arrêter le polling quand le composant démonte
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [isPolling, jobId, refetch]);

  // Effet pour gérer la fin du job (succès ou échec)
  useEffect(() => {
    if (!jobStatus || !isPolling) return;

    if (jobStatus.status === 'completed') {
      // Job terminé avec succès
      setIsPolling(false);
      toast.success('Import terminé avec succès !', { id: 'zero-click-job' });

      // Invalider toutes les données impactées par l'import
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['stock'] });
      queryClient.invalidateQueries({ queryKey: ['invoice-history'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
      queryClient.invalidateQueries({ queryKey: ['zero-click-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['import-sessions'] });

      // Afficher le résumé détaillé de l'import
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
      // Job échoué
      setIsPolling(false);
      toast.error(jobStatus.error || 'Import échoué', { id: 'zero-click-job' });
    }
  }, [jobStatus, isPolling]);

  /**
   * Réinitialise le hook pour permettre un nouveau job.
   * Arrête le polling et nettoie les états.
   */
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

/**
 * Hook pour lister les jobs zero-click récents.
 *
 * Affiche l'historique des imports automatiques avec leur statut
 * et progression. Se rafraîchit automatiquement toutes les 30 secondes.
 *
 * @param {Object} filters - Filtres de recherche
 * @param {string} [filters.status] - Filtrer par statut (pending, processing, completed, failed)
 * @param {number} [filters.limit=50] - Nombre max de jobs à retourner
 *
 * @returns {Object} Query avec la liste des jobs
 *
 * @example
 * const { data: jobs } = useZeroClickJobs({ status: 'completed' });
 */
export function useZeroClickJobs(filters = {}) {
  return useQuery({
    queryKey: ['zero-click-jobs', filters],
    queryFn: () => fetchZeroClickJobs(filters),
    staleTime: 10_000, // 10 secondes
    refetchInterval: 30_000, // Rafraîchir toutes les 30s
  });
}

/**
 * Hook pour obtenir des suggestions de matching fuzzy pour un produit.
 *
 * Utilise un algorithme de recherche floue pour trouver les produits
 * du catalogue qui correspondent le mieux à une description de facture.
 *
 * @param {string} query - Texte à rechercher (nom produit de la facture)
 * @param {Object} options - Options de recherche
 * @param {boolean} [options.enabled=true] - Activer/désactiver la query
 * @param {number} [options.maxResults=5] - Nombre max de suggestions
 * @param {number} [options.minScore=60.0] - Score minimum de confiance (0-100)
 *
 * @returns {Object} Query avec les suggestions triées par score
 *
 * @example
 * const { data: suggestions } = useProductMatchSuggestions(
 *   'tomate cerise bio',
 *   { maxResults: 3, minScore: 70 }
 * );
 * // suggestions = [
 * //   { product_id: 10, name: 'Tomates cerises BIO', score: 95.5 },
 * //   { product_id: 20, name: 'Tomates cerise rouges', score: 78.2 }
 * // ]
 */
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

/**
 * Hook pour lister les sessions d'import de factures.
 *
 * Une session regroupe toutes les opérations liées à l'import d'une facture
 * (extraction, matching, création produits, mouvements stock).
 *
 * @param {Object} filters - Filtres de recherche
 * @param {number} [filters.supplierId] - Filtrer par fournisseur
 * @param {string} [filters.dateFrom] - Date de début
 * @param {string} [filters.dateTo] - Date de fin
 *
 * @returns {Object} Query avec la liste des sessions
 *
 * @example
 * const { data: sessions } = useImportSessions({ supplierId: 42 });
 */
export function useImportSessions(filters = {}) {
  return useQuery({
    queryKey: ['import-sessions', filters],
    queryFn: () => fetchImportSessions(filters),
    staleTime: 30_000,
    refetchInterval: 60_000, // Rafraîchir toutes les 60s
  });
}

/**
 * Hook pour récupérer les détails d'une session d'import.
 *
 * Retourne toutes les lignes, produits créés, mouvements générés
 * et logs d'une session d'import.
 *
 * @param {string} sessionId - ID de la session
 *
 * @returns {Object} Query avec les détails complets
 *
 * @example
 * const { data: session } = useImportSessionDetails('abc-123-def');
 */
export function useImportSessionDetails(sessionId) {
  return useQuery({
    queryKey: ['import-session-details', sessionId],
    queryFn: () => fetchImportSessionDetails(sessionId),
    enabled: Boolean(sessionId),
    staleTime: 10_000,
  });
}
