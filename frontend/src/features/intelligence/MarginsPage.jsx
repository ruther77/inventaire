import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Calculator, AlertTriangle, RefreshCw, Package, Tag } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useMargins } from '../../hooks/useMargins.js';

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

const MarginBar = ({ value, target = 30 }) => {
  const color = value >= target ? 'bg-emerald-500' : value >= target * 0.7 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${Math.min(value, 100)}%` }}></div>
      </div>
      <span className={`text-sm font-semibold ${value >= target ? 'text-emerald-600' : value >= target * 0.7 ? 'text-amber-600' : 'text-rose-600'}`}>
        {value.toFixed(1)}%
      </span>
    </div>
  );
};

export default function MarginsPage() {
  const [activeTab, setActiveTab] = useState('summary');
  const [sortBy, setSortBy] = useState('margin_desc');
  const [searchTerm, setSearchTerm] = useState('');

  const {
    summary,
    products,
    categories,
    alerts,
    isLoading,
    refetchAll,
  } = useMargins({ alertThreshold: 20 });

  // Extract data from queries
  const data = {
    summary: summary.data || {},
    products: products.data || [],
    categories: categories.data || [],
    alerts: alerts.data || [],
  };
  const loading = isLoading;


  const filteredProducts = data.products.filter((p) =>
    p.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedProducts = (() => {
    const list = [...filteredProducts];
    switch (sortBy) {
      case 'margin_desc':
        return list.sort((a, b) => (b.margin_percent || 0) - (a.margin_percent || 0));
      case 'margin_asc':
        return list.sort((a, b) => (a.margin_percent || 0) - (b.margin_percent || 0));
      case 'revenue_desc':
        return list.sort((a, b) => (b.monthly_revenue || 0) - (a.monthly_revenue || 0));
      case 'name_asc':
        return list.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
      default:
        return list;
    }
  })();

  const renderSummaryTab = () => (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Marge Moyenne" value={`${(data.summary?.average_margin || 0).toFixed(1)}%`} hint="Tous produits" icon={Calculator} accent="text-blue-600" bgColor="bg-blue-50" borderColor="border-blue-200" />
        <Stat label="Meilleure Marge" value={`${(data.summary?.best_margin || 0).toFixed(1)}%`} hint={data.summary?.best_margin_product || '-'} icon={TrendingUp} accent="text-emerald-600" bgColor="bg-emerald-50" borderColor="border-emerald-200" />
        <Stat label="Pire Marge" value={`${(data.summary?.worst_margin || 0).toFixed(1)}%`} hint={data.summary?.worst_margin_product || '-'} icon={TrendingDown} accent="text-rose-600" bgColor="bg-rose-50" borderColor="border-rose-200" />
        <Stat label="Alertes Marge" value={data.summary?.margin_alerts || 0} hint="Produits sous seuil" icon={AlertTriangle} accent="text-amber-600" bgColor="bg-amber-50" borderColor="border-amber-200" />
      </div>

      {data.summary?.by_category && (
        <Card className="p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Par Categorie</p>
            <h3 className="text-lg font-semibold text-slate-900">Marges par Categorie</h3>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {Object.entries(data.summary.by_category).map(([category, margin]) => (
              <div key={category} className="rounded-xl border border-slate-200 p-4">
                <p className="text-sm text-slate-500 mb-2">{category}</p>
                <MarginBar value={margin} />
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {data.summary?.top_margin_products?.length > 0 && (
          <Card className="p-4">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-[0.3em] text-emerald-600">Top 5</p>
              <h3 className="text-lg font-semibold text-slate-900">Meilleures Marges</h3>
            </div>
            <div className="space-y-2">
              {data.summary.top_margin_products.map((p, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                  <span className="text-sm text-slate-900">{p.name}</span>
                  <span className="px-2 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold">{p.margin.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </Card>
        )}
        {data.summary?.low_margin_products?.length > 0 && (
          <Card className="p-4">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-[0.3em] text-rose-600">Flop 5</p>
              <h3 className="text-lg font-semibold text-slate-900">Pires Marges</h3>
            </div>
            <div className="space-y-2">
              {data.summary.low_margin_products.map((p, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                  <span className="text-sm text-slate-900">{p.name}</span>
                  <span className="px-2 py-1 rounded-full bg-rose-100 text-rose-700 text-xs font-semibold">{p.margin.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );

  const renderProductsTab = () => (
    <Card className="p-4">
      <div className="mb-4 flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Produits</p>
          <h3 className="text-lg font-semibold text-slate-900">Marges par Produit</h3>
        </div>
        <div className="flex items-center gap-2">
          <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Rechercher..." className="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
            <option value="margin_desc">Marge (decr.)</option>
            <option value="margin_asc">Marge (croiss.)</option>
            <option value="revenue_desc">CA (decr.)</option>
            <option value="name_asc">Nom (A-Z)</option>
          </select>
        </div>
      </div>
      {sortedProducts.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Produit</th>
                <th className="px-3 py-2">Categorie</th>
                <th className="px-3 py-2 text-right">Prix Vente</th>
                <th className="px-3 py-2 text-right">Cout (PAMP)</th>
                <th className="px-3 py-2 text-right">Marge EUR</th>
                <th className="px-3 py-2">Marge %</th>
                <th className="px-3 py-2 text-right">CA Mensuel</th>
              </tr>
            </thead>
            <tbody>
              {sortedProducts.slice(0, 100).map((product, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-900">{product.name}</td>
                  <td className="px-3 py-2"><span className="px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-xs">{product.category || 'Non classe'}</span></td>
                  <td className="px-3 py-2 text-right">{product.selling_price?.toFixed(2)} EUR</td>
                  <td className="px-3 py-2 text-right">{product.cost_price?.toFixed(2)} EUR</td>
                  <td className="px-3 py-2 text-right"><span className={product.margin_amount >= 0 ? 'text-emerald-600' : 'text-rose-600'}>{product.margin_amount?.toFixed(2)} EUR</span></td>
                  <td className="px-3 py-2"><MarginBar value={product.margin_percent || 0} /></td>
                  <td className="px-3 py-2 text-right">{product.monthly_revenue?.toFixed(0)} EUR</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <Package className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucun produit trouve</p>
        </div>
      )}
    </Card>
  );

  const renderCategoriesTab = () => (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {data.categories.map((cat, idx) => (
        <Card key={idx} className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">{cat.name}</h3>
            <span className="px-2 py-1 rounded-full bg-blue-100 text-blue-700 text-xs">{cat.product_count} produits</span>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-slate-500 mb-1">Marge Moyenne</p>
              <MarginBar value={cat.average_margin || 0} />
            </div>
            <div className="flex justify-between">
              <div>
                <p className="text-xs text-slate-500">Marge Min</p>
                <span className="px-2 py-1 rounded-full bg-rose-100 text-rose-700 text-xs font-semibold">{cat.min_margin?.toFixed(1)}%</span>
              </div>
              <div>
                <p className="text-xs text-slate-500">Marge Max</p>
                <span className="px-2 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold">{cat.max_margin?.toFixed(1)}%</span>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500">CA Mensuel</p>
              <p className="text-lg font-semibold text-slate-900">{cat.monthly_revenue?.toFixed(0)} EUR</p>
            </div>
          </div>
        </Card>
      ))}
      {data.categories.length === 0 && (
        <div className="col-span-full text-center py-8 text-slate-500">
          <Tag className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucune categorie disponible</p>
        </div>
      )}
    </div>
  );

  const renderPAMPTab = () => (
    <Card className="p-4">
      <div className="mb-4 flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">PAMP</p>
          <h3 className="text-lg font-semibold text-slate-900">Prix d'Achat Moyen Pondere</h3>
          <p className="text-sm text-slate-500">Calcule automatiquement depuis les factures</p>
        </div>
        <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Rechercher..." className="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
      </div>
      {filteredProducts.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Produit</th>
                <th className="px-3 py-2 text-right">PAMP Actuel</th>
                <th className="px-3 py-2 text-right">Dernier Prix</th>
                <th className="px-3 py-2 text-right">Variation</th>
                <th className="px-3 py-2 text-right">Nb Achats</th>
                <th className="px-3 py-2 text-right">Qte Totale</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.slice(0, 100).map((product, idx) => {
                const variation = product.last_price && product.pamp ? ((product.last_price - product.pamp) / product.pamp * 100) : 0;
                return (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium text-slate-900">{product.name}</td>
                    <td className="px-3 py-2 text-right font-semibold">{product.pamp?.toFixed(3)} EUR</td>
                    <td className="px-3 py-2 text-right">{product.last_price?.toFixed(3)} EUR</td>
                    <td className="px-3 py-2 text-right">
                      {variation !== 0 && (
                        <span className={`flex items-center justify-end gap-1 ${variation > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                          {variation > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                          {variation > 0 ? '+' : ''}{variation.toFixed(1)}%
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right">{product.purchase_count || 0}</td>
                    <td className="px-3 py-2 text-right">{product.total_quantity?.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-500">
          <Calculator className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>Aucun produit trouve</p>
        </div>
      )}
    </Card>
  );

  const renderAlertsTab = () => (
    <div className="space-y-3">
      {data.alerts.length > 0 ? (
        data.alerts.map((alert, idx) => (
          <div key={idx} className={`rounded-xl border p-4 ${
            alert.severity === 'critical' ? 'border-rose-200 bg-rose-50' :
            alert.severity === 'high' ? 'border-amber-200 bg-amber-50' :
            'border-blue-200 bg-blue-50'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-900">{alert.product_name}</p>
                <p className="text-sm text-slate-600">{alert.message}</p>
              </div>
              <div className="text-right">
                <p className="text-sm">Marge actuelle: <span className="font-bold text-rose-600">{alert.current_margin?.toFixed(1)}%</span></p>
                <p className="text-xs text-slate-500">Seuil: {alert.threshold?.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        ))
      ) : (
        <Card className="p-8 text-center text-emerald-600">
          <TrendingUp className="w-12 h-12 mx-auto mb-2" />
          <p className="font-semibold">Tous les produits ont des marges acceptables !</p>
        </Card>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Intelligence</p>
          <h1 className="text-2xl font-semibold text-slate-900">Analyse des Marges</h1>
        </div>
        <Button variant="ghost" onClick={refetchAll} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Rafraichir
        </Button>
      </header>

      <div className="flex flex-wrap gap-2">
        <TabButton active={activeTab === 'summary'} onClick={() => setActiveTab('summary')} icon={Calculator}>Resume</TabButton>
        <TabButton active={activeTab === 'products'} onClick={() => setActiveTab('products')} icon={Package}>Produits</TabButton>
        <TabButton active={activeTab === 'categories'} onClick={() => setActiveTab('categories')} icon={Tag}>Categories</TabButton>
        <TabButton active={activeTab === 'pamp'} onClick={() => setActiveTab('pamp')} icon={TrendingUp}>PAMP</TabButton>
        <TabButton active={activeTab === 'alerts'} onClick={() => setActiveTab('alerts')} icon={AlertTriangle}>Alertes</TabButton>
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
          {activeTab === 'products' && renderProductsTab()}
          {activeTab === 'categories' && renderCategoriesTab()}
          {activeTab === 'pamp' && renderPAMPTab()}
          {activeTab === 'alerts' && renderAlertsTab()}
        </>
      )}
    </div>
  );
}
