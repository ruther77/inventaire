/**
 * Restaurant Page - Gestion Menus et Coûts (Scénario 3.6)
 * Vue unifiée : Menus | Charges | Stock | Prévisions
 */

import { useState } from 'react';
import {
  Utensils,
  Receipt,
  Package,
  TrendingUp,
  Plus,
  Download,
  MoreVertical,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  X,
  Lightbulb,
  Edit3,
  Trophy,
  BarChart3,
  PieChart,
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
              ? 'bg-orange-500 text-white'
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

// Menu Overview Stats
function MenuOverview() {
  const stats = [
    { label: 'Plats Actifs', value: '47', trend: '+3 ce mois', icon: Utensils },
    { label: 'Marge Moy.', value: '68.2%', trend: '+2.1%', trendUp: true, icon: TrendingUp },
    { label: 'Food Cost', value: '31.8%', trend: '-1.5%', trendUp: true, icon: PieChart },
    { label: 'Best Seller', value: 'Burger Chef', subValue: '127 ventes', icon: Trophy },
  ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-orange-400" />
        <h3 className="font-semibold text-white">Vue d'ensemble Menus</h3>
      </div>
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-white/5">
            <div className="flex items-center gap-2 mb-2">
              <stat.icon className="w-4 h-4 text-slate-400" />
              <span className="text-sm text-slate-400">{stat.label}</span>
            </div>
            <div className="text-xl font-bold text-white">{stat.value}</div>
            {stat.subValue ? (
              <div className="text-sm text-slate-400">{stat.subValue}</div>
            ) : (
              <div className={`text-sm ${stat.trendUp ? 'text-emerald-400' : 'text-slate-400'}`}>
                {stat.trendUp ? '↑' : '↓'} {stat.trend}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// Fiches Techniques Table
function FichesTechniques({ onSelectPlat }) {
  const plats = [
    { name: 'Burger Chef', pVente: 16.90, cout: 4.82, marge: 71.5, fc: 28.5, status: 'ok', badge: '🏆 Top vente' },
    { name: 'Entrecôte 300g', pVente: 28.00, cout: 11.20, marge: 60.0, fc: 40.0, status: 'warning', alert: 'Viande +15% ce mois. Ajuster prix?' },
    { name: 'Salade César', pVente: 14.50, cout: 3.48, marge: 76.0, fc: 24.0, status: 'ok' },
    { name: 'Risotto Truffe', pVente: 24.00, cout: 12.00, marge: 50.0, fc: 50.0, status: 'critical', alert: 'Food Cost > 35% ! Recette à optimiser' },
    { name: 'Tiramisu', pVente: 8.50, cout: 1.87, marge: 78.0, fc: 22.0, status: 'ok' },
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ok': return <span className="text-emerald-400">🟢</span>;
      case 'warning': return <span className="text-amber-400">🟡</span>;
      case 'critical': return <span className="text-rose-400">🔴</span>;
      default: return null;
    }
  };

  const getStatusLabel = (status, fc) => {
    switch (status) {
      case 'ok': return <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-400">✅ OK</span>;
      case 'warning': return <span className="px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-400">⚠️ FC↑</span>;
      case 'critical': return <span className="px-2 py-0.5 rounded text-xs bg-rose-500/20 text-rose-400">❌ Crit</span>;
      default: return null;
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Utensils className="w-5 h-5 text-orange-400" />
          <h3 className="font-semibold text-white">Fiches Techniques</h3>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 rounded-lg bg-orange-500 text-white text-sm flex items-center gap-1">
            <Plus className="w-4 h-4" /> Nouveau plat
          </button>
          <button className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-1">
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      <table className="w-full">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-3 text-xs text-slate-400">Plat</th>
            <th className="text-right py-3 text-xs text-slate-400">P.Vente</th>
            <th className="text-right py-3 text-xs text-slate-400">Coût</th>
            <th className="text-right py-3 text-xs text-slate-400">Marge</th>
            <th className="text-right py-3 text-xs text-slate-400">FC%</th>
            <th className="text-center py-3 text-xs text-slate-400">Statut</th>
            <th className="text-center py-3 text-xs text-slate-400">Actions</th>
          </tr>
        </thead>
        <tbody>
          {plats.map((plat, idx) => (
            <>
              <tr
                key={idx}
                className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                onClick={() => onSelectPlat(plat)}
              >
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(plat.status)}
                    <span className="text-white">{plat.name}</span>
                  </div>
                  {plat.badge && (
                    <div className="text-xs text-amber-400 ml-6">{plat.badge}</div>
                  )}
                </td>
                <td className="py-3 text-right text-white">{plat.pVente.toFixed(2)}€</td>
                <td className="py-3 text-right text-white">{plat.cout.toFixed(2)}€</td>
                <td className="py-3 text-right text-white">{plat.marge.toFixed(1)}%</td>
                <td className="py-3 text-right text-white">{plat.fc.toFixed(1)}%</td>
                <td className="py-3 text-center">{getStatusLabel(plat.status, plat.fc)}</td>
                <td className="py-3 text-center">
                  <button className="p-1.5 rounded hover:bg-white/10 text-slate-400">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </td>
              </tr>
              {plat.alert && (
                <tr className="bg-white/5">
                  <td colSpan={7} className="py-2 px-6">
                    <div className="flex items-center gap-2 text-sm">
                      <Lightbulb className="w-4 h-4 text-amber-400" />
                      <span className="text-slate-300">{plat.alert}</span>
                      <button className="ml-2 px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs">
                        {plat.status === 'warning' ? '🔄 Simuler' : '📝 Modifier'}
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Fiche Technique Drawer
function FicheTechniqueDrawer({ plat, onClose }) {
  const ingredients = [
    { name: 'Riz Arborio', qty: 100, unit: 'g', pUnit: 0.003, total: 0.30, pct: 2.5 },
    { name: 'Huile Truffe', qty: 10, unit: 'ml', pUnit: 0.45, total: 4.50, pct: 37.5 },
    { name: 'Parmesan', qty: 30, unit: 'g', pUnit: 0.025, total: 0.75, pct: 6.3 },
    { name: 'Beurre', qty: 20, unit: 'g', pUnit: 0.008, total: 0.16, pct: 1.3 },
    { name: 'Champignons', qty: 50, unit: 'g', pUnit: 0.012, total: 0.60, pct: 5.0 },
    { name: 'Truffe noire', qty: 5, unit: 'g', pUnit: 1.00, total: 5.00, pct: 41.7 },
    { name: 'Bouillon', qty: 200, unit: 'ml', pUnit: 0.002, total: 0.40, pct: 3.3 },
    { name: 'Échalotes', qty: 20, unit: 'g', pUnit: 0.004, total: 0.08, pct: 0.7 },
    { name: 'Vin blanc', qty: 50, unit: 'ml', pUnit: 0.008, total: 0.40, pct: 3.3 },
  ];

  const totalMatieres = ingredients.reduce((sum, i) => sum + i.total, 0);
  const mainOeuvre = 1.50;
  const totalCout = totalMatieres + mainOeuvre;

  const suggestions = [
    { icon: '📈', text: 'Augmenter prix → 28€ (marge 51%)', action: 'Simuler' },
    { icon: '📉', text: 'Réduire truffe 5g → 3g (-40% coût)', action: 'Simuler' },
    { icon: '🔄', text: 'Remplacer huile truffe → huile olive + arôme', action: 'Simuler' },
    { icon: '❌', text: 'Retirer du menu (ventes faibles: 8/sem)', action: null },
  ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white">Fiche Technique - Risotto Truffe</h3>
        <button onClick={onClose} className="p-1.5 rounded hover:bg-white/10 text-slate-400">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Ingrédients */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-slate-300 mb-3">Ingrédients (pour 1 portion)</h4>
        <div className="rounded-xl bg-slate-700/30 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-2 px-3 text-xs text-slate-400">Ingrédient</th>
                <th className="text-right py-2 px-2 text-xs text-slate-400">Qté</th>
                <th className="text-center py-2 px-2 text-xs text-slate-400">Unité</th>
                <th className="text-right py-2 px-2 text-xs text-slate-400">P.Unit</th>
                <th className="text-right py-2 px-2 text-xs text-slate-400">Total</th>
                <th className="text-right py-2 px-2 text-xs text-slate-400">%</th>
                <th className="text-center py-2 px-2 text-xs text-slate-400"></th>
              </tr>
            </thead>
            <tbody>
              {ingredients.map((ing, idx) => (
                <tr key={idx} className="border-b border-white/5">
                  <td className="py-2 px-3 text-white">{ing.name}</td>
                  <td className="py-2 px-2 text-right text-slate-300">{ing.qty}</td>
                  <td className="py-2 px-2 text-center text-slate-400">{ing.unit}</td>
                  <td className="py-2 px-2 text-right text-slate-400">{ing.pUnit.toFixed(3)}€</td>
                  <td className="py-2 px-2 text-right text-white">{ing.total.toFixed(2)}€</td>
                  <td className="py-2 px-2 text-right text-slate-400">{ing.pct.toFixed(1)}%</td>
                  <td className="py-2 px-2 text-center">
                    <button className="text-slate-400 hover:text-white">
                      <Edit3 className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t border-white/10 bg-white/5">
              <tr>
                <td colSpan={4} className="py-2 px-3 text-right text-slate-400">TOTAL MATIÈRES</td>
                <td className="py-2 px-2 text-right font-medium text-white">{totalMatieres.toFixed(2)}€</td>
                <td className="py-2 px-2 text-right text-slate-400">100%</td>
                <td></td>
              </tr>
              <tr>
                <td colSpan={4} className="py-2 px-3 text-right text-slate-400">+ Main d'œuvre</td>
                <td className="py-2 px-2 text-right text-white">{mainOeuvre.toFixed(2)}€</td>
                <td></td>
                <td></td>
              </tr>
              <tr className="font-medium">
                <td colSpan={4} className="py-2 px-3 text-right text-white">= COÛT TOTAL</td>
                <td className="py-2 px-2 text-right text-white">{totalCout.toFixed(2)}€</td>
                <td></td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Analyse & Optimisation */}
      <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          <span className="font-medium text-white">PROBLÈME: Huile truffe + Truffe = 79.2% du coût</span>
        </div>

        <div className="space-y-2">
          <p className="text-sm text-slate-300 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            SUGGESTIONS IA:
          </p>
          <div className="space-y-2 ml-6">
            {suggestions.map((s, idx) => (
              <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-slate-800/50">
                <span>{s.icon}</span>
                <span className="text-sm text-slate-300 flex-1">{s.text}</span>
                {s.action && (
                  <button className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-400">
                    [{s.action}]
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          📊 Analyse complète
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          📝 Modifier recette
        </button>
        <button className="px-4 py-2 rounded-lg bg-orange-500 text-white text-sm">
          💰 Changer prix
        </button>
      </div>
    </div>
  );
}

// Main Component
export default function RestaurantPage() {
  const [activeTab, setActiveTab] = useState('menus');
  const [selectedPlat, setSelectedPlat] = useState(null);

  const tabs = [
    { id: 'menus', label: 'Menus', icon: <Utensils className="w-4 h-4" /> },
    { id: 'charges', label: 'Charges', icon: <Receipt className="w-4 h-4" /> },
    { id: 'stock', label: 'Stock', icon: <Package className="w-4 h-4" /> },
    { id: 'previsions', label: 'Prévisions', icon: <TrendingUp className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Utensils className="w-7 h-7 text-orange-400" />
            Restaurant
          </h1>
          <p className="text-slate-400">Menus, Charges, Stock, Prévisions</p>
        </div>
        <TabNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      </div>

      {/* Content */}
      {activeTab === 'menus' && (
        <div className="space-y-6">
          <MenuOverview />
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <FichesTechniques onSelectPlat={setSelectedPlat} />
            </div>
            <div>
              <FicheTechniqueDrawer plat={selectedPlat} onClose={() => setSelectedPlat(null)} />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'charges' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <Receipt className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Charges Restaurant</h3>
          <p className="text-slate-400">Suivi des dépenses et charges fixes</p>
        </div>
      )}

      {activeTab === 'stock' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <Package className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Stock Restaurant</h3>
          <p className="text-slate-400">Gestion des ingrédients et consommations</p>
        </div>
      )}

      {activeTab === 'previsions' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <TrendingUp className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Prévisions</h3>
          <p className="text-slate-400">Projections et planification</p>
        </div>
      )}
    </div>
  );
}
