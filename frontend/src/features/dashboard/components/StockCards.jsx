import React from 'react';
import Card from '../../../components/ui/Card.jsx';

const statusMap = {
  critical: { label: 'Critique', color: 'text-rose-600 bg-rose-100' },
  warning: { label: 'Surveillance', color: 'text-amber-700 bg-amber-100' },
  ok: { label: 'OK', color: 'text-emerald-600 bg-emerald-100' },
};

export default function StockCards({ items }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">Aucun produit dans cette vue.</p>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {items.map((item) => {
        const status = statusMap[item.status] ?? statusMap.ok;
        const coverage =
          item.seuil_alerte && item.seuil_alerte > 0
            ? Math.min(Math.round((item.stock_actuel / item.seuil_alerte) * 100), 120)
            : 0;
        return (
          <Card key={item.id} className="border-slate-100 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-slate-400">{item.categorie ?? 'Non classé'}</p>
                <h4 className="text-lg font-semibold text-slate-900">{item.nom}</h4>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${status.color}`}>
                {status.label}
              </span>
            </div>
            <div className="mt-4 flex items-center justify-between text-sm">
              <div>
                <p className="text-slate-500">Stock</p>
                <p className="text-xl font-semibold text-slate-900">{item.stock_actuel ?? 0} u</p>
              </div>
              <div className="text-right">
                <p className="text-slate-500">Seuil</p>
                <p className="text-xl font-semibold text-slate-900">{item.seuil_alerte ?? 0} u</p>
              </div>
            </div>
            <div className="mt-3 h-2 rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-500 to-rose-500"
                style={{ width: `${coverage}%` }}
              />
            </div>
          </Card>
        );
      })}
    </div>
  );
}
