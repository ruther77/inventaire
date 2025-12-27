/**
 * Module de hooks pour la finalisation des ventes en caisse (Point of Sale).
 * @module hooks/useCheckout
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { checkoutCart } from '../api/client.js';
import { toast } from 'sonner';

/**
 * Hook pour finaliser une vente au point de vente (checkout).
 *
 * Gère la transaction complète : validation du panier, génération du ticket,
 * mise à jour automatique du stock et invalidation des caches associés.
 * Affiche des notifications toast pour informer l'utilisateur du résultat.
 *
 * @returns {Object} Mutation TanStack pour le checkout
 * @property {Function} mutate - Fonction pour déclencher la vente
 * @property {Function} mutateAsync - Version async de mutate
 * @property {boolean} isLoading - Indique si la vente est en cours
 * @property {boolean} isSuccess - Indique si la vente a réussi
 * @property {Error} error - Erreur éventuelle
 *
 * @example
 * const checkout = useCheckout();
 * const handleCheckout = async () => {
 *   await checkout.mutateAsync(cartData);
 *   // Le stock et l'inventaire sont automatiquement rafraîchis
 * };
 */
export function useCheckout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: checkoutCart,
    onSuccess: (response) => {
      if (response.success) {
        toast.success('Vente finalisée', {
          description: response.receipt_filename ?? 'Ticket généré',
        });
        // Invalider toutes les données impactées par une vente
        queryClient.invalidateQueries({ queryKey: ['products'] });
        queryClient.invalidateQueries({ queryKey: ['inventory'] });
        queryClient.invalidateQueries({ queryKey: ['stock'] });
        queryClient.invalidateQueries({ queryKey: ['stock-timeseries'] });
        queryClient.invalidateQueries({ queryKey: ['stock-recent'] });
        queryClient.invalidateQueries({ queryKey: ['pos'] });
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        queryClient.invalidateQueries({ queryKey: ['supply-plan'] });
      } else {
        toast.error('Échec de la vente', {
          description: response.message ?? 'Veuillez réessayer',
        });
      }
    },
    onError: () => {
      toast.error('Impossible de joindre le serveur PoS.');
    },
  });
}
