import { useEffect, useState } from 'react';
import { fetchCapitalOverview } from '../../api/client.js';

function SummaryCard({ title, value, subtitle }) {
  return (
    <div className="border rounded px-4 py-3 bg-white shadow-sm">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-semibold">{value}</p>
      {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
    </div>
  );
}

function LatestPricesChart({ items }) {
  if (!items || !items.length) {
    return <p className="text-sm text-gray-500">Aucune donnée de prix récente.</p>;
  }
  const maxPrice = Math.max(...items.map((item) => Number(item.prix_achat) || 0), 1);
  return (
    <div className="space-y-2">
      {items.map((item) => {
        const value = Number(item.prix_achat) || 0;
        const width = Math.min(100, (value / maxPrice) * 100);
        return (
          <div key={`${item.code}-${item.created_at}`} className="space-y-1">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{item.code}</span>
              <span>{value.toFixed(2)} €</span>
            </div>
            <div className="h-2 rounded bg-gray-200">
              <div
                className="h-2 rounded bg-gradient-to-r from-blue-500 to-teal-400"
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PortfolioPage({ initialData = null }) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(initialData === null);
  const [selectedEntity, setSelectedEntity] = useState('global');

  useEffect(() => {
    if (initialData) {
      return;
    }

    setLoading(true);
    fetchCapitalOverview()
      .then((response) => setData(response))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p>Chargement du portefeuille...</p>;
  }

  if (!data) {
    return <p>Aucune donnée disponible.</p>;
  }

  const {
    entities = [],
    global_summary: globalSummary = {
      stock_value: 0,
      bank_balance: 0,
      cash_balance: 0,
      total_assets: 0,
    },
    latest_prices: latestPricesRaw = [],
  } = data;
  const latestPrices = Array.isArray(latestPricesRaw) ? latestPricesRaw : [];
  const displayEntities =
    selectedEntity === 'global' ? entities : entities.filter((entity) => entity.code === selectedEntity);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Portefeuille consolidé</h1>
        <p className="text-sm text-gray-500">Suivi du stock et de la trésorerie par business.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <SummaryCard
          title="Capital global"
          value={`${globalSummary.total_assets.toLocaleString('fr-FR')} €`}
          subtitle="Stocks + trésorerie"
        />
        <SummaryCard
          title="Trésorerie disponible"
          value={`${(globalSummary.bank_balance + globalSummary.cash_balance).toLocaleString('fr-FR')} €`}
          subtitle="Banque + caisse"
        />
        <SummaryCard
          title="Stocks valorisés"
          value={`${globalSummary.stock_value.toLocaleString('fr-FR')} €`}
          subtitle="Dernier prix connu"
        />
      </div>

      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-600">Filtrer par entité :</span>
        <select
          value={selectedEntity}
          onChange={(event) => setSelectedEntity(event.target.value)}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="global">Global</option>
          {entities.map((entity) => (
            <option key={entity.entity_id} value={entity.code}>
              {entity.code}
            </option>
          ))}
        </select>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Par entité</h2>
        <div className="space-y-4">
          {displayEntities.length ? (
            displayEntities.map((entity) => (
              <div key={entity.entity_id} className="border rounded p-4 bg-white shadow-sm space-y-4">
                <div>
                  <p className="text-sm text-gray-500">{entity.code}</p>
                  <p className="text-lg font-bold">{entity.name}</p>
                  <div className="grid grid-cols-2 gap-2 text-sm mt-3">
                    <div>
                      <p className="text-gray-400">Stock</p>
                      <p className="font-medium">{entity.stock_value.toLocaleString('fr-FR')} €</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Banque</p>
                      <p className="font-medium">{entity.bank_balance.toLocaleString('fr-FR')} €</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Caisse</p>
                      <p className="font-medium">{entity.cash_balance.toLocaleString('fr-FR')} €</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Total</p>
                      <p className="font-medium">{entity.total_assets.toLocaleString('fr-FR')} €</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs uppercase text-gray-400">Business units</p>
                  {entity.members.length ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {entity.members.map((tenant) => (
                        <div key={tenant.tenant_id} className="rounded border px-3 py-2 text-sm">
                          <p className="font-semibold">{tenant.name}</p>
                          <div className="mt-1 grid grid-cols-2 gap-1 text-xs text-gray-500">
                            <span>Stock</span>
                            <span className="text-right">{tenant.stock_value.toLocaleString('fr-FR')} €</span>
                            <span>Banque</span>
                            <span className="text-right">{tenant.bank_balance.toLocaleString('fr-FR')} €</span>
                            <span>Caisse</span>
                            <span className="text-right">{tenant.cash_balance.toLocaleString('fr-FR')} €</span>
                            <span>Total</span>
                            <span className="text-right text-gray-900 font-semibold">
                              {tenant.total_assets.toLocaleString('fr-FR')} €
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Aucun tenant rattaché.</p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="border rounded p-4 bg-white text-sm text-gray-500">Aucune entité sélectionnée.</div>
          )}
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Derniers prix connus</h2>
          <p className="text-xs text-gray-500">Les lignes les plus récentes par code</p>
        </div>
        <div className="grid gap-6">
          <div className="border rounded px-4 py-3 bg-white shadow-sm">
            <LatestPricesChart items={latestPrices} />
          </div>
          <div className="overflow-x-auto border rounded bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Code</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Fournisseur</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Prix achat</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Quantité</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date facture</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {latestPrices.map((item) => (
                  <tr key={`${item.code}-${item.created_at}`}>
                    <td className="px-4 py-2">{item.code}</td>
                    <td className="px-4 py-2">{item.fournisseur || '—'}</td>
                    <td className="px-4 py-2">
                      {Number(item.prix_achat).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} €
                    </td>
                    <td className="px-4 py-2">{item.quantite ?? '—'}</td>
                    <td className="px-4 py-2">
                      {item.facture_date ? new Date(item.facture_date).toLocaleDateString('fr-FR') : '—'}
                      <details className="text-xs text-gray-400">
                        <summary>Détails</summary>
                        {item.source_context ? (
                          <p>Contexte : {item.source_context}</p>
                        ) : (
                          <p>Aucun contexte fourni.</p>
                        )}
                        <p>Créé le : {item.created_at ? new Date(item.created_at).toLocaleString('fr-FR') : '—'}</p>
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

export { SummaryCard, LatestPricesChart };
export default PortfolioPage;
