import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  createProduct,
  updateProductRequest,
  deleteProductRequest,
} from '../api/client.js';

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      toast.success('Produit créé');
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: () => toast.error('Création impossible'),
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, payload }) => updateProductRequest(productId, payload),
    onSuccess: () => {
      toast.success('Produit mis à jour');
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: () => toast.error('Mise à jour impossible'),
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (productId) => deleteProductRequest(productId),
    onSuccess: () => {
      toast.success('Produit supprimé');
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: () => toast.error('Suppression impossible'),
  });
}
