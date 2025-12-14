import React, { useState } from 'react';
import { Brain, Package, AlertTriangle, TrendingDown, RefreshCw, ShoppingCart, Target, Boxes } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useInventoryIntelligence } from '../../hooks/useInventoryIntelligence.js';
import { staggerContainer, staggerItem, kpiCard, tabContent } from '../../ui/motion.js';

const Stat = ({ label, value, hint, icon: Icon, accent = 'text-slate-900', bgColor = 'bg-white', borderColor = 'border-slate-200' }) => (
  <motion.div
    className={`rounded-2xl border ${borderColor} ${bgColor} p-4 cursor-pointer`}
    variants={staggerItem}
    whileHover={kpiCard.hover}
    whileTap={kpiCard.tap}
  >
    <div className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-[0.3em]">
      {Icon && <Icon className="w-4 h-4" />} {label}
    </div>
    <p className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
  </motion.div>
);

const TabButton = ({ active, onClick, children, icon: Icon, layoutId }) => (
  <button
    onClick={onClick}
    className="relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
  >
    {active && (
      <motion.span
        layoutId={layoutId}
        className="absolute inset-0 bg-slate-900 rounded-lg"
        transition={{ type: 'spring', stiffness: 500, damping: 35 }}
      />
    )}
    <span className={`relative z-10 flex items-center gap-2 ${active ? 'text-white' : 'text-slate-600 hover:text-slate-900'}`}>
      {Icon && <Icon className="w-4 h-4" />}
      {children}
    </span>
  </button>
);

const getABCColor = (classification) => {
  const colors = { A: '#10b981', B: '#f59e0b', C: '#ef4444' };
  return colors[classification] || '#94a3b8';
};

const getXYZColor = (classification) => {
  const colors = { X: '#10b981', Y: '#f59e0b', Z: '#ef4444' };
  return colors[classification] || '#94a3b8';
};

export default function InventoryIntelligencePage() {
  const [activeTab, setActiveTab] = useState('summary');

  const {
    summary,
    suggestions,
    stockoutPredictions,
    deadStock,
    abcXyz,
    isLoading,
    refetchAll,
  } = useInventoryIntelligence({ horizonDays: 30, deadStockThreshold: 90 });

  // Extract data from queries
  const data = {
    summary: summary.data || {},
    reorder: summary.data?.suggestions || suggestions.data || [],
    stockout: stockoutPredictions.data || [],
    deadStock: deadStock.data || [],
    abcxyz: abcXyz.data?.classifications || [],
  };
  const loading = isLoading;


  const renderSummaryTab = () => (
    <motion.div
      className="space-y-6"
      variants={tabContent}
      initial="hidden"
      animate="visible"
      exit="exit"
    >
      <motion.div
        className="grid gap-4 md:grid-cols-4"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <Stat
          label="Stock Optimal"
          value={data.summary?.optimal_stock_count || 0}
          hint="Produits au niveau ideal"
          icon={Target}
          accent="text-emerald-600"
          bgColor="bg-emerald-50"
          borderColor="border-emerald-200"
        />
        <Stat
          label="A Reapprovisionner"
          value={data.summary?.reorder_count || 0}
          hint="Sous le point de commande"
          icon={ShoppingCart}
          accent="text-amber-600"
          bgColor="bg-amber-50"
          borderColor="border-amber-200"
        />
        <Stat
          label="Risque Rupture"
          value={data.summary?.stockout_risk_count || 0}
          hint="Dans les 7 prochains jours"
          icon={AlertTriangle}
          accent="text-rose-600"
          bgColor="bg-rose-50"
          borderColor="border-rose-200"
        />
        <Stat
          label="Stock Mort"
          value={data.summary?.dead_stock_count || 0}
          hint="Sans mouvement 90+ jours"
          icon={TrendingDown}
          accent="text-slate-600"
          bgColor="bg-slate-50"
          borderColor="border-slate-200"
        />
      </motion.div>

      {data.abcxyz.length > 0 && (
        <Card className="p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Classification</p>
            <h3 className="text-lg font-semibold text-slate-900">Repartition ABC-XYZ</h3>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: 'A', count: data.abcxyz.filter(p => p.abc_class === 'A').length },
                { name: 'B', count: data.abcxyz.filter(p => p.abc_class === 'B').length },
                { name: 'C', count: data.abcxyz.filter(p => p.abc_class === 'C').length },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#64748b" />
                <YAxis tick={{ fontSize: 12 }} stroke="#64748b" />
                <Tooltip />
                <Bar dataKey="count" name="Produits">
                  {[
                    { name: 'A', count: data.abcxyz.filter(p => p.abc_class === 'A').length },
                    { name: 'B', count: data.abcxyz.filter(p => p.abc_class === 'B').length },
                    { name: 'C', count: data.abcxyz.filter(p => p.abc_class === 'C').length },
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getABCColor(entry.name)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-emerald-500"></div>
              <span>A: Forte valeur ({data.abcxyz.filter(p => p.abc_class === 'A').length})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-amber-500"></div>
              <span>B: Valeur moyenne ({data.abcxyz.filter(p => p.abc_class === 'B').length})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-rose-500"></div>
              <span>C: Faible valeur ({data.abcxyz.filter(p => p.abc_class === 'C').length})</span>
            </div>
          </div>
        </Card>
      )}
    </motion.div>
  );

  const renderReorderTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Reappro</p>
        <h3 className="text-lg font-semibold text-slate-900">Suggestions de Reapprovisionnement</h3>
        <p className="text-sm text-slate-500">Bases sur EOQ et stock de securite</p>
      </div>
      {data.reorder.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Produit</th>
                <th className="px-3 py-2 text-right">Stock Actuel</th>
                <th className="px-3 py-2 text-right">Point Commande</th>
                <th className="px-3 py-2 text-right">EOQ</th>
                <th className="px-3 py-2 text-right">Qte Suggeree</th>
                <th className="px-3 py-2">Urgence</th>
              </tr>
            </thead>
            <tbody>
              {data.reorder.map((item, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">{item.product_name}</td>
                  <td className="px-3 py-2 text-right">{item.current_stock?.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right">{item.reorder_point?.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right">{item.eoq?.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-semibold text-emerald-600">{item.suggested_quantity?.toFixed(1)}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      item.urgency === 'high' ? 'bg-rose-100 text-rose-700' :
                      item.urgency === 'medium' ? 'bg-amber-100 text-amber-700' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {item.urgency || 'normal'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <ShoppingCart className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucune suggestion de reapprovisionnement</p>
        </div>
      )}
    </Card>
  );

  const renderStockoutTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Alertes</p>
        <h3 className="text-lg font-semibold text-slate-900">Predictions de Rupture</h3>
      </div>
      {data.stockout.length > 0 ? (
        <div className="space-y-3">
          {data.stockout.map((item, idx) => (
            <div key={idx} className={`rounded-xl border p-4 ${
              item.days_until_stockout <= 3 ? 'border-rose-200 bg-rose-50' :
              item.days_until_stockout <= 7 ? 'border-amber-200 bg-amber-50' :
              'border-slate-200 bg-white'
            }`}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold text-slate-900">{item.product_name}</p>
                  <p className="text-sm text-slate-600">Stock actuel: {item.current_stock?.toFixed(1)} unites</p>
                </div>
                <div className="text-right">
                  <p className={`text-2xl font-bold ${
                    item.days_until_stockout <= 3 ? 'text-rose-600' :
                    item.days_until_stockout <= 7 ? 'text-amber-600' :
                    'text-slate-900'
                  }`}>
                    {item.days_until_stockout} j
                  </p>
                  <p className="text-xs text-slate-500">avant rupture</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucun risque de rupture detecte</p>
        </div>
      )}
    </Card>
  );

  const renderDeadStockTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Optimisation</p>
        <h3 className="text-lg font-semibold text-slate-900">Stock Mort</h3>
      </div>
      {data.deadStock.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Produit</th>
                <th className="px-3 py-2 text-right">Quantite</th>
                <th className="px-3 py-2 text-right">Valeur</th>
                <th className="px-3 py-2 text-right">Jours Inactifs</th>
              </tr>
            </thead>
            <tbody>
              {data.deadStock.map((item, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">{item.product_name}</td>
                  <td className="px-3 py-2 text-right">{item.quantity?.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right">{item.value?.toFixed(2)} EUR</td>
                  <td className="px-3 py-2 text-right">
                    <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-medium">
                      {item.days_inactive} j
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <TrendingDown className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucun stock mort detecte</p>
        </div>
      )}
    </Card>
  );

  const renderABCXYZTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Classification</p>
        <h3 className="text-lg font-semibold text-slate-900">Analyse ABC-XYZ</h3>
      </div>
      {data.abcxyz.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Produit</th>
                <th className="px-3 py-2 text-center">ABC</th>
                <th className="px-3 py-2 text-center">XYZ</th>
                <th className="px-3 py-2 text-right">CA Annuel</th>
                <th className="px-3 py-2 text-right">% Cumule</th>
              </tr>
            </thead>
            <tbody>
              {data.abcxyz.slice(0, 50).map((item, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">{item.product_name}</td>
                  <td className="px-3 py-2 text-center">
                    <span className="px-2 py-1 rounded-full text-xs font-bold text-white" style={{ backgroundColor: getABCColor(item.abc_class) }}>
                      {item.abc_class}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span className="px-2 py-1 rounded-full text-xs font-bold text-white" style={{ backgroundColor: getXYZColor(item.xyz_class) }}>
                      {item.xyz_class}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">{item.annual_revenue?.toFixed(2)} EUR</td>
                  <td className="px-3 py-2 text-right">{(item.cumulative_percentage * 100)?.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <Boxes className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucune classification disponible</p>
        </div>
      )}
    </Card>
  );

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Intelligence</p>
          <h1 className="text-2xl font-semibold text-slate-900">Stock Intelligent</h1>
        </div>
        <Button variant="ghost" onClick={refetchAll} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Rafraichir
        </Button>
      </header>

      <div className="flex flex-wrap gap-2 bg-slate-100 p-1 rounded-xl">
        <TabButton active={activeTab === 'summary'} onClick={() => setActiveTab('summary')} icon={Brain} layoutId="inv-tab">Resume</TabButton>
        <TabButton active={activeTab === 'reorder'} onClick={() => setActiveTab('reorder')} icon={ShoppingCart} layoutId="inv-tab">Reappro</TabButton>
        <TabButton active={activeTab === 'stockout'} onClick={() => setActiveTab('stockout')} icon={AlertTriangle} layoutId="inv-tab">Ruptures</TabButton>
        <TabButton active={activeTab === 'deadstock'} onClick={() => setActiveTab('deadstock')} icon={TrendingDown} layoutId="inv-tab">Stock Mort</TabButton>
        <TabButton active={activeTab === 'abcxyz'} onClick={() => setActiveTab('abcxyz')} icon={Boxes} layoutId="inv-tab">ABC-XYZ</TabButton>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center text-slate-500">
            <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
            <p>Chargement...</p>
          </div>
        </div>
      ) : (
        <AnimatePresence mode="wait">
          {activeTab === 'summary' && renderSummaryTab()}
          {activeTab === 'reorder' && renderReorderTab()}
          {activeTab === 'stockout' && renderStockoutTab()}
          {activeTab === 'deadstock' && renderDeadStockTab()}
          {activeTab === 'abcxyz' && renderABCXYZTab()}
        </AnimatePresence>
      )}
    </div>
  );
}
