/**
 * ScoringCriteriaPage - Gestion des critères de scoring
 *
 * Implémentation exacte selon SUPPLIER_SCORING_FRONTEND_INTEGRATION.md
 * Permet de visualiser et modifier les pondérations des critères de scoring.
 */

import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Save,
  RotateCcw,
  Info,
  AlertCircle,
  CheckCircle,
  DollarSign,
  Truck,
  FileText,
  BarChart3,
  Clock,
  Star,
} from 'lucide-react';
import clsx from 'clsx';
import { useScoringCriteria, useUpdateScoringCriteria } from '@/hooks/useSupplierScoring.js';
import Card, { CardHeader, CardContent } from '@/components/ui/Card.jsx';
import Button from '@/components/ui/Button.jsx';
import Badge from '@/components/ui/Badge.jsx';
import { Skeleton } from '@/components/ui/Skeleton.jsx';

// ============================================================================
// CONFIG
// ============================================================================

const CRITERIA_ICONS = {
  price_stability: { icon: DollarSign, color: 'emerald' },
  delivery_reliability: { icon: Truck, color: 'blue' },
  invoice_accuracy: { icon: FileText, color: 'purple' },
  stock_accuracy: { icon: BarChart3, color: 'amber' },
  payment_terms: { icon: Clock, color: 'cyan' },
  responsiveness: { icon: Clock, color: 'orange' },
  product_quality: { icon: Star, color: 'yellow' },
};

// ============================================================================
// CRITERION SLIDER COMPONENT
// ============================================================================

function CriterionSlider({ criterion, weight, onChange, disabled }) {
  const config = CRITERIA_ICONS[criterion.criterion_id] || { icon: BarChart3, color: 'slate' };
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 bg-slate-800/50 rounded-xl border border-white/10"
    >
      <div className="flex items-start gap-4">
        <div className={clsx('p-3 rounded-lg', `bg-${config.color}-500/20`)}>
          <Icon className={clsx('w-5 h-5', `text-${config.color}-400`)} />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h4 className="font-medium text-white">{criterion.name}</h4>
              <p className="text-xs text-slate-400">{criterion.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={weight}
                onChange={(e) => onChange(Number(e.target.value))}
                disabled={disabled}
                className="w-20 px-2 py-1 bg-slate-900 border border-white/10 rounded text-right text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              />
              <span className="text-sm text-slate-400 w-12 text-right">
                ({(weight * 100).toFixed(0)}%)
              </span>
            </div>
          </div>

          {/* Slider */}
          <div className="relative">
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={weight}
              onChange={(e) => onChange(Number(e.target.value))}
              disabled={disabled}
              className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer disabled:cursor-not-allowed accent-blue-500"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ============================================================================
// TOTAL WEIGHT INDICATOR
// ============================================================================

function TotalWeightIndicator({ total }) {
  const isValid = Math.abs(total - 1.0) <= 0.01;

  return (
    <Card padding="md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isValid ? (
            <div className="p-2 rounded-full bg-emerald-500/20">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
          ) : (
            <div className="p-2 rounded-full bg-rose-500/20">
              <AlertCircle className="w-5 h-5 text-rose-400" />
            </div>
          )}
          <div>
            <p className="font-medium text-white">Poids total</p>
            <p className="text-xs text-slate-400">
              {isValid ? 'Les pondérations sont valides' : 'La somme des poids doit être égale à 1.0'}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className={clsx(
            'text-3xl font-bold',
            isValid ? 'text-emerald-400' : 'text-rose-400'
          )}>
            {total.toFixed(2)}
          </span>
          <p className="text-xs text-slate-400">/ 1.00</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(total * 100, 100)}%` }}
          className={clsx(
            'h-full rounded-full transition-colors',
            total > 1.01 ? 'bg-rose-500' : total < 0.99 ? 'bg-amber-500' : 'bg-emerald-500'
          )}
        />
      </div>
    </Card>
  );
}

// ============================================================================
// INFO PANEL COMPONENT
// ============================================================================

function InfoPanel() {
  return (
    <Card padding="md" className="bg-blue-500/10 border-blue-500/30">
      <div className="flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-medium text-white mb-2">À propos des critères de scoring</h4>
          <ul className="text-sm text-slate-300 space-y-1">
            <li>• Chaque critère représente une dimension d'évaluation des fournisseurs</li>
            <li>• Les pondérations déterminent l'importance relative de chaque critère</li>
            <li>• La somme des pondérations doit être exactement égale à 1.0 (100%)</li>
            <li>• Les modifications sont appliquées au prochain recalcul des scores</li>
          </ul>
        </div>
      </div>
    </Card>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function ScoringCriteriaPage() {
  const navigate = useNavigate();

  // Queries
  const criteriaQuery = useScoringCriteria();
  const updateMutation = useUpdateScoringCriteria();

  // Local state for weights
  const [weights, setWeights] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize weights from query data
  useEffect(() => {
    if (criteriaQuery.data) {
      const data = criteriaQuery.data.data || criteriaQuery.data;
      const criteria = data.criteria || [];
      const initialWeights = {};
      criteria.forEach((c) => {
        initialWeights[c.criterion_id] = c.weight;
      });
      setWeights(initialWeights);
      setHasChanges(false);
    }
  }, [criteriaQuery.data]);

  const criteria = criteriaQuery.data?.data?.criteria || criteriaQuery.data?.criteria || [];

  // Calculate total weight
  const totalWeight = useMemo(() => {
    return Object.values(weights).reduce((sum, w) => sum + w, 0);
  }, [weights]);

  const isValid = Math.abs(totalWeight - 1.0) <= 0.01;

  const handleWeightChange = (criterionId, newWeight) => {
    setWeights((prev) => ({
      ...prev,
      [criterionId]: newWeight,
    }));
    setHasChanges(true);
  };

  const handleReset = () => {
    if (criteriaQuery.data) {
      const data = criteriaQuery.data.data || criteriaQuery.data;
      const criteria = data.criteria || [];
      const initialWeights = {};
      criteria.forEach((c) => {
        initialWeights[c.criterion_id] = c.weight;
      });
      setWeights(initialWeights);
      setHasChanges(false);
    }
  };

  const handleSave = async () => {
    if (!isValid) return;

    try {
      await updateMutation.mutateAsync(weights);
      setHasChanges(false);
    } catch (error) {
      console.error('Error updating criteria:', error);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/intelligence/scoring')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
            <h1 className="text-2xl font-semibold text-white">Critères de Scoring</h1>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            disabled={!hasChanges}
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Réinitialiser
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={!hasChanges || !isValid}
            loading={updateMutation.isPending}
          >
            <Save className="w-4 h-4 mr-1" />
            Enregistrer
          </Button>
        </div>
      </div>

      {/* Info Panel */}
      <InfoPanel />

      {/* Total Weight Indicator */}
      <TotalWeightIndicator total={totalWeight} />

      {/* Criteria List */}
      <Card padding="lg">
        <CardHeader
          title="Pondérations des critères"
          description="Ajustez les poids de chaque critère pour personnaliser le scoring"
        />
        <CardContent>
          <div className="space-y-4">
            {criteria.map((criterion) => (
              <CriterionSlider
                key={criterion.criterion_id}
                criterion={criterion}
                weight={weights[criterion.criterion_id] ?? criterion.weight}
                onChange={(value) => handleWeightChange(criterion.criterion_id, value)}
                disabled={updateMutation.isPending}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Save Status */}
      {hasChanges && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-6 right-6 left-6 md:left-auto md:w-96"
        >
          <Card padding="md" className="bg-amber-500/20 border-amber-500/40">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-amber-400" />
                <span className="text-sm text-white">Modifications non enregistrées</span>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
                disabled={!isValid}
                loading={updateMutation.isPending}
              >
                Enregistrer
              </Button>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Success Message */}
      {updateMutation.isSuccess && !hasChanges && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="fixed bottom-6 right-6 left-6 md:left-auto md:w-96"
        >
          <Card padding="md" className="bg-emerald-500/20 border-emerald-500/40">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              <span className="text-sm text-white">Critères mis à jour avec succès</span>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
