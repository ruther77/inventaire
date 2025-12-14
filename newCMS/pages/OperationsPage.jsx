/**
 * Operations Page - Import Facture & Gestion Stock (Scénarios 3.2 & 3.3)
 * Vue unifiée : Catalogue | Factures | Stock | Prix
 */

import { useState } from 'react';
import {
  Package,
  FileText,
  Activity,
  TrendingUp,
  Upload,
  Camera,
  Mail,
  Search,
  Filter,
  Download,
  Plus,
  MoreVertical,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ChevronRight,
  Edit3,
  ShoppingCart,
  History,
  X,
  Lightbulb,
  Link2,
} from 'lucide-react';

// Tab Navigation
function TabNav({ tabs, activeTab, onTabChange }) {
  return (
    <div className="flex gap-1 p-1 rounded-xl bg-slate-800/50 border border-white/10">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === tab.id
              ? 'bg-blue-500 text-white'
              : 'text-slate-400 hover:text-white hover:bg-white/10'
          }`}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
}

// Drop Zone Component
function DropZone() {
  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <Upload className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">Zone Drop (Drag & Drop ou Photo mobile)</h3>
      </div>
      <div className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center hover:border-blue-500/50 transition-colors cursor-pointer">
        <div className="flex flex-col items-center gap-3">
          <div className="p-4 rounded-2xl bg-slate-700/50">
            <FileText className="w-8 h-8 text-slate-400" />
          </div>
          <p className="text-slate-400">Glissez vos factures ici</p>
          <span className="text-slate-500 text-sm">ou</span>
          <div className="flex gap-2">
            <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/20 transition-colors flex items-center gap-2">
              <Upload className="w-4 h-4" /> Parcourir
            </button>
            <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/20 transition-colors flex items-center gap-2">
              <Camera className="w-4 h-4" /> Scanner
            </button>
            <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm hover:bg-white/20 transition-colors flex items-center gap-2">
              <Mail className="w-4 h-4" /> factures@monepicerie.com
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Processing Status Component
function ProcessingStatus() {
  const steps = [
    { label: 'OCR terminé', status: 'done', detail: '47 lignes extraites' },
    { label: 'Matching produits', status: 'done', detail: '45/47 matchés (96%)' },
    { label: 'Prix analysés', status: 'done', detail: '2 anomalies détectées' },
    { label: 'Catégorisation', status: 'done', detail: '100% auto-catégorisé' },
    { label: 'Mise à jour stock', status: 'loading', detail: 'En cours...' },
  ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
        <h3 className="font-semibold text-white">Traitement en cours</h3>
      </div>

      <div className="mb-4 p-3 rounded-lg bg-slate-700/50">
        <span className="text-sm text-slate-300">Facture_METRO_2025-12-10.pdf</span>
      </div>

      <div className="space-y-2">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center gap-3 p-2 rounded-lg bg-white/5">
            {step.status === 'done' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
            )}
            <span className="text-sm text-white">{step.label}</span>
            <span className="text-sm text-slate-400">→ {step.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Attention Points Component
function AttentionPoints() {
  const points = [
    {
      title: '"Huile Olive Extra 5L" → Nouveau produit',
      suggestion: 'Similaire à: "Huile Olive 5L" (existant)',
      actions: ['🔗 Lier à existant', '➕ Créer nouveau', '❓ Ignorer'],
    },
    {
      title: '"Tomates Grappe" → Prix +18% vs dernier achat',
      detail: 'Avant: 2.40€/kg → Maintenant: 2.83€/kg',
      suggestion: 'Saisonnier (décembre) - Historique similaire',
      actions: ['✅ Accepter', '🚫 Contester', '📊 Voir historique'],
    },
  ];

  return (
    <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/20">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-amber-400" />
        <h3 className="font-semibold text-white">2 Points d'attention</h3>
      </div>

      <div className="space-y-4">
        {points.map((point, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-slate-800/50">
            <p className="font-medium text-white">{idx + 1}. {point.title}</p>
            {point.detail && <p className="text-sm text-slate-400 mt-1">{point.detail}</p>}
            <div className="flex items-start gap-2 mt-2">
              <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-slate-300">{point.suggestion}</span>
            </div>
            <div className="flex gap-2 mt-3">
              {point.actions.map((action, i) => (
                <button key={i} className="px-3 py-1.5 rounded-lg text-sm bg-white/10 text-slate-300 hover:bg-white/20 transition-colors">
                  {action}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Import Summary Component
function ImportSummary() {
  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">Résumé Import</h3>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 rounded-lg bg-white/5">
          <div className="text-xs text-slate-400 mb-1">Total HT</div>
          <div className="text-lg font-bold text-white">847.32€</div>
        </div>
        <div className="text-center p-3 rounded-lg bg-white/5">
          <div className="text-xs text-slate-400 mb-1">TVA</div>
          <div className="text-lg font-bold text-white">72.45€</div>
        </div>
        <div className="text-center p-3 rounded-lg bg-white/5">
          <div className="text-xs text-slate-400 mb-1">Total TTC</div>
          <div className="text-lg font-bold text-white">919.77€</div>
        </div>
        <div className="text-center p-3 rounded-lg bg-white/5">
          <div className="text-xs text-slate-400 mb-1">Lignes</div>
          <div className="text-lg font-bold text-white">47</div>
        </div>
      </div>

      <div className="flex gap-2">
        <button className="flex-1 px-4 py-2.5 rounded-lg bg-blue-500 text-white font-medium hover:bg-blue-600 transition-colors">
          ✅ Valider et mettre à jour stock
        </button>
        <button className="px-4 py-2.5 rounded-lg bg-white/10 text-slate-300 hover:bg-white/20 transition-colors">
          📝 Modifier avant validation
        </button>
      </div>
    </div>
  );
}

// Catalog Table Component
function CatalogTable() {
  const products = [
    { name: 'Riz Basmati 5kg', stock: 23, seuil: 10, pAchat: 4.50, pVente: 6.90, marge: 34.8, status: 'ok' },
    { name: 'Huile Olive 1L', stock: 2, seuil: 10, pAchat: null, pVente: 8.50, marge: null, status: 'critical', suggestion: 'Commander 24u chez METRO' },
    { name: 'Café Moulu 250g', stock: 8, seuil: 15, pAchat: 3.20, pVente: 5.90, marge: 45.7, status: 'warning' },
    { name: 'Sucre 1kg', stock: 45, seuil: 20, pAchat: 0.89, pVente: 1.45, marge: 38.6, status: 'ok' },
    { name: 'Tomates kg', stock: 2, seuil: 15, pAchat: 2.83, pVente: 4.50, marge: 37.1, status: 'critical', alert: 'Prix +18% vs moyenne. Saisonnier.' },
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ok': return <span className="text-emerald-400">🟢</span>;
      case 'warning': return <span className="text-amber-400">🟡</span>;
      case 'critical': return <span className="text-rose-400">🔴</span>;
      default: return <span className="text-slate-400">⚪</span>;
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      {/* Smart Filters */}
      <div className="mb-4 p-4 rounded-xl bg-slate-700/30">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Recherche..."
                className="w-full pl-10 pr-4 py-2 rounded-lg bg-slate-800 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
          <button className="px-3 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
            <Filter className="w-4 h-4" /> Cat: Tous ▼
          </button>
          <button className="px-3 py-2 rounded-lg bg-amber-500/20 text-amber-400 text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Stock: ⚠️ 12
          </button>
          <button className="px-3 py-2 rounded-lg bg-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
            Qualité: 🔴 5
          </button>
        </div>
        <div className="flex gap-2 mt-3">
          <span className="text-xs text-slate-500">Suggestions:</span>
          <button className="text-xs text-blue-400 hover:text-blue-300">[Voir ruptures imminentes]</button>
          <button className="text-xs text-blue-400 hover:text-blue-300">[Prix anormaux]</button>
          <button className="text-xs text-blue-400 hover:text-blue-300">[Sans code-barre]</button>
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-white">Table Intelligente</h3>
          <span className="text-sm text-slate-400">(247 produits)</span>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-1">
            <Download className="w-4 h-4" /> Export
          </button>
          <button className="px-3 py-1.5 rounded-lg bg-blue-500 text-white text-sm flex items-center gap-1">
            <Plus className="w-4 h-4" /> Ajouter
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-2 text-xs font-medium text-slate-400">☐</th>
              <th className="text-left py-3 px-2 text-xs font-medium text-slate-400">Produit</th>
              <th className="text-right py-3 px-2 text-xs font-medium text-slate-400">Stock</th>
              <th className="text-right py-3 px-2 text-xs font-medium text-slate-400">Seuil</th>
              <th className="text-right py-3 px-2 text-xs font-medium text-slate-400">P.Achat</th>
              <th className="text-right py-3 px-2 text-xs font-medium text-slate-400">P.Vente</th>
              <th className="text-right py-3 px-2 text-xs font-medium text-slate-400">Marge</th>
              <th className="text-center py-3 px-2 text-xs font-medium text-slate-400">🔧</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product, idx) => (
              <>
                <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                  <td className="py-3 px-2">
                    <input type="checkbox" className="rounded border-slate-600" />
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(product.status)}
                      <span className="text-white">{product.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-right">
                    <span className={product.status === 'critical' ? 'text-rose-400 font-medium' : 'text-white'}>
                      {product.stock} {product.status === 'critical' && '⚠️'}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-right text-slate-400">{product.seuil}</td>
                  <td className="py-3 px-2 text-right text-white">
                    {product.pAchat ? `${product.pAchat.toFixed(2)}€` : '?.??€'}
                    {product.name === 'Tomates kg' && <span className="text-rose-400 ml-1">↑</span>}
                  </td>
                  <td className="py-3 px-2 text-right text-white">{product.pVente.toFixed(2)}€</td>
                  <td className="py-3 px-2 text-right text-white">
                    {product.marge ? `${product.marge}%` : '-'}
                  </td>
                  <td className="py-3 px-2 text-center">
                    <button className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
                {(product.suggestion || product.alert) && (
                  <tr className="bg-white/5">
                    <td></td>
                    <td colSpan={6} className="py-2 px-4">
                      <div className="flex items-center gap-2 text-sm">
                        {product.suggestion && (
                          <>
                            <Lightbulb className="w-4 h-4 text-amber-400" />
                            <span className="text-slate-300">{product.suggestion}</span>
                            <button className="ml-2 px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs">
                              📦 Commander
                            </button>
                          </>
                        )}
                        {product.alert && (
                          <>
                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                            <span className="text-slate-300">{product.alert}</span>
                            <button className="ml-2 px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs">
                              📊 Analyser
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                    <td></td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-center">
        <button className="text-sm text-blue-400 hover:text-blue-300">
          🔽 Charger plus (242 restants)
        </button>
      </div>
    </div>
  );
}

// Product Drawer Component
function ProductDrawer() {
  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-white">Drawer Détail - Huile Olive 1L</h3>
        </div>
        <button className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Prix History Chart */}
      <div className="p-4 rounded-xl bg-slate-700/30 mb-4">
        <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
          <History className="w-4 h-4" /> Historique Prix (6 mois)
        </h4>
        <div className="h-24 flex items-end gap-1">
          <div className="flex-1 bg-blue-500/30 rounded-t" style={{ height: '50%' }}></div>
          <div className="flex-1 bg-blue-500/30 rounded-t" style={{ height: '50%' }}></div>
          <div className="flex-1 bg-blue-500/30 rounded-t" style={{ height: '55%' }}></div>
          <div className="flex-1 bg-blue-500/50 rounded-t" style={{ height: '65%' }}></div>
          <div className="flex-1 bg-blue-500/50 rounded-t" style={{ height: '75%' }}></div>
          <div className="flex-1 bg-blue-500 rounded-t" style={{ height: '90%' }}></div>
        </div>
        <div className="flex justify-between text-xs text-slate-500 mt-2">
          <span>Juil</span><span>Août</span><span>Sept</span><span>Oct</span><span>Nov</span><span>Déc</span>
        </div>
        <div className="flex items-center gap-2 mt-2 p-2 rounded-lg bg-amber-500/10">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-slate-300">Tendance: +22% sur 6 mois</span>
        </div>
      </div>

      {/* Suppliers */}
      <div className="p-4 rounded-xl bg-slate-700/30">
        <h4 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
          <ShoppingCart className="w-4 h-4" /> Fournisseurs
        </h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="pb-2">Fournisseur</th>
              <th className="pb-2">Prix</th>
              <th className="pb-2">Délai</th>
              <th className="pb-2">Score</th>
              <th className="pb-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t border-white/5">
              <td className="py-2">🥇 Direct Prod</td>
              <td className="py-2 text-emerald-400">6.20€</td>
              <td className="py-2 text-slate-400">3 jours</td>
              <td className="py-2">⭐ 4.8</td>
              <td className="py-2"><button className="text-xs text-blue-400">[Commander]</button></td>
            </tr>
            <tr className="border-t border-white/5">
              <td className="py-2">🥈 Metro</td>
              <td className="py-2 text-white">6.80€</td>
              <td className="py-2 text-slate-400">1 jour</td>
              <td className="py-2">⭐ 4.5</td>
              <td className="py-2"><button className="text-xs text-blue-400">[Commander]</button></td>
            </tr>
            <tr className="border-t border-white/5">
              <td className="py-2">🥉 PromoC</td>
              <td className="py-2 text-rose-400">7.10€</td>
              <td className="py-2 text-slate-400">2 jours</td>
              <td className="py-2">⭐ 4.2</td>
              <td className="py-2"><button className="text-xs text-blue-400">[Commander]</button></td>
            </tr>
          </tbody>
        </table>
        <div className="flex items-center gap-2 mt-3 p-2 rounded-lg bg-emerald-500/10">
          <Lightbulb className="w-4 h-4 text-emerald-400" />
          <span className="text-sm text-slate-300">Économie potentielle: 14.40€/mois en changeant pour Direct Prod</span>
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <button className="flex-1 px-4 py-2 rounded-lg bg-blue-500 text-white text-sm font-medium">
          📦 Créer commande
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          📝 Modifier
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          📊 Analyse
        </button>
      </div>
    </div>
  );
}

// Main Component
export default function OperationsPage() {
  const [activeTab, setActiveTab] = useState('factures');

  const tabs = [
    { id: 'catalogue', label: 'Catalogue', icon: <Package className="w-4 h-4" /> },
    { id: 'factures', label: 'Factures', icon: <FileText className="w-4 h-4" /> },
    { id: 'stock', label: 'Stock', icon: <Activity className="w-4 h-4" /> },
    { id: 'prix', label: 'Prix', icon: <TrendingUp className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Opérations</h1>
          <p className="text-slate-400">Catalogue, Factures, Stock, Prix</p>
        </div>
        <TabNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      </div>

      {/* Content based on active tab */}
      {activeTab === 'factures' && (
        <div className="space-y-6">
          <DropZone />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ProcessingStatus />
            <AttentionPoints />
          </div>
          <ImportSummary />
        </div>
      )}

      {activeTab === 'catalogue' && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            <CatalogTable />
          </div>
          <div>
            <ProductDrawer />
          </div>
        </div>
      )}

      {activeTab === 'stock' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <Activity className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Mouvements de Stock</h3>
          <p className="text-slate-400">Vue des entrées/sorties et ajustements</p>
        </div>
      )}

      {activeTab === 'prix' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <TrendingUp className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Suivi des Prix</h3>
          <p className="text-slate-400">Historique et comparaison fournisseurs</p>
        </div>
      )}
    </div>
  );
}
