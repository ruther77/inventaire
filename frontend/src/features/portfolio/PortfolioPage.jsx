import { useState } from 'react';
import { Briefcase, TrendingUp, Building2, Wallet } from 'lucide-react';
import { usePortfolio } from '../../hooks/usePortfolio.js';
import Card from '../../components/ui/Card.jsx';
import EmptyState, { EmptyData } from '../../components/ui/EmptyState.jsx';
import Skeleton from '../../components/ui/Skeleton.jsx';

function SummaryCard({ title, value, subtitle, icon: Icon }) {
  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="p-2 rounded-lg bg-orange-500/10">
            <Icon className="h-5 w-5 text-orange-400" />
          </div>
        )}
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="text-2xl font-semibold text-white mt-1">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
      </div>
    </Card>
  );
}

function LatestPricesChart({ items }) {
  if (!items || !items.length) {
    return <EmptyData className="py-6" />;
  }
  const maxPrice = Math.max(...items.map((item) => Number(item.prix_achat) || 0), 1);
  return (
    <div className="space-y-3">
      {items.map((item) => {
        const value = Number(item.prix_achat) || 0;
        const width = Math.min(100, (value / maxPrice) * 100);
        return (
          <div key={`${item.code}-${item.created_at}`} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-300">{item.code}</span>
              <span className="text-amber-400 font-medium">{value.toFixed(2)} €</span>
            </div>
            <div className="h-2 rounded-full bg-white/5">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-orange-500 to-amber-400"
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PortfolioPage() {
  const [selectedEntity, setSelectedEntity] = useState('global');

  const { entities, globalSummary, latestPrices, isLoading } = usePortfolio();

  if (!isLoading && !entities.length && !globalSummary.total_assets) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-orange-400">Portefeuille consolidé</h1>
          <p className="text-sm text-slate-400">Suivi du stock et de la trésorerie par business.</p>
        </div>
        <Card className="p-8">
          <EmptyState
            icon={Briefcase}
            title="Aucune donnée de portefeuille"
            description="Les données de votre portefeuille apparaîtront ici une fois que vous aurez configuré vos entités et importé des transactions."
            size="lg"
          />
        </Card>
      </div>
    );
  }

  const displayEntities =
    selectedEntity === 'global' ? entities : entities.filter((entity) => entity.code === selectedEntity);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-orange-400">Portefeuille consolidé</h1>
        <p className="text-sm text-slate-400">Suivi du stock et de la trésorerie par business.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard
          icon={TrendingUp}
          title="Capital global"
          value={`${globalSummary.total_assets.toLocaleString('fr-FR')} €`}
          subtitle="Stocks + trésorerie"
        />
        <SummaryCard
          icon={Wallet}
          title="Trésorerie disponible"
          value={`${(globalSummary.bank_balance + globalSummary.cash_balance).toLocaleString('fr-FR')} €`}
          subtitle="Banque + caisse"
        />
        <SummaryCard
          icon={Building2}
          title="Stocks valorisés"
          value={`${globalSummary.stock_value.toLocaleString('fr-FR')} €`}
          subtitle="Dernier prix connu"
        />
      </div>

      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-400">Filtrer par entité :</span>
        <select
          value={selectedEntity}
          onChange={(event) => setSelectedEntity(event.target.value)}
          className="border border-white/10 rounded-lg bg-white/5 px-3 py-2 text-sm text-white focus:border-orange-500/50 focus:outline-none"
        >
          <option value="global" className="bg-slate-800">Global</option>
          {entities.map((entity) => (
            <option key={entity.entity_id} value={entity.code} className="bg-slate-800">
              {entity.code}
            </option>
          ))}
        </select>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-amber-400">Par entité</h2>
        <div className="space-y-4">
          {displayEntities.length ? (
            displayEntities.map((entity) => (
              <Card key={entity.entity_id} className="p-4 space-y-4">
                <div>
                  <p className="text-sm text-slate-500">{entity.code}</p>
                  <p className="text-lg font-bold text-white">{entity.name}</p>
                  <div className="grid grid-cols-2 gap-2 text-sm mt-3">
                    <div>
                      <p className="text-slate-500">Stock</p>
                      <p className="font-medium text-white">{entity.stock_value.toLocaleString('fr-FR')} €</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Banque</p>
                      <p className="font-medium text-white">{entity.bank_balance.toLocaleString('fr-FR')} €</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Caisse</p>
                      <p className="font-medium text-white">{entity.cash_balance.toLocaleString('fr-FR')} €</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Total</p>
                      <p className="font-medium text-amber-400">{entity.total_assets.toLocaleString('fr-FR')} €</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs uppercase tracking-wider text-slate-500">Business units</p>
                  {entity.members.length ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {entity.members.map((tenant) => (
                        <div key={tenant.tenant_id} className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm">
                          <p className="font-semibold text-white">{tenant.name}</p>
                          <div className="mt-1 grid grid-cols-2 gap-1 text-xs text-slate-400">
                            <span>Stock</span>
                            <span className="text-right text-slate-300">{tenant.stock_value.toLocaleString('fr-FR')} €</span>
                            <span>Banque</span>
                            <span className="text-right text-slate-300">{tenant.bank_balance.toLocaleString('fr-FR')} €</span>
                            <span>Caisse</span>
                            <span className="text-right text-slate-300">{tenant.cash_balance.toLocaleString('fr-FR')} €</span>
                            <span>Total</span>
                            <span className="text-right text-amber-400 font-semibold">
                              {tenant.total_assets.toLocaleString('fr-FR')} €
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">Aucun tenant rattaché.</p>
                  )}
                </div>
              </Card>
            ))
          ) : (
            <Card className="p-4">
              <p className="text-sm text-slate-400">Aucune entité sélectionnée.</p>
            </Card>
          )}
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-amber-400">Derniers prix connus</h2>
          <p className="text-xs text-slate-500">Les lignes les plus récentes par code</p>
        </div>
        <div className="grid gap-6">
          <Card className="p-4">
            <LatestPricesChart items={latestPrices} />
          </Card>
          <Card className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Fournisseur</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Prix achat</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Quantité</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Date facture</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {latestPrices.map((item) => (
                  <tr key={`${item.code}-${item.created_at}`} className="hover:bg-white/5">
                    <td className="px-4 py-3 text-white font-medium">{item.code}</td>
                    <td className="px-4 py-3 text-slate-300">{item.fournisseur || '—'}</td>
                    <td className="px-4 py-3 text-amber-400 font-medium">
                      {Number(item.prix_achat).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} €
                    </td>
                    <td className="px-4 py-3 text-slate-300">{item.quantite ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-300">
                      {item.facture_date ? new Date(item.facture_date).toLocaleDateString('fr-FR') : '—'}
                      <details className="text-xs text-slate-500 mt-1">
                        <summary className="cursor-pointer hover:text-slate-400">Détails</summary>
                        {item.source_context ? (
                          <p className="mt-1">Contexte : {item.source_context}</p>
                        ) : (
                          <p className="mt-1">Aucun contexte fourni.</p>
                        )}
                        <p>Créé le : {item.created_at ? new Date(item.created_at).toLocaleString('fr-FR') : '—'}</p>
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      </section>
    </div>
  );
}

export { SummaryCard, LatestPricesChart };
export default PortfolioPage;
