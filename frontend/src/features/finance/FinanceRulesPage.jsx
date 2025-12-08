import React, { useMemo, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Input from '../../components/ui/Input.jsx';
import Select from '../../components/ui/Select.jsx';
import Modal, { ConfirmDialog } from '../../components/ui/Modal.jsx';
import Badge, { StatusBadge } from '../../components/ui/Badge.jsx';
import { Filter, Eye, Trash2, AlertCircle } from 'lucide-react';
import { useFinanceCategories, useFinanceRules, useFinanceRuleMutations } from '../../hooks/useFinanceCategories.js';
import { searchFinanceTransactions } from '../../api/client.js';

export default function FinanceRulesPage() {
  const [entityFilter, setEntityFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [form, setForm] = useState({ entity_id: '', category_id: '', name: '', keywords: '', apply_to_autre_only: true });
  const [testingRule, setTestingRule] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const catQuery = useFinanceCategories({});
  const rulesQuery = useFinanceRules({
    entityId: entityFilter || undefined,
    isActive: activeFilter === '' ? undefined : activeFilter === 'true',
  });
  const mutations = useFinanceRuleMutations();

  const categories = catQuery.data ?? [];
  const rules = rulesQuery.data ?? [];
  const categoryById = useMemo(() => {
    const map = new Map();
    categories.forEach((c) => map.set(c.id, c));
    return map;
  }, [categories]);

  // Live preview: search matching transactions for current keywords in form
  const keywords = form.keywords
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean);
  const previewQuery = keywords.join(' ');

  const { data: previewData } = useQuery({
    queryKey: ['finance', 'transaction-preview', previewQuery, form.entity_id],
    queryFn: () =>
      searchFinanceTransactions({
        q: previewQuery,
        entityId: form.entity_id || undefined,
        size: 1, // We only need the total count
        page: 1,
      }),
    enabled: previewQuery.length > 0 && modalOpen,
    staleTime: 2000,
  });

  const previewCount = previewData?.total ?? 0;

  const openCreate = () => {
    setEditingRule(null);
    setForm({ entity_id: '', category_id: '', name: '', keywords: '', apply_to_autre_only: true });
    setModalOpen(true);
  };

  const openEdit = (rule) => {
    setEditingRule(rule);
    setForm({
      entity_id: rule.entity_id,
      category_id: rule.category_id,
      name: rule.name,
      keywords: (rule.keywords || []).join(', '),
      apply_to_autre_only: rule.apply_to_autre_only,
    });
    setModalOpen(true);
  };

  const submitRule = () => {
    const payload = {
      entity_id: Number(form.entity_id),
      category_id: Number(form.category_id),
      name: form.name,
      keywords: form.keywords
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean),
      apply_to_autre_only: Boolean(form.apply_to_autre_only),
    };
    if (editingRule) {
      mutations.update.mutate(
        { id: editingRule.id, payload },
        { onSuccess: () => setModalOpen(false) },
      );
    } else {
      mutations.create.mutate(payload, { onSuccess: () => setModalOpen(false) });
    }
  };

  const handleDelete = (ruleId) => {
    mutations.remove.mutate(ruleId, {
      onSuccess: () => setDeleteConfirm(null),
    });
  };

  const openTestModal = (rule) => {
    setTestingRule(rule);
  };

  const closeTestModal = () => {
    setTestingRule(null);
  };

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Règles & catégories</p>
          <h1 className="text-2xl font-semibold text-slate-900">Gestion des règles</h1>
        </div>
        <Button variant="brand" onClick={openCreate}>
          Nouvelle règle
        </Button>
      </header>

      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            placeholder="Filtrer par entity_id"
            className="w-40"
          />
          <Select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)} className="w-40">
            <option value="">Actives + inactives</option>
            <option value="true">Actives</option>
            <option value="false">Inactives</option>
          </Select>
          <Button variant="ghost" onClick={() => rulesQuery.refetch()}>
            Rafraîchir
          </Button>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="px-3 py-2">Nom</th>
                <th className="px-3 py-2">Entity</th>
                <th className="px-3 py-2">Catégorie</th>
                <th className="px-3 py-2">Mots-clés</th>
                <th className="px-3 py-2 text-center">Transactions</th>
                <th className="px-3 py-2">Statut</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <RuleRow
                  key={r.id}
                  rule={r}
                  categoryById={categoryById}
                  onEdit={openEdit}
                  onTest={openTestModal}
                  onDelete={setDeleteConfirm}
                />
              ))}
              {rules.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                    Aucune règle
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal
        open={modalOpen}
        title={editingRule ? 'Modifier la règle' : 'Créer une règle'}
        onClose={() => setModalOpen(false)}
        actions={[
          { label: 'Annuler', onClick: () => setModalOpen(false) },
          { label: 'Enregistrer', variant: 'primary', onClick: submitRule },
        ]}
      >
        <div className="grid gap-3">
          <Input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Nom de la règle"
          />
          <div className="grid gap-2 md:grid-cols-2">
            <Input
              value={form.entity_id}
              onChange={(e) => setForm({ ...form, entity_id: e.target.value })}
              placeholder="Entity ID"
            />
            <Select
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            >
              <option value="">Catégorie</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name || cat.code}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1">
            <Input
              value={form.keywords}
              onChange={(e) => setForm({ ...form, keywords: e.target.value })}
              placeholder="Mots-clés (séparés par virgule)"
            />
            {form.keywords && (
              <div className="flex items-center gap-2 text-xs">
                {previewQuery ? (
                  <>
                    <Eye className="h-3.5 w-3.5 text-slate-400" />
                    <span className="text-slate-600">
                      <strong className="font-semibold text-brand-600">{previewCount}</strong>{' '}
                      transaction{previewCount > 1 ? 's' : ''} correspondante{previewCount > 1 ? 's' : ''}
                    </span>
                  </>
                ) : (
                  <span className="text-slate-400">Tapez des mots-clés pour voir la prévisualisation</span>
                )}
              </div>
            )}
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.apply_to_autre_only}
              onChange={(e) => setForm({ ...form, apply_to_autre_only: e.target.checked })}
            />
            Limiter aux lignes "autre"
          </label>
        </div>
      </Modal>

      {/* Test Rule Modal */}
      {testingRule && <TestRuleModal rule={testingRule} onClose={closeTestModal} />}

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteConfirm !== null}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => handleDelete(deleteConfirm)}
        title="Supprimer la règle"
        description="Êtes-vous sûr de vouloir supprimer cette règle ? Cette action est irréversible."
        confirmLabel="Supprimer"
        variant="destructive"
        loading={mutations.remove.isLoading}
      />
    </div>
  );
}

// RuleRow component with transaction count
function RuleRow({ rule, categoryById, onEdit, onTest, onDelete }) {
  const keywords = (rule.keywords || []).join(' ');

  const { data: matchData } = useQuery({
    queryKey: ['finance', 'rule-matches', rule.id, keywords, rule.entity_id, rule.category_id],
    queryFn: () =>
      searchFinanceTransactions({
        q: keywords,
        entityId: rule.entity_id || undefined,
        categoryId: rule.category_id || undefined,
        size: 1,
        page: 1,
      }),
    enabled: keywords.length > 0,
    staleTime: 60000, // Cache for 1 minute
  });

  const matchCount = matchData?.total ?? 0;

  return (
    <tr className="border-t border-slate-100 hover:bg-slate-50/50 transition-colors">
      <td className="px-3 py-2">
        <div className="font-semibold text-slate-900">{rule.name}</div>
      </td>
      <td className="px-3 py-2 text-slate-700">{rule.entity_id}</td>
      <td className="px-3 py-2 text-slate-700">
        {rule.category_name || categoryById.get(rule.category_id)?.name || rule.category_id}
      </td>
      <td className="px-3 py-2 text-slate-700">
        <div className="flex items-center gap-2">
          {(rule.keywords || []).length === 0 ? (
            <span className="text-slate-400">—</span>
          ) : (
            <span className="truncate max-w-xs">{(rule.keywords || []).join(', ')}</span>
          )}
          {rule.apply_to_autre_only && (
            <Badge variant="info" size="xs" title="Limité aux lignes 'autre'">
              <Filter className="h-3 w-3" />
            </Badge>
          )}
        </div>
      </td>
      <td className="px-3 py-2 text-center">
        {keywords ? (
          <Badge variant={matchCount > 0 ? 'brand' : 'default'} size="sm">
            {matchCount}
          </Badge>
        ) : (
          <span className="text-slate-400">—</span>
        )}
      </td>
      <td className="px-3 py-2">
        <StatusBadge status={rule.is_active ? 'active' : 'inactive'} size="sm" />
      </td>
      <td className="px-3 py-2 text-right">
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onTest(rule)}
            disabled={!keywords}
            title="Tester la règle"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onEdit(rule)}>
            Éditer
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(rule.id)}
            className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </td>
    </tr>
  );
}

// Test Rule Modal Component
function TestRuleModal({ rule, onClose }) {
  const keywords = (rule.keywords || []).join(' ');

  const { data, isLoading } = useQuery({
    queryKey: ['finance', 'rule-test', rule.id, keywords, rule.entity_id, rule.category_id],
    queryFn: () =>
      searchFinanceTransactions({
        q: keywords,
        entityId: rule.entity_id || undefined,
        categoryId: rule.category_id || undefined,
        size: 20,
        page: 1,
      }),
    enabled: keywords.length > 0,
  });

  const transactions = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <Modal
      open={true}
      onClose={onClose}
      title={`Test de la règle : ${rule.name}`}
      size="xl"
      actions={[{ label: 'Fermer', onClick: onClose }]}
    >
      <div className="space-y-3">
        <div className="flex items-center gap-3 text-sm">
          <Badge variant="brand">{total} transactions trouvées</Badge>
          {rule.apply_to_autre_only && (
            <Badge variant="info" size="sm">
              <Filter className="h-3 w-3 mr-1" />
              Limité aux lignes "autre"
            </Badge>
          )}
        </div>

        <div className="text-sm text-slate-600">
          <strong>Mots-clés :</strong> {(rule.keywords || []).join(', ')}
        </div>

        {isLoading ? (
          <div className="py-8 text-center text-slate-500">Chargement...</div>
        ) : transactions.length === 0 ? (
          <div className="py-8 text-center">
            <AlertCircle className="h-12 w-12 text-slate-300 mx-auto mb-2" />
            <p className="text-slate-500">Aucune transaction ne correspond à cette règle</p>
          </div>
        ) : (
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div className="max-h-96 overflow-y-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 sticky top-0">
                  <tr className="text-left text-slate-600">
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Libellé</th>
                    <th className="px-3 py-2 font-medium text-right">Montant</th>
                    <th className="px-3 py-2 font-medium">Catégorie</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 text-slate-700">
                        {new Date(tx.date_operation).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-3 py-2 text-slate-900">
                        <div className="max-w-md truncate">{tx.libelle}</div>
                        {tx.note && <div className="text-xs text-slate-500 truncate">{tx.note}</div>}
                      </td>
                      <td className="px-3 py-2 text-right font-mono">
                        <span className={tx.amount < 0 ? 'text-rose-600' : 'text-emerald-600'}>
                          {tx.amount?.toFixed(2)} €
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        {tx.category_name ? (
                          <Badge variant="default" size="sm">
                            {tx.category_name}
                          </Badge>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {total > 20 && (
              <div className="px-3 py-2 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 text-center">
                Affichage des 20 premiers résultats sur {total}
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
