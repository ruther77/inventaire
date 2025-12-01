import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Filter, Pencil, Trash2, Columns } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Modal from '../../components/ui/Modal.jsx';
import { useProducts } from '../../hooks/useProducts.js';
import {
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
} from '../../hooks/useCatalogMutations.js';

const statusConfig = {
  critical: {
    label: 'Critique',
    className: 'bg-rose-50 text-rose-600',
  },
  warning: {
    label: 'Surveillance',
    className: 'bg-amber-50 text-amber-700',
  },
  ok: {
    label: 'OK',
    className: 'bg-emerald-50 text-emerald-700',
  },
};

const SECTION_DEFINITIONS = [
  {
    id: 'operations',
    label: 'Catalogue',
    groups: [
      {
        title: 'Gestion',
        items: [
          {
            id: 'operations.manage',
            label: 'Recherche & listing',
            description: 'Filtres, création produit et tableau principal.',
          },
        ],
      },
    ],
  },
  {
    id: 'insights',
    label: 'Insights',
    groups: [
      {
        title: 'Santé stock',
        items: [
          {
            id: 'insights.health',
            label: 'Répartition statuts',
            description: 'Vue synthétique critique/surveillance/OK.',
          },
        ],
      },
    ],
  },
];

const getStatus = (product) => {
  const stock = product.stock_actuel ?? 0;
  const threshold = product.seuil_alerte ?? 8;
  if (stock === 0) return 'critical';
  if (stock < threshold) return 'warning';
  return 'ok';
};

const defaultForm = {
  nom: '',
  prix_achat: '',
  prix_vente: '',
  tva: '0',
  categorie: '',
  seuil_alerte: '0',
  stock_actuel: '0',
  codes: '',
};

export default function CatalogPage() {
  const { data: products = [], isLoading, isError } = useProducts();
  const createMutation = useCreateProduct();
  const updateMutation = useUpdateProduct();
  const deleteMutation = useDeleteProduct();

  const [filters, setFilters] = useState({
    search: '',
    category: 'all',
    status: 'all',
  });
  const [density, setDensity] = useState('comfortable');
  const [editor, setEditor] = useState({ open: false, mode: 'create', product: null });
  const [formValues, setFormValues] = useState(defaultForm);
  const defaultPanel =
    SECTION_DEFINITIONS[0]?.groups?.[0]?.items?.[0]?.id ?? 'operations.manage';
  const [searchParams, setSearchParams] = useSearchParams();
  const sectionParam = searchParams.get('section');
  const [activePanel, setActivePanel] = useState(sectionParam || defaultPanel);
  useEffect(() => {
    if (sectionParam && sectionParam !== activePanel) {
      setActivePanel(sectionParam);
    } else if (!sectionParam && activePanel !== defaultPanel) {
      setActivePanel(defaultPanel);
    }
  }, [sectionParam, activePanel, defaultPanel]);
  const sectionOptions = useMemo(() => {
    const options = [];
    SECTION_DEFINITIONS.forEach((section) => {
      section.groups?.forEach((group) => {
        group.items?.forEach((item) => {
          options.push({
            id: item.id,
            label: `${section.label} · ${item.label}`,
          });
        });
      });
    });
    return options;
  }, []);
  const handlePanelSelect = (panelId) => {
    const params = new URLSearchParams(searchParams);
    if (!panelId || panelId === defaultPanel) {
      params.delete('section');
    } else {
      params.set('section', panelId);
    }
    setSearchParams(params);
  };
  const filtered = useMemo(() => {
    return products.filter((product) => {
      const matchesStatus =
        filters.status === 'all' || getStatus(product) === filters.status;
      const matchesCategory =
        filters.category === 'all' ||
        (product.categorie ?? 'Non classé') === filters.category;
      const matchesSearch =
        !filters.search ||
        product.nom.toLowerCase().includes(filters.search.toLowerCase());
      return matchesStatus && matchesCategory && matchesSearch;
    });
  }, [products, filters]);

  const categories = useMemo(
    () => Array.from(new Set(products.map((p) => p.categorie ?? 'Non classé'))),
    [products],
  );
  const statusBreakdown = useMemo(() => {
    return filtered.reduce(
      (acc, product) => {
        const key = getStatus(product);
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      },
      { critical: 0, warning: 0, ok: 0 },
    );
  }, [filtered]);

  const rowPadding = density === 'compact' ? 'py-2' : 'py-3';
  const cellPadding = density === 'compact' ? 'px-2' : 'px-4';

  const toggleDensity = () => {
    setDensity((prev) => (prev === 'compact' ? 'comfortable' : 'compact'));
  };

  const openCreateModal = () => {
    setFormValues(defaultForm);
    setEditor({ open: true, mode: 'create', product: null });
  };

  const openEditModal = (product) => {
    setFormValues({
      nom: product.nom,
      prix_achat: String(product.prix_achat ?? ''),
      prix_vente: String(product.prix_vente ?? ''),
      tva: String(product.tva ?? ''),
      categorie: product.categorie ?? '',
      seuil_alerte: String(product.seuil_alerte ?? '0'),
      stock_actuel: String(product.stock_actuel ?? '0'),
      codes: (product.codes ?? []).join(', '),
    });
    setEditor({ open: true, mode: 'edit', product });
  };

  const closeModal = () => {
    setEditor({ open: false, mode: 'create', product: null });
    setFormValues(defaultForm);
  };

  const handleChange = (field) => (event) => {
    setFormValues((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleSubmit = (event) => {
    if (event) {
      event.preventDefault();
    }
    const payload = {
      nom: formValues.nom,
      prix_achat: parseFloat(formValues.prix_achat) || 0,
      prix_vente: parseFloat(formValues.prix_vente) || 0,
      tva: parseFloat(formValues.tva) || 0,
      categorie: formValues.categorie || null,
      seuil_alerte: parseFloat(formValues.seuil_alerte) || 0,
      stock_actuel: parseFloat(formValues.stock_actuel) || 0,
      actif: true,
      codes: formValues.codes
        ? formValues.codes.split(/[,;\s]+/).filter(Boolean)
        : [],
    };

    if (editor.mode === 'create') {
      createMutation.mutate(payload, { onSuccess: closeModal });
    } else if (editor.product) {
      updateMutation.mutate(
        {
          productId: editor.product.id,
          payload,
        },
        { onSuccess: closeModal },
      );
    }
  };

  const handleDelete = (productId) => {
    if (!window.confirm('Supprimer ce produit ?')) return;
    deleteMutation.mutate(productId);
  };

  const renderPanel = () => {
    switch (activePanel) {
      case 'operations.manage':
        return (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
            <div className="flex flex-col gap-4">
              <Card className="space-y-4 border-slate-200/80 bg-white">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Filter className="h-4 w-4 text-brand-500" />
                  <span>Filtres</span>
                </div>
                <div className="space-y-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recherche</label>
                    <input
                      type="search"
                      placeholder="Référence, catégorie…"
                      className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-brand-400 focus:outline-none"
                      value={filters.search}
                      onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Catégorie</label>
                    <select
                      className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-brand-400 focus:outline-none"
                      value={filters.category}
                      onChange={(event) => setFilters((prev) => ({ ...prev, category: event.target.value }))}
                    >
                      <option value="all">Toutes</option>
                      {categories.map((category) => (
                        <option key={category} value={category}>
                          {category}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Statut stock</label>
                    <select
                      className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-brand-400 focus:outline-none"
                      value={filters.status}
                      onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
                    >
                      <option value="all">Tous</option>
                      <option value="critical">Critique</option>
                      <option value="warning">Surveillance</option>
                      <option value="ok">OK</option>
                    </select>
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-3 py-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Densité</p>
                    <p className="text-sm text-slate-700">{density === 'compact' ? 'Compacte' : 'Confort'}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={toggleDensity} className="gap-2 text-sm">
                    <Columns className="h-4 w-4" />
                    {density === 'compact' ? 'Confort' : 'Compacte'}
                  </Button>
                </div>
              </Card>
              <Card className="space-y-3 border-slate-200/80 bg-white">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">santé stock</p>
                <div className="grid grid-cols-3 gap-3">
                  {['critical', 'warning', 'ok'].map((key) => (
                    <div
                      key={key}
                      className={`rounded-2xl border px-3 py-3 text-center text-sm font-semibold ${
                        key === 'critical'
                          ? 'border-rose-100 bg-rose-50 text-rose-700'
                          : key === 'warning'
                            ? 'border-amber-100 bg-amber-50 text-amber-700'
                            : 'border-emerald-100 bg-emerald-50 text-emerald-700'
                      }`}
                    >
                      <p className="text-[11px] uppercase tracking-wide text-slate-500">{statusConfig[key].label}</p>
                      <p className="text-xl">{statusBreakdown[key]}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            <div className="space-y-4">
              <Card className="flex flex-col gap-4 border-slate-200/80 bg-white">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.4em] text-slate-400">catalogue</p>
                    <h2 className="text-2xl font-semibold text-slate-900">Approvisionnement & gouvernance produit</h2>
                    <p className="text-sm text-slate-500">
                      Recherchez, filtrez et cadrez les actions fournisseurs directement depuis la console.
                    </p>
                  </div>
                  <Button variant="brand" size="lg" onClick={openCreateModal}>
                    Nouveau produit
                  </Button>
                </div>

                <div className="overflow-hidden rounded-2xl border border-slate-100">
                  {isLoading ? (
                    <div className="space-y-2 p-4">
                      {[...Array(6)].map((_, idx) => (
                        <div key={idx} className="h-10 animate-pulse rounded-xl bg-slate-100" />
                      ))}
                    </div>
                  ) : isError ? (
                    <p className="p-6 text-sm text-rose-500">Impossible de récupérer la liste de produits.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-slate-100">
                        <thead>
                          <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                            <th className={`${cellPadding} ${rowPadding} sticky top-0 bg-slate-50`}>Produit</th>
                            <th className={`${cellPadding} ${rowPadding} sticky top-0 bg-slate-50`}>Catégorie</th>
                            <th className={`${cellPadding} ${rowPadding} sticky top-0 bg-slate-50`}>Prix vente TTC</th>
                            <th className={`${cellPadding} ${rowPadding} sticky top-0 bg-slate-50`}>Stock</th>
                            <th className={`${cellPadding} ${rowPadding} sticky top-0 bg-slate-50`}>Statut</th>
                            <th className={`${cellPadding} ${rowPadding} sticky top-0 bg-slate-50 text-right`}>Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-sm">
                          {filtered.map((product) => {
                            const status = statusConfig[getStatus(product)];
                            return (
                              <tr key={product.id} className="hover:bg-slate-50/60">
                                <td className={`${cellPadding} ${rowPadding}`}>
                                  <p className="font-medium text-slate-900">{product.nom}</p>
                                  <p className="text-xs text-slate-400">ID #{product.id}</p>
                                </td>
                                <td className={`${cellPadding} ${rowPadding} text-slate-600`}>
                                  {product.categorie ?? 'Non classé'}
                                </td>
                                <td className={`${cellPadding} ${rowPadding} font-semibold text-slate-900`}>
                                  {product.prix_vente.toFixed(2)} € TTC
                                </td>
                                <td className={`${cellPadding} ${rowPadding} text-slate-600`}>
                                  {product.stock_actuel ?? 0} u
                                </td>
                                <td className={`${cellPadding} ${rowPadding}`}>
                                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${status.className}`}>
                                    {status.label}
                                  </span>
                                </td>
                                <td className={`${cellPadding} ${rowPadding} text-right`}>
                                  <div className="flex justify-end gap-2">
                                    <button
                                      type="button"
                                      className="rounded-full bg-slate-100 p-2 text-slate-600 hover:bg-slate-200"
                                      onClick={() => openEditModal(product)}
                                    >
                                      <Pencil className="h-4 w-4" />
                                    </button>
                                    <button
                                      type="button"
                                      className="rounded-full bg-rose-50 p-2 text-rose-600 hover:bg-rose-100"
                                      onClick={() => handleDelete(product.id)}
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                          {filtered.length === 0 && (
                            <tr>
                              <td colSpan={6} className="px-6 py-8 text-center text-sm text-slate-500">
                                Aucun produit ne correspond à vos filtres.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>
        );
      case 'insights.health':
        return (
          <Card className="flex flex-col gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-slate-400">santé catalogue</p>
              <h3 className="text-xl font-semibold text-slate-900">Statuts stock</h3>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {['critical', 'warning', 'ok'].map((key) => (
                <div
                  key={key}
                  className={`rounded-2xl border px-4 py-3 ${
                    key === 'critical'
                      ? 'border-rose-100 bg-rose-50 text-rose-700'
                      : key === 'warning'
                      ? 'border-amber-100 bg-amber-50 text-amber-700'
                      : 'border-emerald-100 bg-emerald-50 text-emerald-700'
                  }`}
                >
                  <p className="text-xs uppercase tracking-widest text-slate-500">
                    {statusConfig[key].label}
                  </p>
                  <p className="text-2xl font-semibold">{statusBreakdown[key]}</p>
                  <p className="text-xs text-slate-600">références</p>
                </div>
              ))}
            </div>
          </Card>
        );
      default:
        return (
          <Card>
            <p className="text-sm text-slate-500">Sélectionnez un panneau à afficher.</p>
          </Card>
        );
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="lg:hidden">
        <label className="text-xs uppercase tracking-[0.3em] text-slate-400" htmlFor="mobile-catalog-section">
          Section
        </label>
        <select
          id="mobile-catalog-section"
          value={activePanel}
          onChange={(event) => handlePanelSelect(event.target.value)}
          className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm text-slate-700 focus:border-brand-400 focus:outline-none"
        >
          {sectionOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      {renderPanel()}
      <Modal
        open={editor.open}
        onClose={closeModal}
        title={editor.mode === 'create' ? 'Nouveau produit' : 'Modifier le produit'}
        description="Renseignez les informations catalogue. Les tarifs HT seront synchronisés avec les règles d’inflation."
        actions={[
          { label: 'Annuler', onClick: closeModal },
          {
            label: editor.mode === 'create' ? 'Créer' : 'Enregistrer',
            variant: 'primary',
            onClick: handleSubmit,
          },
        ]}
      >
        <form className="grid gap-4" onSubmit={handleSubmit}>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Nom</label>
            <input
              type="text"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
              value={formValues.nom}
              onChange={handleChange('nom')}
              required
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Prix d'achat (HT)</label>
              <input
                type="number"
                step="0.01"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
                value={formValues.prix_achat}
                onChange={handleChange('prix_achat')}
              />
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Prix de vente (TTC)</label>
              <input
                type="number"
                step="0.01"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
                value={formValues.prix_vente}
                onChange={handleChange('prix_vente')}
              />
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">TVA (%)</label>
              <input
                type="number"
                step="0.01"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
                value={formValues.tva}
                onChange={handleChange('tva')}
              />
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Seuil alerte</label>
              <input
                type="number"
                step="0.01"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
                value={formValues.seuil_alerte}
                onChange={handleChange('seuil_alerte')}
              />
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Stock actuel</label>
              <input
                type="number"
                step="0.01"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
                value={formValues.stock_actuel}
                onChange={handleChange('stock_actuel')}
              />
            </div>
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Catégorie</label>
            <input
              type="text"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
              value={formValues.categorie}
              onChange={handleChange('categorie')}
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Codes-barres</label>
            <textarea
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm shadow-sm"
              value={formValues.codes}
              onChange={handleChange('codes')}
              placeholder="Séparer par virgule ou retour ligne"
              rows={3}
            />
          </div>
        </form>
      </Modal>
    </div>
  );
}
