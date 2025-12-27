import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  FileText,
  AlertTriangle,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  ShoppingCart,
  DollarSign,
  ArrowRight
} from 'lucide-react';
import { useProducts } from '@/hooks/useProducts.js';
import { useDashboardMetrics } from '@/hooks/useDashboard.js';
import Button from '@/components/ui/Button.jsx';

// KPI Card Component
function KPICard({ label, value, trend, trendDirection, color, onClick }) {
  return (
    <div
      className="bg-white/5 border border-white/10 rounded-2xl p-6 cursor-pointer transition-all hover:bg-white/10 hover:-translate-y-0.5"
      onClick={onClick}
    >
      <p className="text-xs uppercase tracking-wider text-slate-400 mb-2">{label}</p>
      <p className={`text-3xl font-bold font-display mb-2 ${color || 'text-white'}`}>
        {value}
      </p>
      {trend && (
        <div className={`text-sm flex items-center gap-1 ${
          trendDirection === 'up' ? 'text-emerald-400' :
          trendDirection === 'down' ? 'text-rose-400' : 'text-slate-400'
        }`}>
          {trendDirection === 'up' && <TrendingUp className="w-4 h-4" />}
          {trendDirection === 'down' && <TrendingDown className="w-4 h-4" />}
          {trend}
        </div>
      )}
    </div>
  );
}

// Chart Bar Component
function ChartBar({ height, label, value, onClick }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className="w-10 bg-gradient-to-t from-teal-500 to-emerald-400 rounded-t-md cursor-pointer transition-all hover:opacity-80 hover:scale-y-105 origin-bottom"
        style={{ height: `${height}%` }}
        onClick={onClick}
      />
      <span className="text-xs text-slate-500">{label}</span>
    </div>
  );
}

// Alert Item Component
function AlertItem({ icon, iconBg, title, description, actionLabel, onAction, onClick }) {
  return (
    <div
      className="flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 cursor-pointer transition-all"
      onClick={onClick}
    >
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${iconBg}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{title}</p>
        <p className="text-xs text-slate-400 truncate">{description}</p>
      </div>
      <Button
        size="sm"
        variant="brand"
        onClick={(e) => { e.stopPropagation(); onAction?.(); }}
      >
        {actionLabel}
      </Button>
    </div>
  );
}

// Period Button Component
function PeriodButton({ active, children, onClick }) {
  return (
    <button
      className={`px-4 py-2 rounded-lg text-sm transition-all ${
        active
          ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400'
          : 'border border-white/10 text-slate-400 hover:bg-white/5'
      }`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function OperationsPilotage() {
  const navigate = useNavigate();
  const { data: products = [] } = useProducts();
  const { data: dashboardData } = useDashboardMetrics();

  // Calculate KPIs from data
  const kpis = useMemo(() => {
    const apiKpis = dashboardData?.kpis || {};
    const activeProducts = apiKpis.total_produits || products.length;
    const pendingInvoices = apiKpis.pending_invoices || 0;
    const pendingAmount = apiKpis.pending_amount || 0;
    const stockAlertCount = apiKpis.alerte_stock_bas || 0;
    const criticalAlerts = apiKpis.stock_epuise || 0;
    const warningAlerts = stockAlertCount - criticalAlerts;

    return {
      activeProducts,
      pendingInvoices,
      pendingAmount,
      stockAlerts: stockAlertCount,
      criticalAlerts,
      warningAlerts,
      avgRotation: apiKpis.avg_rotation || 0,
    };
  }, [products, dashboardData]);

  // Get top alerts
  const alerts = useMemo(() => {
    const lowStockAlerts = products
      .filter(p => (p.stock_actuel || 0) < (p.seuil_alerte || 10))
      .slice(0, 2)
      .map(p => ({
        type: 'stock',
        icon: '⚠️',
        iconBg: 'bg-rose-500/20',
        title: `Rupture imminente - ${p.nom}`,
        description: `Stock: ${p.stock_actuel || 0}${p.unite || ''} • Seuil: ${p.seuil_alerte || 10}${p.unite || ''}`,
        actionLabel: 'Commander',
        path: '/operations/stock',
      }));

    return [
      ...lowStockAlerts,
      {
        type: 'invoice',
        icon: '📄',
        iconBg: 'bg-amber-500/20',
        title: 'Factures en attente',
        description: `${kpis.pendingInvoices} factures • €${kpis.pendingAmount.toLocaleString()} à traiter`,
        actionLabel: 'Traiter',
        path: '/operations/factures',
      },
    ].slice(0, 3);
  }, [products, kpis]);

  // Chart data from API weekly_variation
  const chartData = useMemo(() => {
    const weeklyData = dashboardData?.weekly_variation || [];
    if (weeklyData.length === 0) {
      // Fallback: pas de données de mouvements
      return [];
    }

    // Calculer les valeurs max pour normaliser les hauteurs
    const maxSorties = Math.max(...weeklyData.map(w => w.sorties || 0), 1);

    return weeklyData.map((week, idx) => {
      const date = new Date(week.semaine);
      const weekNum = Math.ceil((date.getDate() + new Date(date.getFullYear(), date.getMonth(), 1).getDay()) / 7);
      return {
        label: `S${weekNum}`,
        height: Math.round(((week.sorties || 0) / maxSorties) * 100),
        value: week.sorties || 0,
        entrees: week.entrees || 0,
      };
    });
  }, [dashboardData]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-display text-white">Pilotage Opérations</h1>
        <p className="text-slate-400 mt-1">Vue d'ensemble de l'activité opérationnelle</p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          label="Produits actifs"
          value={kpis.activeProducts.toLocaleString()}
          trend="+12 ce mois"
          trendDirection="up"
          onClick={() => navigate('/operations/catalogue')}
        />
        <KPICard
          label="Factures en attente"
          value={kpis.pendingInvoices}
          trend={`€${kpis.pendingAmount.toLocaleString()} à traiter`}
          trendDirection="down"
          onClick={() => navigate('/operations/factures')}
        />
        <KPICard
          label="Alertes stock"
          value={kpis.stockAlerts}
          color="text-amber-400"
          trend={`${kpis.criticalAlerts} critiques, ${kpis.warningAlerts} moyennes`}
          onClick={() => navigate('/operations/stock')}
        />
        <KPICard
          label="Rotation moyenne"
          value={`${kpis.avgRotation}j`}
          trend="-2j vs mois dernier"
          trendDirection="up"
          onClick={() => navigate('/operations/stock')}
        />
      </div>

      {/* Sales Chart */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h2 className="text-lg font-semibold text-white">Évolution des ventes</h2>
          <div className="flex gap-2">
            <PeriodButton>7j</PeriodButton>
            <PeriodButton active>30j</PeriodButton>
            <PeriodButton>90j</PeriodButton>
            <PeriodButton>12m</PeriodButton>
          </div>
        </div>

        <div
          className="h-72 rounded-xl flex items-end justify-around px-4 pb-4"
          style={{ background: 'linear-gradient(180deg, rgba(16,185,129,0.1) 0%, transparent 100%)' }}
        >
          {chartData.length > 0 ? (
            chartData.map((bar, idx) => (
              <ChartBar
                key={idx}
                height={bar.height}
                label={bar.label}
                value={bar.value}
                onClick={() => alert(`${bar.label}: ${bar.value.toLocaleString()} sorties, ${bar.entrees?.toLocaleString() || 0} entrées`)}
              />
            ))
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500">
              Aucune donnée de mouvements disponible
            </div>
          )}
        </div>
      </div>

      {/* Active Alerts */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-white">Alertes actives</h2>
          <span className="text-sm text-slate-400">{alerts.length + kpis.stockAlerts} alertes</span>
        </div>

        <div className="space-y-3">
          {alerts.map((alert, idx) => (
            <AlertItem
              key={idx}
              icon={alert.icon}
              iconBg={alert.iconBg}
              title={alert.title}
              description={alert.description}
              actionLabel={alert.actionLabel}
              onAction={() => navigate(alert.path)}
              onClick={() => navigate(alert.path)}
            />
          ))}
        </div>

        {alerts.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            Aucune alerte active
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group"
          onClick={() => navigate('/operations/factures')}
        >
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-emerald-400" />
            <span className="text-white font-medium">Importer une facture</span>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" />
        </button>

        <button
          className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group"
          onClick={() => navigate('/operations/stock')}
        >
          <div className="flex items-center gap-3">
            <Package className="w-5 h-5 text-teal-400" />
            <span className="text-white font-medium">Gérer le stock</span>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" />
        </button>

        <button
          className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group"
          onClick={() => navigate('/operations/prix')}
        >
          <div className="flex items-center gap-3">
            <DollarSign className="w-5 h-5 text-amber-400" />
            <span className="text-white font-medium">Analyser les prix</span>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" />
        </button>
      </div>
    </div>
  );
}
