import { Ghost } from 'lucide-react';

export default function EmptyState({ title = 'Aucune donnée', description = 'Revenez plus tard ou ajustez vos filtres.', icon: Icon = Ghost }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-white/10 bg-white/5 px-6 py-8 text-center">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-slate-400">
        <Icon className="h-6 w-6" />
      </div>
      <p className="text-sm font-medium text-white">{title}</p>
      {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
    </div>
  );
}
