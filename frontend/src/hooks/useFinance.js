/**
 * Module de hooks pour la gestion des finances et de la trésorerie.
 *
 * Ce module fournit tous les hooks nécessaires pour gérer:
 * - Les transactions bancaires (recherche, pagination infinie, filtres)
 * - La catégorisation automatique et manuelle des transactions
 * - Les règles de catégorisation et suggestions IA
 * - Le rapprochement bancaire (réconciliation)
 * - Les comptes bancaires
 * - La détection d'anomalies
 * - Le feedback machine learning pour améliorer les prédictions
 * - L'import de relevés bancaires (CSV, PDF)
 *
 * @module hooks/useFinance
 */
import { useMemo } from 'react';
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  useOfflineCreate,
  useOfflineUpdate,
  useOfflineDelete,
} from './useOfflineMutation.js';
import {
  searchFinanceTransactions,
  suggestFinanceAutreTop,
  autocompleteFinanceCategories,
  batchCategorizeFinanceTransactions,
  updateFinanceTransaction,
  lockFinanceTransaction,
  importFinanceBankStatements,
  importFinanceBankStatementsPDF,
  runFinanceReconciliation,
  refreshFinanceAnomalies,
  fetchFinanceAnomalies,
  updateFinanceMatchStatus,
  fetchFinanceMatches,
  fetchFinanceAccounts,
  getFinanceAccount,
  createFinanceAccount,
  updateFinanceAccount,
  deleteFinanceAccount,
  deduplicateFinanceTransactions,
  refreshFinanceStats,
  // Phase 4: Feedback catégorisation
  recordCategoryFeedback,
  fetchCategoryFeedbackStats,
  fetchCommonCorrections,
} from '../api/client';

/**
 * Hook de recherche et pagination infinie des transactions bancaires.
 *
 * Permet de charger les transactions par pages successives avec défilement infini.
 * Les filtres sont stabilisés en mémoire pour éviter les re-renders inutiles.
 *
 * @param {Object} filters - Filtres de recherche
 * @param {number} [filters.entityId] - ID de l'entité/tenant
 * @param {number} [filters.accountId] - ID du compte bancaire
 * @param {number} [filters.categoryId] - ID de la catégorie
 * @param {string} [filters.dateFrom] - Date de début (YYYY-MM-DD)
 * @param {string} [filters.dateTo] - Date de fin (YYYY-MM-DD)
 * @param {number} [filters.amountMin] - Montant minimum
 * @param {number} [filters.amountMax] - Montant maximum
 * @param {string} [filters.q] - Recherche textuelle (libellé, référence)
 * @param {number} [filters.size=100] - Nombre d'éléments par page
 *
 * @returns {Object} Résultat de la query infinie
 * @property {Array} data.pages - Pages de transactions chargées
 * @property {Function} fetchNextPage - Charge la page suivante
 * @property {boolean} hasNextPage - Indique s'il reste des pages
 * @property {boolean} isFetchingNextPage - Indique si la page suivante charge
 * @property {boolean} isLoading - Indique si le premier chargement est en cours
 *
 * @example
 * const { data, fetchNextPage, hasNextPage } = useFinanceTransactions({
 *   accountId: 42,
 *   dateFrom: '2025-01-01',
 *   categoryId: null,
 *   q: 'AMAZON'
 * });
 *
 * // Afficher toutes les transactions de toutes les pages
 * const allTransactions = data?.pages.flatMap(page => page.items) || [];
 */
export const useFinanceTransactions = (filters = {}) => {
  // Stabiliser les valeurs des filtres pour éviter les re-renders inutiles
  const { entityId, accountId, categoryId, dateFrom, dateTo, amountMin, amountMax, q, size: filterSize } = filters;
  const size = filterSize || 100;

  // Créer une clé stable basée sur les valeurs primitives (pas l'objet)
  const queryKey = useMemo(
    () => ['finance', 'transactions', { entityId, accountId, categoryId, dateFrom, dateTo, amountMin, amountMax, q, size }],
    [entityId, accountId, categoryId, dateFrom, dateTo, amountMin, amountMax, q, size]
  );

  return useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam = 1 }) => searchFinanceTransactions({ ...filters, page: pageParam, size }),
    getNextPageParam: (lastPage) => {
      const total = lastPage?.total ?? 0;
      const page = lastPage?.page ?? 1;
      const sz = lastPage?.size ?? size;
      const maxPage = Math.ceil(total / sz);
      return page < maxPage ? page + 1 : undefined;
    },
    placeholderData: (previousData) => previousData,
  });
};

/**
 * Hook pour obtenir les suggestions de catégories "Autre" les plus fréquentes.
 *
 * Retourne les libellés "Autre" les plus utilisés pour aider à créer
 * de nouvelles catégories ou règles de catégorisation automatique.
 *
 * @param {Object} params - Paramètres de la requête
 * @param {number} [params.limit=10] - Nombre maximum de suggestions
 *
 * @returns {Object} Query avec les suggestions triées par fréquence
 *
 * @example
 * const { data: suggestions } = useFinanceAutreSuggestions({ limit: 20 });
 * // suggestions = [{ label: 'AMAZON', count: 45 }, ...]
 */
export const useFinanceAutreSuggestions = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'autre-top', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => suggestFinanceAutreTop(params),
    staleTime: 5 * 60 * 1000, // 5 minutes - les suggestions changent peu
  });
};

/**
 * Hook d'autocomplétion pour les catégories de dépenses.
 *
 * Recherche des catégories correspondant à la saisie utilisateur
 * pour faciliter la sélection dans les formulaires.
 *
 * @param {Object} params - Paramètres de recherche
 * @param {string} params.q - Texte de recherche (minimum 1 caractère)
 * @param {number} [params.limit=10] - Nombre max de résultats
 *
 * @returns {Object} Query avec la liste des catégories correspondantes
 *
 * @example
 * const { data: categories } = useFinanceCategoriesAutocomplete({ q: 'fourni' });
 * // categories = [{ id: 5, name: 'Fournitures bureau' }, ...]
 */
export const useFinanceCategoriesAutocomplete = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'categories-autocomplete', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => autocompleteFinanceCategories(params),
    enabled: !!params.q, // N'exécute que si une recherche est saisie
    staleTime: 30 * 1000, // 30 secondes pour l'autocomplete
  });
};

/**
 * Hook de catégorisation en masse de transactions.
 *
 * Permet de catégoriser plusieurs transactions d'un coup selon des critères
 * communs (même libellé, même montant, même période, etc.).
 * Supporte le mode offline avec mise en queue des mutations.
 *
 * @returns {Object} Mutation de catégorisation en masse
 * @property {Function} mutate - Fonction pour lancer la catégorisation
 * @property {boolean} isPending - Indique si la mutation est en cours
 * @property {boolean} isSuccess - Indique si la mutation a réussi
 *
 * @example
 * const { mutate: batchCategorize } = useFinanceBatchCategorize();
 *
 * // Catégoriser toutes les transactions Amazon en "Fournitures"
 * batchCategorize({
 *   filters: { q: 'AMAZON' },
 *   categoryId: 5
 * });
 */
export const useFinanceBatchCategorize = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: '/finance/transactions/batch-categorize',
    mutationFn: batchCategorizeFinanceTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'autre-top'] });
    },
    metadata: {
      description: 'Catégorisation en masse de transactions',
    },
  });
};

/**
 * Hook de mise à jour d'une transaction bancaire.
 *
 * Permet de modifier une transaction (catégorie, montant, libellé, etc.)
 * avec mise à jour optimiste de l'UI et rollback automatique en cas d'erreur.
 * Supporte le mode offline avec synchronisation différée.
 *
 * @returns {Object} Mutation de mise à jour
 * @property {Function} mutate - Fonction de mise à jour
 * @property {boolean} isPending - Indique si la mutation est en cours
 *
 * @example
 * const { mutate: updateTransaction } = useUpdateFinanceTransaction();
 *
 * updateTransaction({
 *   transactionId: 123,
 *   payload: {
 *     category_id: 5,
 *     autre: 'Fournitures bureau - Amazon'
 *   }
 * });
 */
export const useUpdateFinanceTransaction = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: (variables) => `/finance/transactions/${variables.transactionId}`,
    mutationFn: updateFinanceTransaction,
    onMutate: async ({ transactionId, payload }) => {
      // Annuler les refetch en cours pour éviter les conflits
      await queryClient.cancelQueries({ queryKey: ['finance', 'transactions'] });

      // Sauvegarder l'état actuel pour rollback éventuel
      const previousData = queryClient.getQueriesData({ queryKey: ['finance', 'transactions'] });

      // Mise à jour optimiste: appliquer immédiatement le changement dans l'UI
      queryClient.setQueriesData({ queryKey: ['finance', 'transactions'] }, (old) => {
        if (!old?.pages) return old;

        return {
          ...old,
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items?.map((tx) =>
              tx.id === transactionId || tx.transaction_id === transactionId
                ? { ...tx, ...payload }
                : tx
            ),
          })),
        };
      });

      return { previousData };
    },
    onError: (err, variables, context) => {
      // Rollback: restaurer l'état précédent si erreur
      if (context?.previousData) {
        context.previousData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      // Rafraîchir les données pour synchroniser avec le serveur
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'autre-top'] });
    },
    metadata: {
      description: 'Mise à jour d\'une transaction',
    },
  });
};

/**
 * Hook pour verrouiller une transaction bancaire.
 *
 * Une transaction verrouillée ne peut plus être modifiée automatiquement
 * par les règles de catégorisation ou les jobs de réconciliation.
 *
 * @returns {Object} Mutation de verrouillage
 *
 * @example
 * const { mutate: lockTransaction } = useLockFinanceTransaction();
 * lockTransaction({ transactionId: 123, locked: true });
 */
export const useLockFinanceTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: lockFinanceTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
    },
  });
};

/**
 * Hook d'import de relevés bancaires au format CSV.
 *
 * Permet d'importer des transactions depuis un fichier CSV fourni par la banque.
 * Les transactions sont automatiquement parsées et catégorisées via l'IA.
 *
 * @returns {Object} Mutation d'import CSV
 *
 * @example
 * const { mutate: importCSV, isPending } = useFinanceImport();
 *
 * importCSV({
 *   file: csvFile,
 *   accountId: 42,
 *   format: 'bnp_paribas'
 * });
 */
export const useFinanceImport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importFinanceBankStatements,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
    },
  });
};

/**
 * Hook d'import de relevés bancaires au format PDF.
 *
 * Utilise l'OCR pour extraire les transactions depuis un PDF de relevé bancaire.
 * Plus flexible que le CSV mais potentiellement moins précis.
 *
 * @returns {Object} Mutation d'import PDF
 *
 * @example
 * const { mutate: importPDF } = useFinanceImportPDF();
 *
 * importPDF({
 *   file: pdfFile,
 *   accountId: 42
 * });
 */
export const useFinanceImportPDF = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importFinanceBankStatementsPDF,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'imports'] });
    },
  });
};

/**
 * Hook pour lancer le rapprochement bancaire (réconciliation).
 *
 * Compare les transactions bancaires avec les factures/achats et détecte:
 * - Les transactions sans facture correspondante
 * - Les factures non payées
 * - Les montants qui ne correspondent pas
 * - Les doublons potentiels
 *
 * @returns {Object} Mutation de réconciliation
 *
 * @example
 * const { mutate: reconcile, isPending } = useFinanceReconciliation();
 * reconcile({ accountId: 42, dateFrom: '2025-01-01', dateTo: '2025-01-31' });
 */
export const useFinanceReconciliation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runFinanceReconciliation,
    onSuccess: () => {
      // Rafraîchir toutes les données impactées par la réconciliation
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'matches'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'anomalies'] });
      queryClient.invalidateQueries({ queryKey: ['bank-reconciliation'] });
    },
  });
};

/**
 * Hook pour récupérer les anomalies financières détectées.
 *
 * Les anomalies incluent: doublons, montants suspects, transactions non catégorisées,
 * écarts de réconciliation, etc.
 *
 * @param {Object} params - Paramètres de filtrage
 * @param {string} [params.severity] - Niveau de sévérité (low, medium, high, critical)
 *
 * @returns {Object} Query avec la liste des anomalies
 *
 * @example
 * const { data: anomalies } = useFinanceAnomalies({ severity: 'high' });
 */
export const useFinanceAnomalies = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'anomalies', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceAnomalies(params.severity),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook pour rafraîchir la détection d'anomalies.
 *
 * Lance une nouvelle analyse complète des transactions pour détecter
 * les anomalies récentes.
 *
 * @returns {Object} Mutation de rafraîchissement
 *
 * @example
 * const { mutate: refreshAnomalies, isPending } = useFinanceRefreshAnomalies();
 * refreshAnomalies();
 */
export const useFinanceRefreshAnomalies = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshFinanceAnomalies,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'anomalies'] });
      queryClient.invalidateQueries({ queryKey: ['anomaly-detection'] });
    },
  });
};

/**
 * Hook pour mettre à jour le statut d'un match de réconciliation.
 *
 * Permet de valider ou rejeter un match proposé entre une transaction
 * bancaire et une facture/achat.
 *
 * @returns {Object} Mutation de mise à jour du match
 *
 * @example
 * const { mutate: updateMatch } = useFinanceMatchStatus();
 *
 * // Valider un match
 * updateMatch({ matchId: 123, status: 'validated' });
 *
 * // Rejeter un match
 * updateMatch({ matchId: 124, status: 'rejected' });
 */
export const useFinanceMatchStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateFinanceMatchStatus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'matches'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['bank-reconciliation'] });
    },
  });
};

/**
 * Hook pour récupérer les matches de réconciliation.
 *
 * Retourne les associations proposées entre transactions bancaires
 * et factures/achats avec leur score de confiance.
 *
 * @param {Object} params - Paramètres de filtrage
 * @param {string} [params.status] - Statut (pending, validated, rejected)
 *
 * @returns {Object} Query avec la liste des matches
 *
 * @example
 * const { data: matches } = useFinanceMatches({ status: 'pending' });
 */
export const useFinanceMatches = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'matches', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceMatches(params.status),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// ============================================================================
// GESTION DES COMPTES BANCAIRES
// ============================================================================

/**
 * Hook pour récupérer la liste des comptes bancaires.
 *
 * @param {Object} params - Paramètres de filtrage
 * @param {number} [params.entityId] - ID de l'entité/tenant
 * @param {boolean} [params.active] - Filtrer par statut actif
 *
 * @returns {Object} Query avec la liste des comptes
 *
 * @example
 * const { data: accounts } = useFinanceAccounts({ active: true });
 */
export const useFinanceAccounts = (params = {}) => {
  const queryKey = useMemo(() => ['finance', 'accounts', params], [params]);
  return useQuery({
    queryKey,
    queryFn: () => fetchFinanceAccounts(params),
    staleTime: 5 * 60 * 1000, // 5 minutes - les comptes changent rarement
  });
};

/**
 * Hook pour récupérer les détails d'un compte bancaire.
 *
 * @param {number} accountId - ID du compte à charger
 *
 * @returns {Object} Query avec les détails du compte
 *
 * @example
 * const { data: account } = useFinanceAccount(42);
 */
export const useFinanceAccount = (accountId) => {
  return useQuery({
    queryKey: ['finance', 'account', accountId],
    queryFn: () => getFinanceAccount(accountId),
    enabled: !!accountId, // Ne charge que si l'ID est fourni
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook pour créer un nouveau compte bancaire.
 *
 * @returns {Object} Mutation de création
 *
 * @example
 * const { mutate: createAccount } = useCreateFinanceAccount();
 *
 * createAccount({
 *   name: 'Compte courant professionnel',
 *   bank: 'BNP Paribas',
 *   iban: 'FR76...',
 *   currency: 'EUR'
 * });
 */
export const useCreateFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useOfflineCreate({
    endpoint: '/finance/accounts',
    mutationFn: createFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
    },
    metadata: {
      description: 'Création d\'un compte bancaire',
    },
  });
};

/**
 * Hook pour mettre à jour un compte bancaire existant.
 *
 * @returns {Object} Mutation de mise à jour
 *
 * @example
 * const { mutate: updateAccount } = useUpdateFinanceAccount();
 *
 * updateAccount({
 *   accountId: 42,
 *   name: 'Nouveau nom du compte',
 *   active: false
 * });
 */
export const useUpdateFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useOfflineUpdate({
    endpoint: (variables) => `/finance/accounts/${variables.accountId}`,
    mutationFn: updateFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'account'] });
    },
    metadata: {
      description: 'Mise à jour d\'un compte bancaire',
    },
  });
};

/**
 * Hook pour supprimer un compte bancaire.
 *
 * @returns {Object} Mutation de suppression
 *
 * @example
 * const { mutate: deleteAccount } = useDeleteFinanceAccount();
 * deleteAccount(42);
 */
export const useDeleteFinanceAccount = () => {
  const queryClient = useQueryClient();
  return useOfflineDelete({
    endpoint: (variables) => `/finance/accounts/${variables}`,
    mutationFn: deleteFinanceAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'accounts'] });
    },
    metadata: {
      description: 'Suppression d\'un compte bancaire',
    },
  });
};

// ============================================================================
// DÉDUPLICATION & STATISTIQUES
// ============================================================================

/**
 * Hook pour détecter et supprimer les transactions en double.
 *
 * Identifie les transactions avec même montant, date et référence
 * puis supprime automatiquement les doublons.
 *
 * @returns {Object} Mutation de déduplication
 *
 * @example
 * const { mutate: deduplicate, isPending } = useDeduplicateTransactions();
 * deduplicate({ accountId: 42 });
 */
export const useDeduplicateTransactions = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deduplicateFinanceTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'imports'] });
    },
  });
};

/**
 * Hook pour recalculer les statistiques financières.
 *
 * Régénère les agrégations, totaux, moyennes et KPIs financiers
 * à partir des transactions.
 *
 * @returns {Object} Mutation de rafraîchissement
 *
 * @example
 * const { mutate: refreshStats } = useRefreshFinanceStats();
 * refreshStats();
 */
export const useRefreshFinanceStats = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshFinanceStats,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance'] });
    },
  });
};

// ============================================================================
// PHASE 4: FEEDBACK CATÉGORISATION (ML Learning Loop)
// ============================================================================

/**
 * Mutation pour enregistrer un feedback de correction de catégorie.
 * Utilisé quand un utilisateur corrige manuellement une catégorie prédite par l'IA.
 *
 * @example
 * const { mutate: recordFeedback } = useCategoryFeedback();
 * recordFeedback({
 *   transactionId: 123,
 *   payload: {
 *     actual_category_id: 5,
 *     predicted_category_id: 3,
 *     confidence_score: 0.85,
 *     correction_source: 'user_manual'
 *   }
 * });
 */
export const useCategoryFeedback = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ transactionId, payload }) => recordCategoryFeedback(transactionId, payload),
    onSuccess: () => {
      // Invalider les stats de feedback après enregistrement
      queryClient.invalidateQueries({ queryKey: ['finance', 'feedback'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
    },
  });
};

/**
 * Query pour récupérer les statistiques globales de feedback.
 * Retourne: total_corrections, unique_transactions, avg_wrong_confidence, etc.
 *
 * @example
 * const { data: stats, isLoading } = useCategoryFeedbackStats();
 * // stats = { total_corrections: 150, avg_wrong_confidence: 0.72, ... }
 */
export const useCategoryFeedbackStats = () => {
  return useQuery({
    queryKey: ['finance', 'feedback', 'stats'],
    queryFn: fetchCategoryFeedbackStats,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Query pour récupérer les patterns de correction les plus fréquents.
 * Utile pour créer des règles automatiques basées sur les corrections répétées.
 *
 * @param {number} limit - Nombre max de patterns à retourner (défaut: 10)
 *
 * @example
 * const { data: corrections } = useCommonCorrections(20);
 * // corrections = [{ from_category: 'Autre', to_category: 'Fournitures', count: 45 }, ...]
 */
export const useCommonCorrections = (limit = 10) => {
  const queryKey = useMemo(() => ['finance', 'feedback', 'common-corrections', limit], [limit]);
  return useQuery({
    queryKey,
    queryFn: () => fetchCommonCorrections(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
