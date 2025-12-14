import { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus, Award } from 'lucide-react';
import DataTable from '../../../components/ui/DataTable.jsx';
import Badge from '../../../components/ui/Badge.jsx';

/**
 * SupplierScoringTable - Table des fournisseurs avec scores
 * Affiche la liste des fournisseurs avec tri, filtres et pagination
 */
export default function SupplierScoringTable({
  suppliers = [],
  loading = false,
  onSupplierClick,
  selectedSupplierId = null,
}) {
  const getScoreColor = (score) => {
    if (score >= 75) return 'text-emerald-400';
    if (score >= 50) return 'text-amber-400';
    return 'text-rose-400';
  };

  const getScoreBadgeVariant = (score) => {
    if (score >= 75) return 'success-solid';
    if (score >= 50) return 'warning-solid';
    return 'error-solid';
  };

  const getTrendIcon = (trend) => {
    if (trend === 'improving' || trend > 0) return TrendingUp;
    if (trend === 'declining' || trend < 0) return TrendingDown;
    return Minus;
  };

  const getTrendColor = (trend) => {
    if (trend === 'improving' || trend > 0) return 'text-emerald-400';
    if (trend === 'declining' || trend < 0) return 'text-rose-400';
    return 'text-slate-400';
  };

  const columns = useMemo(
    () => [
      {
        key: 'rank',
        header: 'Rang',
        width: '60px',
        sortable: true,
        render: (_, row, index) => (
          <div className="flex items-center gap-2">
            {index === 0 && <Award className="h-4 w-4 text-amber-400" />}
            <span className="font-mono text-sm text-slate-300">#{index + 1}</span>
          </div>
        ),
      },
      {
        key: 'name',
        header: 'Fournisseur',
        sortable: true,
        render: (value, row) => (
          <div>
            <p className="font-medium text-white">{value}</p>
            <p className="text-xs text-slate-400">
              {row.data_points || 0} facture{(row.data_points || 0) > 1 ? 's' : ''}
            </p>
          </div>
        ),
      },
      {
        key: 'overall_score',
        header: 'Score',
        sortable: true,
        align: 'center',
        getValue: (row) => row.overall_score * 100,
        render: (value, row) => {
          const score = Math.round((row.overall_score || 0) * 100);
          return (
            <div className="flex flex-col items-center gap-1">
              <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                {score}
              </span>
              <Badge variant={getScoreBadgeVariant(score)} size="xs">
                {score >= 75 ? 'Excellent' : score >= 50 ? 'Moyen' : 'Faible'}
              </Badge>
            </div>
          );
        },
      },
      {
        key: 'trend',
        header: 'Tendance',
        sortable: true,
        align: 'center',
        render: (value, row) => {
          const TrendIcon = getTrendIcon(value);
          const trendColor = getTrendColor(value);
          const trendLabel =
            value === 'improving' || value > 0
              ? 'En hausse'
              : value === 'declining' || value < 0
                ? 'En baisse'
                : 'Stable';

          return (
            <div className="flex items-center justify-center gap-2">
              <TrendIcon className={`h-4 w-4 ${trendColor}`} />
              <span className={`text-sm ${trendColor}`}>{trendLabel}</span>
            </div>
          );
        },
      },
      {
        key: 'price_stability_score',
        header: 'Prix',
        sortable: true,
        align: 'center',
        getValue: (row) => (row.price_stability_score || 0) * 100,
        render: (value, row) => {
          const score = Math.round((row.price_stability_score || 0) * 100);
          return (
            <span className={`font-semibold ${getScoreColor(score)}`}>
              {score}
            </span>
          );
        },
      },
      {
        key: 'delivery_reliability_score',
        header: 'Livraison',
        sortable: true,
        align: 'center',
        getValue: (row) => (row.delivery_reliability_score || 0) * 100,
        render: (value, row) => {
          const score = Math.round((row.delivery_reliability_score || 0) * 100);
          return (
            <span className={`font-semibold ${getScoreColor(score)}`}>
              {score}
            </span>
          );
        },
      },
      {
        key: 'invoice_accuracy_score',
        header: 'Factures',
        sortable: true,
        align: 'center',
        getValue: (row) => (row.invoice_accuracy_score || 0) * 100,
        render: (value, row) => {
          const score = Math.round((row.invoice_accuracy_score || 0) * 100);
          return (
            <span className={`font-semibold ${getScoreColor(score)}`}>
              {score}
            </span>
          );
        },
      },
      {
        key: 'last_calculated',
        header: 'Dernière MAJ',
        sortable: true,
        render: (value) => {
          if (!value) return <span className="text-slate-500">—</span>;
          const date = new Date(value);
          return (
            <span className="text-sm text-slate-300">
              {date.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: 'short',
              })}
            </span>
          );
        },
      },
    ],
    []
  );

  const handleExport = (data) => {
    const csvContent = [
      ['Fournisseur', 'Score Global', 'Tendance', 'Prix', 'Livraison', 'Factures', 'Factures Analysées', 'Dernière MAJ'],
      ...data.map((row) => [
        row.name,
        Math.round((row.overall_score || 0) * 100),
        row.trend || 'stable',
        Math.round((row.price_stability_score || 0) * 100),
        Math.round((row.delivery_reliability_score || 0) * 100),
        Math.round((row.invoice_accuracy_score || 0) * 100),
        row.data_points || 0,
        row.last_calculated || 'N/A',
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `supplier-scoring-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <DataTable
      data={suppliers}
      columns={columns}
      loading={loading}
      pagination
      pageSize={10}
      sortable
      defaultSort={{ key: 'overall_score', direction: 'desc' }}
      searchable
      searchPlaceholder="Rechercher un fournisseur..."
      onRowClick={(row) => onSupplierClick?.(row)}
      rowClassName={(row) =>
        row.name === selectedSupplierId
          ? 'bg-blue-500/10 border-l-2 border-blue-500'
          : ''
      }
      exportable
      onExport={handleExport}
      emptyMessage="Aucun fournisseur analysé"
      compact
      striped
    />
  );
}
