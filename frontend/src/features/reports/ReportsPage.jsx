import { useState } from 'react';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Download, RefreshCw } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import MetricCard from '../../components/ui/MetricCard.jsx';
import Button from '../../components/ui/Button.jsx';
import api from '../../api/client.js';
import { useReportsOverview } from '../../hooks/useReports.js';

const chartColors = ['#2563eb', '#0891b2', '#16a34a', '#f97316', '#f43f5e', '#c026d3'];

const exportConfigs = [
  { type: 'stock', label: 'Inventaire complet' },
  { type: 'alerts', label: 'Produits sous seuil' },
  { type: 'rotation', label: 'Rotation 30 jours' },
  { type: 'negative_stock', label: 'Stocks négatifs' },
];

export default function ReportsPage() {
  const overviewQuery = useReportsOverview();
  const data = overviewQuery.data;
  const [exportingType, setExportingType] = useState('');
  const [exportError, setExportError] = useState('');

  const kpis = data?.kpis ?? {
    total_products: 0,
    units_available: 0,
    stock_value: 0,
    alert_count: 0,
    negative_count: 0,
  };

  const resolveFilename = (header, fallback) => {
    if (!header) return fallback;
    const match = /filename="?([^"]+)"?/i.exec(header);
    return match?.[1] ?? fallback;
  };

  const handleExport = async (type) => {
    setExportError('');
    setExportingType(type);
    try {
      const response = await api.get(`/reports/export/${type}`, {
        responseType: 'blob',
      });
      const filename = resolveFilename(
        response.headers?.['content-disposition'],
        `rapport_${type}.csv`,
      );
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      setExportError("Impossible d'exporter ce rapport. Vérifiez la connexion API.");
    } finally {
      setExportingType('');
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 text-white">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-300">rapports consolidés</p>
            <h1 className="text-3xl font-semibold">Pilotage catalogue & couverture</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-200">
              Analysez la santé des rayons, identifiez les alertes critiques et exportez un cliché
              exploitable pour vos revues hebdomadaires. Les données proviennent directement du
              moteur FastAPI, prêtes à partager.
            </p>
          </div>
          <Button
            variant="ghost"
            iconOnly
            aria-label="Actualiser les données"
            onClick={() => overviewQuery.refetch()}
          >
            <RefreshCw className={overviewQuery.isFetching ? 'animate-spin' : ''} />
          </Button>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Références actives"
          value={kpis.total_products.toLocaleString('fr-FR')}
          hint={`${kpis.units_available.toLocaleString('fr-FR')} unités`}
        />
        <MetricCard
          label="Valeur stock HT"
          value={`${kpis.stock_value.toLocaleString('fr-FR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          })} €`}
          hint="Basé sur les prix de vente"
        />
        <MetricCard
          label="Alertes seuil"
          value={kpis.alert_count.toLocaleString('fr-FR')}
          hint="Produits à traiter"
        />
        <MetricCard
          label="Stocks négatifs"
          value={kpis.negative_count.toLocaleString('fr-FR')}
          hint="Validation mouvement requise"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="h-[360px]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-slate-400">par catégorie</p>
              <h3 className="text-lg font-semibold text-slate-900">Répartition des volumes</h3>
            </div>
          </div>
          {overviewQuery.isLoading && <p className="text-sm text-slate-500">Chargement…</p>}
          {overviewQuery.isError && (
            <p className="text-sm text-rose-500">Impossible de calculer la répartition.</p>
          )}
          {data?.category_breakdown?.length > 0 && (
            <ResponsiveContainer width="100%" height="85%">
              <PieChart>
                <Pie
                  data={data.category_breakdown}
                  dataKey="value"
                  nameKey="category"
                  innerRadius={60}
                  outerRadius={110}
                  paddingAngle={4}
                >
                  {data.category_breakdown.map((entry, index) => (
                    <Cell
                      key={`cell-${entry.category}`}
                      fill={chartColors[index % chartColors.length]}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => value.toLocaleString('fr-FR')} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card className="h-[360px]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-slate-400">rotation 30j</p>
              <h3 className="text-lg font-semibold text-slate-900">Entrées vs sorties</h3>
            </div>
          </div>
          {data?.rotation?.length ? (
            <ResponsiveContainer width="100%" height="85%">
              <BarChart data={data.rotation.slice(0, 8)}>
                <XAxis dataKey="nom" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="sorties_30j" radius={[8, 8, 0, 0]} fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500">Pas de mouvements consignés sur 30 jours.</p>
          )}
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900">Top valorisation</h3>
            <span className="text-xs uppercase tracking-[0.3em] text-slate-400">achat</span>
          </div>
          <div className="space-y-3">
            {(data?.top_value ?? []).map((entry) => (
              <div
                key={entry.id}
                className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2"
              >
                <div>
                  <p className="font-medium text-slate-900">{entry.nom}</p>
                  <p className="text-xs text-slate-500">
                    {entry.stock.toLocaleString('fr-FR')} u • {entry.prix_achat?.toFixed(2) ?? '—'} €
                  </p>
                </div>
                <p className="text-sm font-semibold text-slate-900">
                  {entry.valeur_achat.toLocaleString('fr-FR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{' '}
                  €
                </p>
              </div>
            ))}
            {!data?.top_value?.length && (
              <p className="text-sm text-slate-500">Aucun produit valorisé disponible.</p>
            )}
          </div>
        </Card>

        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900">Flux fournisseurs (30 j)</h3>
            <span className="text-xs uppercase tracking-[0.3em] text-slate-400">entrées</span>
          </div>
          <div className="space-y-3">
            {(data?.supplier_inflows ?? []).map((entry) => (
              <div
                key={entry.fournisseur}
                className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2"
              >
                <div>
                  <p className="font-medium text-slate-900">{entry.fournisseur}</p>
                  <p className="text-xs text-slate-500">
                    {entry.quantite?.toLocaleString('fr-FR') ?? 0} u
                  </p>
                </div>
                <p className="text-sm font-semibold text-slate-900">
                  {(entry.valeur ?? 0).toLocaleString('fr-FR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{' '}
                  €
                </p>
              </div>
            ))}
            {!data?.supplier_inflows?.length && (
              <p className="text-sm text-slate-500">Aucun mouvement d&apos;entrée analysable.</p>
            )}
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ReportTable
          title="Produits sous seuil"
          subtitle="À prioriser pour l'approvisionnement"
          rows={data?.low_stock ?? []}
          emptyLabel="Aucune alerte de stock."
        />
        <ReportTable
          title="Stocks négatifs"
          subtitle="À corriger dans les mouvements"
          rows={data?.negative_stock ?? []}
          emptyLabel="Aucun stock négatif détecté."
        />
      </div>

      <Card className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">exports csv</p>
          <h3 className="text-lg font-semibold text-slate-900">Partager les rapports</h3>
        </div>
        <div className="flex flex-wrap gap-3">
          {exportConfigs.map((config) => (
            <Button
              key={config.type}
              variant="ghost"
              size="md"
              onClick={() => handleExport(config.type)}
              disabled={exportingType === config.type}
            >
              <Download className="h-4 w-4" />
              {exportingType === config.type ? 'Export…' : config.label}
            </Button>
          ))}
        </div>
        {exportError && <p className="text-sm text-rose-600">{exportError}</p>}
      </Card>
    </div>
  );
}

function ReportTable({ title, subtitle, rows, emptyLabel }) {
  return (
    <Card className="flex flex-col gap-3">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{subtitle}</p>
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">{emptyLabel}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                <th className="px-3 py-2">Produit</th>
                <th className="px-3 py-2">Catégorie</th>
                <th className="px-3 py-2">Stock</th>
                <th className="px-3 py-2">Seuil</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {rows.map((row) => (
                <tr key={row.id}>
                  <td className="px-3 py-2 text-slate-900">{row.nom}</td>
                  <td className="px-3 py-2 text-slate-500">{row.categorie ?? '—'}</td>
                  <td className="px-3 py-2 font-semibold text-slate-900">
                    {row.stock_actuel?.toLocaleString('fr-FR')}
                  </td>
                  <td className="px-3 py-2 text-slate-500">
                    {row.seuil_alerte?.toLocaleString('fr-FR') ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
