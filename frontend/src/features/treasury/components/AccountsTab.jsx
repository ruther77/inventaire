import React, { useState } from 'react';
import { Wallet, ArrowDownCircle, ArrowUpCircle, Plus, Settings, X, Trash2 } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import { roundAmount } from '../../../utils/banking.js';
import { useClickOutsideAndEscape } from '../../../hooks/useClickOutside.js';
import {
  useCreateFinanceAccount,
  useUpdateFinanceAccount,
  useDeleteFinanceAccount,
} from '../../../hooks/useFinance.js';

const ACCOUNT_STATUS_STYLES = {
  connected: 'bg-emerald-500/20 text-emerald-400',
  error: 'bg-rose-500/20 text-rose-400',
  warning: 'bg-amber-500/20 text-amber-400',
  disconnected: 'bg-white/10 text-slate-400',
  disabled: 'bg-white/10 text-slate-500',
};

const StatusBadge = ({ status }) => {
  const base = ACCOUNT_STATUS_STYLES[status] || 'bg-white/10 text-slate-400';
  const labels = {
    connected: 'Connecté',
    error: 'Erreur',
    warning: 'Attention',
    disconnected: 'Déconnecté',
    disabled: 'Désactivé',
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${base}`}>
      {labels[status] || status}
    </span>
  );
};

const ACCOUNT_TYPES = [
  { value: 'BANQUE', label: 'Compte bancaire' },
  { value: 'CAISSE', label: 'Caisse' },
  { value: 'CB', label: 'Carte bancaire' },
  { value: 'PLATFORM', label: 'Plateforme (SumUp, PayPal...)' },
  { value: 'AUTRE', label: 'Autre' },
];

function AddAccountModal({ isOpen, onClose, onSuccess }) {
  const [form, setForm] = useState({
    label: '',
    type: 'BANQUE',
    entity_id: 1,
    iban: '',
    bic: '',
    currency: 'EUR',
    is_active: true,
  });
  const createAccount = useCreateFinanceAccount();
  const modalRef = useClickOutsideAndEscape(onClose, { enabled: isOpen });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createAccount.mutateAsync(form);
      onSuccess?.();
      onClose();
      setForm({ label: '', type: 'BANQUE', entity_id: 1, iban: '', bic: '', currency: 'EUR', is_active: true });
    } catch (err) {
      console.error('Erreur creation compte:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div ref={modalRef} className="bg-slate-800 border border-white/10 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">Ajouter un compte</h2>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Nom du compte *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              value={form.label}
              onChange={(e) => setForm({ ...form, label: e.target.value })}
              placeholder="Ex: LCL - Compte principal"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Type de compte</label>
            <select
              className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
            >
              {ACCOUNT_TYPES.map((t) => (
                <option key={t.value} value={t.value} className="bg-slate-800">{t.label}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">IBAN</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                value={form.iban}
                onChange={(e) => setForm({ ...form, iban: e.target.value })}
                placeholder="FR76..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">BIC</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                value={form.bic}
                onChange={(e) => setForm({ ...form, bic: e.target.value })}
                placeholder="CRLYFRPP"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="ghost" onClick={onClose}>Annuler</Button>
            <Button type="submit" variant="brand" disabled={createAccount.isLoading}>
              {createAccount.isLoading ? 'Creation...' : 'Ajouter'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ManageAccountModal({ isOpen, onClose, account, onSuccess }) {
  const [form, setForm] = useState({
    label: account?.label || '',
    type: account?.type || 'BANQUE',
    iban: account?.iban || '',
    bic: account?.bic || '',
    is_active: account?.is_active ?? true,
  });
  const [confirmDelete, setConfirmDelete] = useState(false);
  const updateAccount = useUpdateFinanceAccount();
  const deleteAccount = useDeleteFinanceAccount();
  const modalRef = useClickOutsideAndEscape(onClose, { enabled: isOpen && !!account });

  React.useEffect(() => {
    if (account) {
      setForm({
        label: account.label || '',
        type: account.type || 'BANQUE',
        iban: account.iban || '',
        bic: account.bic || '',
        is_active: account.is_active ?? true,
      });
    }
  }, [account]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateAccount.mutateAsync({ accountId: account.id, payload: form });
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Erreur mise a jour compte:', err);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteAccount.mutateAsync(account.id);
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Erreur suppression compte:', err);
    }
  };

  if (!isOpen || !account) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div ref={modalRef} className="bg-slate-800 border border-white/10 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">Gerer le compte</h2>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Nom du compte *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              value={form.label}
              onChange={(e) => setForm({ ...form, label: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Type de compte</label>
            <select
              className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
            >
              {ACCOUNT_TYPES.map((t) => (
                <option key={t.value} value={t.value} className="bg-slate-800">{t.label}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">IBAN</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                value={form.iban}
                onChange={(e) => setForm({ ...form, iban: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">BIC</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-white/10 bg-white/5 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                value={form.bic}
                onChange={(e) => setForm({ ...form, bic: e.target.value })}
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="rounded border-white/20"
            />
            <label htmlFor="is_active" className="text-sm text-slate-300">Compte actif</label>
          </div>

          <div className="flex justify-between items-center pt-4 border-t border-white/10">
            {!confirmDelete ? (
              <button
                type="button"
                onClick={() => setConfirmDelete(true)}
                className="text-rose-600 hover:text-rose-700 text-sm flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Supprimer
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm text-rose-600">Confirmer ?</span>
                <Button type="button" variant="danger" size="sm" onClick={handleDelete} disabled={deleteAccount.isLoading}>
                  Oui
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>
                  Non
                </Button>
              </div>
            )}
            <div className="flex gap-3">
              <Button type="button" variant="ghost" onClick={onClose}>Annuler</Button>
              <Button type="submit" variant="brand" disabled={updateAccount.isLoading}>
                {updateAccount.isLoading ? 'Enregistrement...' : 'Enregistrer'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AccountsTab({ accounts = [], onRefresh, isLoading = false }) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);

  const handleAccountCreated = () => {
    onRefresh?.();
  };

  const handleAccountUpdated = () => {
    setSelectedAccount(null);
    onRefresh?.();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-amber-400">Comptes bancaires</h2>
          <p className="text-sm text-slate-400">Vue d'ensemble de vos comptes et soldes</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={onRefresh} disabled={isLoading}>
            Rafraîchir
          </Button>
          <Button variant="brand" className="inline-flex items-center gap-2" onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4" />
            Ajouter un compte
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {accounts.map((acc) => (
          <Card key={acc.id || acc.label} className="p-4 hover:border-white/20 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-xs uppercase tracking-widest text-slate-500">
                  {acc.provider || 'Compte'}
                </p>
                <p className="text-sm font-semibold text-white">{acc.label}</p>
              </div>
              <StatusBadge status={acc.status || 'connected'} />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-300">
                <span className="flex items-center gap-1">
                  <ArrowDownCircle className="w-3 h-3 text-emerald-400" />
                  Entrées
                </span>
                <span className="font-semibold text-emerald-400">{roundAmount(acc.inflow || 0)} €</span>
              </div>
              <div className="flex justify-between text-xs text-slate-300">
                <span className="flex items-center gap-1">
                  <ArrowUpCircle className="w-3 h-3 text-rose-400" />
                  Sorties
                </span>
                <span className="font-semibold text-rose-400">{roundAmount(acc.outflow || 0)} €</span>
              </div>
              <div className="h-px bg-white/10 my-2" />
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-slate-400">Solde</span>
                <span className={`text-lg font-bold ${acc.balance >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {roundAmount(acc.balance || 0)} €
                </span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-white/10 flex justify-between items-center">
              <span className="text-xs text-slate-500">
                {acc.operations ? `${acc.operations} opérations` : 'Aucune opération'}
              </span>
              <Button variant="ghost" size="sm" className="text-xs" onClick={() => setSelectedAccount(acc)}>
                <Settings className="w-3 h-3 mr-1" />
                Gérer
              </Button>
            </div>
          </Card>
        ))}

        {accounts.length === 0 && (
          <div className="col-span-full text-center py-12 text-slate-400">
            <Wallet className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-semibold text-white">Aucun compte bancaire</p>
            <p className="text-sm mt-1">Ajoutez votre premier compte pour commencer</p>
          </div>
        )}
      </div>

      <AddAccountModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={handleAccountCreated}
      />
      <ManageAccountModal
        isOpen={!!selectedAccount}
        onClose={() => setSelectedAccount(null)}
        account={selectedAccount}
        onSuccess={handleAccountUpdated}
      />
    </div>
  );
}
