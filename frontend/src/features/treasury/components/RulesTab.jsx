import React, { useState } from 'react';
import { Plus, Trash2, Edit2, Tag, Check, X } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import Input from '../../../components/ui/Input.jsx';
import Select from '../../../components/ui/Select.jsx';
import Modal from '../../../components/ui/Modal.jsx';

export default function RulesTab({
  rules = [],
  categories = [],
  onCreate,
  onUpdate,
  onDelete,
  onRefresh,
  isLoading = false,
}) {
  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [form, setForm] = useState({
    name: '',
    keywords: '',
    category_id: '',
    is_active: true,
  });

  const openCreate = () => {
    setEditingRule(null);
    setForm({ name: '', keywords: '', category_id: '', is_active: true });
    setShowModal(true);
  };

  const openEdit = (rule) => {
    setEditingRule(rule);
    setForm({
      name: rule.name || '',
      keywords: (rule.keywords || []).join(', '),
      category_id: rule.category_id || '',
      is_active: rule.is_active !== false,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      name: form.name.trim(),
      keywords: form.keywords.split(',').map((k) => k.trim()).filter(Boolean),
      category_id: Number(form.category_id),
      is_active: form.is_active,
    };

    if (editingRule) {
      await onUpdate?.(editingRule.id, payload);
    } else {
      await onCreate?.(payload);
    }
    setShowModal(false);
  };

  const handleDelete = async (rule) => {
    if (window.confirm(`Supprimer la règle "${rule.name}" ?`)) {
      await onDelete?.(rule.id);
    }
  };

  const categoryById = categories.reduce((acc, cat) => {
    acc[cat.id] = cat;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Règles de catégorisation</h2>
          <p className="text-sm text-slate-500">
            Créez des règles pour catégoriser automatiquement vos transactions
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={onRefresh} disabled={isLoading}>
            Rafraîchir
          </Button>
          <Button variant="brand" onClick={openCreate} className="inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Nouvelle règle
          </Button>
        </div>
      </div>

      {/* Rules List */}
      <div className="grid gap-3 md:grid-cols-2">
        {rules.map((rule) => {
          const category = categoryById[rule.category_id];
          return (
            <Card key={rule.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-slate-900">{rule.name}</p>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                        rule.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {rule.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Catégorie : {category?.name || rule.category_name || `#${rule.category_id}`}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(rule.keywords || []).slice(0, 5).map((kw, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-xs text-slate-600"
                      >
                        <Tag className="w-3 h-3 mr-1" />
                        {kw}
                      </span>
                    ))}
                    {(rule.keywords || []).length > 5 && (
                      <span className="text-xs text-slate-400">
                        +{rule.keywords.length - 5} autres
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(rule)}>
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(rule)}>
                    <Trash2 className="w-4 h-4 text-rose-500" />
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}

        {rules.length === 0 && (
          <div className="col-span-full text-center py-12 text-slate-500">
            <Tag className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-semibold">Aucune règle configurée</p>
            <p className="text-sm mt-1">Créez votre première règle pour catégoriser automatiquement vos transactions</p>
          </div>
        )}
      </div>

      {/* Modal Create/Edit */}
      {showModal && (
        <Modal onClose={() => setShowModal(false)} title={editingRule ? 'Modifier la règle' : 'Nouvelle règle'}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nom de la règle</label>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Ex: Factures Metro"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Mots-clés</label>
              <Input
                value={form.keywords}
                onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                placeholder="metro, cash carry (séparés par virgule)"
              />
              <p className="text-xs text-slate-500 mt-1">
                Les transactions contenant ces mots seront catégorisées automatiquement
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Catégorie cible</label>
              <Select
                value={form.category_id}
                onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                required
              >
                <option value="">Sélectionner une catégorie</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name || cat.code}
                  </option>
                ))}
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                className="rounded border-slate-300"
              />
              <label htmlFor="is_active" className="text-sm text-slate-700">
                Règle active
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-200">
              <Button type="button" variant="ghost" onClick={() => setShowModal(false)}>
                Annuler
              </Button>
              <Button type="submit" variant="brand">
                {editingRule ? 'Enregistrer' : 'Créer'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
