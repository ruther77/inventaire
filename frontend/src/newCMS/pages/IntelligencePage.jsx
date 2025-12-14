/**
 * Intelligence Page - Décisions Assistées par IA (Scénario 3.5)
 * Vue unifiée : Dashboard | Stock | Prévisions | Anomalies | Scoring | Marges
 */

import { useState } from 'react';
import {
  Brain,
  TrendingUp,
  AlertTriangle,
  Users,
  Calculator,
  Zap,
  DollarSign,
  Package,
  ChevronRight,
  CheckCircle2,
  XCircle,
  BarChart3,
  LineChart,
  Mail,
  RefreshCw,
  Eye,
  Lightbulb,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

// Tab Navigation
function TabNav({ tabs, activeTab, onTabChange }) {
  return (
    <div className="flex gap-1 p-1 rounded-xl bg-slate-800/50 border border-white/10 overflow-x-auto">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
            activeTab === tab.id
              ? 'bg-pink-500 text-white'
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

// Global Score Card
function GlobalScoreCard() {
  return (
    <div className="p-6 rounded-2xl bg-gradient-to-br from-pink-500/20 to-purple-500/20 border border-pink-500/30">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 mb-1">Score global santé</p>
          <div className="text-4xl font-bold text-white">7.2<span className="text-xl text-slate-400">/10</span></div>
        </div>
        <div className="w-20 h-20 rounded-full border-4 border-pink-500/50 flex items-center justify-center">
          <Brain className="w-10 h-10 text-pink-400" />
        </div>
      </div>
    </div>
  );
}

// Recommendation Card Component
function RecommendationCard({ type, title, impact, description, details, suggestions, actions }) {
  const getTypeStyles = () => {
    switch (type) {
      case 'margin':
        return { icon: DollarSign, color: 'emerald', label: 'OPTIMISATION MARGE' };
      case 'stock':
        return { icon: Package, color: 'blue', label: 'OPTIMISATION STOCK' };
      case 'supplier':
        return { icon: Users, color: 'purple', label: 'SCORING FOURNISSEURS' };
      default:
        return { icon: Lightbulb, color: 'amber', label: 'RECOMMANDATION' };
    }
  };

  const typeConfig = getTypeStyles();
  const Icon = typeConfig.icon;

  return (
    <div className={`p-6 rounded-2xl bg-slate-800/50 border border-${typeConfig.color}-500/20`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl bg-${typeConfig.color}-500/20`}>
            <Icon className={`w-5 h-5 text-${typeConfig.color}-400`} />
          </div>
          <div>
            <span className={`text-xs font-medium text-${typeConfig.color}-400`}>{typeConfig.label}</span>
            <h3 className="font-semibold text-white">{title}</h3>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium bg-${typeConfig.color}-500/20 text-${typeConfig.color}-400`}>
          Impact: {impact}
        </span>
      </div>

      <p className="text-slate-300 mb-4">{description}</p>

      {details && (
        <div className="mb-4 rounded-xl bg-slate-700/30 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                {details.headers.map((h, idx) => (
                  <th key={idx} className="text-left py-2 px-3 text-xs text-slate-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {details.rows.map((row, idx) => (
                <tr key={idx} className="border-b border-white/5">
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx} className="py-2 px-3 text-slate-300">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {suggestions && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-white/5 mb-4">
          <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <span className="text-sm text-slate-300">{suggestions}</span>
        </div>
      )}

      {actions && (
        <div className="flex flex-wrap gap-2">
          {actions.map((action, idx) => (
            <button
              key={idx}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                action.primary
                  ? `bg-${typeConfig.color}-500 text-white hover:bg-${typeConfig.color}-600`
                  : 'bg-white/10 text-slate-300 hover:bg-white/20'
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ABC-XYZ Matrix
function ABCXYZMatrix() {
  const matrix = [
    ['', 'X', 'Y', 'Z'],
    ['A', '12', '8', '3 ← Focus'],
    ['B', '23', '15', '11'],
    ['C', '18', '24', '45 ⚠️'],
  ];

  return (
    <div className="p-4 rounded-xl bg-slate-700/30">
      <h4 className="text-sm font-medium text-slate-300 mb-3">Classification ABC-XYZ:</h4>
      <table className="w-full text-sm">
        <tbody>
          {matrix.map((row, rowIdx) => (
            <tr key={rowIdx}>
              {row.map((cell, cellIdx) => (
                <td
                  key={cellIdx}
                  className={`py-2 px-3 text-center ${
                    rowIdx === 0 || cellIdx === 0
                      ? 'font-medium text-slate-400'
                      : cell.includes('⚠️')
                      ? 'text-amber-400'
                      : cell.includes('Focus')
                      ? 'text-emerald-400'
                      : 'text-white'
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-slate-500 mt-2">45 produits CZ = sur-stock potentiel</p>
    </div>
  );
}

// Supplier Scoring Table
function SupplierScoringTable() {
  const suppliers = [
    { name: 'FourniPlus', score: 2.1, delay: '+3j moy', price: '+12%', rec: '⚠️ Remplacer' },
    { name: 'QuickFood', score: 2.8, delay: 'OK', price: '+8%', rec: '🔄 Renégocier' },
    { name: 'DistribLocal', score: 3.2, delay: '-1j', price: '+5%', rec: '👀 Surveiller' },
  ];

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-white/10">
          <th className="text-left py-2 text-xs text-slate-400">Fournisseur</th>
          <th className="text-center py-2 text-xs text-slate-400">Score</th>
          <th className="text-center py-2 text-xs text-slate-400">Délai</th>
          <th className="text-center py-2 text-xs text-slate-400">Prix</th>
          <th className="text-left py-2 text-xs text-slate-400">Recommandation</th>
        </tr>
      </thead>
      <tbody>
        {suppliers.map((s, idx) => (
          <tr key={idx} className="border-b border-white/5">
            <td className="py-2 text-white">{s.name}</td>
            <td className="py-2 text-center">
              <span className={s.score < 3 ? 'text-rose-400' : 'text-amber-400'}>{s.score}/5</span>
            </td>
            <td className="py-2 text-center text-slate-400">{s.delay}</td>
            <td className="py-2 text-center text-rose-400">{s.price}</td>
            <td className="py-2 text-slate-300">{s.rec}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Cash Flow Forecast
function CashFlowForecast() {
  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <LineChart className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">Prévisions Cash-Flow (30 jours)</h3>
      </div>

      {/* Simple Chart Visualization */}
      <div className="h-32 flex items-end justify-between gap-1 mb-4 px-4">
        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-blue-500/50 rounded-t" style={{ height: '80%' }}></div>
          <span className="text-xs text-slate-500 mt-1">Déc</span>
        </div>
        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-blue-500/40 rounded-t" style={{ height: '60%' }}></div>
          <span className="text-xs text-slate-500 mt-1">S2</span>
        </div>
        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-blue-500/40 rounded-t" style={{ height: '50%' }}></div>
          <span className="text-xs text-slate-500 mt-1">S3</span>
        </div>
        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-amber-500/50 rounded-t" style={{ height: '40%' }}></div>
          <span className="text-xs text-slate-500 mt-1">S4</span>
        </div>
        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-emerald-500/50 rounded-t" style={{ height: '70%' }}></div>
          <span className="text-xs text-slate-500 mt-1">Janv</span>
        </div>
        <div className="flex-1 flex flex-col items-center">
          <div className="w-full bg-emerald-500/40 rounded-t" style={{ height: '85%' }}></div>
          <span className="text-xs text-slate-500 mt-1">S2</span>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-slate-300">Creux prévu: 15 janvier</span>
        </div>
      </div>

      <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-500/10">
        <Lightbulb className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
        <span className="text-sm text-slate-300">
          Conseil: Décaler paiement fournisseur METRO au 20/01 (+5 jours)
        </span>
      </div>

      <div className="flex gap-2 mt-4">
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          📅 Planifier
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          📊 Scénarios
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          💳 Options financement
        </button>
      </div>
    </div>
  );
}

// Main Component
export default function IntelligencePage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: <Brain className="w-4 h-4" /> },
    { id: 'stock', label: 'Stock Intel', icon: <Zap className="w-4 h-4" /> },
    { id: 'previsions', label: 'Prévisions', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'anomalies', label: 'Anomalies', icon: <AlertTriangle className="w-4 h-4" /> },
    { id: 'scoring', label: 'Scoring', icon: <Users className="w-4 h-4" /> },
    { id: 'marges', label: 'Marges', icon: <Calculator className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-7 h-7 text-pink-400" />
            Intelligence
          </h1>
          <p className="text-slate-400">IA & Analytics</p>
        </div>
        <TabNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      </div>

      {/* Content */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          <GlobalScoreCard />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Margin Optimization */}
            <RecommendationCard
              type="margin"
              title="Augmenter le prix de 5 produits sous-margés"
              impact="+847€/mois"
              description="Produits identifiés avec une marge inférieure à la cible"
              details={{
                headers: ['Produit', 'Prix act.', 'Prix sug.', 'Impact'],
                rows: [
                  ['Café Premium 500g', '8.90€', '9.90€', '+124€/mois'],
                  ['Miel Bio 500g', '12.50€', '14.90€', '+216€/mois'],
                  ['Huile Truffe 100ml', '18.00€', '22.00€', '+180€/mois'],
                ],
              }}
              suggestions="Basé sur: élasticité prix, prix concurrence, historique ventes"
              actions={[
                { label: '✅ Appliquer tout', primary: true },
                { label: '📝 Modifier' },
                { label: '📊 Simulation' },
                { label: '❌ Ignorer' },
              ]}
            />

            {/* Stock Optimization */}
            <RecommendationCard
              type="stock"
              title="Réduire le sur-stock sur 8 produits à rotation lente"
              impact="-2 340€"
              description="Produits avec couverture excessive (>3 mois)"
              suggestions="Suggestion: Déstockage progressif sur produits CZ (-20% prix)"
              actions={[
                { label: '📋 Voir liste', primary: true },
                { label: '🏷️ Créer promo' },
                { label: '📊 Simulation' },
              ]}
            >
              <ABCXYZMatrix />
            </RecommendationCard>
          </div>

          {/* Supplier Scoring */}
          <div className="p-6 rounded-2xl bg-slate-800/50 border border-purple-500/20">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-purple-500/20">
                  <Users className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <span className="text-xs font-medium text-purple-400">SCORING FOURNISSEURS</span>
                  <h3 className="font-semibold text-white">3 fournisseurs sous-performants identifiés</h3>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-purple-500/20 text-purple-400">
                Économie: 1 200€/an
              </span>
            </div>

            <div className="mb-4 rounded-xl bg-slate-700/30 p-4">
              <SupplierScoringTable />
            </div>

            <div className="flex gap-2">
              <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
                <Mail className="w-4 h-4" /> Générer email négociation
              </button>
              <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
                <RefreshCw className="w-4 h-4" /> Trouver alternatives
              </button>
              <button className="px-4 py-2 rounded-lg bg-purple-500 text-white text-sm flex items-center gap-2">
                <Eye className="w-4 h-4" /> Détails
              </button>
            </div>
          </div>

          {/* Cash Flow */}
          <CashFlowForecast />
        </div>
      )}

      {activeTab !== 'dashboard' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <Brain className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">
            {tabs.find((t) => t.id === activeTab)?.label}
          </h3>
          <p className="text-slate-400">Module d'intelligence en cours de chargement...</p>
        </div>
      )}
    </div>
  );
}
