import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Button, SectionHeader } from '@/components/ui';
import { fetchRestaurantOverview, fetchRestaurantAlerts, fetchRestaurantFoodCostAnalysis } from '@/api/client.js';
import {
  RestaurantKPICards,
  FoodCostAnalysisPanel,
  RestaurantAlertsWidget,
} from './components';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, Utensils, Download } from 'lucide-react';

/**
 * RestaurantOverviewPage - Dashboard principal restaurant avec Food Cost
 */
export default function RestaurantOverviewPage() {
  const [dateRange, setDateRange] = useState({
    dateFrom: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
    dateTo: new Date().toISOString().split('T')[0],
  });

  // Queries
  const overviewQuery = useQuery({
    queryKey: ['restaurant', 'overview', dateRange],
    queryFn: () => fetchRestaurantOverview(dateRange),
  });

  const alertsQuery = useQuery({
    queryKey: ['restaurant', 'alerts'],
    queryFn: () => fetchRestaurantAlerts(),
  });

  const foodCostQuery = useQuery({
    queryKey: ['restaurant', 'food-cost-analysis', dateRange],
    queryFn: () => fetchRestaurantFoodCostAnalysis({ ...dateRange, granularity: 'daily' }),
  });

  const overview = overviewQuery.data || {};
  const alerts = alertsQuery.data || [];
  const foodCostData = foodCostQuery.data || {};

  const {
    kpis = {},
    top_profitable_plats = [],
    top_unprofitable_plats = [],
  } = overview;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value) => `${value?.toFixed(1) || 0}%`;

  const handleExport = () => {
    // TODO: Implémenter l'export CSV
    console.log('Export CSV');
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <Card className="bg-gradient-to-br from-orange-500 to-amber-400 text-white">
        <div className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-white/70">Restaurant Overview</p>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold mb-2">Food Cost & Rentabilité</h1>
              <p className="text-sm text-white/90">
                Suivez vos KPIs restaurant, analysez votre food cost et optimisez vos marges en temps réel.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              className="bg-white/10 border-white/20 text-white hover:bg-white/20"
            >
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>
      </Card>

      {/* KPIs */}
      <RestaurantKPICards data={kpis} isLoading={overviewQuery.isLoading} />

      {/* Food Cost Analysis + Alertes */}
      <div className="grid lg:grid-cols-[1fr,400px] gap-6">
        <FoodCostAnalysisPanel data={foodCostData} isLoading={foodCostQuery.isLoading} />
        <RestaurantAlertsWidget alerts={alerts} isLoading={alertsQuery.isLoading} />
      </div>

      {/* Top 5 plats */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top rentables */}
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              <h3 className="text-lg font-semibold text-slate-900">Top 5 - Plus rentables</h3>
            </div>

            {overviewQuery.isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
              </div>
            ) : top_profitable_plats.length === 0 ? (
              <p className="text-sm text-slate-500">Aucune donnée disponible</p>
            ) : (
              <div className="space-y-3">
                {top_profitable_plats.map((plat, idx) => (
                  <div
                    key={plat.id}
                    className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-200 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 bg-emerald-600 text-white rounded-full font-bold text-sm">
                        {idx + 1}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{plat.nom}</p>
                        <p className="text-xs text-slate-500">{plat.categorie || 'Sans catégorie'}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-emerald-600">{formatPercent(plat.marge_pct)}</p>
                      <p className="text-xs text-slate-500">{formatCurrency(plat.marge_brute)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Top à surveiller */}
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Utensils className="w-5 h-5 text-rose-600" />
              <h3 className="text-lg font-semibold text-slate-900">Top 5 - À surveiller</h3>
            </div>

            {overviewQuery.isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
              </div>
            ) : top_unprofitable_plats.length === 0 ? (
              <p className="text-sm text-slate-500">Aucune donnée disponible</p>
            ) : (
              <div className="space-y-3">
                {top_unprofitable_plats.map((plat, idx) => (
                  <div
                    key={plat.id}
                    className="flex items-center justify-between p-3 bg-rose-50 border border-rose-200 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 bg-rose-600 text-white rounded-full font-bold text-sm">
                        {idx + 1}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{plat.nom}</p>
                        <p className="text-xs text-slate-500">{plat.categorie || 'Sans catégorie'}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-rose-600">{formatPercent(plat.marge_pct)}</p>
                      <p className="text-xs text-slate-500">{formatCurrency(plat.cout_matiere)} coût</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Graphique comparaison marges par catégorie */}
      {overview.margin_by_category && overview.margin_by_category.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Marges par catégorie</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={overview.margin_by_category} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="category" stroke="#64748b" style={{ fontSize: '12px' }} />
                <YAxis stroke="#64748b" style={{ fontSize: '12px' }} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => [`${value.toFixed(1)}%`, '']}
                />
                <Legend />
                <Bar dataKey="marge_pct" fill="#10b981" name="Marge moyenne %" radius={[8, 8, 0, 0]} />
                <Bar dataKey="food_cost_pct" fill="#f43f5e" name="Food Cost %" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
}
