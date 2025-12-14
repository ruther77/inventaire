/**
 * ScoringPage - Scoring et analyse des fournisseurs (Version améliorée 2025)
 *
 * Permet de visualiser et comparer les performances fournisseurs:
 * - Score global et par dimension
 * - Historique des scores avec graphique
 * - Comparaison multi-fournisseurs
 * - Alertes et recommandations
 * - Export des données
 */

import { useState } from 'react';
import { RefreshCw, Filter, Download, Award, TrendingUp } from 'lucide-react';
import { useSuppliersRanking } from '../../hooks/useSupplierScoring.js';
import Card, { CardHeader, CardContent } from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Badge from '../../components/ui/Badge.jsx';
import { Skeleton } from '../../components/ui/Skeleton.jsx';
import {
  SupplierScoringTable,
  SupplierDetailModal,
  ScoringCriteriaPanel,
  SupplierAlertsWidget,
} from './components/index.js';

export default function ScoringPage() {
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [filters, setFilters] = useState({
    minScore: null,
    maxScore: null,
    category: null,
  });

  // Queries
  const rankingQuery = useSuppliersRanking({ limit: 50 });

  const isLoading = rankingQuery.isLoading;
  const suppliers = rankingQuery.data || [];

  // Filtrer les fournisseurs
  const filteredSuppliers = suppliers.filter((supplier) => {
    const score = (supplier.overall_score || 0) * 100;
    if (filters.minScore !== null && score < filters.minScore) return false;
    if (filters.maxScore !== null && score > filters.maxScore) return false;
    if (filters.category && supplier.category !== filters.category) return false;
    return true;
  });

  // Calculer les statistiques
  const stats = {
    total: suppliers.length,
    excellent: suppliers.filter((s) => (s.overall_score || 0) * 100 >= 75).length,
    medium: suppliers.filter(
      (s) => (s.overall_score || 0) * 100 >= 50 && (s.overall_score || 0) * 100 < 75
    ).length,
    poor: suppliers.filter((s) => (s.overall_score || 0) * 100 < 50).length,
    improving: suppliers.filter((s) => s.trend === 'improving').length,
    declining: suppliers.filter((s) => s.trend === 'declining').length,
  };

  const handleSupplierClick = (supplier) => {
    setSelectedSupplier(supplier);
    setShowDetailModal(true);
  };

  const handleRefresh = () => {
    rankingQuery.refetch();
  };

  const handleExportAll = () => {
    const csvContent = [
      [
        'Fournisseur',
        'Score Global',
        'Tendance',
        'Stabilité Prix',
        'Fiabilité Livraison',
        'Précision Factures',
        'Qualité',
        'Conditions Paiement',
        'Factures Analysées',
        'Dernière MAJ',
      ],
      ...suppliers.map((s) => [
        s.name,
        Math.round((s.overall_score || 0) * 100),
        s.trend || 'stable',
        Math.round((s.price_stability_score || 0) * 100),
        Math.round((s.delivery_reliability_score || 0) * 100),
        Math.round((s.invoice_accuracy_score || 0) * 100),
        Math.round((s.quality_score || 0) * 100),
        Math.round((s.payment_terms_score || 0) * 100),
        s.data_points || 0,
        s.last_calculated || 'N/A',
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute(
      'download',
      `supplier-scoring-complet-${new Date().toISOString().split('T')[0]}.csv`
    );
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
          <h1 className="text-2xl font-semibold text-white">Scoring Fournisseurs</h1>
          <p className="text-sm text-slate-400">
            Évaluez et comparez la performance de vos fournisseurs sur 5 dimensions clés
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            loading={rankingQuery.isFetching}
            iconOnly
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={handleExportAll}>
            <Download className="h-4 w-4" />
            Exporter tout
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-6">
          <Card padding="md" variant="ghost">
            <div className="flex flex-col items-center text-center">
              <div className="p-2 rounded-lg bg-blue-500/20 mb-2">
                <Award className="h-5 w-5 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-xs text-slate-400">Fournisseurs</p>
            </div>
          </Card>

          <Card padding="md" variant="ghost">
            <div className="flex flex-col items-center text-center">
              <div className="p-2 rounded-lg bg-emerald-500/20 mb-2">
                <div className="h-5 w-5 rounded-full bg-emerald-500" />
              </div>
              <p className="text-2xl font-bold text-emerald-400">{stats.excellent}</p>
              <p className="text-xs text-slate-400">Excellents</p>
            </div>
          </Card>

          <Card padding="md" variant="ghost">
            <div className="flex flex-col items-center text-center">
              <div className="p-2 rounded-lg bg-amber-500/20 mb-2">
                <div className="h-5 w-5 rounded-full bg-amber-500" />
              </div>
              <p className="text-2xl font-bold text-amber-400">{stats.medium}</p>
              <p className="text-xs text-slate-400">Moyens</p>
            </div>
          </Card>

          <Card padding="md" variant="ghost">
            <div className="flex flex-col items-center text-center">
              <div className="p-2 rounded-lg bg-rose-500/20 mb-2">
                <div className="h-5 w-5 rounded-full bg-rose-500" />
              </div>
              <p className="text-2xl font-bold text-rose-400">{stats.poor}</p>
              <p className="text-xs text-slate-400">Faibles</p>
            </div>
          </Card>

          <Card padding="md" variant="ghost">
            <div className="flex flex-col items-center text-center">
              <div className="p-2 rounded-lg bg-emerald-500/20 mb-2">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-emerald-400">{stats.improving}</p>
              <p className="text-xs text-slate-400">En hausse</p>
            </div>
          </Card>

          <Card padding="md" variant="ghost">
            <div className="flex flex-col items-center text-center">
              <div className="p-2 rounded-lg bg-rose-500/20 mb-2">
                <TrendingUp className="h-5 w-5 text-rose-400 rotate-180" />
              </div>
              <p className="text-2xl font-bold text-rose-400">{stats.declining}</p>
              <p className="text-xs text-slate-400">En baisse</p>
            </div>
          </Card>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Alerts Widget (left column) */}
        <div className="lg:col-span-1">
          <SupplierAlertsWidget
            suppliers={suppliers}
            onSupplierClick={handleSupplierClick}
          />
        </div>

        {/* Main Table (right column) */}
        <div className="lg:col-span-2">
          <Card padding="lg">
            <CardHeader
              title="Classement des Fournisseurs"
              description={`${filteredSuppliers.length} fournisseur${filteredSuppliers.length > 1 ? 's' : ''} analysé${filteredSuppliers.length > 1 ? 's' : ''}`}
            />
            <CardContent>
              <SupplierScoringTable
                suppliers={filteredSuppliers}
                loading={isLoading}
                onSupplierClick={handleSupplierClick}
                selectedSupplierId={selectedSupplier?.name}
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Methodology Panel */}
      <ScoringCriteriaPanel />

      {/* Detail Modal */}
      <SupplierDetailModal
        supplier={selectedSupplier}
        open={showDetailModal}
        onClose={() => {
          setShowDetailModal(false);
          setSelectedSupplier(null);
        }}
      />
    </div>
  );
}
