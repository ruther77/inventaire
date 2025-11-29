import { useMutation, useQueryClient } from '@tanstack/react-query';
import { checkoutCart } from '../api/client.js';
import { toast } from 'sonner';

export function useCheckout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: checkoutCart,
    onSuccess: (response) => {
      if (response.success) {
        toast.success('Vente finalisée', {
          description: response.receipt_filename ?? 'Ticket généré',
        });
        queryClient.invalidateQueries({ queryKey: ['products'] });
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
