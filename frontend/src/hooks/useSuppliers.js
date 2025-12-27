/**
 * Module de hooks pour la gestion des fournisseurs.
 *
 * Ce module fournit:
 * - La liste paginée des fournisseurs avec filtres
 * - Les détails d'un fournisseur
 * - Les opérations CRUD (création, modification, suppression)
 * - La gestion automatique des toasts et invalidations de cache
 *
 * @module hooks/useSuppliers
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  fetchSuppliers,
  fetchSupplier,
  createSupplier,
  updateSupplier,
  deleteSupplier,
} from '../api/client.js';

/**
 * Hook pour récupérer la liste paginée des fournisseurs.
 *
 * @param {Object} params - Paramètres de recherche et filtrage
 * @param {number} [params.page] - Numéro de page
 * @param {number} [params.per_page] - Nombre de résultats par page
 * @param {string} [params.q] - Recherche textuelle (nom, email, téléphone)
 * @param {boolean} [params.active] - Filtrer par statut actif
 *
 * @returns {Object} Query avec la liste des fournisseurs
 *
 * @example
 * const { data: suppliers, isLoading } = useSuppliers({ active: true });
 *
 * suppliers?.forEach(supplier => {
 *   console.log(supplier.name, supplier.email, supplier.total_orders);
 * });
 */
export function useSuppliers(params = {}) {
  return useQuery({
    queryKey: ['suppliers', params],
    queryFn: () => fetchSuppliers(params),
    staleTime: 30_000, // 30 secondes
  });
}

/**
 * Hook pour récupérer les détails d'un fournisseur.
 *
 * Retourne les informations complètes incluant:
 * - Coordonnées et contacts
 * - Historique des commandes
 * - Statistiques (nombre de factures, montant total, délais moyens)
 * - Produits fournis
 *
 * @param {number} id - ID du fournisseur
 *
 * @returns {Object} Query avec les détails du fournisseur
 *
 * @example
 * const { data: supplier } = useSupplier(42);
 *
 * return (
 *   <div>
 *     <h1>{supplier.name}</h1>
 *     <p>Email: {supplier.email}</p>
 *     <p>Total commandes: {supplier.total_orders}</p>
 *     <p>Délai moyen: {supplier.avg_delivery_days} jours</p>
 *   </div>
 * );
 */
export function useSupplier(id) {
  return useQuery({
    queryKey: ['supplier', id],
    queryFn: () => fetchSupplier(id),
    enabled: !!id, // Ne charge que si un ID est fourni
    staleTime: 30_000,
  });
}

/**
 * Hook pour créer un nouveau fournisseur.
 *
 * Affiche automatiquement un toast de succès/erreur et invalide
 * le cache de la liste des fournisseurs.
 *
 * @returns {Object} Mutation de création
 *
 * @example
 * const { mutate: createNewSupplier, isPending } = useCreateSupplier();
 *
 * const handleSubmit = (formData) => {
 *   createNewSupplier({
 *     name: formData.name,
 *     email: formData.email,
 *     phone: formData.phone,
 *     address: formData.address
 *   });
 * };
 */
export function useCreateSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createSupplier,
    onSuccess: () => {
      toast.success('Fournisseur créé avec succès');
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || 'Erreur lors de la création';
      toast.error(message);
    },
  });
}

/**
 * Hook pour mettre à jour un fournisseur existant.
 *
 * Affiche automatiquement un toast de succès/erreur et invalide
 * le cache du fournisseur et de la liste.
 *
 * @returns {Object} Mutation de mise à jour
 *
 * @example
 * const { mutate: updateExistingSupplier } = useUpdateSupplier();
 *
 * const handleUpdate = (id, changes) => {
 *   updateExistingSupplier({
 *     id,
 *     data: {
 *       email: 'nouveau@email.com',
 *       phone: '0123456789'
 *     }
 *   });
 * };
 */
export function useUpdateSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => updateSupplier(id, data),
    onSuccess: (_, variables) => {
      toast.success('Fournisseur mis à jour');
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      queryClient.invalidateQueries({ queryKey: ['supplier', variables.id] });
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || 'Erreur lors de la mise à jour';
      toast.error(message);
    },
  });
}

/**
 * Hook pour supprimer un fournisseur.
 *
 * Attention: la suppression peut être refusée si le fournisseur
 * a des factures ou commandes liées.
 *
 * @returns {Object} Mutation de suppression
 *
 * @example
 * const { mutate: deleteExistingSupplier } = useDeleteSupplier();
 *
 * const handleDelete = (id) => {
 *   if (confirm('Supprimer ce fournisseur ?')) {
 *     deleteExistingSupplier(id);
 *   }
 * };
 */
export function useDeleteSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteSupplier,
    onSuccess: () => {
      toast.success('Fournisseur supprimé');
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
    },
    onError: (error) => {
      const message = error?.response?.data?.detail || 'Erreur lors de la suppression';
      toast.error(message);
    },
  });
}
