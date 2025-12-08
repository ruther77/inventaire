import React from 'react';
import { ArrowDownCircle, ArrowUpCircle, Wallet, Activity } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import { roundAmount } from '../../../utils/banking.js';

const Stat = ({ label, value, hint, icon: Icon, accent = 'text-slate-900', bgColor = 'bg-white', borderColor = 'border-slate-200' }) => (
  <div className={`rounded-2xl border ${borderColor} ${bgColor} p-4 transition-all hover:shadow-md`}>
    <div className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-[0.3em]">
      {Icon && <Icon className="w-4 h-4" />} {label}
    </div>
    <p className={`mt-1 text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
  </div>
);

export default function TreasurySummary({ treasury = {}, anomaliesCount = 0, pendingMatchesCount = 0 }) {
  const totalInflow = treasury.total_inflow || 0;
  const totalOutflow = treasury.total_outflow || 0;
  const netBalance = treasury.net_balance || 0;

  return (
    <div className="grid gap-3 md:grid-cols-4">
      <Stat
        label="Cash-in"
        value={`${roundAmount(totalInflow)} €`}
        hint="Total entrées"
        icon={ArrowDownCircle}
        accent="text-emerald-600"
        bgColor="bg-emerald-50"
        borderColor="border-emerald-200"
      />
      <Stat
        label="Cash-out"
        value={`${roundAmount(totalOutflow)} €`}
        hint="Total sorties"
        icon={ArrowUpCircle}
        accent="text-rose-600"
        bgColor="bg-rose-50"
        borderColor="border-rose-200"
      />
      <Stat
        label="Net"
        value={`${roundAmount(netBalance)} €`}
        hint="Solde de la période"
        icon={Wallet}
        accent={netBalance >= 0 ? 'text-emerald-700' : 'text-rose-700'}
        bgColor={netBalance >= 0 ? 'bg-emerald-50' : 'bg-rose-50'}
        borderColor={netBalance >= 0 ? 'border-emerald-200' : 'border-rose-200'}
      />
      <Stat
        label="Alertes"
        value={`${anomaliesCount} / ${pendingMatchesCount}`}
        hint="Anomalies / Reco en attente"
        icon={Activity}
        accent={anomaliesCount > 0 ? 'text-rose-600' : 'text-emerald-600'}
        bgColor={anomaliesCount > 0 ? 'bg-rose-50' : 'bg-white'}
        borderColor={anomaliesCount > 0 ? 'border-rose-200' : 'border-slate-200'}
      />
    </div>
  );
}
