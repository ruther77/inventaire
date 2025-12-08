import { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Select from '../../../components/ui/Select.jsx';
import { useFinanceCategories } from '../../../hooks/useFinanceCategories.js';
import { updateTransactionCategory } from '../../../api/client.js';

/**
 * CategoryInlineEdit - Composant pour l'édition inline des catégories de transaction
 *
 * @param {number} transactionId - ID de la transaction
 * @param {number} currentCategoryId - ID de la catégorie actuelle
 * @param {string} currentCategoryName - Nom de la catégorie actuelle
 * @param {function} onUpdate - Callback après mise à jour (transactionId, newCategoryId)
 */
export default function CategoryInlineEdit({
  transactionId,
  currentCategoryId,
  currentCategoryName,
  onUpdate,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState(currentCategoryId);
  const selectRef = useRef(null);
  const queryClient = useQueryClient();

  // Récupérer les catégories disponibles
  const { data: categories = [], isLoading: categoriesLoading } = useFinanceCategories();

  // Mutation pour mettre à jour la catégorie
  const updateMutation = useMutation({
    mutationFn: ({ transactionId, categoryId }) =>
      updateTransactionCategory({ transactionId, categoryId }),
    onSuccess: (data, variables) => {
      // Invalider les queries pour rafraîchir les données
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'categories-stats'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'dashboard-summary'] });

      // Trouver le nom de la nouvelle catégorie
      const newCategory = categories.find((c) => c.id === variables.categoryId);
      const newCategoryName = newCategory?.label || newCategory?.name || 'Catégorie';

      // Toast de succès avec option Undo
      let undoToastId;
      const handleUndo = async () => {
        // Annuler le toast
        if (undoToastId) toast.dismiss(undoToastId);

        // Restaurer l'ancienne catégorie
        try {
          await updateTransactionCategory({
            transactionId: variables.transactionId,
            categoryId: currentCategoryId,
          });
          queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
          queryClient.invalidateQueries({ queryKey: ['finance', 'categories-stats'] });
          queryClient.invalidateQueries({ queryKey: ['finance', 'dashboard-summary'] });
          toast.success('Modification annulée');
          if (onUpdate) {
            onUpdate(variables.transactionId, currentCategoryId);
          }
        } catch (error) {
          toast.error('Erreur lors de l\'annulation');
        }
      };

      undoToastId = toast.success(
        `Catégorie mise à jour: ${newCategoryName}`,
        {
          action: {
            label: 'Annuler',
            onClick: handleUndo,
          },
          duration: 5000,
        }
      );

      // Appeler le callback onUpdate si fourni
      if (onUpdate) {
        onUpdate(variables.transactionId, variables.categoryId);
      }

      // Quitter le mode édition
      setIsEditing(false);
    },
    onError: (error) => {
      toast.error('Erreur lors de la mise à jour de la catégorie');
      console.error('Update category error:', error);
      // Restaurer la valeur précédente
      setSelectedCategoryId(currentCategoryId);
      setIsEditing(false);
    },
  });

  // Focus automatique sur le select en mode édition
  useEffect(() => {
    if (isEditing && selectRef.current) {
      selectRef.current.focus();
    }
  }, [isEditing]);

  // Handler pour le changement de catégorie
  const handleCategoryChange = (e) => {
    const newCategoryId = parseInt(e.target.value, 10);
    setSelectedCategoryId(newCategoryId);

    // Si la catégorie a changé, sauvegarder
    if (newCategoryId !== currentCategoryId) {
      updateMutation.mutate({
        transactionId,
        categoryId: newCategoryId,
      });
    } else {
      // Sinon, simplement quitter le mode édition
      setIsEditing(false);
    }
  };

  // Handler pour Escape (annuler)
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      setSelectedCategoryId(currentCategoryId);
      setIsEditing(false);
    }
  };

  // Handler pour le blur (perte de focus)
  const handleBlur = () => {
    // Si la valeur n'a pas changé, simplement quitter le mode édition
    if (selectedCategoryId === currentCategoryId) {
      setIsEditing(false);
    }
    // Sinon, le handleCategoryChange aura déjà été appelé
  };

  // Handler pour activer le mode édition
  const handleClick = () => {
    if (!isEditing) {
      setIsEditing(true);
    }
  };

  // Trouver le nom de la catégorie actuelle dans la liste
  const displayName = currentCategoryName || 'Non catégorisé';

  // Mode édition
  if (isEditing) {
    return (
      <Select
        ref={selectRef}
        value={selectedCategoryId || ''}
        onChange={handleCategoryChange}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        disabled={categoriesLoading || updateMutation.isPending}
        className="min-w-[180px]"
      >
        <option value="">-- Sélectionner --</option>
        {categories.map((category) => (
          <option key={category.id} value={category.id}>
            {category.label || category.name || `Catégorie ${category.id}`}
          </option>
        ))}
      </Select>
    );
  }

  // Mode lecture (affichage avec style cliquable)
  return (
    <button
      type="button"
      onClick={handleClick}
      className="group inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 transition-all hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-1"
      title="Cliquer pour modifier la catégorie"
    >
      <span>{displayName}</span>
      <svg
        className="h-3.5 w-3.5 opacity-0 transition-opacity group-hover:opacity-100"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
        />
      </svg>
    </button>
  );
}
