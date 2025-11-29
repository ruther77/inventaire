export default function SectionHeader({ title, description, actions }) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm uppercase tracking-[0.4em] text-slate-400">
          {title}
        </p>
        {description && (
          <p className="text-lg font-semibold text-slate-900">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
