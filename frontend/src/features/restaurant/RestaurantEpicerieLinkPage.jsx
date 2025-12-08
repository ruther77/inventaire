import { useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import {
  useRestaurantPlatMappings,
  useSyncRestaurantIngredients,
  useEpicerieProducts,
  useUpdatePlatMapping,
  useDeletePlatMapping,
} from '../../hooks/useRestaurant.js';

function RatioInput({ platId, epicerieId, initialRatio, onSave, disabled }) {
  const [value, setValue] = useState(initialRatio ?? 1);

  const handleBlur = () => {
    const newRatio = parseFloat(value);
    if (newRatio > 0 && newRatio !== initialRatio) {
      onSave(platId, epicerieId, newRatio);
    }
  };

  return (
    <input
      type="number"
      step="0.01"
      min="0.01"
      className="w-20 rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-right"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onBlur={handleBlur}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.target.blur();
        }
      }}
      disabled={disabled}
    />
  );
}

export default function RestaurantEpicerieLinkPage() {
  const mappings = useRestaurantPlatMappings();
  const platLinks = mappings.data ?? [];
  const syncIngredients = useSyncRestaurantIngredients();
  const epicerieProducts = useEpicerieProducts();
  const updatePlatMapping = useUpdatePlatMapping();
  const deletePlatMapping = useDeletePlatMapping();
  const [searchPlat, setSearchPlat] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  const handleRatioSave = (platId, epicerieId, ratio) => {
    updatePlatMapping.mutate({
      platId,
      payload: {
        produit_epicerie_id: epicerieId,
        ratio,
      },
    });
  };

  const categories = [...new Set(platLinks.map((l) => l.plat_categorie || 'Divers'))].sort();

  const filteredLinks = platLinks
    .filter((link) =>
      searchPlat ? link.plat_nom.toLowerCase().includes(searchPlat.toLowerCase()) : true
    )
    .filter((link) =>
      categoryFilter === 'all' ? true : (link.plat_categorie || 'Divers') === categoryFilter
    );

  const linkedCount = platLinks.filter((l) => l.produit_epicerie_id).length;
  const unlinkedCount = platLinks.length - linkedCount;

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">liens epicerie</p>
            <h1 className="text-2xl font-semibold text-slate-900">Produits associes</h1>
            <p className="text-sm text-slate-500 mt-1">
              Associez chaque plat du restaurant a un produit de l'epicerie pour le suivi des couts et des stocks.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => syncIngredients.mutate()}
            disabled={syncIngredients.isLoading}
          >
            {syncIngredients.isLoading ? 'Synchronisation...' : 'Synchro auto'}
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-widest text-slate-400">Total plats</p>
            <p className="text-2xl font-semibold text-slate-900">{platLinks.length}</p>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="text-xs uppercase tracking-widest text-emerald-600">Lies</p>
            <p className="text-2xl font-semibold text-emerald-700">{linkedCount}</p>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-xs uppercase tracking-widest text-amber-600">Non lies</p>
            <p className="text-2xl font-semibold text-amber-700">{unlinkedCount}</p>
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="Rechercher un plat..."
            className="flex-1 min-w-[200px] rounded-2xl border border-slate-200 px-4 py-2 text-sm"
            value={searchPlat}
            onChange={(e) => setSearchPlat(e.target.value)}
          />
          <select
            className="rounded-2xl border border-slate-200 px-4 py-2 text-sm"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="all">Toutes les categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        {mappings.isLoading ? (
          <p className="text-sm text-slate-500">Chargement...</p>
        ) : filteredLinks.length === 0 ? (
          <p className="text-sm text-slate-500">Aucun plat trouve.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-3 py-2">Plat</th>
                  <th className="px-3 py-2">Produit Epicerie</th>
                  <th className="px-3 py-2 text-right">Ratio</th>
                  <th className="px-3 py-2 text-right">Prix achat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLinks.map((link) => {
                  const selectedProduct = (epicerieProducts.data ?? []).find(
                    (p) => p.id === link.produit_epicerie_id
                  );
                  return (
                    <tr key={`${link.plat_id}-${link.produit_epicerie_id ?? 'none'}`}>
                      <td className="px-3 py-2">
                        <p className="font-semibold text-slate-900">{link.plat_nom}</p>
                        <p className="text-xs text-slate-400">{link.plat_categorie ?? 'Divers'}</p>
                      </td>
                      <td className="px-3 py-2">
                        <select
                          className="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm bg-white"
                          value={link.produit_epicerie_id ?? ''}
                          onChange={(e) => {
                            const epicerieId = e.target.value;
                            if (epicerieId) {
                              updatePlatMapping.mutate({
                                platId: link.plat_id,
                                payload: {
                                  produit_epicerie_id: Number(epicerieId),
                                  ratio: link.ratio ?? 1,
                                },
                              });
                            } else if (link.produit_epicerie_id) {
                              deletePlatMapping.mutate(link.plat_id);
                            }
                          }}
                        >
                          <option value="">-- Selectionner --</option>
                          {[...(epicerieProducts.data ?? [])]
                            .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'))
                            .map((prod) => (
                              <option key={prod.id} value={prod.id}>
                                {prod.nom} ({(prod.prix_achat ?? 0).toFixed(2)}EUR)
                              </option>
                            ))}
                        </select>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <RatioInput
                          key={`${link.plat_id}-${link.produit_epicerie_id}`}
                          platId={link.plat_id}
                          epicerieId={link.produit_epicerie_id}
                          initialRatio={link.ratio}
                          onSave={handleRatioSave}
                          disabled={!link.produit_epicerie_id}
                        />
                      </td>
                      <td className="px-3 py-2 text-right">
                        {selectedProduct?.prix_achat != null
                          ? Number(selectedProduct.prix_achat).toFixed(2)
                          : link.prix_achat != null
                          ? Number(link.prix_achat).toFixed(2)
                          : '--'}{' '}
                        EUR
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
