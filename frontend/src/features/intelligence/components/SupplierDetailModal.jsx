import { useState } from 'react';
import {
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  CheckCircle,
  Package,
  FileText,
  Calendar
} from 'lucide-react';
import Modal from '../../../components/ui/Modal.jsx';
import Card, { CardHeader, CardContent } from '../../../components/ui/Card.jsx';
import Badge from '../../../components/ui/Badge.jsx';
import ScoreHistoryChart from './ScoreHistoryChart.jsx';
import { useSupplierScoreHistory } from '../../../hooks/useSupplierScoring.js';

/**
 * SupplierDetailModal - Modal avec détails complets d'un fournisseur
 */
export default function SupplierDetailModal({ supplier, open, onClose }) {
  const [activeTab, setActiveTab] = useState('overview');

  const historyQuery = useSupplierScoreHistory(supplier?.name, 12);
  const history = historyQuery.data || [];

  if (!supplier) return null;

  const score = Math.round((supplier.overall_score || 0) * 100);
  const getScoreColor = (s) => {
    if (s >= 75) return 'text-emerald-400';
    if (s >= 50) return 'text-amber-400';
    return 'text-rose-400';
  };

  const getScoreBgColor = (s) => {
    if (s >= 75) return 'bg-emerald-500/20';
    if (s >= 50) return 'bg-amber-500/20';
    return 'bg-rose-500/20';
  };

  const getTrendIcon = (trend) => {
    if (trend === 'improving' || trend > 0) return TrendingUp;
    if (trend === 'declining' || trend < 0) return TrendingDown;
    return Minus;
  };

  const getTrendColor = (trend) => {
    if (trend === 'improving' || trend > 0) return 'text-emerald-400';
    if (trend === 'declining' || trend < 0) return 'text-rose-400';
    return 'text-slate-400';
  };

  const dimensions = [
    {
      key: 'price_stability_score',
      label: 'Stabilité des Prix',
      description: 'Variation des prix dans le temps',
      icon: TrendingUp,
    },
    {
      key: 'delivery_reliability_score',
      label: 'Fiabilité Livraison',
      description: 'Respect des délais de livraison',
      icon: Package,
    },
    {
      key: 'invoice_accuracy_score',
      label: 'Précision Factures',
      description: 'Correspondance commande/facture',
      icon: FileText,
    },
    {
      key: 'quality_score',
      label: 'Qualité',
      description: 'Retours et réclamations',
      icon: CheckCircle,
    },
    {
      key: 'payment_terms_score',
      label: 'Conditions Paiement',
      description: 'Flexibilité et délais de paiement',
      icon: Calendar,
    },
  ];

  const TrendIcon = getTrendIcon(supplier.trend);
  const trendColor = getTrendColor(supplier.trend);

  const tabs = [
    { id: 'overview', label: 'Vue d\'ensemble' },
    { id: 'history', label: 'Historique' },
    { id: 'recommendations', label: 'Recommandations' },
  ];

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={supplier.name}
      size="xl"
      description={`Dernière mise à jour: ${supplier.last_calculated || 'N/A'}`}
    >
      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10 pb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-500/20 text-blue-400'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Score Global */}
            <div className={`rounded-2xl ${getScoreBgColor(score)} p-6 text-center`}>
              <p className="text-xs uppercase tracking-wider text-slate-400 mb-2">
                Score Global
              </p>
              <div className="flex items-center justify-center gap-3">
                <span className={`text-6xl font-bold ${getScoreColor(score)}`}>
                  {score}
                </span>
                <div className="text-left">
                  <p className="text-lg text-slate-400">/100</p>
                  <div className={`flex items-center gap-1 ${trendColor}`}>
                    <TrendIcon className="h-4 w-4" />
                    <span className="text-sm capitalize">{supplier.trend || 'stable'}</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 flex items-center justify-center gap-4 text-sm text-slate-400">
                <div className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  <span>{supplier.data_points || 0} factures analysées</span>
                </div>
              </div>
            </div>

            {/* Dimensions */}
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
                Détail par Dimension
              </h3>
              <div className="space-y-4">
                {dimensions.map((dim) => {
                  const dimScore = Math.round((supplier[dim.key] || 0) * 100);
                  const DimIcon = dim.icon;

                  return (
                    <div key={dim.key} className="glass-panel p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${getScoreBgColor(dimScore)}`}>
                            <DimIcon className={`h-4 w-4 ${getScoreColor(dimScore)}`} />
                          </div>
                          <div>
                            <p className="font-medium text-white">{dim.label}</p>
                            <p className="text-xs text-slate-400">{dim.description}</p>
                          </div>
                        </div>
                        <span className={`text-2xl font-bold ${getScoreColor(dimScore)}`}>
                          {dimScore}
                        </span>
                      </div>
                      {/* Progress bar */}
                      <div className="relative h-2 rounded-full bg-white/5 overflow-hidden">
                        <div
                          className={`absolute left-0 top-0 h-full rounded-full transition-all duration-500 ${
                            dimScore >= 75
                              ? 'bg-emerald-500'
                              : dimScore >= 50
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                          }`}
                          style={{ width: `${dimScore}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <ScoreHistoryChart data={history} loading={historyQuery.isLoading} />
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {score >= 75 ? (
              <Card variant="ghost" className="border border-emerald-500/20 bg-emerald-500/5">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-emerald-400 mb-2">
                      Excellent fournisseur !
                    </h3>
                    <p className="text-sm text-slate-300">
                      Ce fournisseur affiche d'excellentes performances sur tous les critères.
                      Continuez à maintenir cette relation de qualité.
                    </p>
                  </div>
                </div>
              </Card>
            ) : (
              <>
                <div className="flex items-start gap-3 p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
                  <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-amber-400 mb-2">
                      Axes d'amélioration détectés
                    </h3>
                    <p className="text-sm text-slate-300 mb-3">
                      Voici nos recommandations pour améliorer la relation avec ce fournisseur :
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  {supplier.price_stability_score < 0.6 && (
                    <Card variant="ghost" padding="md">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-rose-500/20">
                          <TrendingDown className="h-4 w-4 text-rose-400" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-white mb-1">Stabilité des Prix</h4>
                          <p className="text-sm text-slate-400">
                            Négocier des prix fixes sur une période plus longue pour réduire la volatilité
                          </p>
                        </div>
                      </div>
                    </Card>
                  )}

                  {supplier.delivery_reliability_score < 0.6 && (
                    <Card variant="ghost" padding="md">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-rose-500/20">
                          <Package className="h-4 w-4 text-rose-400" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-white mb-1">Fiabilité Livraison</h4>
                          <p className="text-sm text-slate-400">
                            Prévoir des stocks de sécurité supplémentaires ou chercher un fournisseur alternatif
                          </p>
                        </div>
                      </div>
                    </Card>
                  )}

                  {supplier.invoice_accuracy_score < 0.6 && (
                    <Card variant="ghost" padding="md">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-rose-500/20">
                          <FileText className="h-4 w-4 text-rose-400" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-white mb-1">Précision Factures</h4>
                          <p className="text-sm text-slate-400">
                            Vérifier systématiquement les factures à réception et signaler les erreurs
                          </p>
                        </div>
                      </div>
                    </Card>
                  )}

                  {supplier.quality_score < 0.6 && (
                    <Card variant="ghost" padding="md">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-rose-500/20">
                          <AlertCircle className="h-4 w-4 text-rose-400" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-white mb-1">Qualité Produits</h4>
                          <p className="text-sm text-slate-400">
                            Documenter les problèmes de qualité et envisager une renégociation des standards
                          </p>
                        </div>
                      </div>
                    </Card>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
