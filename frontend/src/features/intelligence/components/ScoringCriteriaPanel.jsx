import { useState } from 'react';
import { Info, Settings } from 'lucide-react';
import Card, { CardHeader, CardContent } from '../../../components/ui/Card.jsx';
import Badge from '../../../components/ui/Badge.jsx';
import Button from '../../../components/ui/Button.jsx';

/**
 * ScoringCriteriaPanel - Panel de configuration et affichage des critères de scoring
 */
export default function ScoringCriteriaPanel({ editable = false }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const criteria = [
    {
      key: 'price_stability',
      label: 'Stabilité des Prix',
      weight: 25,
      description: 'Mesure la variation des prix dans le temps pour détecter les augmentations brusques',
      calculation: 'Écart-type des prix sur 90 jours',
      thresholds: {
        excellent: '< 5% de variation',
        good: '5-10% de variation',
        poor: '> 10% de variation',
      },
    },
    {
      key: 'delivery_reliability',
      label: 'Fiabilité Livraison',
      weight: 25,
      description: 'Évalue le respect des délais de livraison promis',
      calculation: 'Ratio livraisons à temps / total livraisons',
      thresholds: {
        excellent: '> 95% à temps',
        good: '85-95% à temps',
        poor: '< 85% à temps',
      },
    },
    {
      key: 'invoice_accuracy',
      label: 'Précision Factures',
      weight: 20,
      description: 'Vérifie la correspondance entre commandes et factures',
      calculation: 'Taux de factures sans erreur',
      thresholds: {
        excellent: '> 98% exactes',
        good: '95-98% exactes',
        poor: '< 95% exactes',
      },
    },
    {
      key: 'quality',
      label: 'Qualité Produits',
      weight: 20,
      description: 'Analyse les retours et réclamations qualité',
      calculation: 'Taux de produits sans défaut',
      thresholds: {
        excellent: '< 1% de retours',
        good: '1-3% de retours',
        poor: '> 3% de retours',
      },
    },
    {
      key: 'payment_terms',
      label: 'Conditions Paiement',
      weight: 10,
      description: 'Évalue la flexibilité et les délais de paiement offerts',
      calculation: 'Délai moyen de paiement accordé',
      thresholds: {
        excellent: '> 60 jours',
        good: '30-60 jours',
        poor: '< 30 jours',
      },
    },
  ];

  const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);

  return (
    <Card padding="lg">
      <CardHeader
        title={
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-blue-400" />
            <span>Méthodologie de Scoring</span>
          </div>
        }
        action={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Réduire' : 'Voir détails'}
          </Button>
        }
      />

      <CardContent>
        {/* Summary */}
        <div className="mb-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-slate-300 leading-relaxed">
                Le score global est une moyenne pondérée des 5 dimensions ci-dessous,
                calculée sur les <strong>90 derniers jours</strong> de données.
                Les scores sont mis à jour quotidiennement.
              </p>
            </div>
          </div>
        </div>

        {/* Criteria Grid */}
        <div className="grid gap-4 md:grid-cols-5">
          {criteria.map((criterion) => (
            <div
              key={criterion.key}
              className="glass-panel p-4 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-semibold text-white text-sm">{criterion.label}</h4>
                <Badge variant="brand-solid" size="xs">
                  {criterion.weight}%
                </Badge>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {criterion.description}
              </p>

              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-white/10 space-y-3">
                  <div>
                    <p className="text-xs font-medium text-slate-300 mb-1">Calcul</p>
                    <p className="text-xs text-slate-400">{criterion.calculation}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-300 mb-2">Seuils</p>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-emerald-400">Excellent</span>
                        <span className="text-slate-400">{criterion.thresholds.excellent}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-amber-400">Moyen</span>
                        <span className="text-slate-400">{criterion.thresholds.good}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-rose-400">Faible</span>
                        <span className="text-slate-400">{criterion.thresholds.poor}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div className="mt-6 pt-6 border-t border-white/10">
          <p className="text-xs text-slate-500 text-center">
            Total des poids: {totalWeight}% • Période d'analyse: 90 jours glissants •
            Mise à jour: quotidienne
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
