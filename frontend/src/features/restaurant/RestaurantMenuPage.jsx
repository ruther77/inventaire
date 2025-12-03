import { useMemo, useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Input from '../../components/ui/Input.jsx';
import Select from '../../components/ui/Select.jsx';
import {
  useRestaurantIngredients,
  useCreateRestaurantIngredient,
  useRestaurantPlats,
  useCreateRestaurantPlat,
  useAttachIngredientToPlat,
  useUpdateRestaurantIngredientPrice,
  useUpdateRestaurantPlatPrice,
  useRestaurantIngredientPriceHistory,
  useRestaurantPlatPriceHistory,
  useRestaurantPlatMappings,
  useSyncRestaurantIngredients,
} from '../../hooks/useRestaurant.js';

export default function RestaurantMenuPage() {
  const ingredients = useRestaurantIngredients();
  const plats = useRestaurantPlats();
  const createIngredient = useCreateRestaurantIngredient();
  const createPlat = useCreateRestaurantPlat();
  const attachIngredient = useAttachIngredientToPlat();

  const menuList = plats.data ?? [];
  const lowMargins = [...menuList].sort((a, b) => a.marge_pct - b.marge_pct).slice(0, 3);
  const highMargins = [...menuList].sort((a, b) => b.marge_pct - a.marge_pct).slice(0, 3);

  const [ingredientForm, setIngredientForm] = useState({
    nom: '',
    unite_base: 'kg',
    cout_unitaire: '',
  });

  const [platForm, setPlatForm] = useState({
    nom: '',
    categorie: '',
    prix_vente_ttc: '',
  });

  const [bomForm, setBomForm] = useState({
    plat_id: '',
    ingredient_id: '',
    quantite: '',
    unite: '',
  });

  const [ingredientUpdate, setIngredientUpdate] = useState({ ingredientId: '', price: '' });
  const [platUpdate, setPlatUpdate] = useState({ platId: '', price: '' });
  const [historyIngredientId, setHistoryIngredientId] = useState(null);
  const [historyPlatId, setHistoryPlatId] = useState(null);
  const [tab, setTab] = useState('plats');
  const [platFilter, setPlatFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [ingredientFilter, setIngredientFilter] = useState('');

  const updateIngredientPrice = useUpdateRestaurantIngredientPrice();
  const updatePlatPrice = useUpdateRestaurantPlatPrice();
  const ingredientHistory = useRestaurantIngredientPriceHistory(historyIngredientId);
  const platHistory = useRestaurantPlatPriceHistory(historyPlatId);

  const syncIngredients = useSyncRestaurantIngredients();
  const selectedPlat = platUpdate.platId
    ? (plats.data ?? []).find((plat) => plat.id === Number(platUpdate.platId))
    : null;
  const selectedIngredient = ingredientUpdate.ingredientId
    ? (ingredients.data ?? []).find((ing) => ing.id === Number(ingredientUpdate.ingredientId))
    : null;

  const ingredientHistoryEntries = ingredientHistory.data ?? [];
  const platHistoryEntries = platHistory.data ?? [];
  const platsByCategory = menuList.reduce((acc, plat) => {
    const key = plat.categorie || 'Divers';
    if (!acc[key]) acc[key] = [];
    acc[key].push(plat);
    return acc;
  }, {});
  const sortedCategories = Object.keys(platsByCategory).sort((a, b) => a.localeCompare(b));
  const filteredPlats = menuList
    .filter((plat) => plat.nom.toLowerCase().includes(platFilter.toLowerCase()))
    .filter((plat) => (categoryFilter === 'all' ? true : (plat.categorie || 'Divers') === categoryFilter));
  const ingredientList = ingredients.data ?? [];
  const filteredIngredients = ingredientList.filter((ing) =>
    ing.nom.toLowerCase().includes(ingredientFilter.toLowerCase()),
  );
  const visibleCategories = sortedCategories.filter((category) =>
    filteredPlats.some((plat) => (plat.categorie || 'Divers') === category),
  );

  const formatDate = (value) => {
    if (!value) return '-';
    const date = new Date(value);
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleIngredientSubmit = (event) => {
    event.preventDefault();
    if (!ingredientForm.nom) return;
    createIngredient.mutate(
      {
        nom: ingredientForm.nom,
        unite_base: ingredientForm.unite_base,
        cout_unitaire: parseFloat(ingredientForm.cout_unitaire || '0'),
      },
      {
        onSuccess: () => setIngredientForm({ nom: '', unite_base: 'kg', cout_unitaire: '' }),
      },
    );
  };

  const handlePlatSubmit = (event) => {
    event.preventDefault();
    if (!platForm.nom) return;
    createPlat.mutate(
      {
        nom: platForm.nom,
        categorie: platForm.categorie || undefined,
        prix_vente_ttc: parseFloat(platForm.prix_vente_ttc || '0'),
      },
      {
        onSuccess: () => setPlatForm({ nom: '', categorie: '', prix_vente_ttc: '' }),
      },
    );
  };

  const handleBomSubmit = (event) => {
    event.preventDefault();
    if (!bomForm.plat_id || !bomForm.ingredient_id || !bomForm.quantite) return;
    attachIngredient.mutate(
      {
        platId: Number(bomForm.plat_id),
        payload: {
          ingredient_id: Number(bomForm.ingredient_id),
          quantite: parseFloat(bomForm.quantite),
          unite: bomForm.unite || undefined,
        },
        },
      {
        onSuccess: () => setBomForm({ plat_id: '', ingredient_id: '', quantite: '', unite: '' }),
      },
    );
  };

  const handleIngredientPriceSubmit = (event) => {
    event.preventDefault();
    if (!ingredientUpdate.ingredientId) return;
    const ingredientId = Number(ingredientUpdate.ingredientId);
    const price = parseFloat(ingredientUpdate.price || '0');
    if (Number.isNaN(price)) return;
    updateIngredientPrice.mutate(
      { ingredientId, payload: { cout_unitaire: price } },
      {
        onSuccess: () => {
          setIngredientUpdate((prev) => ({ ...prev, price: '' }));
          setHistoryIngredientId(ingredientId);
        },
      },
    );
  };

  const handlePlatPriceSubmit = (event) => {
    event.preventDefault();
    if (!platUpdate.platId) return;
    const platId = Number(platUpdate.platId);
    const price = parseFloat(platUpdate.price || '0');
    if (Number.isNaN(price)) return;
    updatePlatPrice.mutate(
      { platId, payload: { prix_vente_ttc: price } },
      {
        onSuccess: () => {
          setPlatUpdate((prev) => ({ ...prev, price: '' }));
          setHistoryPlatId(platId);
        },
      },
    );
  };

  const mappings = useRestaurantPlatMappings();
  const platLinks = mappings.data ?? [];
  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">cuisine</p>
          <h2 className="text-2xl font-semibold text-slate-900">Ingrédients & matières premières</h2>
        </div>
        <form className="grid gap-4 md:grid-cols-3" onSubmit={handleIngredientSubmit}>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Nom</label>
            <input
              type="text"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={ingredientForm.nom}
              onChange={(event) => setIngredientForm((prev) => ({ ...prev, nom: event.target.value }))}
              required
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Unité</label>
            <input
              type="text"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={ingredientForm.unite_base}
              onChange={(event) => setIngredientForm((prev) => ({ ...prev, unite_base: event.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Coût unitaire (€)</label>
            <input
              type="number"
              step="0.01"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={ingredientForm.cout_unitaire}
              onChange={(event) => setIngredientForm((prev) => ({ ...prev, cout_unitaire: event.target.value }))}
            />
          </div>
          <div className="md:col-span-3 flex justify-end">
            <Button type="submit" variant="brand">
              Ajouter l’ingrédient
            </Button>
          </div>
        </form>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                <th className="px-3 py-2">Nom</th>
                <th className="px-3 py-2">Unité</th>
                <th className="px-3 py-2">Coût (€)</th>
                <th className="px-3 py-2">Stock</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(ingredients.data ?? []).map((ing) => (
                <tr key={ing.id}>
                  <td className="px-3 py-2 text-slate-900">{ing.nom}</td>
                  <td className="px-3 py-2 text-slate-600">{ing.unite_base}</td>
                  <td className="px-3 py-2 text-slate-600">{ing.cout_unitaire.toFixed(2)} €</td>
                  <td className="px-3 py-2 text-slate-600">{ing.stock_actuel.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">modulation</p>
            <h3 className="text-lg font-semibold text-slate-900">Coûts matières</h3>
          </div>
          <form className="grid gap-4" onSubmit={handleIngredientPriceSubmit}>
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Ingrédient</label>
              <select
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                value={ingredientUpdate.ingredientId}
                onChange={(event) => {
                  const value = event.target.value;
                  setIngredientUpdate((prev) => ({ ...prev, ingredientId: value }));
                  setHistoryIngredientId(value ? Number(value) : null);
                }}
              >
                <option value="">Choisir l’ingrédient</option>
                {(ingredients.data ?? []).map((ing) => (
                  <option key={ing.id} value={ing.id}>
                    {ing.nom}
                  </option>
                ))}
              </select>
              {selectedIngredient && (
                <p className="text-xs text-slate-500">
                  Coût actuel : <span className="font-semibold text-slate-900">{selectedIngredient.cout_unitaire.toFixed(2)} €</span>
                </p>
              )}
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Nouveau coût unitaire (€)</label>
              <input
                type="number"
                step="0.01"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                value={ingredientUpdate.price}
                onChange={(event) => setIngredientUpdate((prev) => ({ ...prev, price: event.target.value }))}
              />
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={!ingredientUpdate.ingredientId || updateIngredientPrice.isLoading}>
                {updateIngredientPrice.isLoading ? 'Mise à jour…' : 'Réajuster le coût'}
              </Button>
            </div>
          </form>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Historique récent</p>
            {ingredientHistory.isLoading ? (
              <p className="text-sm text-slate-500">Chargement…</p>
            ) : ingredientHistoryEntries.length === 0 ? (
              <p className="text-sm text-slate-500">Sélectionnez un ingrédient pour voir ses dernières modulations.</p>
            ) : (
              <ul className="space-y-3">
                {ingredientHistoryEntries.slice(0, 4).map((entry) => (
                  <li key={entry.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm">
                    <div>
                      <p className="font-semibold text-slate-900">{entry.ingredient_nom}</p>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{formatDate(entry.changed_at)}</p>
                    </div>
                    <span className="text-sm font-semibold text-slate-700">{entry.cout_unitaire.toFixed(2)} €</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">menu</p>
            <h3 className="text-lg font-semibold text-slate-900">Prix de vente</h3>
          </div>
          <form className="grid gap-4" onSubmit={handlePlatPriceSubmit}>
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Plat</label>
              <select
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                value={platUpdate.platId}
                onChange={(event) => {
                  const value = event.target.value;
                  setPlatUpdate((prev) => ({ ...prev, platId: value }));
                  setHistoryPlatId(value ? Number(value) : null);
                }}
              >
                <option value="">Choisir un plat</option>
                {(plats.data ?? []).map((plat) => (
                  <option key={plat.id} value={plat.id}>
                    {plat.nom}
                  </option>
                ))}
              </select>
              {selectedPlat && (
                <p className="text-xs text-slate-500">
                  Prix actuel : <span className="font-semibold text-slate-900">{selectedPlat.prix_vente_ttc.toFixed(2)} €</span>
                </p>
              )}
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-semibold text-slate-700">Nouveau prix TTC (€)</label>
              <input
                type="number"
                step="0.01"
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
                value={platUpdate.price}
                onChange={(event) => setPlatUpdate((prev) => ({ ...prev, price: event.target.value }))}
              />
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={!platUpdate.platId || updatePlatPrice.isLoading}>
                {updatePlatPrice.isLoading ? 'Mise à jour…' : 'Mettre à jour la carte'}
              </Button>
            </div>
          </form>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Historique récent</p>
            {platHistory.isLoading ? (
              <p className="text-sm text-slate-500">Chargement…</p>
            ) : platHistoryEntries.length === 0 ? (
              <p className="text-sm text-slate-500">Choisissez un plat pour suivre ses dérives.</p>
            ) : (
              <ul className="space-y-3">
                {platHistoryEntries.slice(0, 4).map((entry) => (
                  <li key={entry.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm">
                    <div>
                      <p className="font-semibold text-slate-900">{entry.plat_nom}</p>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{formatDate(entry.changed_at)}</p>
                    </div>
                    <span className="text-sm font-semibold text-slate-700">{entry.prix_vente_ttc.toFixed(2)} €</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">menu</p>
          <h2 className="text-2xl font-semibold text-slate-900">Plats & fiches techniques</h2>
        </div>
        <form className="grid gap-4 md:grid-cols-3" onSubmit={handlePlatSubmit}>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Nom</label>
            <input
              type="text"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={platForm.nom}
              onChange={(event) => setPlatForm((prev) => ({ ...prev, nom: event.target.value }))}
              required
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Catégorie</label>
            <input
              type="text"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={platForm.categorie}
              onChange={(event) => setPlatForm((prev) => ({ ...prev, categorie: event.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-semibold text-slate-700">Prix TTC (€)</label>
            <input
              type="number"
              step="0.01"
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={platForm.prix_vente_ttc}
              onChange={(event) => setPlatForm((prev) => ({ ...prev, prix_vente_ttc: event.target.value }))}
            />
          </div>
          <div className="md:col-span-3 flex justify-end">
            <Button type="submit" variant="brand">
              Ajouter le plat
            </Button>
          </div>
        </form>

        <form className="grid gap-4 md:grid-cols-4" onSubmit={handleBomSubmit}>
          <div>
            <label className="text-sm font-semibold text-slate-700">Plat</label>
            <select
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={bomForm.plat_id}
              onChange={(event) => setBomForm((prev) => ({ ...prev, plat_id: event.target.value }))}
            >
              <option value="">Choisir</option>
              {(plats.data ?? []).map((plat) => (
                <option key={plat.id} value={plat.id}>
                  {plat.nom}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Ingrédient</label>
            <select
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={bomForm.ingredient_id}
              onChange={(event) => setBomForm((prev) => ({ ...prev, ingredient_id: event.target.value }))}
            >
              <option value="">Choisir</option>
              {(ingredients.data ?? []).map((ing) => (
                <option key={ing.id} value={ing.id}>
                  {ing.nom}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Quantité</label>
            <input
              type="number"
              step="0.001"
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={bomForm.quantite}
              onChange={(event) => setBomForm((prev) => ({ ...prev, quantite: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Unité</label>
            <input
              type="text"
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm"
              value={bomForm.unite}
              onChange={(event) => setBomForm((prev) => ({ ...prev, unite: event.target.value }))}
            />
          </div>
          <div className="md:col-span-4 flex justify-end">
            <Button type="submit" variant="ghost">
              Ajouter à la fiche technique
            </Button>
          </div>
        </form>

        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="Rechercher un plat"
            className="w-full max-w-xs rounded-2xl border border-slate-200 px-4 py-2 text-sm"
            value={platFilter}
            onChange={(event) => setPlatFilter(event.target.value)}
          />
          <select
            className="w-full max-w-xs rounded-2xl border border-slate-200 px-4 py-2 text-sm"
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value)}
          >
            <option value="all">Toutes les catégories</option>
            {sortedCategories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <Input
            placeholder="Filtrer les ingrédients (optionnel)"
            value={ingredientFilter}
            onChange={(event) => setIngredientFilter(event.target.value)}
            className="w-full max-w-xs rounded-2xl border border-slate-200 px-4 py-2 text-sm"
          />
        </div>

        <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">liens épicerie</p>
            <h2 className="text-lg font-semibold text-slate-900">Produits associés</h2>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncIngredients.mutate()}
            disabled={syncIngredients.isLoading}
          >
            {syncIngredients.isLoading ? 'Synchronisation…' : 'Synchro auto'}
          </Button>
        </div>
          {!platLinks.length && !mappings.isLoading ? (
            <p className="text-sm text-slate-500">Aucune correspondance Epicerie définie pour les plats.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Plat</th>
                    <th className="px-3 py-2">Produit Épicerie</th>
                    <th className="px-3 py-2 text-right">Ratio</th>
                    <th className="px-3 py-2 text-right">Prix achat</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {platLinks.map((link) => (
                    <tr key={`${link.plat_id}-${link.produit_epicerie_id}`}>
                      <td className="px-3 py-2">
                        <p className="font-semibold text-slate-900">{link.plat_nom}</p>
                        <p className="text-xs text-slate-400">{link.plat_categorie ?? 'Divers'}</p>
                      </td>
                      <td className="px-3 py-2">
                        {link.epicerie_nom ?? '—'}
                        <div className="text-xs text-slate-400">{link.produit_epicerie_id ?? '—'}</div>
                      </td>
                      <td className="px-3 py-2 text-right">{link.ratio ?? '—'}</td>
                      <td className="px-3 py-2 text-right">{link.prix_achat != null ? Number(link.prix_achat).toFixed(2) : '—'} €</td>
                    </tr>
                  ))}
                  {mappings.isLoading && (
                    <tr>
                      <td colSpan={4} className="px-3 py-2 text-sm text-slate-500">
                        Chargement des prix Épicerie…
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <div className="grid gap-4">
          {visibleCategories.length === 0 ? (
            <div className="rounded-2xl border border-slate-200 p-4 text-sm text-slate-500">
              Aucun plat ne correspond aux filtres. Supprime la recherche ou change de catégorie.
            </div>
          ) : (
            <>
              {visibleCategories.map((category) => {
                const platsInCategory = filteredPlats
                  .filter((plat) => (plat.categorie || 'Divers') === category)
                  .sort((a, b) => a.nom.localeCompare(b.nom));

                return (
                  <div key={category} className="space-y-3 rounded-2xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Catégorie</p>
                        <h3 className="text-lg font-semibold text-slate-900">{category}</h3>
                      </div>
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                        {platsByCategory[category].length} plat(s)
                      </span>
                    </div>
                    <div className="grid gap-3 lg:grid-cols-2">
                      {platsInCategory.map((plat) => (
                        <div key={plat.id} className="rounded-2xl border border-slate-100 p-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-lg font-semibold text-slate-900">{plat.nom}</p>
                              <p className="text-xs text-slate-500">
                                Marge {plat.marge_pct?.toFixed(1) ?? 'N/C'} % · Coût {plat.cout_matiere?.toFixed(2) ?? '0'} €
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold text-slate-900">{plat.prix_vente_ttc.toFixed(2)} €</p>
                              <div className="mt-1 flex gap-2 text-xs text-brand-700">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setPlatUpdate({ platId: plat.id, price: plat.prix_vente_ttc })}
                                >
                                  MAJ prix
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => setHistoryPlatId(plat.id)}>
                                  Historique
                                </Button>
                              </div>
                            </div>
                          </div>
                          <table className="mt-3 w-full divide-y divide-slate-100 text-sm">
                            <thead>
                              <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                                <th className="py-1">Ingrédient</th>
                                <th className="py-1">Quantité</th>
                                <th className="py-1">Unité</th>
                              </tr>
                            </thead>
                            <tbody>
                              {(plat.ingredients ?? []).map((item) => (
                                <tr key={item.id}>
                                  <td className="py-1 text-slate-900">{item.nom}</td>
                                  <td className="py-1 text-slate-600">{Number(item.quantite).toFixed(3)}</td>
                                  <td className="py-1 text-slate-600">{item.unite || '-'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
      </Card>

      <Card className="grid gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-3">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">priorité</p>
          <h3 className="text-lg font-semibold text-slate-900">Plats à marge faible</h3>
          {lowMargins.length === 0 ? (
            <p className="text-sm text-slate-500">Aucun plat ne descend sous 30 % de marge.</p>
          ) : (
            <ul className="space-y-3">
              {lowMargins.map((plat) => (
                <li key={plat.id} className="rounded-2xl border border-slate-100 p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{plat.nom}</p>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{plat.categorie ?? 'NC'}</p>
                    </div>
                    <span className="text-sm font-semibold text-rose-600">{plat.marge_pct.toFixed(1)} %</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Coût matière : <span className="font-semibold text-slate-700">{plat.cout_matiere.toFixed(2)} €</span>
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex flex-col gap-3">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">performances</p>
          <h3 className="text-lg font-semibold text-slate-900">Meilleures marges</h3>
          {highMargins.length === 0 ? (
            <p className="text-sm text-slate-500">Ajoutez des plats pour visualiser vos top performers.</p>
          ) : (
            <ul className="space-y-3">
              {highMargins.map((plat) => (
                <li key={plat.id} className="rounded-2xl border border-slate-100 p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{plat.nom}</p>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{plat.categorie ?? 'NC'}</p>
                    </div>
                    <span className="text-sm font-semibold text-emerald-600">{plat.marge_pct.toFixed(1)} %</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Prix carte : <span className="font-semibold text-slate-700">{plat.prix_vente_ttc.toFixed(2)} €</span>
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Card>
    </div>
  );
}
