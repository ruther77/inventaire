/**
 * Module de hooks pour les mutations du catalogue produits (création, modification, suppression).
 * @module hooks/useCatalogMutations
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  createProduct,
  updateProductRequest,
  deleteProductRequest,
} from '../api/client.js';

/**
 * Hook pour créer un nouveau produit dans le catalogue.
 *
 * Invalide automatiquement les caches des produits, inventaire, stock,
 * plan d'approvisionnement et tableau de bord après création réussie.
 * Affiche une notification toast de succès ou d'erreur.
 *
 * @returns {Object} Mutation TanStack pour la création de produit
 * @property {Function} mutate - Fonction pour créer le produit
 * @property {boolean} isLoading - Indique si la création est en cours
 *
 * @example
 * const createProduct = useCreateProduct();
 * createProduct.mutate({
 *   nom: 'Nouveau produit',
 *   prix: 10.50,
 *   categorie_id: 3
 * });
 */
export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      toast.success('Produit créé');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['stock'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: () => toast.error('Création impossible'),
  });
}

/**
 * Hook pour mettre à jour un produit existant.
 *
 * Permet de modifier toutes les propriétés d'un produit (nom, prix, stock, etc.).
 * Invalide automatiquement tous les caches liés aux produits et aux marges.
 *
 * @returns {Object} Mutation TanStack pour la mise à jour de produit
 * @property {Function} mutate - Fonction pour mettre à jour ({productId, payload})
 *
 * @example
 * const updateProduct = useUpdateProduct();
 * updateProduct.mutate({
 *   productId: 42,
 *   payload: { prix: 12.99, stock: 150 }
 * });
 */
export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, payload }) => updateProductRequest(productId, payload),
    onSuccess: () => {
      toast.success('Produit mis à jour');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['stock'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['margins'] });
    },
    onError: () => toast.error('Mise à jour impossible'),
  });
}

/**
 * Hook pour supprimer un produit du catalogue.
 *
 * Supprime définitivement le produit et toutes ses données associées.
 * Invalide automatiquement les caches pour refléter la suppression.
 *
 * @returns {Object} Mutation TanStack pour la suppression de produit
 * @property {Function} mutate - Fonction pour supprimer (productId)
 *
 * @example
 * const deleteProduct = useDeleteProduct();
 * deleteProduct.mutate(productId);
 */
export function useDeleteProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (productId) => deleteProductRequest(productId),
    onSuccess: () => {
      toast.success('Produit supprimé');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['stock'] });
      queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['margins'] });
    },
    onError: () => toast.error('Suppression impossible'),
  });
}
