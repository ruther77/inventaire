import { Package, Euro, AlertTriangle, TrendingUp } from 'lucide-react';
import MetricCard, { MetricCardGroup } from '../../../components/ui/MetricCard.jsx';

/**
 * DashboardMetrics - Grille de KPIs avec états loading et interactions
 * Pattern: Skeleton loading, click-to-filter, expandable details
 */
export default function DashboardMetrics({
  kpis,
  analytics,
  loading = false,
  onMetricClick,
}) {
  const formatNumber = (value) => {
    if (value === undefined || value === null) return '—';
    return Number(value).toLocaleString('fr-FR');
  };

  const formatCurrency = (value) => {
    if (value === undefined || value === null) return '—';
    return `${Number(value).toLocaleString('fr-FR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })} €`;
  };

  const metrics = [
    {
      id: 'total_produits',
      label: 'Références',
      value: formatNumber(kpis?.total_produits),
      hint: 'Produits actifs',
      icon: Package,
      onClick: () => onMetricClick?.('products'),
    },
    {
      id: 'valeur_stock',
      label: 'Valeur stock HT',
      value: formatCurrency(kpis?.valeur_stock_ht),
      hint: `${formatNumber(kpis?.quantite_stock_total)} unités`,
      icon: Euro,
      trend: kpis?.valeur_stock_trend,
      trendLabel: 'vs mois dernier',
      onClick: () => onMetricClick?.('stock-value'),
    },
    {
      id: 'alertes',
      label: 'Alertes stock',
      value: kpis?.alerte_stock_bas ?? '—',
      hint: `${kpis?.stock_epuise ?? 0} rupture(s)`,
      icon: AlertTriangle,
      status: kpis?.alerte_stock_bas > 5 ? 'warning' : kpis?.alerte_stock_bas > 0 ? 'info' : undefined,
      trend: kpis?.alerte_stock_bas > 0 ? `+${kpis.alerte_stock_bas}` : undefined,
      onClick: () => onMetricClick?.('alerts'),
    },
    {
      id: 'actives',
      label: 'Références actives',
      value: formatNumber(analytics?.active),
      hint: `${analytics?.categories ?? 0} familles suivies`,
      icon: TrendingUp,
      onClick: () => onMetricClick?.('active'),
    },
  ];

  return (
    <MetricCardGroup columns={4}>
      {metrics.map((metric) => (
        <MetricCard
          key={metric.id}
          label={metric.label}
          value={metric.value}
          hint={metric.hint}
          icon={metric.icon}
          trend={metric.trend}
          trendLabel={metric.trendLabel}
          status={metric.status}
          loading={loading}
          onClick={metric.onClick}
        />
      ))}
    </MetricCardGroup>
  );
}

/**
 * DashboardMetricsCompact - Version compacte pour sidebar ou mobile
 */
export function DashboardMetricsCompact({ kpis, loading }) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex justify-between animate-pulse">
            <div className="h-4 w-24 bg-slate-200 rounded" />
            <div className="h-4 w-16 bg-slate-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  const items = [
    { label: 'Références', value: kpis?.total_produits },
    { label: 'Stock HT', value: `${(kpis?.valeur_stock_ht / 1000).toFixed(0)}k €` },
    { label: 'Alertes', value: kpis?.alerte_stock_bas, highlight: kpis?.alerte_stock_bas > 0 },
    { label: 'Ruptures', value: kpis?.stock_epuise, highlight: kpis?.stock_epuise > 0 },
  ];

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.label} className="flex items-center justify-between py-1.5">
          <span className="text-sm text-slate-600">{item.label}</span>
          <span
            className={`font-semibold ${
              item.highlight ? 'text-amber-600' : 'text-slate-900'
            }`}
          >
            {item.value ?? '—'}
          </span>
        </div>
      ))}
    </div>
  );
}
