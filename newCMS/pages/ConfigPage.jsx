/**
 * Config Page - Règles et Audit Trail (Scénario 3.7)
 * Vue unifiée : Règles | Audit | Utilisateurs
 */

import { useState } from 'react';
import {
  Settings,
  Shield,
  Users,
  Plus,
  Search,
  Filter,
  Download,
  ChevronRight,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
  Play,
  Pause,
  Edit3,
  Trash2,
  Copy,
  RotateCcw,
  Mail,
  Clock,
  User,
  FileText,
  Bot,
  Tag,
  Bell,
  X,
  Save,
  TestTube,
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
              ? 'bg-slate-500 text-white'
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

// Rules Category Component
function RulesCategory({ title, count, stats, rules }) {
  const [expanded, setExpanded] = useState(true);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-400">🟢 Actif</span>;
      case 'test':
        return <span className="px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-400">🟡 Test</span>;
      case 'paused':
        return <span className="px-2 py-0.5 rounded text-xs bg-slate-500/20 text-slate-400">⏸️ Pause</span>;
      default:
        return null;
    }
  };

  return (
    <div className="rounded-xl bg-slate-800/50 border border-white/10 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          {expanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
          <span className="font-medium text-white">{title}</span>
          <span className="px-2 py-0.5 rounded-full text-xs bg-blue-500/20 text-blue-400">{count} règles actives</span>
        </div>
        <button className="px-3 py-1.5 rounded-lg bg-white/10 text-slate-300 text-sm">
          ⚙️ Configurer
        </button>
      </button>

      {expanded && (
        <div className="border-t border-white/10">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10 bg-slate-900/30">
                <th className="text-left py-2 px-4 text-xs text-slate-400">Priorité</th>
                <th className="text-left py-2 px-4 text-xs text-slate-400">Condition</th>
                <th className="text-left py-2 px-4 text-xs text-slate-400">Action</th>
                <th className="text-center py-2 px-4 text-xs text-slate-400">État</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule, idx) => (
                <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                  <td className="py-3 px-4 text-slate-300">{rule.priority}</td>
                  <td className="py-3 px-4 text-white">{rule.condition}</td>
                  <td className="py-3 px-4 text-slate-300">→ {rule.action}</td>
                  <td className="py-3 px-4 text-center">{getStatusBadge(rule.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {stats && (
            <div className="p-4 bg-slate-900/30 border-t border-white/10">
              <span className="text-sm text-slate-400">📊 Stats: {stats}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Rule Editor Component
function RuleEditor({ onClose }) {
  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Edit3 className="w-5 h-5 text-blue-400" />
          Éditeur de Règle
        </h3>
        <button onClick={onClose} className="p-1.5 rounded hover:bg-white/10 text-slate-400">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Rule Name */}
      <div className="mb-4">
        <label className="text-sm text-slate-400 mb-1 block">Nom:</label>
        <input
          type="text"
          defaultValue="Alerte prix anormal"
          className="w-full px-4 py-2 rounded-lg bg-slate-700/50 border border-white/10 text-white"
        />
      </div>

      {/* SI Conditions */}
      <div className="p-4 rounded-xl bg-slate-700/30 mb-4">
        <div className="text-sm font-medium text-slate-300 mb-3">SI</div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <select className="px-3 py-2 rounded-lg bg-slate-800 border border-white/10 text-white text-sm">
              <option>Prix achat</option>
              <option>Stock</option>
              <option>Fournisseur</option>
            </select>
            <select className="px-3 py-2 rounded-lg bg-slate-800 border border-white/10 text-white text-sm">
              <option>augmente de &gt;</option>
              <option>diminue de &gt;</option>
              <option>est égal à</option>
            </select>
            <input
              type="text"
              defaultValue="15"
              className="w-20 px-3 py-2 rounded-lg bg-slate-800 border border-white/10 text-white text-sm"
            />
            <span className="text-slate-400">%</span>
          </div>

          <button className="text-xs text-blue-400 hover:text-blue-300">[+ ET]</button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 w-8">ET</span>
            <select className="px-3 py-2 rounded-lg bg-slate-800 border border-white/10 text-white text-sm">
              <option>Fournisseur</option>
              <option>Catégorie</option>
            </select>
            <select className="px-3 py-2 rounded-lg bg-slate-800 border border-white/10 text-white text-sm">
              <option>n'est pas</option>
              <option>est</option>
            </select>
            <select className="px-3 py-2 rounded-lg bg-slate-800 border border-white/10 text-white text-sm">
              <option>[Saisonnier]</option>
              <option>[Tous]</option>
            </select>
          </div>

          <button className="text-xs text-blue-400 hover:text-blue-300">[+ OU]</button>
        </div>
      </div>

      {/* ALORS Actions */}
      <div className="p-4 rounded-xl bg-slate-700/30 mb-4">
        <div className="text-sm font-medium text-slate-300 mb-3">ALORS</div>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input type="checkbox" defaultChecked className="rounded border-slate-600" />
            <span className="text-sm text-slate-300">Créer alerte niveau</span>
            <select className="px-2 py-1 rounded bg-slate-800 border border-white/10 text-amber-400 text-sm">
              <option>⚠️ Warning</option>
              <option>🔴 Critique</option>
              <option>🔵 Info</option>
            </select>
          </label>

          <label className="flex items-center gap-2">
            <input type="checkbox" defaultChecked className="rounded border-slate-600" />
            <span className="text-sm text-slate-300">Notifier</span>
            <select className="px-2 py-1 rounded bg-slate-800 border border-white/10 text-white text-sm">
              <option>Admin</option>
              <option>Chef</option>
              <option>Tous</option>
            </select>
            <span className="text-sm text-slate-400">par</span>
            <select className="px-2 py-1 rounded bg-slate-800 border border-white/10 text-white text-sm">
              <option>Email</option>
              <option>SMS</option>
              <option>Push</option>
            </select>
          </label>

          <label className="flex items-center gap-2">
            <input type="checkbox" className="rounded border-slate-600" />
            <span className="text-sm text-slate-300">Bloquer l'import (demande validation)</span>
          </label>

          <label className="flex items-center gap-2">
            <input type="checkbox" defaultChecked className="rounded border-slate-600" />
            <span className="text-sm text-slate-300">Suggérer action:</span>
            <input
              type="text"
              defaultValue="Vérifier avec fournisseur"
              className="flex-1 px-2 py-1 rounded bg-slate-800 border border-white/10 text-white text-sm"
            />
          </label>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          <TestTube className="w-4 h-4" /> Tester sur données
        </button>
        <button className="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm flex items-center gap-2">
          <Save className="w-4 h-4" /> Sauvegarder
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm">
          ❌ Annuler
        </button>
      </div>
    </div>
  );
}

// Audit Trail View
function AuditTrailView() {
  const logs = [
    { time: '11/12 14:32:15', user: 'chef', action: '📝 Modification prix produit', detail: 'Prix Tomates 2.40€ → 2.83€', icon: Edit3 },
    { time: '11/12 14:28:03', user: 'système', action: '🤖 Auto-catégorisation facture', detail: '47 lignes - Facture METRO', icon: Bot },
    { time: '11/12 14:25:47', user: 'admin', action: '✅ Validation rapprochement', detail: '12 matchs', icon: CheckCircle2 },
    { time: '11/12 13:15:22', user: 'chef', action: '📥 Import facture', detail: 'Facture BRAKE - 1 234.50€', icon: FileText },
    { time: '11/12 10:45:00', user: 'système', action: '⚠️ Alerte générée', detail: 'Stock Tomates < seuil min', icon: AlertTriangle },
  ];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="p-4 rounded-xl bg-slate-800/50 border border-white/10">
        <div className="flex items-center gap-4">
          <select className="px-3 py-2 rounded-lg bg-slate-700 border border-white/10 text-white text-sm">
            <option>Tous types ▼</option>
          </select>
          <select className="px-3 py-2 rounded-lg bg-slate-700 border border-white/10 text-white text-sm">
            <option>Tous users ▼</option>
          </select>
          <select className="px-3 py-2 rounded-lg bg-slate-700 border border-white/10 text-white text-sm">
            <option>7 derniers jours ▼</option>
          </select>
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Recherche..."
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-slate-700 border border-white/10 text-white placeholder-slate-500"
            />
          </div>
          <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
            <Download className="w-4 h-4" /> Exporter
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="rounded-xl bg-slate-800/50 border border-white/10 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-xs text-slate-400">Horodatage</th>
              <th className="text-left py-3 px-4 text-xs text-slate-400">Utilisateur</th>
              <th className="text-left py-3 px-4 text-xs text-slate-400">Action</th>
              <th className="text-left py-3 px-4 text-xs text-slate-400">Détails</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, idx) => (
              <tr key={idx} className="border-b border-white/5 hover:bg-white/5 cursor-pointer">
                <td className="py-3 px-4 text-sm text-slate-400 font-mono">{log.time}</td>
                <td className="py-3 px-4">
                  <span className={`text-sm ${log.user === 'système' ? 'text-blue-400' : 'text-white'}`}>
                    {log.user}
                  </span>
                </td>
                <td className="py-3 px-4 text-sm text-white">{log.action}</td>
                <td className="py-3 px-4 text-sm text-slate-400">{log.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="p-4 bg-slate-900/30 border-t border-white/10">
          <span className="text-sm text-slate-400">📊 Résumé période: 847 actions | 12 utilisateurs | 3 alertes système</span>
        </div>
      </div>

      {/* Action Detail Drawer */}
      <div className="p-6 rounded-xl bg-slate-800/50 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white flex items-center gap-2">
            <Search className="w-4 h-4 text-blue-400" />
            Détail Action
          </h4>
          <button className="p-1.5 rounded hover:bg-white/10 text-slate-400">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 rounded-xl bg-slate-700/30 mb-4">
          <h5 className="font-medium text-white mb-3">📝 Modification prix produit</h5>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-white/5">
                <td className="py-2 text-slate-400">Utilisateur</td>
                <td className="py-2 text-white">chef</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-2 text-slate-400">Horodatage</td>
                <td className="py-2 text-white">11/12 14:32</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-2 text-slate-400">IP</td>
                <td className="py-2 text-white font-mono">192.168.1.50</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-2 text-slate-400">Produit</td>
                <td className="py-2 text-white">Tomates kg</td>
              </tr>
              <tr className="border-b border-white/5">
                <td className="py-2 text-slate-400">Prix achat</td>
                <td className="py-2">
                  <span className="text-slate-400">2.40€</span>
                  <span className="mx-2 text-slate-500">→</span>
                  <span className="text-white">2.83€</span>
                  <span className="ml-2 text-rose-400">+17.9%</span>
                </td>
              </tr>
              <tr>
                <td className="py-2 text-slate-400">Source</td>
                <td className="py-2 text-white">Facture #F4521</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="space-y-2 text-sm mb-4">
          <p className="text-slate-400">💡 Contexte: Import automatique depuis facture METRO</p>
          <p className="text-slate-400">🔗 Règle déclenchée: "MAJ prix si facture validée"</p>
        </div>

        <div className="flex gap-2">
          <button className="px-4 py-2 rounded-lg bg-amber-500/20 text-amber-400 text-sm flex items-center gap-2">
            <RotateCcw className="w-4 h-4" /> Annuler cette action
          </button>
          <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
            <Mail className="w-4 h-4" /> Signaler
          </button>
          <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
            <Copy className="w-4 h-4" /> Copier référence
          </button>
        </div>
      </div>
    </div>
  );
}

// Main Component
export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState('regles');
  const [showRuleEditor, setShowRuleEditor] = useState(false);

  const tabs = [
    { id: 'regles', label: 'Règles', icon: <Settings className="w-4 h-4" /> },
    { id: 'audit', label: 'Audit', icon: <Shield className="w-4 h-4" /> },
    { id: 'utilisateurs', label: 'Utilisateurs', icon: <Users className="w-4 h-4" /> },
  ];

  const categorisationRules = [
    { priority: 1, condition: 'Libellé contient "METRO"', action: 'Cat: Achats', status: 'active' },
    { priority: 2, condition: 'Libellé contient "EDF"', action: 'Cat: Énergie', status: 'active' },
    { priority: 3, condition: 'Montant > 5000€', action: 'Flag: Review', status: 'active' },
    { priority: 4, condition: 'Type = Virement récurrent', action: 'Cat: Fixe', status: 'test' },
  ];

  const stockRules = [
    { priority: 1, condition: 'Stock < Seuil min', action: 'Alerte Rouge', status: 'active' },
    { priority: 2, condition: 'Stock < 150% Seuil', action: 'Alerte Jaune', status: 'active' },
    { priority: 3, condition: 'DLC < 7 jours', action: 'Alerte DLC', status: 'active' },
    { priority: 4, condition: 'Rotation < 0.5/mois', action: 'Flag: Dormant', status: 'active' },
    { priority: 5, condition: 'Sur-stock > 300%', action: 'Flag: Excess', status: 'active' },
  ];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Settings className="w-7 h-7 text-slate-400" />
            Configuration
          </h1>
          <p className="text-slate-400">Règles, Audit, Utilisateurs</p>
        </div>
        <TabNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      </div>

      {/* Content */}
      {activeTab === 'regles' && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-blue-400" />
                <h2 className="font-semibold text-white">Moteur de Règles</h2>
              </div>
              <button
                onClick={() => setShowRuleEditor(true)}
                className="px-4 py-2 rounded-lg bg-blue-500 text-white text-sm flex items-center gap-2"
              >
                <Plus className="w-4 h-4" /> Nouvelle
              </button>
            </div>

            <RulesCategory
              title="Catégorisation Automatique"
              count={12}
              stats="847 applications ce mois | 94% succès"
              rules={categorisationRules}
            />

            <RulesCategory
              title="Alertes Stock"
              count={5}
              stats="156 alertes ce mois | 23 résolues"
              rules={stockRules}
            />
          </div>

          <div>
            {showRuleEditor && <RuleEditor onClose={() => setShowRuleEditor(false)} />}
          </div>
        </div>
      )}

      {activeTab === 'audit' && <AuditTrailView />}

      {activeTab === 'utilisateurs' && (
        <div className="p-8 rounded-2xl bg-slate-800/50 border border-white/10 text-center">
          <Users className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Gestion Utilisateurs</h3>
          <p className="text-slate-400">Rôles, permissions et accès</p>
        </div>
      )}
    </div>
  );
}
