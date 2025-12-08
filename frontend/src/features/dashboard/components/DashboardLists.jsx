import { useMemo } from 'react';
import clsx from 'clsx';
import { TrendingUp, TrendingDown, AlertTriangle, Package, Truck } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import { ListSkeleton } from '../../../components/ui/Skeleton.jsx';
import { EmptyList } from '../../../components/ui/EmptyState.jsx';
import { StatusBadge } from '../../../components/ui/Badge.jsx';
import Tooltip from '../../../components/ui/Tooltip.jsx';

/**
 * DashboardList - Liste générique avec ranking, loading et empty states
 * Pattern: Polymorphic rendering, status indicators, hover actions
 */
export function DashboardList({
  title,
  subtitle,
  items = [],
  loading = false,
  emptyMessage = 'Aucune donnée',
  valueKey = 'value',
  labelKey = 'nom',
  renderItem,
  showRank = false,
  maxItems = 5,
  suffix = '',
  onItemClick,
}) {
  const displayItems = items.slice(0, maxItems);

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div>
        {subtitle && (
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            {subtitle}
          </p>
        )}
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      </div>

      {/* Content */}
      {loading ? (
        <ListSkeleton items={maxItems} />
      ) : displayItems.length === 0 ? (
        <p className="text-sm text-slate-500 py-4">{emptyMessage}</p>
      ) : (
        <ul className="space-y-2">
          {displayItems.map((item, index) => (
            <li key={`${item[labelKey]}-${index}`}>
              {renderItem ? (
                renderItem(item, index)
              ) : (
                <DefaultListItem
                  item={item}
                  index={index}
                  labelKey={labelKey}
                  valueKey={valueKey}
                  showRank={showRank}
                  suffix={suffix}
                  onClick={onItemClick ? () => onItemClick(item) : undefined}
                />
              )}
            </li>
          ))}
        </ul>
      )}

      {/* Footer - voir plus */}
      {!loading && items.length > maxItems && (
        <button
          type="button"
          className="text-xs text-brand-600 hover:text-brand-700 font-medium text-left"
        >
          Voir les {items.length - maxItems} autres →
        </button>
      )}
    </div>
  );
}

/**
 * DefaultListItem - Item de liste par défaut
 */
function DefaultListItem({
  item,
  index,
  labelKey,
  valueKey,
  showRank,
  suffix,
  onClick,
}) {
  const value = item[valueKey];
  const formattedValue = typeof value === 'number'
    ? value.toLocaleString('fr-FR')
    : value;

  return (
    <div
      className={clsx(
        'flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2 text-sm',
        'transition-all duration-150',
        onClick && 'cursor-pointer hover:bg-slate-50 hover:border-slate-200'
      )}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="flex items-center gap-3 min-w-0">
        {showRank && (
          <span
            className={clsx(
              'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold',
              index === 0 && 'bg-amber-100 text-amber-700',
              index === 1 && 'bg-slate-200 text-slate-600',
              index === 2 && 'bg-orange-100 text-orange-700',
              index > 2 && 'bg-slate-100 text-slate-500'
            )}
          >
            {index + 1}
          </span>
        )}
        <span className="font-medium text-slate-900 truncate">
          {item[labelKey]}
        </span>
      </div>
      <span className="text-slate-600 flex-shrink-0 ml-2">
        {formattedValue}{suffix}
      </span>
    </div>
  );
}

/**
 * TopStockList - Top des stocks par valeur
 */
export function TopStockList({ items, loading }) {
  return (
    <DashboardList
      title="Top stock (HT)"
      items={items}
      loading={loading}
      valueKey="valeur_stock"
      showRank
      suffix=" €"
      renderItem={(item, index) => (
        <div className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2 text-sm hover:bg-slate-50 transition-colors">
          <div className="flex items-center gap-3">
            <RankBadge rank={index + 1} />
            <div className="min-w-0">
              <p className="font-medium text-slate-900 truncate">{item.nom}</p>
              <p className="text-xs text-slate-500">{item.categorie || 'NC'}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="font-semibold text-slate-900">
              {Number(item.valeur_stock).toLocaleString('fr-FR')} €
            </p>
            <p className="text-xs text-slate-500">
              {item.stock_actuel} u
            </p>
          </div>
        </div>
      )}
    />
  );
}

/**
 * TopSalesList - Top des ventes
 */
export function TopSalesList({ items, loading }) {
  return (
    <DashboardList
      title="Top ventes"
      items={items}
      loading={loading}
      valueKey="quantite_vendue"
      showRank
      suffix=" u"
    />
  );
}

/**
 * SuppliersList - Répartition par fournisseur
 */
export function SuppliersList({ items, loading }) {
  return (
    <DashboardList
      title="Fournisseurs"
      items={items}
      loading={loading}
      labelKey="fournisseur"
      valueKey="valeur"
      suffix=" €"
      renderItem={(item) => (
        <div className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2 text-sm hover:bg-slate-50 transition-colors">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-slate-100 p-1.5">
              <Truck className="h-4 w-4 text-slate-500" />
            </div>
            <span className="font-medium text-slate-900">{item.fournisseur}</span>
          </div>
          <span className="text-slate-600">
            {Number(item.valeur).toLocaleString('fr-FR')} €
          </span>
        </div>
      )}
    />
  );
}

/**
 * MarginAlertsList - Alertes marge
 */
export function MarginAlertsList({ items, loading }) {
  return (
    <DashboardList
      title="Alertes marge"
      subtitle="Produits à surveiller"
      items={items}
      loading={loading}
      labelKey="nom"
      valueKey="marge_pct"
      emptyMessage="Aucune alerte marge"
      renderItem={(item) => {
        const margin = Number(item.marge_pct);
        const isLow = margin < 10;
        const isNegative = margin < 0;

        return (
          <div className="flex items-center justify-between rounded-2xl border border-slate-100 px-3 py-2 text-sm hover:bg-slate-50 transition-colors">
            <div className="flex items-center gap-2 min-w-0">
              {isNegative ? (
                <AlertTriangle className="h-4 w-4 text-rose-500 flex-shrink-0" />
              ) : isLow ? (
                <TrendingDown className="h-4 w-4 text-amber-500 flex-shrink-0" />
              ) : (
                <TrendingUp className="h-4 w-4 text-emerald-500 flex-shrink-0" />
              )}
              <span className="font-medium text-slate-900 truncate">{item.nom}</span>
            </div>
            <span
              className={clsx(
                'font-semibold',
                isNegative && 'text-rose-600',
                isLow && !isNegative && 'text-amber-600',
                !isLow && 'text-slate-600'
              )}
            >
              {margin.toFixed(1)} %
            </span>
          </div>
        );
      }}
    />
  );
}

/**
 * LowStockList - Produits en stock bas
 */
export function LowStockList({ items, loading, onReorder }) {
  return (
    <DashboardList
      title="Stock critique"
      subtitle="Réapprovisionnement conseillé"
      items={items}
      loading={loading}
      emptyMessage="Aucun stock critique"
      renderItem={(item) => {
        const stock = item.stock_actuel ?? 0;
        const threshold = item.seuil_alerte ?? 8;
        const isOut = stock === 0;
        const percentage = Math.min(100, (stock / threshold) * 100);

        return (
          <div className="rounded-2xl border border-slate-100 px-3 py-2 text-sm hover:bg-slate-50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-slate-900 truncate">{item.nom}</span>
              <StatusBadge status={isOut ? 'critical' : 'low'} />
            </div>
            <div className="flex items-center gap-3">
              {/* Progress bar */}
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all',
                    isOut ? 'bg-rose-500' : 'bg-amber-500'
                  )}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="text-xs text-slate-500">
                {stock}/{threshold}
              </span>
            </div>
          </div>
        );
      }}
    />
  );
}

/**
 * RankBadge - Badge de classement
 */
function RankBadge({ rank }) {
  return (
    <span
      className={clsx(
        'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold',
        rank === 1 && 'bg-amber-100 text-amber-700',
        rank === 2 && 'bg-slate-200 text-slate-600',
        rank === 3 && 'bg-orange-100 text-orange-700',
        rank > 3 && 'bg-slate-100 text-slate-500'
      )}
    >
      {rank}
    </span>
  );
}

/**
 * DashboardListsGrid - Grille de listes pour le dashboard
 */
export default function DashboardListsGrid({ data, loading = false }) {
  return (
    <Card className="grid gap-6 lg:grid-cols-3 p-6">
      <TopStockList items={data?.top_stock_value} loading={loading} />
      <TopSalesList items={data?.top_sales} loading={loading} />
      <SuppliersList items={data?.supplier_breakdown} loading={loading} />
    </Card>
  );
}
