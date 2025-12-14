import React, { useState } from 'react';
import { TrendingUp, Calendar, DollarSign, Package, RefreshCw, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useForecasting, useCashFlowForecast } from '../../hooks/useForecasting.js';

const Stat = ({ label, value, hint, icon: Icon, accent = 'text-slate-900', bgColor = 'bg-white', borderColor = 'border-slate-200' }) => (
  <div className={`rounded-2xl border ${borderColor} ${bgColor} p-4 transition-all hover:shadow-md`}>
    <div className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-[0.3em]">
      {Icon && <Icon className="w-4 h-4" />} {label}
    </div>
    <p className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
  </div>
);

const TabButton = ({ active, onClick, children, icon: Icon }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
      active ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
    }`}
  >
    {Icon && <Icon className="w-4 h-4" />}
    {children}
  </button>
);

export default function ForecastingPage() {
  const [activeTab, setActiveTab] = useState('summary');
  const [horizon, setHorizon] = useState(30);

  const { summary, cashFlow: cashFlowQuery, isLoading, refetchAll } = useForecasting({ cashFlowHorizon: horizon });

  // Extract data from queries
  const data = {
    summary: summary.data || {},
    sales: summary.data?.sales_forecasts || [],
    stockDepletion: summary.data?.stock_depletion || [],
    cashFlow: cashFlowQuery.data?.forecasts || cashFlowQuery.data || [],
  };
  const loading = isLoading;


  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
  };

  const renderSummaryTab = () => (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="CA Prevu (30j)" value={formatCurrency(data.summary?.predicted_revenue_30d)} hint="Holt-Winters" icon={DollarSign} accent="text-emerald-600" bgColor="bg-emerald-50" borderColor="border-emerald-200" />
        <Stat label="Ruptures Prevues" value={data.summary?.predicted_stockouts || 0} hint="30 prochains jours" icon={Package} accent="text-amber-600" bgColor="bg-amber-50" borderColor="border-amber-200" />
        <Stat label="Cash Flow Prevu" value={formatCurrency(data.summary?.predicted_cash_flow_30d)} hint="Solde a 30 jours" icon={TrendingUp} accent={data.summary?.predicted_cash_flow_30d >= 0 ? 'text-emerald-600' : 'text-rose-600'} bgColor={data.summary?.predicted_cash_flow_30d >= 0 ? 'bg-emerald-50' : 'bg-rose-50'} borderColor={data.summary?.predicted_cash_flow_30d >= 0 ? 'border-emerald-200' : 'border-rose-200'} />
        <Stat label="Confiance" value={`${((data.summary?.model_confidence || 0) * 100).toFixed(0)}%`} hint="Precision modele" icon={AlertCircle} accent="text-blue-600" bgColor="bg-blue-50" borderColor="border-blue-200" />
      </div>

      {data.cashFlow.length > 0 && (
        <Card className="p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Projection</p>
            <h3 className="text-lg font-semibold text-slate-900">Tresorerie Previsionnelle</h3>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.cashFlow}>
                <defs>
                  <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#64748b" />
                <YAxis tick={{ fontSize: 10 }} stroke="#64748b" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                <Tooltip formatter={(value) => [formatCurrency(value), 'Solde']} />
                <Area type="monotone" dataKey="balance" stroke="#10b981" fillOpacity={1} fill="url(#colorBalance)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );

  const renderSalesTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Ventes</p>
        <h3 className="text-lg font-semibold text-slate-900">Previsions de Ventes</h3>
      </div>
      {data.sales.length > 0 ? (
        <>
          <div className="h-64 mb-6">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.sales}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#64748b" />
                <YAxis tick={{ fontSize: 10 }} stroke="#64748b" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                <Tooltip formatter={(value) => [formatCurrency(value), '']} />
                <Line type="monotone" dataKey="predicted" stroke="#10b981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="lower_bound" stroke="#10b981" strokeWidth={1} strokeDasharray="3 3" dot={false} />
                <Line type="monotone" dataKey="upper_bound" stroke="#10b981" strokeWidth={1} strokeDasharray="3 3" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2 text-right">Prevision</th>
                  <th className="px-3 py-2 text-right">Borne Basse</th>
                  <th className="px-3 py-2 text-right">Borne Haute</th>
                </tr>
              </thead>
              <tbody>
                {data.sales.slice(0, 14).map((item, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium text-slate-900">{item.date}</td>
                    <td className="px-3 py-2 text-right text-emerald-600 font-semibold">{formatCurrency(item.predicted)}</td>
                    <td className="px-3 py-2 text-right text-slate-500">{formatCurrency(item.lower_bound)}</td>
                    <td className="px-3 py-2 text-right text-slate-500">{formatCurrency(item.upper_bound)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Pas assez de donnees pour generer des previsions</p>
        </div>
      )}
    </Card>
  );

  const renderStockDepletionTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Stock</p>
        <h3 className="text-lg font-semibold text-slate-900">Epuisement des Stocks</h3>
      </div>
      {data.stockDepletion.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Produit</th>
                <th className="px-3 py-2 text-right">Stock</th>
                <th className="px-3 py-2 text-right">Conso/Jour</th>
                <th className="px-3 py-2 text-right">Date Rupture</th>
                <th className="px-3 py-2 text-right">Jours</th>
                <th className="px-3 py-2">Risque</th>
              </tr>
            </thead>
            <tbody>
              {data.stockDepletion.map((item, idx) => (
                <tr key={idx} className={`border-b border-slate-100 hover:bg-slate-50 ${item.days_remaining <= 7 ? 'bg-rose-50' : item.days_remaining <= 14 ? 'bg-amber-50' : ''}`}>
                  <td className="px-3 py-2 font-medium text-slate-900">{item.product_name}</td>
                  <td className="px-3 py-2 text-right">{item.current_stock?.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right">{item.avg_daily_consumption?.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right">{item.depletion_date || '-'}</td>
                  <td className="px-3 py-2 text-right font-semibold">
                    <span className={item.days_remaining <= 7 ? 'text-rose-600' : item.days_remaining <= 14 ? 'text-amber-600' : 'text-slate-900'}>
                      {item.days_remaining !== null ? `${item.days_remaining} j` : '-'}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      item.risk_level === 'critical' ? 'bg-rose-100 text-rose-700' :
                      item.risk_level === 'high' ? 'bg-amber-100 text-amber-700' :
                      'bg-emerald-100 text-emerald-700'
                    }`}>
                      {item.risk_level || 'low'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <Package className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucune prediction disponible</p>
        </div>
      )}
    </Card>
  );

  const renderCashFlowTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Tresorerie</p>
        <h3 className="text-lg font-semibold text-slate-900">Projection Cash Flow</h3>
      </div>
      {data.cashFlow.length > 0 ? (
        <>
          <div className="h-64 mb-6">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.cashFlow}>
                <defs>
                  <linearGradient id="colorInflow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorOutflow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#64748b" />
                <YAxis tick={{ fontSize: 10 }} stroke="#64748b" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                <Tooltip formatter={(value, name) => [formatCurrency(value), name === 'inflow' ? 'Entrees' : name === 'outflow' ? 'Sorties' : 'Solde']} />
                <Area type="monotone" dataKey="inflow" stroke="#10b981" fillOpacity={1} fill="url(#colorInflow)" />
                <Area type="monotone" dataKey="outflow" stroke="#ef4444" fillOpacity={1} fill="url(#colorOutflow)" />
                <Line type="monotone" dataKey="balance" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2 text-right">Entrees</th>
                  <th className="px-3 py-2 text-right">Sorties</th>
                  <th className="px-3 py-2 text-right">Net</th>
                  <th className="px-3 py-2 text-right">Solde</th>
                </tr>
              </thead>
              <tbody>
                {data.cashFlow.slice(0, 14).map((item, idx) => (
                  <tr key={idx} className={`border-b border-slate-100 hover:bg-slate-50 ${item.balance < 0 ? 'bg-rose-50' : ''}`}>
                    <td className="px-3 py-2 font-medium text-slate-900">{item.date}</td>
                    <td className="px-3 py-2 text-right text-emerald-600">{formatCurrency(item.inflow)}</td>
                    <td className="px-3 py-2 text-right text-rose-600">{formatCurrency(item.outflow)}</td>
                    <td className="px-3 py-2 text-right"><span className={item.net >= 0 ? 'text-emerald-600' : 'text-rose-600'}>{formatCurrency(item.net)}</span></td>
                    <td className="px-3 py-2 text-right font-semibold"><span className={item.balance >= 0 ? 'text-blue-600' : 'text-rose-600'}>{formatCurrency(item.balance)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <DollarSign className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucune projection disponible</p>
        </div>
      )}
    </Card>
  );

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Intelligence</p>
          <h1 className="text-2xl font-semibold text-slate-900">Previsions</h1>
        </div>
        <div className="flex items-center gap-2">
          <select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
            <option value={7}>7 jours</option>
            <option value={14}>14 jours</option>
            <option value={30}>30 jours</option>
            <option value={60}>60 jours</option>
            <option value={90}>90 jours</option>
          </select>
          <Button variant="ghost" onClick={refetchAll} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Rafraichir
          </Button>
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        <TabButton active={activeTab === 'summary'} onClick={() => setActiveTab('summary')} icon={TrendingUp}>Resume</TabButton>
        <TabButton active={activeTab === 'sales'} onClick={() => setActiveTab('sales')} icon={DollarSign}>Ventes</TabButton>
        <TabButton active={activeTab === 'stock'} onClick={() => setActiveTab('stock')} icon={Package}>Epuisement Stock</TabButton>
        <TabButton active={activeTab === 'cashflow'} onClick={() => setActiveTab('cashflow')} icon={Calendar}>Tresorerie</TabButton>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center text-slate-500">
            <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
            <p>Chargement...</p>
          </div>
        </div>
      ) : (
        <>
          {activeTab === 'summary' && renderSummaryTab()}
          {activeTab === 'sales' && renderSalesTab()}
          {activeTab === 'stock' && renderStockDepletionTab()}
          {activeTab === 'cashflow' && renderCashFlowTab()}
        </>
      )}
    </div>
  );
}
