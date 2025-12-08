/**
 * Tests pour CategoryInlineEdit
 *
 * Ce fichier contient des exemples de tests unitaires et d'intégration
 * pour le composant CategoryInlineEdit.
 *
 * Pour exécuter les tests:
 * npm run test CategoryInlineEdit.test.jsx
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import CategoryInlineEdit from './CategoryInlineEdit';
import * as apiClient from '../../../api/client';
import * as useFinanceCategoriesHook from '../../../hooks/useFinanceCategories';

// Mock des dépendances
vi.mock('../../../api/client');
vi.mock('../../../hooks/useFinanceCategories');
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  },
}));

// Helper pour wrapper avec React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('CategoryInlineEdit', () => {
  const mockCategories = [
    { id: 1, name: 'Fournitures', label: 'Fournitures' },
    { id: 2, name: 'Salaires', label: 'Salaires' },
    { id: 3, name: 'Loyer', label: 'Loyer' },
  ];

  beforeEach(() => {
    // Reset tous les mocks avant chaque test
    vi.clearAllMocks();

    // Mock du hook useFinanceCategories
    vi.spyOn(useFinanceCategoriesHook, 'useFinanceCategories').mockReturnValue({
      data: mockCategories,
      isLoading: false,
      error: null,
    });

    // Mock de l'API updateTransactionCategory
    vi.spyOn(apiClient, 'updateTransactionCategory').mockResolvedValue({
      success: true,
    });
  });

  describe('Mode Lecture', () => {
    it('affiche le nom de la catégorie actuelle', () => {
      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Fournitures')).toBeInTheDocument();
    });

    it('affiche "Non catégorisé" si pas de catégorie', () => {
      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={null}
          currentCategoryName={null}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Non catégorisé')).toBeInTheDocument();
    });

    it('affiche l\'icône de modification au survol', () => {
      const { container } = render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByRole('button');
      expect(button).toHaveClass('group');

      // Vérifier que l'icône SVG est présente
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('passe en mode édition au click', () => {
      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Vérifier qu'un select est maintenant affiché
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('Mode Édition', () => {
    it('affiche toutes les catégories disponibles', async () => {
      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition
      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Vérifier que toutes les catégories sont dans le select
      await waitFor(() => {
        expect(screen.getByText('Fournitures')).toBeInTheDocument();
        expect(screen.getByText('Salaires')).toBeInTheDocument();
        expect(screen.getByText('Loyer')).toBeInTheDocument();
      });
    });

    it('sélectionne la catégorie actuelle par défaut', async () => {
      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={2}
          currentCategoryName="Salaires"
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition
      fireEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        const select = screen.getByRole('combobox');
        expect(select).toHaveValue('2');
      });
    });

    it('annule avec Escape', async () => {
      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition
      fireEvent.click(screen.getByRole('button'));

      const select = screen.getByRole('combobox');

      // Appuyer sur Escape
      fireEvent.keyDown(select, { key: 'Escape' });

      // Vérifier qu'on est revenu en mode lecture
      await waitFor(() => {
        expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
        expect(screen.getByRole('button')).toBeInTheDocument();
      });
    });

    it('sauvegarde lors du changement de catégorie', async () => {
      const onUpdate = vi.fn();

      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
          onUpdate={onUpdate}
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition
      fireEvent.click(screen.getByRole('button'));

      const select = screen.getByRole('combobox');

      // Changer la catégorie
      fireEvent.change(select, { target: { value: '3' } });

      // Vérifier que l'API a été appelée
      await waitFor(() => {
        expect(apiClient.updateTransactionCategory).toHaveBeenCalledWith({
          transactionId: 1,
          categoryId: 3,
        });
      });

      // Vérifier que le callback a été appelé
      await waitFor(() => {
        expect(onUpdate).toHaveBeenCalledWith(1, 3);
      });
    });

    it('ne sauvegarde pas si la catégorie n\'a pas changé', async () => {
      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition
      fireEvent.click(screen.getByRole('button'));

      const select = screen.getByRole('combobox');

      // Sélectionner la même catégorie
      fireEvent.change(select, { target: { value: '1' } });

      // Vérifier que l'API n'a PAS été appelée
      expect(apiClient.updateTransactionCategory).not.toHaveBeenCalled();
    });
  });

  describe('Gestion des erreurs', () => {
    it('affiche un toast d\'erreur en cas d\'échec', async () => {
      const { toast } = await import('sonner');

      // Mock d'une erreur API
      vi.spyOn(apiClient, 'updateTransactionCategory').mockRejectedValue(
        new Error('Network error')
      );

      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition et changer
      fireEvent.click(screen.getByRole('button'));
      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: '2' } });

      // Vérifier que le toast d'erreur a été affiché
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining('Erreur')
        );
      });
    });

    it('restaure la valeur précédente en cas d\'erreur', async () => {
      vi.spyOn(apiClient, 'updateTransactionCategory').mockRejectedValue(
        new Error('Network error')
      );

      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition et changer
      fireEvent.click(screen.getByRole('button'));
      fireEvent.change(screen.getByRole('combobox'), { target: { value: '2' } });

      // Attendre l'erreur et vérifier qu'on est revenu en mode lecture
      await waitFor(() => {
        expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
      });

      // Vérifier qu'on affiche toujours l'ancienne catégorie
      expect(screen.getByText('Fournitures')).toBeInTheDocument();
    });
  });

  describe('Loading states', () => {
    it('désactive le select pendant le chargement des catégories', () => {
      vi.spyOn(useFinanceCategoriesHook, 'useFinanceCategories').mockReturnValue({
        data: [],
        isLoading: true,
        error: null,
      });

      render(
        <CategoryInlineEdit
          transactionId={1}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
        />,
        { wrapper: createWrapper() }
      );

      // Passer en mode édition
      fireEvent.click(screen.getByRole('button'));

      const select = screen.getByRole('combobox');
      expect(select).toBeDisabled();
    });
  });

  describe('Callback onUpdate', () => {
    it('appelle onUpdate avec les bons paramètres', async () => {
      const onUpdate = vi.fn();

      render(
        <CategoryInlineEdit
          transactionId={123}
          currentCategoryId={1}
          currentCategoryName="Fournitures"
          onUpdate={onUpdate}
        />,
        { wrapper: createWrapper() }
      );

      // Changer la catégorie
      fireEvent.click(screen.getByRole('button'));
      fireEvent.change(screen.getByRole('combobox'), { target: { value: '2' } });

      await waitFor(() => {
        expect(onUpdate).toHaveBeenCalledWith(123, 2);
      });
    });

    it('fonctionne sans callback onUpdate', async () => {
      // Ne devrait pas crasher sans callback
      expect(() => {
        render(
          <CategoryInlineEdit
            transactionId={1}
            currentCategoryId={1}
            currentCategoryName="Fournitures"
          />,
          { wrapper: createWrapper() }
        );
      }).not.toThrow();
    });
  });
});

/**
 * Tests d'intégration
 */
describe('CategoryInlineEdit - Tests d\'intégration', () => {
  it('workflow complet: affichage → édition → sauvegarde → toast', async () => {
    const { toast } = await import('sonner');
    const onUpdate = vi.fn();

    render(
      <CategoryInlineEdit
        transactionId={1}
        currentCategoryId={1}
        currentCategoryName="Fournitures"
        onUpdate={onUpdate}
      />,
      { wrapper: createWrapper() }
    );

    // 1. Affichage initial
    expect(screen.getByText('Fournitures')).toBeInTheDocument();

    // 2. Click pour éditer
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('combobox')).toBeInTheDocument();

    // 3. Changement de catégorie
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '2' } });

    // 4. Vérifier l'appel API
    await waitFor(() => {
      expect(apiClient.updateTransactionCategory).toHaveBeenCalled();
    });

    // 5. Vérifier le toast de succès
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalled();
    });

    // 6. Vérifier le callback
    expect(onUpdate).toHaveBeenCalledWith(1, 2);
  });
});
