import { useState, useMemo } from 'react';
import Modal from '../../../components/ui/Modal.jsx';
import Select from '../../../components/ui/Select.jsx';
import Input from '../../../components/ui/Input.jsx';
import { useFinanceCategories } from '../../../hooks/useFinanceCategories.js';
import { useFinanceBatchCategorize } from '../../../hooks/useFinance.js';

/**
 * BulkCategorizeModal - Modal pour recatégoriser plusieurs transactions en lot
 */
export default function BulkCategorizeModal({ isOpen, onClose, selectedIds, onConfirm }) {
  const [categoryId, setCategoryId] = useState('');
  const [createRule, setCreateRule] = useState(false);
  const [keywords, setKeywords] = useState('');
  const [error, setError] = useState('');

  const { data: categories = [], isLoading: categoriesLoading } = useFinanceCategories();
  const batchCategorize = useFinanceBatchCategorize();

  const selectedCount = selectedIds?.length || 0;

  // Reset state when modal closes
  const handleClose = () => {
    setCategoryId('');
    setCreateRule(false);
    setKeywords('');
    setError('');
    onClose();
  };

  const handleApply = async () => {
    setError('');

    if (!categoryId) {
      setError('Veuillez sélectionner une catégorie');
      return;
    }

    if (createRule && !keywords.trim()) {
      setError('Veuillez entrer des mots-clés pour la règle automatique');
      return;
    }

    const payload = {
      transaction_ids: selectedIds,
      category_id: parseInt(categoryId, 10),
    };

    if (createRule && keywords.trim()) {
      payload.create_rule = true;
      payload.keywords = keywords
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean);
    }

    try {
      await batchCategorize.mutateAsync(payload);

      if (onConfirm) {
        onConfirm(categoryId);
      }

      handleClose();
    } catch (err) {
      setError(err.message || 'Erreur lors de la recatégorisation');
    }
  };

  const categoriesOptions = useMemo(() => {
    if (!categories || categories.length === 0) return [];
    return categories.map((cat) => ({
      value: cat.id,
      label: cat.label || cat.name || `Catégorie ${cat.id}`,
    }));
  }, [categories]);

  return (
    <Modal
      open={isOpen}
      onClose={handleClose}
      title={`Recatégoriser ${selectedCount} transaction${selectedCount > 1 ? 's' : ''}`}
      description="Sélectionnez une catégorie et configurez éventuellement une règle automatique"
      size="md"
      actions={[
        {
          label: 'Annuler',
          variant: 'ghost',
          onClick: handleClose,
          disabled: batchCategorize.isLoading,
        },
        {
          label: 'Appliquer',
          variant: 'primary',
          onClick: handleApply,
          loading: batchCategorize.isLoading,
          disabled: !categoryId || batchCategorize.isLoading,
        },
      ]}
    >
      <div className="space-y-4">
        {/* Category Selection */}
        <div>
          <label htmlFor="category-select" className="block text-sm font-medium text-slate-700 mb-1.5">
            Catégorie <span className="text-rose-500">*</span>
          </label>
          <Select
            id="category-select"
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
            disabled={categoriesLoading || batchCategorize.isLoading}
          >
            <option value="">Sélectionnez une catégorie</option>
            {categoriesOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
          {categoriesLoading && (
            <p className="mt-1 text-xs text-slate-500">Chargement des catégories...</p>
          )}
        </div>

        {/* Auto Rule Checkbox */}
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            id="create-rule"
            checked={createRule}
            onChange={(e) => setCreateRule(e.target.checked)}
            disabled={batchCategorize.isLoading}
            className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
          />
          <label htmlFor="create-rule" className="flex-1 text-sm text-slate-700">
            <span className="font-medium">Créer une règle automatique</span>
            <p className="mt-0.5 text-xs text-slate-500">
              Les transactions futures contenant ces mots-clés seront automatiquement catégorisées
            </p>
          </label>
        </div>

        {/* Keywords Input - shown only if create rule is checked */}
        {createRule && (
          <div>
            <Input
              label="Mots-clés"
              placeholder="Ex: AMAZON, SPOTIFY, NETFLIX"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              hint="Séparez les mots-clés par des virgules"
              disabled={batchCategorize.isLoading}
              error={createRule && keywords.trim() === '' ? 'Requis pour la règle automatique' : ''}
            />
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">
            <p className="text-sm text-rose-700">{error}</p>
          </div>
        )}

        {/* Info Message */}
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
          <p className="text-sm text-blue-700">
            Cette action affectera {selectedCount} transaction{selectedCount > 1 ? 's' : ''}
          </p>
        </div>
      </div>
    </Modal>
  );
}
