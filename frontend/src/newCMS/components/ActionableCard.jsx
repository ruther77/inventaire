/**
 * Carte CTA générique (titre, description, actions alignées à droite).
 */
export default function ActionableCard({ title, description, actions }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-800/50 p-4 flex items-center justify-between gap-3">
      <div>
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        {description && <p className="text-sm text-slate-400 mt-0.5">{description}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}
