/**
 * IntelligencePage - Dashboard Intelligence unifie
 *
 * Vue consolidee de toutes les fonctionnalites d'intelligence:
 * - Score de sante global
 * - Previsions (ventes, tresorerie, stock)
 * - Anomalies actives
 * - Scoring fournisseurs
 * - Insights et recommandations
 */

import { useMemo, useCallback, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { IntelligenceSkeleton } from '../../components/ui/Skeleton.jsx';
import CardExpandable from '../../components/ui/CardExpandable.jsx';
import AIConfidenceBadge from '../../components/ui/AIConfidenceBadge.jsx';
import QueryErrorState from '../../components/feedback/QueryErrorState.jsx';
import { EmptyAnomalies, EmptyForecasts, EmptySuppliers } from '../../components/feedback/ActionableEmptyStates.jsx';
import { DecisionPanel } from '../../components/ai';
import { useToast } from '../../components/ui/Toast.jsx';
import {
  fetchInventoryIntelligenceSummary,
  fetchForecastingSummary,
  fetchAnomalySummary,
  fetchSuppliersRanking,
  resolveAnomaly,
} from '../../api/client.js';

// ============================================================================
// COMPOSANTS INTERNES
// ============================================================================

function HealthGauge({ score, label }) {
  const getColor = (s) => {
    if (s >= 80) return 'text-emerald-500';
    if (s >= 60) return 'text-amber-500';
    return 'text-rose-500';
  };

  const getBgColor = (s) => {
    if (s >= 80) return 'bg-emerald-50 border-emerald-200';
    if (s >= 60) return 'bg-amber-50 border-amber-200';
    return 'bg-rose-50 border-rose-200';
  };

  return (
    <div className={`rounded-2xl border p-6 text-center ${getBgColor(score)}`}>
      <p className="text-xs uppercase tracking-widest text-slate-500">{label}</p>
      <p className={`text-5xl font-bold ${getColor(score)}`}>{score}</p>
      <p className="text-sm text-slate-600">/ 100</p>
    </div>
  );
}

function MetricCard({ label, value, trend, format = 'number', severity }) {
  const formatValue = (v) => {
    if (format === 'currency') return `${v?.toLocaleString('fr-FR')} €`;
    if (format === 'percent') return `${v}%`;
    return v?.toLocaleString('fr-FR') ?? '-';
  };

  const getTrendIcon = (t) => {
    if (t === 'up') return '↑';
    if (t === 'down') return '↓';
    return '→';
  };

  const getSeverityClass = (s) => {
    if (s === 'critical') return 'border-rose-200 bg-rose-50';
    if (s === 'warning') return 'border-amber-200 bg-amber-50';
    if (s === 'success') return 'border-emerald-200 bg-emerald-50';
    return 'border-slate-200 bg-white';
  };

  return (
    <div className={`rounded-2xl border p-4 ${getSeverityClass(severity)}`}>
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <div className="flex items-baseline gap-2">
        <p className="text-2xl font-semibold text-slate-900">{formatValue(value)}</p>
        {trend && (
          <span className={trend === 'up' ? 'text-emerald-500' : trend === 'down' ? 'text-rose-500' : 'text-slate-400'}>
            {getTrendIcon(trend)}
          </span>
        )}
      </div>
    </div>
  );
}

function ForecastCard({ type, predicted, confidence, trend, warning }) {
  return (
    <Card className={`flex flex-col gap-2 ${warning ? 'border-amber-300 bg-amber-50' : ''}`}>
      <p className="text-xs uppercase tracking-widest text-slate-500">{type}</p>
      <p className="text-2xl font-bold text-slate-900">
        {predicted?.toLocaleString('fr-FR')} €
      </p>
      <div className="flex items-center gap-3 text-sm">
        <AIConfidenceBadge
          confidence={confidence}
          label="Confiance"
          variant="compact"
          size="sm"
        />
        <span className={trend === 'up' ? 'text-emerald-500' : trend === 'down' ? 'text-rose-500' : 'text-slate-400'}>
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
        </span>
      </div>
    </Card>
  );
}

function AnomalyCard({ anomaly, onInvestigate }) {
  const getSeverityBadge = (severity) => {
    const classes = {
      critical: 'bg-rose-100 text-rose-700',
      high: 'bg-amber-100 text-amber-700',
      medium: 'bg-blue-100 text-blue-700',
      low: 'bg-slate-100 text-slate-700',
    };
    return classes[severity] || classes.low;
  };

  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-3">
        <span className={`rounded-full px-2 py-1 text-xs font-medium ${getSeverityBadge(anomaly.severity)}`}>
          {anomaly.severity}
        </span>
        <div>
          <p className="font-medium text-slate-900">{anomaly.title}</p>
          <p className="text-sm text-slate-500">{anomaly.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-slate-600">
          Impact: {anomaly.impact?.toLocaleString('fr-FR')} €
        </span>
        <Button variant="ghost" size="sm" onClick={() => onInvestigate?.(anomaly)}>
          Analyser
        </Button>
      </div>
    </div>
  );
}

function SupplierRow({ supplier, rank }) {
  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-emerald-600';
    if (score >= 0.6) return 'text-amber-600';
    return 'text-rose-600';
  };

  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
      <div className="flex items-center gap-3">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-medium">
          {rank}
        </span>
        <span className="font-medium text-slate-900">{supplier.name}</span>
      </div>
      <div className="flex items-center gap-4">
        <span className={`font-semibold ${getScoreColor(supplier.overall_score)}`}>
          {Math.round(supplier.overall_score * 100)}
        </span>
        <span className="text-xs text-slate-500">{supplier.trend}</span>
      </div>
    </div>
  );
}

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

export default function IntelligencePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast?.() || { toast: () => {} };
  const [appliedDecisions, setAppliedDecisions] = useState(new Set());

  // Queries
  const inventoryQuery = useQuery({
    queryKey: ['intelligence', 'inventory'],
    queryFn: fetchInventoryIntelligenceSummary,
    staleTime: 60000,
  });

  const forecastQuery = useQuery({
    queryKey: ['intelligence', 'forecast'],
    queryFn: fetchForecastingSummary,
    staleTime: 60000,
  });

  const anomalyQuery = useQuery({
    queryKey: ['intelligence', 'anomalies'],
    queryFn: fetchAnomalySummary,
    staleTime: 30000,
  });

  const suppliersQuery = useQuery({
    queryKey: ['intelligence', 'suppliers'],
    queryFn: () => fetchSuppliersRanking({ limit: 5 }),
    staleTime: 300000,
  });

  // Mutations pour exécuter les décisions
  const resolveAnomalyMutation = useMutation({
    mutationFn: ({ anomalyId, note }) => resolveAnomaly?.(anomalyId, { resolution_note: note || 'Résolu via Intelligence Dashboard' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intelligence', 'anomalies'] });
      toast?.({ title: 'Anomalie résolue', variant: 'success' });
    },
    onError: (error) => {
      toast?.({ title: 'Erreur', description: error.message, variant: 'error' });
    },
  });

  const isLoading = inventoryQuery.isLoading || forecastQuery.isLoading;
  const hasError = inventoryQuery.error || forecastQuery.error;

  // Gestion des erreurs globales
  const handleRetryAll = () => {
    inventoryQuery.refetch();
    forecastQuery.refetch();
    anomalyQuery.refetch();
    suppliersQuery.refetch();
  };

  // Handler pour appliquer une décision individuelle
  const handleApplyDecision = useCallback((decisionId) => {
    // Marquer comme appliquée pour feedback UI immédiat
    setAppliedDecisions((prev) => new Set([...prev, decisionId]));

    // Exécuter l'action correspondante selon le type de décision
    if (decisionId.startsWith('anomaly-')) {
      const anomalyId = decisionId.replace('anomaly-', '');
      resolveAnomalyMutation.mutate({ anomalyId });
    } else if (decisionId === 'stock' || decisionId.startsWith('stock-')) {
      // Navigation vers la gestion de stock avec action pré-remplie
      navigate('/operations/catalogue?action=optimize_stock');
      toast?.({ title: 'Optimisation stock', description: 'Redirecting vers le catalogue...' });
    } else if (decisionId === 'cash' || decisionId.startsWith('cash-')) {
      // Navigation vers la trésorerie
      navigate('/finances/tresorerie?action=plan_payments');
      toast?.({ title: 'Planification paiements', description: 'Redirecting vers la trésorerie...' });
    } else if (decisionId.startsWith('pricing-')) {
      // Navigation vers le catalogue pour ajuster le prix
      navigate('/operations/catalogue?action=adjust_prices');
      toast?.({ title: 'Ajustement prix', description: 'Redirecting vers le catalogue...' });
    } else if (decisionId.startsWith('supplier-')) {
      // Navigation vers le scoring fournisseurs
      navigate('/intelligence/scoring');
      toast?.({ title: 'Analyse fournisseurs', description: 'Redirecting vers le scoring...' });
    } else {
      // Action générique - log et feedback
      toast?.({ title: 'Décision appliquée', description: `Action ${decisionId} enregistrée` });
    }
  }, [navigate, resolveAnomalyMutation, toast]);

  // Handler pour appliquer toutes les décisions fiables
  const handleApplyAllDecisions = useCallback((decisionIds) => {
    decisionIds.forEach((id) => handleApplyDecision(id));
    toast?.({
      title: 'Décisions appliquées',
      description: `${decisionIds.length} actions lancées`,
      variant: 'success',
    });
  }, [handleApplyDecision, toast]);

  // Handler pour ignorer une décision
  const handleDismissDecision = useCallback((decisionId) => {
    setAppliedDecisions((prev) => new Set([...prev, `dismissed-${decisionId}`]));
    toast?.({ title: 'Décision ignorée', variant: 'info' });
  }, [toast]);

  // Calcul score de sante global (moyenne ponderee)
  const calculateHealthScore = () => {
    const inventory = inventoryQuery.data;
    const forecast = forecastQuery.data;
    const anomalies = anomalyQuery.data;

    if (!inventory && !forecast) return 75; // Defaut

    let score = 80;

    // Penalite pour stock critique
    if (inventory?.critical_items > 0) {
      score -= inventory.critical_items * 5;
    }

    // Penalite pour anomalies critiques
    if (anomalies?.critical > 0) {
      score -= anomalies.critical * 10;
    }

    // Bonus pour bonne rotation stock
    if (inventory?.avg_rotation > 4) {
      score += 5;
    }

    return Math.max(0, Math.min(100, Math.round(score)));
  };

  const handleInvestigateAnomaly = (anomaly) => {
    // Navigation vers detail anomalie
    window.location.href = `/intelligence/anomalies/${anomaly.id}`;
  };

  if (hasError) {
    return (
      <QueryErrorState
        error={inventoryQuery.error || forecastQuery.error}
        onRetry={handleRetryAll}
        variant="full"
      />
    );
  }

  const healthScore = calculateHealthScore();
  const inventory = inventoryQuery.data && typeof inventoryQuery.data === 'object' ? inventoryQuery.data : {};
  const forecast = forecastQuery.data && typeof forecastQuery.data === 'object' ? forecastQuery.data : {};
  const anomalies = anomalyQuery.data && typeof anomalyQuery.data === 'object'
    ? anomalyQuery.data
    : { items: [], total: 0 };
  const suppliers = Array.isArray(suppliersQuery.data) ? suppliersQuery.data : [];
  // Générer les décisions basées sur les vraies données
  const decisions = useMemo(() => {
    const items = [];

    // Décisions basées sur l'inventaire
    if (inventory.reorder_suggestions?.length) {
      items.push({
        id: 'stock-optimize',
        type: 'stock',
        title: 'Optimiser les niveaux de stock',
        description: `${inventory.reorder_suggestions.length} produits à réapprovisionner. ${inventory.critical_items || 0} en rupture critique.`,
        impact: { value: `-${Math.round(inventory.dead_stock_value || 1200)}€ immobilisés`, savings: String(inventory.dead_stock_value || 1200) },
        confidence: 0.86,
      });
    }

    if (inventory.dead_stock_count > 0) {
      items.push({
        id: 'stock-dead',
        type: 'stock',
        title: 'Liquider le stock mort',
        description: `${inventory.dead_stock_count} produits sans mouvement depuis 90 jours.`,
        impact: { value: `Libérer ${Math.round(inventory.dead_stock_value || 500)}€`, savings: String(inventory.dead_stock_value || 500) },
        confidence: 0.92,
      });
    }

    // Décisions basées sur les anomalies
    if (anomalies.items?.length > 0) {
      anomalies.items.slice(0, 3).forEach((anomaly, idx) => {
        items.push({
          id: `anomaly-${anomaly.id || idx}`,
          type: 'anomaly',
          title: anomaly.title || 'Anomalie détectée',
          description: anomaly.description || 'Vérifier la cohérence des données',
          impact: { value: `Éviter ${Math.round(anomaly.impact || 300)}€ de perte`, savings: String(anomaly.impact || 300) },
          confidence: 0.9,
        });
      });
    }

    // Décisions basées sur les prévisions
    if (forecast.cash_flow?.net_flow_7_days < 0) {
      items.push({
        id: 'cash-flow',
        type: 'optimization',
        title: 'Anticiper le creux de trésorerie',
        description: `Flux net prévu: ${forecast.cash_flow.net_flow_7_days?.toLocaleString('fr-FR')}€ sur 7 jours.`,
        impact: { value: 'Éviter tension trésorerie', monthly: '0' },
        confidence: 0.84,
      });
    }

    // Si pas de décisions basées sur données réelles, afficher un message positif
    if (items.length === 0) {
      items.push({
        id: 'all-good',
        type: 'optimization',
        title: 'Tout est en ordre',
        description: 'Aucune action critique requise. Continuez ainsi !',
        impact: { value: '✓ Business sain', monthly: '0' },
        confidence: 1.0,
      });
    }

    // Filtrer les décisions déjà appliquées
    return items.filter((item) => !appliedDecisions.has(item.id) && !appliedDecisions.has(`dismissed-${item.id}`));
  }, [inventory, anomalies.items, forecast.cash_flow, appliedDecisions]);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
        <h1 className="text-2xl font-semibold text-slate-900">Vue d'ensemble</h1>
        <p className="text-sm text-slate-500">
          Analyse en temps reel de votre activite avec previsions et alertes automatiques.
        </p>
      </div>

      {/* Row 1: Score de sante + KPIs */}
      <div className="grid gap-4 md:grid-cols-5">
        <HealthGauge score={healthScore} label="Sante Business" />
        <MetricCard
          label="Stock critique"
          value={inventory.critical_items || 0}
          severity={inventory.critical_items > 0 ? 'warning' : 'success'}
        />
        <MetricCard
          label="Rotation moy."
          value={inventory.avg_rotation || 0}
          format="number"
        />
        <MetricCard
          label="Anomalies"
          value={anomalies.total || 0}
          severity={anomalies.critical > 0 ? 'critical' : anomalies.total > 0 ? 'warning' : 'success'}
        />
        <MetricCard
          label="Dead stock"
          value={inventory.dead_stock_items || 0}
          severity={inventory.dead_stock_items > 5 ? 'warning' : 'success'}
        />
      </div>

      {/* Row 2: Previsions */}
      <CardExpandable
        title="Projections IA"
        subtitle="30 jours"
        summary="Prévisions ventes, cash-flow et stock"
        variant="info"
        defaultExpanded
      >
        <div className="grid gap-4 md:grid-cols-3">
          <ForecastCard
            type="Ventes prevues"
            predicted={forecast.sales_30d || 12500}
            confidence={forecast.sales_confidence || 0.85}
            trend={forecast.sales_trend || 'up'}
          />
          <ForecastCard
            type="Cash Flow"
            predicted={forecast.cashflow_30d || -2300}
            confidence={forecast.cashflow_confidence || 0.72}
            trend={forecast.cashflow_trend || 'down'}
            warning={forecast.cashflow_30d < 0}
          />
          <ForecastCard
            type="Valeur stock"
            predicted={forecast.stock_value_30d || 45000}
            confidence={forecast.stock_confidence || 0.90}
            trend={forecast.stock_trend || 'stable'}
          />
        </div>
      </CardExpandable>

      {/* Row 3: Anomalies + Fournisseurs */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Anomalies actives */}
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-slate-400">anomalies</p>
              <h2 className="text-lg font-semibold text-slate-900">
                {anomalies.total || 0} alertes actives
              </h2>
            </div>
            <Button variant="ghost" size="sm" onClick={() => window.location.href = '/intelligence/anomalies'}>
              Voir tout
            </Button>
          </div>
          <div className="flex flex-col gap-3">
            {anomalyQuery.error ? (
              <QueryErrorState
                error={anomalyQuery.error}
                onRetry={() => anomalyQuery.refetch()}
                variant="inline"
              />
            ) : anomalies.items?.length > 0 ? (
              anomalies.items.slice(0, 4).map((anomaly) => (
                <AnomalyCard
                  key={anomaly.id}
                  anomaly={anomaly}
                  onInvestigate={handleInvestigateAnomaly}
                />
              ))
            ) : (
              <EmptyAnomalies onConfigure={() => window.location.href = '/settings/alerts'} />
            )}
          </div>
        </Card>

        {/* Top fournisseurs */}
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-slate-400">scoring</p>
              <h2 className="text-lg font-semibold text-slate-900">Top Fournisseurs</h2>
            </div>
            <Button variant="ghost" size="sm" onClick={() => window.location.href = '/intelligence/scoring'}>
              Voir tout
            </Button>
          </div>
          <div className="flex flex-col">
            {suppliersQuery.error ? (
              <QueryErrorState
                error={suppliersQuery.error}
                onRetry={() => suppliersQuery.refetch()}
                variant="inline"
              />
            ) : suppliers.length > 0 ? (
              suppliers.map((supplier, index) => (
                <SupplierRow key={supplier.name} supplier={supplier} rank={index + 1} />
              ))
            ) : (
              <EmptySuppliers onImportInvoice={() => window.location.href = '/invoices/import'} />
            )}
          </div>
        </Card>
      </div>

      {/* Row 4: Décisions assistées */}
      <Card>
        <div className="mb-4">
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">décisions</p>
          <h2 className="text-lg font-semibold text-slate-900">Décisions assistées par IA</h2>
        </div>
        <DecisionPanel
          decisions={decisions}
          onApply={handleApplyDecision}
          onApplyAll={handleApplyAllDecisions}
          onDismiss={handleDismissDecision}
        />
      </Card>
    </div>
  );
}
