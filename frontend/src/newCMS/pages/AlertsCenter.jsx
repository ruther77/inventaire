/**
 * Alerts Center - Gestion des Urgences (Scénario 3.9)
 * Centre de notifications actionnable
 */

import { useState } from 'react';
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Clock,
  Package,
  DollarSign,
  TrendingUp,
  Utensils,
  MessageSquare,
  Mail,
  MapPin,
  ChevronRight,
  X,
  Check,
  Phone,
  Lightbulb,
  Calendar,
  Settings,
} from 'lucide-react';

// Alert Summary Stats
function AlertSummary() {
  const stats = [
    { label: 'Critiques', count: 3, color: 'rose', icon: AlertCircle },
    { label: 'Warnings', count: 8, color: 'amber', icon: AlertTriangle },
    { label: 'Infos', count: 12, color: 'blue', icon: Info },
    { label: 'Résolues (7j)', count: 47, color: 'emerald', icon: CheckCircle2 },
  ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center gap-2 mb-4">
        <Bell className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">Résumé Alertes</h3>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className={`p-4 rounded-xl bg-${stat.color}-500/10 border border-${stat.color}-500/20`}>
            <div className="flex items-center gap-2 mb-2">
              <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
              <span className="text-sm text-slate-400">{stat.label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{stat.count}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Critical Alert Card
function CriticalAlertCard({ alert }) {
  return (
    <div className="p-6 rounded-xl bg-slate-800/50 border border-rose-500/30">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-rose-500/20">
            <AlertCircle className="w-5 h-5 text-rose-400" />
          </div>
          <div>
            <span className="text-xs text-slate-500">#{alert.id}</span>
            <h4 className="font-semibold text-white">{alert.title}</h4>
          </div>
        </div>
        <span className="text-xs text-slate-400">{alert.time}</span>
      </div>

      {/* Alert Details */}
      <div className="space-y-2 mb-4 p-3 rounded-lg bg-slate-900/50">
        {alert.details.map((detail, idx) => (
          <div key={idx} className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">{detail.icon}</span>
            <span className="text-slate-300">{detail.label}:</span>
            <span className={detail.highlight ? 'text-rose-400 font-medium' : 'text-white'}>{detail.value}</span>
          </div>
        ))}
      </div>

      {/* Suggested Actions */}
      {alert.suggestions && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-medium text-slate-300">ACTIONS SUGGÉRÉES:</span>
          </div>
          <div className="space-y-2">
            {alert.suggestions.map((suggestion, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-300">{idx + 1}. {suggestion.icon} {suggestion.text}</span>
                </div>
                <button className="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-400 text-xs">
                  [{suggestion.action}]
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Impact */}
      {alert.impact && (
        <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <div className="flex items-center gap-2 mb-2">
            <Utensils className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-medium text-white">{alert.impact.title}</span>
          </div>
          <ul className="text-sm text-slate-300 space-y-1 ml-6">
            {alert.impact.items.map((item, idx) => (
              <li key={idx}>• {item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        <button className="px-4 py-2 rounded-lg bg-emerald-500 text-white text-sm font-medium flex items-center gap-2">
          <Check className="w-4 h-4" /> Marquer résolu
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          <Clock className="w-4 h-4" /> Rappel 1h
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          <Mail className="w-4 h-4" /> Escalader
        </button>
        <button className="px-4 py-2 rounded-lg bg-white/10 text-slate-300 text-sm flex items-center gap-2">
          <MessageSquare className="w-4 h-4" /> Commenter
        </button>
      </div>
    </div>
  );
}

// Warning List
function WarningsList() {
  const warnings = [
    { text: 'Stock faible: Huile Olive 1L (8 unités, seuil: 15)', icon: '⚠️' },
    { text: 'DLC proche: Yaourts (expire dans 3 jours)', icon: '⚠️' },
    { text: 'Prix anormal: Beurre +22% vs mois dernier', icon: '⚠️' },
    { text: 'Facture en attente: BRAKE #B-7901 depuis 5 jours', icon: '⚠️' },
  ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-amber-500/20">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-white">Warnings</h3>
          <span className="text-sm text-slate-400">- À traiter dans les 24h</span>
        </div>
        <button className="text-sm text-blue-400 hover:text-blue-300">Voir tout</button>
      </div>

      <div className="space-y-2">
        {warnings.map((warning, idx) => (
          <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 cursor-pointer">
            <div className="flex items-center gap-2">
              <span>{warning.icon}</span>
              <span className="text-sm text-slate-300">{warning.text}</span>
            </div>
            <button className="px-2 py-1 rounded text-xs bg-white/10 text-blue-400 flex items-center gap-1">
              🔗 Détail
            </button>
          </div>
        ))}
        <button className="w-full text-center text-sm text-slate-500 hover:text-slate-400 py-2">
          + 4 autres...
        </button>
      </div>
    </div>
  );
}

// Notification Settings
function NotificationSettings() {
  const settings = [
    { type: '🔴 Critique', inApp: true, email: true, sms: true, push: true },
    { type: '🟡 Warning', inApp: true, email: true, sms: false, push: true },
    { type: '🔵 Info', inApp: true, email: false, sms: false, push: false },
  ];

  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-slate-400" />
          <h3 className="font-semibold text-white">Paramètres Notifications</h3>
        </div>
        <button className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
          ⚙️ Modifier préférences
        </button>
      </div>

      <table className="w-full">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-2 text-xs text-slate-400">Type d'alerte</th>
            <th className="text-center py-2 text-xs text-slate-400">In-App</th>
            <th className="text-center py-2 text-xs text-slate-400">Email</th>
            <th className="text-center py-2 text-xs text-slate-400">SMS</th>
            <th className="text-center py-2 text-xs text-slate-400">Push Mobile</th>
          </tr>
        </thead>
        <tbody>
          {settings.map((setting, idx) => (
            <tr key={idx} className="border-b border-white/5">
              <td className="py-3 text-sm text-white">{setting.type}</td>
              <td className="py-3 text-center">{setting.inApp ? '✅' : '❌'}</td>
              <td className="py-3 text-center">{setting.email ? '✅' : '❌'}</td>
              <td className="py-3 text-center">{setting.sms ? '✅' : '❌'}</td>
              <td className="py-3 text-center">{setting.push ? '✅' : '❌'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Main Component
export default function AlertsCenter() {
  const criticalAlerts = [
    {
      id: 'ALT-2847',
      title: 'RUPTURE IMMINENTE - Tomates Grappe',
      time: 'Il y a 15 min',
      details: [
        { icon: '📦', label: 'Stock actuel', value: '2 kg', highlight: true },
        { icon: '📈', label: 'Consommation moyenne', value: '15 kg/jour' },
        { icon: '⏰', label: 'Rupture estimée', value: "Aujourd'hui 14h00", highlight: true },
      ],
      suggestions: [
        { icon: '📦', text: 'Commander 50kg METRO (livraison express 4h)', action: 'Commander' },
        { icon: '🏪', text: 'Acheter 20kg au marché Rungis (disponible)', action: 'Itinéraire' },
        { icon: '📋', text: 'Retirer plats concernés du menu temporairement', action: 'Voir plats' },
      ],
      impact: {
        title: 'Impact menu: 4 plats utilisent ce produit',
        items: [
          'Salade Tomates Mozza (12 ventes/jour)',
          'Bruschetta (8 ventes/jour)',
          'Burger Veggie (6 ventes/jour)',
          'Gaspacho (4 ventes/jour)',
        ],
      },
    },
    {
      id: 'ALT-2845',
      title: 'ANOMALIE FINANCIÈRE - Transaction suspecte',
      time: 'Il y a 2h',
      details: [
        { icon: '💳', label: 'Transaction', value: 'VIR INCONNU -4 500€', highlight: true },
        { icon: '📅', label: 'Date', value: '11/12/2025' },
        { icon: '❓', label: 'Correspondance', value: 'Aucune facture trouvée', highlight: true },
      ],
      suggestions: [
        { icon: '🔍', text: 'Investiguer la transaction', action: 'Investiguer' },
        { icon: '🏦', text: 'Contacter la banque', action: 'Appeler' },
      ],
      analysis: {
        title: 'ANALYSE IA:',
        items: [
          'Montant inhabituel pour ce type de virement',
          'Bénéficiaire non reconnu dans l\'historique',
          'Score de confiance: 12% (très suspect)',
        ],
      },
    },
  ];

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bell className="w-7 h-7 text-blue-400" />
            Centre de Notifications
          </h1>
          <p className="text-slate-400">Alertes et actions prioritaires</p>
        </div>
      </div>

      {/* Summary */}
      <AlertSummary />

      {/* Critical Alerts */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle className="w-5 h-5 text-rose-400" />
          <h2 className="text-lg font-semibold text-white">Alertes Critiques</h2>
          <span className="text-sm text-slate-400">- Action immédiate requise</span>
        </div>

        <div className="space-y-4">
          {criticalAlerts.map((alert) => (
            <CriticalAlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      </div>

      {/* Warnings */}
      <WarningsList />

      {/* Settings */}
      <NotificationSettings />
    </div>
  );
}
