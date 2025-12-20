# Supplier Scoring - Guide d'intégration Frontend

## Vue d'ensemble

Ce guide explique comment intégrer les endpoints Supplier Scoring dans le frontend React.

## Configuration de l'API Client

### 1. Ajouter les types TypeScript

```typescript
// src/types/supplierScoring.ts

export type Grade = 'A' | 'B' | 'C' | 'D' | 'F';
export type Trend = 'improving' | 'stable' | 'declining' | 'up' | 'down';
export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertType = 'score_drop' | 'delivery_issues' | 'quality_degradation' | 'price_spike';

export interface SupplierScore {
  supplier_id: number | null;
  supplier_name: string;
  overall_score: number;
  grade: Grade;
  delivery_score: number;
  quality_score: number;
  price_score: number;
  reliability_score: number;
  trend: Trend;
  last_updated: string;
  dimensions: Record<string, number>;
  metrics: Record<string, any>;
}

export interface SupplierOverview {
  total_suppliers: number;
  average_score: number;
  score_distribution: Record<Grade, number>;
  top_suppliers: SupplierScore[];
  bottom_suppliers: SupplierScore[];
  trends: Record<string, any>;
  alerts_summary: Record<string, number>;
}

export interface SupplierRankingItem {
  rank: number;
  supplier_id: number | null;
  supplier_name: string;
  score: number;
  grade: Grade;
  dimensions: Record<string, number>;
  last_updated: string | null;
  trend: Trend | null;
}

export interface SuppliersList {
  suppliers: SupplierRankingItem[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ScoreHistoryItem {
  date: string;
  score: number;
  grade: Grade;
  breakdown: Record<string, number>;
}

export interface ScoreHistory {
  supplier_id: number | null;
  supplier_name: string;
  history: ScoreHistoryItem[];
  trend_analysis: {
    direction: string;
    average_score?: number;
    recent_average?: number;
    variation?: number;
    note?: string;
  } | null;
}

export interface ScoringCriterion {
  criterion_id: string;
  name: string;
  weight: number;
  description: string;
  enabled: boolean;
}

export interface ScoringCriteriaList {
  criteria: ScoringCriterion[];
  total_weight: number;
}

export interface SupplierAlert {
  alert_id: string;
  supplier_id: number | null;
  supplier_name: string;
  alert_type: AlertType;
  message: string;
  severity: AlertSeverity;
  created_at: string;
  acknowledged: boolean;
  details?: Record<string, any>;
}

export interface AlertsList {
  alerts: SupplierAlert[];
  total_count: number;
  unacknowledged_count: number;
}

export interface SupplierDetails {
  supplier_id: number | null;
  supplier_name: string;
  current_score: SupplierScore;
  history: ScoreHistoryItem[];
  recent_deliveries: any[];
  recent_issues: any[];
  alerts: SupplierAlert[];
  statistics: Record<string, any>;
  recommendations: string[];
}
```

### 2. Créer les hooks React Query

```typescript
// src/hooks/useSupplierScoring.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type {
  SupplierOverview,
  SuppliersList,
  SupplierDetails,
  ScoreHistory,
  ScoringCriteriaList,
  AlertsList,
} from '@/types/supplierScoring';

// Keys pour React Query
export const supplierScoringKeys = {
  all: ['supplier-scoring'] as const,
  overview: () => [...supplierScoringKeys.all, 'overview'] as const,
  suppliers: (params?: any) => [...supplierScoringKeys.all, 'suppliers', params] as const,
  supplier: (id: number) => [...supplierScoringKeys.all, 'supplier', id] as const,
  history: (id: number, limit?: number) =>
    [...supplierScoringKeys.all, 'history', id, limit] as const,
  criteria: () => [...supplierScoringKeys.all, 'criteria'] as const,
  alerts: (params?: any) => [...supplierScoringKeys.all, 'alerts', params] as const,
};

// Hook: Vue d'ensemble
export function useSupplierOverview() {
  return useQuery({
    queryKey: supplierScoringKeys.overview(),
    queryFn: async () => {
      const response = await apiClient.get<SupplierOverview>(
        '/supplier-scoring/overview'
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Hook: Liste des fournisseurs
export function useSuppliersList(params?: {
  page?: number;
  per_page?: number;
  sort_by?: 'score' | 'name' | 'grade';
  order?: 'asc' | 'desc';
  min_score?: number;
  grade_filter?: string;
}) {
  return useQuery({
    queryKey: supplierScoringKeys.suppliers(params),
    queryFn: async () => {
      const response = await apiClient.get<SuppliersList>(
        '/supplier-scoring/suppliers',
        { params }
      );
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Hook: Détails d'un fournisseur
export function useSupplierDetails(supplierId: number) {
  return useQuery({
    queryKey: supplierScoringKeys.supplier(supplierId),
    queryFn: async () => {
      const response = await apiClient.get<SupplierDetails>(
        `/supplier-scoring/suppliers/${supplierId}`
      );
      return response.data;
    },
    enabled: !!supplierId,
  });
}

// Hook: Historique
export function useSupplierHistory(supplierId: number, limit: number = 20) {
  return useQuery({
    queryKey: supplierScoringKeys.history(supplierId, limit),
    queryFn: async () => {
      const response = await apiClient.get<ScoreHistory>(
        `/supplier-scoring/suppliers/${supplierId}/history`,
        { params: { limit } }
      );
      return response.data;
    },
    enabled: !!supplierId,
  });
}

// Hook: Critères de scoring
export function useScoringCriteria() {
  return useQuery({
    queryKey: supplierScoringKeys.criteria(),
    queryFn: async () => {
      const response = await apiClient.get<ScoringCriteriaList>(
        '/supplier-scoring/criteria'
      );
      return response.data;
    },
  });
}

// Hook: Mettre à jour les critères
export function useUpdateScoringCriteria() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (weights: Record<string, number>) => {
      const response = await apiClient.put<ScoringCriteriaList>(
        '/supplier-scoring/criteria',
        { weights }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: supplierScoringKeys.criteria() });
      queryClient.invalidateQueries({ queryKey: supplierScoringKeys.all });
    },
  });
}

// Hook: Alertes
export function useSupplierAlerts(params?: {
  severity?: string;
  acknowledged?: boolean;
  limit?: number;
}) {
  return useQuery({
    queryKey: supplierScoringKeys.alerts(params),
    queryFn: async () => {
      const response = await apiClient.get<AlertsList>(
        '/supplier-scoring/alerts',
        { params }
      );
      return response.data;
    },
    refetchInterval: 60 * 1000, // Rafraîchir toutes les minutes
  });
}

// Hook: Recalculer les scores
export function useRecalculateScores() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      supplier_names?: string[] | null;
      period_days?: number;
      force?: boolean;
    }) => {
      const response = await apiClient.post(
        '/supplier-scoring/recalculate',
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalider tous les caches liés aux scores
      queryClient.invalidateQueries({ queryKey: supplierScoringKeys.all });
    },
  });
}
```

## Composants React

### 1. Page Overview

```tsx
// src/features/supplierScoring/SupplierScoringOverview.tsx

import React from 'react';
import { useSupplierOverview } from '@/hooks/useSupplierScoring';
import { Card, MetricCard, Skeleton } from '@/components/ui';

export function SupplierScoringOverview() {
  const { data, isLoading, error } = useSupplierOverview();

  if (isLoading) {
    return <Skeleton count={4} />;
  }

  if (error) {
    return <div>Erreur lors du chargement: {error.message}</div>;
  }

  if (!data) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Métriques principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Fournisseurs"
          value={data.total_suppliers}
          icon="users"
        />
        <MetricCard
          title="Score moyen"
          value={data.average_score.toFixed(1)}
          suffix="/100"
          trend={data.trends.overall_trend}
        />
        <MetricCard
          title="En amélioration"
          value={data.trends.improving_count}
          icon="trending-up"
          variant="success"
        />
        <MetricCard
          title="En déclin"
          value={data.trends.declining_count}
          icon="trending-down"
          variant="warning"
        />
      </div>

      {/* Distribution des grades */}
      <Card title="Distribution des grades">
        <div className="flex gap-4">
          {Object.entries(data.score_distribution).map(([grade, count]) => (
            <div key={grade} className="flex-1 text-center">
              <div className={`text-3xl font-bold grade-${grade}`}>
                {grade}
              </div>
              <div className="text-sm text-gray-600">{count} fournisseurs</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Top et Bottom suppliers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Top 5 fournisseurs">
          <SupplierList suppliers={data.top_suppliers} />
        </Card>
        <Card title="À améliorer">
          <SupplierList suppliers={data.bottom_suppliers} />
        </Card>
      </div>

      {/* Alertes */}
      <Card title="Résumé des alertes">
        <AlertsSummary summary={data.alerts_summary} />
      </Card>
    </div>
  );
}
```

### 2. Liste des fournisseurs

```tsx
// src/features/supplierScoring/SuppliersListPage.tsx

import React, { useState } from 'react';
import { useSuppliersList } from '@/hooks/useSupplierScoring';
import { DataTable, Select, Input, Button } from '@/components/ui';

export function SuppliersListPage() {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [sortBy, setSortBy] = useState<'score' | 'name' | 'grade'>('score');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [minScore, setMinScore] = useState<number | undefined>();
  const [gradeFilter, setGradeFilter] = useState<string | undefined>();

  const { data, isLoading } = useSuppliersList({
    page,
    per_page: perPage,
    sort_by: sortBy,
    order,
    min_score: minScore,
    grade_filter: gradeFilter,
  });

  const columns = [
    { key: 'rank', label: 'Rang', sortable: false },
    { key: 'supplier_name', label: 'Fournisseur', sortable: true },
    { key: 'score', label: 'Score', sortable: true },
    { key: 'grade', label: 'Grade', sortable: true },
    { key: 'trend', label: 'Tendance', sortable: false },
    { key: 'last_updated', label: 'Mis à jour', sortable: false },
  ];

  return (
    <div className="space-y-6">
      {/* Filtres */}
      <div className="flex gap-4">
        <Input
          type="number"
          placeholder="Score min"
          value={minScore ?? ''}
          onChange={(e) => setMinScore(e.target.value ? Number(e.target.value) : undefined)}
        />
        <Select
          value={gradeFilter ?? ''}
          onChange={(e) => setGradeFilter(e.target.value || undefined)}
        >
          <option value="">Tous les grades</option>
          <option value="A">Grade A</option>
          <option value="B">Grade B</option>
          <option value="C">Grade C</option>
          <option value="D">Grade D</option>
          <option value="F">Grade F</option>
        </Select>
        <Button onClick={() => { setMinScore(undefined); setGradeFilter(undefined); }}>
          Réinitialiser
        </Button>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={data?.suppliers ?? []}
        loading={isLoading}
        pagination={{
          page,
          perPage,
          totalPages: data?.total_pages ?? 1,
          totalCount: data?.total_count ?? 0,
          onPageChange: setPage,
          onPerPageChange: setPerPage,
        }}
        onSort={(key) => {
          if (key === sortBy) {
            setOrder(order === 'asc' ? 'desc' : 'asc');
          } else {
            setSortBy(key as any);
            setOrder('desc');
          }
        }}
      />
    </div>
  );
}
```

### 3. Détails d'un fournisseur

```tsx
// src/features/supplierScoring/SupplierDetailsPage.tsx

import React from 'react';
import { useParams } from 'react-router-dom';
import { useSupplierDetails, useSupplierHistory } from '@/hooks/useSupplierScoring';
import { Card, Tabs, TabPanel } from '@/components/ui';
import { ScoreChart } from './components/ScoreChart';
import { RecommendationsList } from './components/RecommendationsList';

export function SupplierDetailsPage() {
  const { supplierId } = useParams<{ supplierId: string }>();
  const id = Number(supplierId);

  const { data: details, isLoading } = useSupplierDetails(id);
  const { data: history } = useSupplierHistory(id, 30);

  if (isLoading) {
    return <div>Chargement...</div>;
  }

  if (!details) {
    return <div>Fournisseur introuvable</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{details.supplier_name}</h1>
          <div className="flex items-center gap-4 mt-2">
            <span className={`text-4xl font-bold grade-${details.current_score.grade}`}>
              {details.current_score.grade}
            </span>
            <span className="text-2xl text-gray-600">
              {details.current_score.overall_score.toFixed(1)}/100
            </span>
            <TrendBadge trend={details.current_score.trend} />
          </div>
        </div>
      </div>

      {/* Scores par dimension */}
      <Card title="Scores par dimension">
        <DimensionScoresChart dimensions={details.current_score.dimensions} />
      </Card>

      {/* Tabs */}
      <Tabs>
        <TabPanel label="Historique">
          <ScoreChart data={history?.history ?? []} />
        </TabPanel>

        <TabPanel label="Livraisons">
          <DeliveriesList deliveries={details.recent_deliveries} />
        </TabPanel>

        <TabPanel label="Incidents">
          <IssuesList issues={details.recent_issues} />
        </TabPanel>

        <TabPanel label="Alertes">
          <AlertsList alerts={details.alerts} />
        </TabPanel>

        <TabPanel label="Statistiques">
          <StatisticsPanel statistics={details.statistics} />
        </TabPanel>
      </Tabs>

      {/* Recommandations */}
      {details.recommendations.length > 0 && (
        <Card title="Recommandations">
          <RecommendationsList recommendations={details.recommendations} />
        </Card>
      )}
    </div>
  );
}
```

### 4. Gestion des critères

```tsx
// src/features/supplierScoring/ScoringCriteriaPage.tsx

import React, { useState } from 'react';
import { useScoringCriteria, useUpdateScoringCriteria } from '@/hooks/useSupplierScoring';
import { Card, Button, Input, toast } from '@/components/ui';

export function ScoringCriteriaPage() {
  const { data, isLoading } = useScoringCriteria();
  const updateMutation = useUpdateScoringCriteria();

  const [weights, setWeights] = useState<Record<string, number>>({});

  React.useEffect(() => {
    if (data) {
      const initialWeights = Object.fromEntries(
        data.criteria.map(c => [c.criterion_id, c.weight])
      );
      setWeights(initialWeights);
    }
  }, [data]);

  const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0);

  const handleSave = async () => {
    if (Math.abs(totalWeight - 1.0) > 0.01) {
      toast.error('La somme des poids doit être égale à 1.0');
      return;
    }

    try {
      await updateMutation.mutateAsync(weights);
      toast.success('Critères mis à jour avec succès');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  if (isLoading) {
    return <div>Chargement...</div>;
  }

  return (
    <div className="space-y-6">
      <Card title="Critères de scoring">
        <div className="space-y-4">
          {data?.criteria.map((criterion) => (
            <div key={criterion.criterion_id} className="flex items-center gap-4">
              <div className="flex-1">
                <div className="font-medium">{criterion.name}</div>
                <div className="text-sm text-gray-600">{criterion.description}</div>
              </div>
              <Input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={weights[criterion.criterion_id] ?? 0}
                onChange={(e) => setWeights({
                  ...weights,
                  [criterion.criterion_id]: Number(e.target.value)
                })}
                className="w-24"
              />
              <span className="text-gray-600">
                ({(weights[criterion.criterion_id] * 100).toFixed(0)}%)
              </span>
            </div>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <div>
            <span className="font-medium">Total: </span>
            <span className={totalWeight === 1.0 ? 'text-green-600' : 'text-red-600'}>
              {totalWeight.toFixed(2)}
            </span>
          </div>
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending || Math.abs(totalWeight - 1.0) > 0.01}
          >
            Enregistrer
          </Button>
        </div>
      </Card>
    </div>
  );
}
```

### 5. Alertes

```tsx
// src/features/supplierScoring/AlertsPage.tsx

import React, { useState } from 'react';
import { useSupplierAlerts } from '@/hooks/useSupplierScoring';
import { Card, Badge, Button, Select } from '@/components/ui';

export function AlertsPage() {
  const [severity, setSeverity] = useState<string | undefined>();
  const [acknowledged, setAcknowledged] = useState<boolean | undefined>();

  const { data, isLoading } = useSupplierAlerts({
    severity,
    acknowledged,
    limit: 100,
  });

  return (
    <div className="space-y-6">
      {/* Filtres */}
      <div className="flex gap-4">
        <Select
          value={severity ?? ''}
          onChange={(e) => setSeverity(e.target.value || undefined)}
        >
          <option value="">Toutes les sévérités</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
        </Select>

        <Select
          value={acknowledged === undefined ? '' : acknowledged.toString()}
          onChange={(e) => {
            const val = e.target.value;
            setAcknowledged(val === '' ? undefined : val === 'true');
          }}
        >
          <option value="">Toutes les alertes</option>
          <option value="false">Non acquittées</option>
          <option value="true">Acquittées</option>
        </Select>
      </div>

      {/* Résumé */}
      <Card>
        <div className="flex gap-8">
          <div>
            <div className="text-3xl font-bold">{data?.total_count ?? 0}</div>
            <div className="text-sm text-gray-600">Alertes totales</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-orange-600">
              {data?.unacknowledged_count ?? 0}
            </div>
            <div className="text-sm text-gray-600">Non acquittées</div>
          </div>
        </div>
      </Card>

      {/* Liste des alertes */}
      <div className="space-y-3">
        {data?.alerts.map((alert) => (
          <Card key={alert.alert_id} className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant={alert.severity}>{alert.severity}</Badge>
                  <Badge variant="outline">{alert.alert_type}</Badge>
                  <span className="text-sm text-gray-600">
                    {alert.supplier_name}
                  </span>
                </div>
                <div className="text-gray-900">{alert.message}</div>
                <div className="text-sm text-gray-500 mt-1">
                  {new Date(alert.created_at).toLocaleString()}
                </div>
              </div>
              {!alert.acknowledged && (
                <Button size="sm" variant="outline">
                  Acquitter
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

## Routes

```tsx
// src/app/routes.tsx

import { SupplierScoringOverview } from '@/features/supplierScoring/SupplierScoringOverview';
import { SuppliersListPage } from '@/features/supplierScoring/SuppliersListPage';
import { SupplierDetailsPage } from '@/features/supplierScoring/SupplierDetailsPage';
import { ScoringCriteriaPage } from '@/features/supplierScoring/ScoringCriteriaPage';
import { AlertsPage } from '@/features/supplierScoring/AlertsPage';

export const routes = [
  // ... autres routes
  {
    path: '/supplier-scoring',
    element: <SupplierScoringOverview />,
  },
  {
    path: '/supplier-scoring/suppliers',
    element: <SuppliersListPage />,
  },
  {
    path: '/supplier-scoring/suppliers/:supplierId',
    element: <SupplierDetailsPage />,
  },
  {
    path: '/supplier-scoring/criteria',
    element: <ScoringCriteriaPage />,
  },
  {
    path: '/supplier-scoring/alerts',
    element: <AlertsPage />,
  },
];
```

## Navigation

```tsx
// src/app/SidebarNav.tsx

const menuItems = [
  // ... autres items
  {
    label: 'Supplier Scoring',
    icon: 'star',
    children: [
      { label: 'Vue d\'ensemble', path: '/supplier-scoring' },
      { label: 'Fournisseurs', path: '/supplier-scoring/suppliers' },
      { label: 'Critères', path: '/supplier-scoring/criteria' },
      { label: 'Alertes', path: '/supplier-scoring/alerts', badge: unacknowledgedCount },
    ],
  },
];
```

## Best Practices

### 1. Caching
- Utiliser React Query pour le cache automatique
- Invalider le cache après les mutations
- Configurer des `staleTime` appropriés

### 2. Performance
- Pagination côté serveur
- Lazy loading des graphiques
- Virtualisation pour les longues listes

### 3. UX
- Skeleton loaders pendant le chargement
- Messages d'erreur clairs
- Feedbacks visuels pour les actions
- Confirmations pour les actions destructives

### 4. Accessibilité
- Labels ARIA
- Navigation au clavier
- Contraste suffisant pour les grades

## Conclusion

Ce guide fournit une base solide pour intégrer les endpoints Supplier Scoring dans le frontend React. Les composants peuvent être adaptés selon le design system du projet.
