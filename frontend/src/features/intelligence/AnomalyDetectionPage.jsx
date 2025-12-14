import React, { useState } from 'react';
import { AlertTriangle, Search, TrendingUp, Receipt, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useAnomalyDetection } from '../../hooks/useAnomalyDetection.js';

const Stat = ({ label, value, hint, icon: Icon, accent = 'text-slate-900', bgColor = 'bg-white', borderColor = 'border-slate-200' }) => (
  <div className={`rounded-2xl border ${borderColor} ${bgColor} p-4 transition-all hover:shadow-md`}>
    <div className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-[0.3em]">
      {Icon && <Icon className="w-4 h-4" />} {label}
    </div>
    <p className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
  </div>
);

const TabButton = ({ active, onClick, children, icon: Icon }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
      active ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
    }`}
  >
    {Icon && <Icon className="w-4 h-4" />}
    {children}
  </button>
);

export default function AnomalyDetectionPage() {
  const [activeTab, setActiveTab] = useState('summary');
  const [scanResults, setScanResults] = useState(null);
  const [threshold, setThreshold] = useState(3);

  const {
    summary,
    outliers,
    duplicates,
    roundAmounts,
    isLoading,
    scan,
    refetchAll,
  } = useAnomalyDetection({ daysBack: 90 });

  // Extract data from queries
  const data = {
    summary: summary.data || {},
    outliers: outliers.data || [],
    duplicates: duplicates.data || [],
    roundAmounts: roundAmounts.data || [],
  };
  const loading = isLoading;

  const runScan = () => {
    scan.mutate({}, {
      onSuccess: (result) => {
        setScanResults(result);
      },
    });
  };


  const renderSummaryTab = () => (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Anomalies Totales" value={data.summary?.total_anomalies || 0} hint="Detectees ce mois" icon={AlertTriangle} accent="text-rose-600" bgColor="bg-rose-50" borderColor="border-rose-200" />
        <Stat label="Critiques" value={data.summary?.critical_count || 0} hint="Action immediate" icon={XCircle} accent="text-rose-600" bgColor="bg-rose-50" borderColor="border-rose-200" />
        <Stat label="En Attente" value={data.summary?.pending_count || 0} hint="A examiner" icon={AlertTriangle} accent="text-amber-600" bgColor="bg-amber-50" borderColor="border-amber-200" />
        <Stat label="Resolues" value={data.summary?.resolved_count || 0} hint="Ce mois" icon={CheckCircle} accent="text-emerald-600" bgColor="bg-emerald-50" borderColor="border-emerald-200" />
      </div>

      {data.summary?.by_type && (
        <Card className="p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Repartition</p>
            <h3 className="text-lg font-semibold text-slate-900">Par Type</h3>
          </div>
          <div className="grid gap-3 md:grid-cols-4">
            {Object.entries(data.summary.by_type).map(([type, count]) => (
              <div key={type} className="rounded-xl border border-slate-200 p-4 text-center">
                <p className="text-2xl font-bold text-slate-900">{count}</p>
                <p className="text-sm text-slate-500">{type.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {data.summary?.recent_anomalies?.length > 0 && (
        <Card className="p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Recentes</p>
            <h3 className="text-lg font-semibold text-slate-900">Anomalies Recentes</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Description</th>
                  <th className="px-3 py-2">Severite</th>
                  <th className="px-3 py-2">Statut</th>
                </tr>
              </thead>
              <tbody>
                {data.summary.recent_anomalies.map((anomaly, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-2">{new Date(anomaly.detected_at).toLocaleDateString('fr-FR')}</td>
                    <td className="px-3 py-2"><span className="px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-xs">{anomaly.type}</span></td>
                    <td className="px-3 py-2 text-slate-900">{anomaly.description}</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        anomaly.severity === 'critical' ? 'bg-rose-100 text-rose-700' :
                        anomaly.severity === 'high' ? 'bg-amber-100 text-amber-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {anomaly.severity}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${anomaly.status === 'resolved' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                        {anomaly.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );

  const renderScanTab = () => (
    <div className="space-y-6">
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Scanner les Anomalies</h3>
            <p className="text-sm text-slate-500">Lancez un scan complet pour detecter les anomalies financieres</p>
          </div>
          <Button onClick={runScan} disabled={scan.isPending}>
            {scan.isPending ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
            {scan.isPending ? 'Scan en cours...' : 'Lancer le Scan'}
          </Button>
        </div>
        {scan.isPending && <div className="mt-4 h-2 bg-slate-200 rounded-full overflow-hidden"><div className="h-full bg-emerald-500 animate-pulse" style={{ width: '60%' }}></div></div>}
      </Card>

      {scanResults && (
        <Card className="p-4">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Resultats</p>
            <h3 className="text-lg font-semibold text-slate-900">{scanResults.total_found || 0} anomalies detectees</h3>
          </div>
          {scanResults.anomalies?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-200">
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Description</th>
                    <th className="px-3 py-2 text-right">Montant</th>
                    <th className="px-3 py-2">Severite</th>
                    <th className="px-3 py-2 text-right">Confiance</th>
                  </tr>
                </thead>
                <tbody>
                  {scanResults.anomalies.map((anomaly, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-3 py-2"><span className="px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-xs">{anomaly.type}</span></td>
                      <td className="px-3 py-2 text-slate-900">{anomaly.description}</td>
                      <td className="px-3 py-2 text-right">{anomaly.amount ? `${anomaly.amount.toFixed(2)} EUR` : '-'}</td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          anomaly.severity === 'critical' ? 'bg-rose-100 text-rose-700' :
                          anomaly.severity === 'high' ? 'bg-amber-100 text-amber-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          {anomaly.severity}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right">{((anomaly.confidence || 0) * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-emerald-600">
              <CheckCircle className="w-12 h-12 mx-auto mb-2" />
              <p className="font-semibold">Aucune anomalie detectee !</p>
            </div>
          )}
        </Card>
      )}
    </div>
  );

  const renderOutliersTab = () => (
    <Card className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Transactions</p>
          <h3 className="text-lg font-semibold text-slate-900">Valeurs Aberrantes</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">Seuil Z-Score:</span>
          <input type="number" value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} className="w-20 rounded-lg border border-slate-200 px-2 py-1 text-sm" step="0.5" min="1" max="5" />
        </div>
      </div>
      {data.outliers.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2 text-right">Montant</th>
                <th className="px-3 py-2 text-right">Z-Score</th>
              </tr>
            </thead>
            <tbody>
              {data.outliers.map((item, idx) => (
                <tr key={idx} className={`border-b border-slate-100 hover:bg-slate-50 ${item.z_score > 4 ? 'bg-rose-50' : ''}`}>
                  <td className="px-3 py-2">{new Date(item.date).toLocaleDateString('fr-FR')}</td>
                  <td className="px-3 py-2 text-slate-900">{item.description}</td>
                  <td className="px-3 py-2 text-right font-semibold">{item.amount?.toFixed(2)} EUR</td>
                  <td className="px-3 py-2 text-right">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.z_score > 4 ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>
                      {item.z_score?.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-emerald-600">
          <CheckCircle className="w-12 h-12 mx-auto mb-2" />
          <p>Aucune transaction aberrante detectee</p>
        </div>
      )}
    </Card>
  );

  const renderDuplicatesTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Factures</p>
        <h3 className="text-lg font-semibold text-slate-900">Doublons Potentiels</h3>
      </div>
      {data.duplicates.length > 0 ? (
        <div className="space-y-4">
          {data.duplicates.map((group, idx) => (
            <div key={idx} className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm font-semibold text-amber-800 mb-2">Groupe #{idx + 1} - Similarite: {(group.similarity * 100).toFixed(0)}%</p>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="px-3 py-2">N Facture</th>
                      <th className="px-3 py-2">Fournisseur</th>
                      <th className="px-3 py-2">Date</th>
                      <th className="px-3 py-2 text-right">Montant</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.invoices?.map((inv, i) => (
                      <tr key={i} className="border-t border-amber-200">
                        <td className="px-3 py-2">{inv.invoice_number}</td>
                        <td className="px-3 py-2">{inv.vendor}</td>
                        <td className="px-3 py-2">{new Date(inv.date).toLocaleDateString('fr-FR')}</td>
                        <td className="px-3 py-2 text-right font-semibold">{inv.total?.toFixed(2)} EUR</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-emerald-600">
          <CheckCircle className="w-12 h-12 mx-auto mb-2" />
          <p>Aucun doublon de facture detecte</p>
        </div>
      )}
    </Card>
  );

  const renderRoundAmountsTab = () => (
    <Card className="p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Transactions</p>
        <h3 className="text-lg font-semibold text-slate-900">Montants Ronds Suspects</h3>
        <p className="text-sm text-slate-500">Les montants ronds peuvent indiquer des estimations ou des fraudes</p>
      </div>
      {data.roundAmounts.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2 text-right">Montant</th>
                <th className="px-3 py-2">Categorie</th>
                <th className="px-3 py-2">Risque</th>
              </tr>
            </thead>
            <tbody>
              {data.roundAmounts.map((item, idx) => (
                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2">{new Date(item.date).toLocaleDateString('fr-FR')}</td>
                  <td className="px-3 py-2 text-slate-900">{item.description}</td>
                  <td className="px-3 py-2 text-right font-semibold text-amber-600">{item.amount?.toFixed(2)} EUR</td>
                  <td className="px-3 py-2">{item.category || '-'}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.risk_level === 'high' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>
                      {item.risk_level || 'medium'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-emerald-600">
          <CheckCircle className="w-12 h-12 mx-auto mb-2" />
          <p>Aucune transaction suspecte detectee</p>
        </div>
      )}
    </Card>
  );

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Intelligence</p>
          <h1 className="text-2xl font-semibold text-slate-900">Detection d'Anomalies</h1>
        </div>
        <Button variant="ghost" onClick={refetchAll} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Rafraichir
        </Button>
      </header>

      <div className="flex flex-wrap gap-2">
        <TabButton active={activeTab === 'summary'} onClick={() => setActiveTab('summary')} icon={AlertTriangle}>Resume</TabButton>
        <TabButton active={activeTab === 'scan'} onClick={() => setActiveTab('scan')} icon={Search}>Scanner</TabButton>
        <TabButton active={activeTab === 'outliers'} onClick={() => setActiveTab('outliers')} icon={TrendingUp}>Outliers</TabButton>
        <TabButton active={activeTab === 'duplicates'} onClick={() => setActiveTab('duplicates')} icon={Receipt}>Doublons</TabButton>
        <TabButton active={activeTab === 'round'} onClick={() => setActiveTab('round')} icon={AlertTriangle}>Montants Ronds</TabButton>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center text-slate-500">
            <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
            <p>Chargement...</p>
          </div>
        </div>
      ) : (
        <>
          {activeTab === 'summary' && renderSummaryTab()}
          {activeTab === 'scan' && renderScanTab()}
          {activeTab === 'outliers' && renderOutliersTab()}
          {activeTab === 'duplicates' && renderDuplicatesTab()}
          {activeTab === 'round' && renderRoundAmountsTab()}
        </>
      )}
    </div>
  );
}
