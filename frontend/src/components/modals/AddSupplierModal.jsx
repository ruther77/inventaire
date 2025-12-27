import { useState, useCallback, useEffect } from 'react';
import { Building2, User, Phone, Mail, MapPin, CreditCard, FileText, AlertTriangle, Loader2 } from 'lucide-react';
import Modal from '@/components/ui/Modal.jsx';
import Button from '@/components/ui/Button.jsx';
import { useCreateSupplier, useUpdateSupplier } from '@/hooks/useSuppliers.js';

const initialFormState = {
  nom: '',
  email: '',
  telephone: '',
  adresse: '',
  contact_nom: '',
  iban: '',
  siret: '',
  delai_paiement: '30',
  notes: '',
  actif: true,
};

export default function AddSupplierModal({ open, onClose, onSuccess, supplier = null }) {
  const [form, setForm] = useState(initialFormState);
  const [errors, setErrors] = useState({});

  const createSupplier = useCreateSupplier();
  const updateSupplier = useUpdateSupplier();

  const isEditMode = Boolean(supplier);

  // Pre-fill form in edit mode
  useEffect(() => {
    if (supplier) {
      setForm({
        nom: supplier.nom || '',
        email: supplier.email || '',
        telephone: supplier.telephone || '',
        adresse: supplier.adresse || '',
        contact_nom: supplier.contact_nom || '',
        iban: supplier.iban || '',
        siret: supplier.siret || '',
        delai_paiement: String(supplier.delai_paiement ?? 30),
        notes: supplier.notes || '',
        actif: supplier.actif ?? true,
      });
    } else {
      setForm(initialFormState);
    }
  }, [supplier, open]);

  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  }, [errors]);

  const validate = useCallback(() => {
    const newErrors = {};

    if (!form.nom.trim()) {
      newErrors.nom = 'Le nom est requis';
    } else if (form.nom.trim().length < 2) {
      newErrors.nom = 'Minimum 2 caractères';
    }

    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = 'Email invalide';
    }

    if (form.delai_paiement && (isNaN(form.delai_paiement) || parseInt(form.delai_paiement) < 0)) {
      newErrors.delai_paiement = 'Délai invalide';
    }

    if (form.siret && !/^\d{14}$/.test(form.siret.replace(/\s/g, ''))) {
      newErrors.siret = 'SIRET doit contenir 14 chiffres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [form]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    if (!validate()) return;

    const payload = {
      nom: form.nom.trim(),
      email: form.email.trim() || null,
      telephone: form.telephone.trim() || null,
      adresse: form.adresse.trim() || null,
      contact_nom: form.contact_nom.trim() || null,
      iban: form.iban.trim() || null,
      siret: form.siret.replace(/\s/g, '').trim() || null,
      delai_paiement: parseInt(form.delai_paiement) || 30,
      notes: form.notes.trim() || null,
      actif: form.actif,
    };

    const mutation = isEditMode ? updateSupplier : createSupplier;
    const mutationPayload = isEditMode ? { id: supplier.id, data: payload } : payload;

    mutation.mutate(mutationPayload, {
      onSuccess: () => {
        setForm(initialFormState);
        setErrors({});
        onSuccess?.();
        onClose();
      },
    });
  }, [form, validate, createSupplier, updateSupplier, isEditMode, supplier, onSuccess, onClose]);

  const handleClose = useCallback(() => {
    setForm(initialFormState);
    setErrors({});
    onClose();
  }, [onClose]);

  const isPending = createSupplier.isPending || updateSupplier.isPending;

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={isEditMode ? 'Modifier le fournisseur' : 'Ajouter un fournisseur'}
      description={isEditMode ? 'Mettre à jour les informations' : 'Créer un nouveau fournisseur'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Section Informations principales */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            Informations principales
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Nom */}
            <div className="md:col-span-2">
              <label htmlFor="nom" className="block text-sm font-medium text-slate-300 mb-1.5">
                Nom du fournisseur <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                id="nom"
                name="nom"
                value={form.nom}
                onChange={handleChange}
                placeholder="Ex: Metro France, Brake..."
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.nom ? 'border-rose-500' : 'border-white/10'
                } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all`}
              />
              {errors.nom && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.nom}
                </p>
              )}
            </div>

            {/* SIRET */}
            <div>
              <label htmlFor="siret" className="block text-sm font-medium text-slate-300 mb-1.5">
                SIRET
              </label>
              <input
                type="text"
                id="siret"
                name="siret"
                value={form.siret}
                onChange={handleChange}
                placeholder="123 456 789 00012"
                maxLength={17}
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.siret ? 'border-rose-500' : 'border-white/10'
                } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all`}
              />
              {errors.siret && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.siret}
                </p>
              )}
            </div>

            {/* Actif */}
            <div className="flex items-center gap-3 pt-6">
              <input
                type="checkbox"
                id="actif"
                name="actif"
                checked={form.actif}
                onChange={handleChange}
                className="w-5 h-5 rounded bg-white/5 border border-white/20 text-cyan-500 focus:ring-cyan-500/50 focus:ring-offset-0"
              />
              <label htmlFor="actif" className="text-sm font-medium text-slate-300">
                Fournisseur actif
              </label>
            </div>
          </div>
        </div>

        {/* Section Contact */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <User className="w-4 h-4" />
            Contact
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Contact nom */}
            <div>
              <label htmlFor="contact_nom" className="block text-sm font-medium text-slate-300 mb-1.5">
                Nom du contact
              </label>
              <input
                type="text"
                id="contact_nom"
                name="contact_nom"
                value={form.contact_nom}
                onChange={handleChange}
                placeholder="Jean Dupont"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all"
              />
            </div>

            {/* Téléphone */}
            <div>
              <label htmlFor="telephone" className="block text-sm font-medium text-slate-300 mb-1.5">
                <Phone className="w-3.5 h-3.5 inline mr-1.5" />
                Téléphone
              </label>
              <input
                type="tel"
                id="telephone"
                name="telephone"
                value={form.telephone}
                onChange={handleChange}
                placeholder="+33 1 23 45 67 89"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all"
              />
            </div>

            {/* Email */}
            <div className="md:col-span-2">
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-1.5">
                <Mail className="w-3.5 h-3.5 inline mr-1.5" />
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="contact@fournisseur.fr"
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.email ? 'border-rose-500' : 'border-white/10'
                } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all`}
              />
              {errors.email && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.email}
                </p>
              )}
            </div>

            {/* Adresse */}
            <div className="md:col-span-2">
              <label htmlFor="adresse" className="block text-sm font-medium text-slate-300 mb-1.5">
                <MapPin className="w-3.5 h-3.5 inline mr-1.5" />
                Adresse
              </label>
              <textarea
                id="adresse"
                name="adresse"
                value={form.adresse}
                onChange={handleChange}
                rows={2}
                placeholder="123 rue du Commerce, 75001 Paris"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all resize-none"
              />
            </div>
          </div>
        </div>

        {/* Section Paiement */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <CreditCard className="w-4 h-4" />
            Paiement
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* IBAN */}
            <div>
              <label htmlFor="iban" className="block text-sm font-medium text-slate-300 mb-1.5">
                IBAN
              </label>
              <input
                type="text"
                id="iban"
                name="iban"
                value={form.iban}
                onChange={handleChange}
                placeholder="FR76 1234 5678 9012 3456 7890 123"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all"
              />
            </div>

            {/* Délai de paiement */}
            <div>
              <label htmlFor="delai_paiement" className="block text-sm font-medium text-slate-300 mb-1.5">
                Délai de paiement (jours)
              </label>
              <input
                type="number"
                id="delai_paiement"
                name="delai_paiement"
                value={form.delai_paiement}
                onChange={handleChange}
                min="0"
                max="365"
                placeholder="30"
                className={`w-full px-4 py-3 rounded-xl bg-white/5 border ${
                  errors.delai_paiement ? 'border-rose-500' : 'border-white/10'
                } text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all`}
              />
              {errors.delai_paiement && (
                <p className="mt-1.5 text-sm text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {errors.delai_paiement}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-slate-300 mb-1.5">
            <FileText className="w-3.5 h-3.5 inline mr-1.5" />
            Notes
          </label>
          <textarea
            id="notes"
            name="notes"
            value={form.notes}
            onChange={handleChange}
            rows={3}
            placeholder="Notes internes sur ce fournisseur..."
            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isPending}
            className="bg-cyan-500 hover:bg-cyan-600"
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {isEditMode ? 'Mise à jour...' : 'Création...'}
              </>
            ) : (
              isEditMode ? 'Mettre à jour' : 'Créer le fournisseur'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
