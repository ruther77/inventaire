import React, { useMemo, useState } from 'react';
import { TrendingUp, Wallet, ArrowDownCircle, ArrowUpCircle, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { useFinanceMatches, useFinanceAnomalies } from '../../hooks/useFinance.js';
import {
  useFinanceCategories,
  useFinanceRules,
  useFinanceCategoryStats,
  useFinanceAccountsOverviewStats,
  useFinanceTimeline,
  useFinanceTreasury,
} from '../../hooks/useFinanceCategories.js';
import { roundAmount } from '../../utils/banking.js';
import { DashboardSkeleton } from '../../components/ui/Skeleton.jsx';
import QueryErrorState from '../../components/feedback/QueryErrorState.jsx';

const Stat = ({ label, value, hint, icon: Icon, accent = 'text-white', bgColor = 'bg-white/5', borderColor = 'border-white/10' }) => (
  <div className={`rounded-2xl border ${borderColor} ${bgColor} p-4 transition-all hover:border-white/20`}>
    <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-[0.3em]">
      {Icon && <Icon className="w-4 h-4" />} {label}
    </div>
    <p className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
  </div>
);

export default function FinanceOverview() {
  const [months, setMonths] = useState(12);

  // Hooks optimisés - agrégation côté serveur (beaucoup plus rapide)
  const catQuery = useFinanceCategories({});
  const rulesQuery = useFinanceRules({});
  const catStats = useFinanceCategoryStats({});
  const accountsStats = useFinanceAccountsOverviewStats({});
  const matchesQuery = useFinanceMatches({ status: 'pending' });
  const anomaliesQuery = useFinanceAnomalies({});

  // Nouveaux hooks optimisés pour les graphiques - date filters passed to backend
  const timelineQuery = useFinanceTimeline({
    months: months === 'all' ? null : months,
    granularity: 'monthly',
  });
  const treasuryQuery = useFinanceTreasury({
    months: months === 'all' ? null : months,
  });

  // Données extraites des requêtes
  const rules = Array.isArray(rulesQuery.data) ? rulesQuery.data : [];
  const categories = Array.isArray(catQuery.data) ? catQuery.data : [];
  const catStatsData = Array.isArray(catStats.data) ? catStats.data : [];
  const accounts = Array.isArray(accountsStats.data) ? accountsStats.data : [];
  const pendingMatches = Array.isArray(matchesQuery.data) ? matchesQuery.data : [];
  const anomalies = Array.isArray(anomaliesQuery.data) ? anomaliesQuery.data : [];
  const treasury = treasuryQuery.data ?? {};

  // Timeline depuis l'API (déjà agrégée côté serveur)
  const treasuryTimeline = useMemo(() => {
    const data = Array.isArray(timelineQuery.data) ? timelineQuery.data : [];
    return data.map((item) => ({
      month: item.period,
      balance: item.cumulative_balance,
      inflow: item.inflow,
      outflow: item.outflow,
      net: item.net,
    }));
  }, [timelineQuery.data]);

  // Totaux depuis l'API treasury
  const totals = useMemo(() => ({
    entrees: treasury.total_inflow || 0,
    sorties: treasury.total_outflow || 0,
    net: treasury.net_balance || 0,
  }), [treasury]);

  const categoryById = useMemo(() => {
    const map = new Map();
    categories.forEach((c) => map.set(c.id, c));
    return map;
  }, [categories]);

  const hasError = treasuryQuery.isError && !treasuryQuery.data;

  if (hasError) {
    return (
      <QueryErrorState
        error={treasuryQuery.error}
        onRetry={() => treasuryQuery.refetch()}
        variant="full"
      />
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Finance overview</p>
          <h1 className="text-2xl font-semibold text-orange-400">Trésorerie & catégorisation</h1>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={months}
            onChange={(e) => setMonths(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
          >
            <option value="all">Tout l'historique</option>
            {[3, 6, 12, 24, 36].map((m) => (
              <option key={m} value={m}>
                {m} mois
              </option>
            ))}
          </select>
          <Button variant="ghost" onClick={() => {
            timelineQuery.refetch();
            treasuryQuery.refetch();
            catStats.refetch();
            accountsStats.refetch();
          }}>
            Rafraîchir
          </Button>
        </div>
      </header>

      {/* Enhanced KPIs Section */}
      <div className="grid gap-3 md:grid-cols-4">
        <Stat
          label="Cash-in"
          value={`${roundAmount(totals.entrees)} €`}
          hint="Total entrées"
          icon={ArrowDownCircle}
          accent="text-emerald-400"
          bgColor="bg-emerald-500/10"
          borderColor="border-emerald-500/30"
        />
        <Stat
          label="Cash-out"
          value={`${roundAmount(totals.sorties)} €`}
          hint="Total sorties"
          icon={ArrowUpCircle}
          accent="text-rose-400"
          bgColor="bg-rose-500/10"
          borderColor="border-rose-500/30"
        />
        <Stat
          label="Net"
          value={`${roundAmount(totals.net)} €`}
          hint="Solde de la période"
          icon={Wallet}
          accent={totals.net >= 0 ? 'text-emerald-400' : 'text-rose-400'}
          bgColor={totals.net >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10'}
          borderColor={totals.net >= 0 ? 'border-emerald-500/30' : 'border-rose-500/30'}
        />
        <Stat
          label="Alertes"
          value={`${anomalies.length} / ${pendingMatches.length}`}
          hint="Anomalies / Reco en attente"
          icon={Activity}
          accent={anomalies.length > 0 ? 'text-rose-400' : 'text-emerald-400'}
          bgColor={anomalies.length > 0 ? 'bg-rose-500/10' : 'bg-white/5'}
          borderColor={anomalies.length > 0 ? 'border-rose-500/30' : 'border-white/10'}
        />
      </div>

      {/* Account Balances KPIs */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Soldes par compte</p>
            <h3 className="text-lg font-semibold text-amber-400">Vue d'ensemble des comptes</h3>
          </div>
          <Button variant="ghost" onClick={() => accountsStats.refetch()}>
            Rafraîchir
          </Button>
        </div>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((acc) => (
            <div key={acc.id} className="rounded-xl border border-white/10 bg-white/5 p-4 hover:border-white/20 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-white">{acc.label}</p>
                <Wallet className={`w-5 h-5 ${acc.balance >= 0 ? 'text-emerald-400' : 'text-rose-400'}`} />
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-slate-300">
                  <span className="flex items-center gap-1">
                    <ArrowDownCircle className="w-3 h-3 text-emerald-400" />
                    Entrées
                  </span>
                  <span className="font-semibold text-emerald-400">{roundAmount(acc.inflow)} €</span>
                </div>
                <div className="flex justify-between text-xs text-slate-300">
                  <span className="flex items-center gap-1">
                    <ArrowUpCircle className="w-3 h-3 text-rose-400" />
                    Sorties
                  </span>
                  <span className="font-semibold text-rose-400">{roundAmount(acc.outflow)} €</span>
                </div>
                <div className="h-px bg-white/10 my-2"></div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-semibold text-slate-400">Solde</span>
                  <span className={`text-lg font-bold ${acc.balance >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {roundAmount(acc.balance)} €
                  </span>
                </div>
              </div>
            </div>
          ))}
          {accounts.length === 0 && (
            <div className="col-span-full text-center py-8 text-slate-400">
              <Wallet className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <p>Aucun compte disponible</p>
            </div>
          )}
        </div>
      </Card>

      {/* Treasury Chart */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Évolution</p>
            <h3 className="text-lg font-semibold text-amber-400">Trésorerie cumulée</h3>
          </div>
          <div className="text-xs text-slate-500">
            {treasuryTimeline.length > 0 && (
              <span>
                {treasuryTimeline[0]?.month} → {treasuryTimeline[treasuryTimeline.length - 1]?.month}
              </span>
            )}
          </div>
        </div>
        {treasuryTimeline.length > 0 ? (
          <div className="h-64" key={`treasury-chart-${months}`}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={treasuryTimeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  stroke="#64748b"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#64748b"
                  tickFormatter={(value) => `${roundAmount(value)}€`}
                />
                <Tooltip
                  formatter={(value) => [`${roundAmount(value)} €`, 'Solde cumulé']}
                  labelFormatter={(label) => `Mois: ${label}`}
                  contentStyle={{
                    backgroundColor: '#1a1a24',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#fff'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="balance"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <p>Aucune donnée de trésorerie disponible</p>
            </div>
          </div>
        )}
      </Card>

      {/* Alerts Summary */}
      <Card className={`p-4 ${anomalies.length > 0 ? 'border-amber-500/30 bg-amber-500/10' : ''}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Alertes système</p>
            <h3 className="text-lg font-semibold text-white">
              {anomalies.length === 0 && '✓ Tout est OK'}
              {anomalies.length > 0 && `${anomalies.length} anomalie(s) détectée(s)`}
            </h3>
            {pendingMatches.length > 0 && (
              <p className="text-sm text-slate-300 mt-2">
                <span className="font-semibold text-amber-400">{pendingMatches.length}</span> rapprochement(s) en attente
              </p>
            )}
          </div>
          {anomalies.length > 0 && (
            <div className="rounded-xl bg-rose-500/20 border border-rose-500/30 px-4 py-2 text-rose-400 text-sm font-semibold">
              <Activity className="w-4 h-4 inline mr-1" />
              {anomalies.length} anomalie{anomalies.length > 1 ? 's' : ''}
            </div>
          )}
        </div>
      </Card>

      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Catégories</p>
            <h3 className="text-lg font-semibold text-amber-400">Répartition par catégorie</h3>
          </div>
          <Button variant="ghost" onClick={() => catQuery.refetch()}>
            Rafraîchir
          </Button>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400">
                <th className="px-3 py-2">Catégorie</th>
                <th className="px-3 py-2 text-right">Entrées</th>
                <th className="px-3 py-2 text-right">Sorties</th>
                <th className="px-3 py-2 text-right">Lignes</th>
              </tr>
            </thead>
            <tbody>
              {catStatsData.map((cat) => (
                <tr key={cat.id || cat.code} className="border-t border-white/10">
                  <td className="px-3 py-2 font-semibold text-white">{cat.name || cat.code || 'Sans catégorie'}</td>
                  <td className="px-3 py-2 text-right text-emerald-400">{roundAmount(cat.inflow || 0)} €</td>
                  <td className="px-3 py-2 text-right text-rose-400">{roundAmount(cat.outflow || 0)} €</td>
                  <td className="px-3 py-2 text-right text-slate-300">{cat.lines || 0}</td>
                </tr>
              ))}
              {catStatsData.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-4 text-center text-slate-400">
                    Aucune catégorie
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Règles</p>
            <h3 className="text-lg font-semibold text-amber-400">Règles de catégorisation</h3>
            <p className="text-sm text-slate-400">Liste des règles actives et mots-clés associés.</p>
          </div>
          <Button variant="ghost" onClick={() => rulesQuery.refetch()}>
            Rafraîchir
          </Button>
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {rulesQuery.isLoading && <p className="text-sm text-slate-400">Chargement des règles...</p>}
          {rulesQuery.isError && (
            <p className="text-sm text-rose-400">
              Erreur: {rulesQuery.error?.message || 'Impossible de charger les règles'}
            </p>
          )}
          {rules.map((rule) => (
            <div key={rule.id} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
              <p className="text-sm font-semibold text-white">{rule.name}</p>
              <p className="text-xs text-slate-400">
                Catégorie: <span className="text-amber-400">{rule.category_name || categoryById.get(rule.category_id)?.name || rule.category_id}</span> · Active:{' '}
                <span className={rule.is_active ? 'text-emerald-400' : 'text-slate-500'}>{rule.is_active ? 'oui' : 'non'}</span>
              </p>
              <p className="text-xs text-slate-500 truncate">
                Mots-clés: {(rule.keywords || []).length ? (rule.keywords || []).join(', ') : '—'}
              </p>
            </div>
          ))}
          {!rulesQuery.isLoading && !rulesQuery.isError && rules.length === 0 && (
            <p className="text-sm text-slate-400">Aucune règle configurée</p>
          )}
        </div>
      </Card>
    </div>
  );
}
