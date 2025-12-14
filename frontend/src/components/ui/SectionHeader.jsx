export default function SectionHeader({ title, description, actions }) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-200">
          {title}
        </p>
        {description && (
          <p className="text-xl font-semibold text-white">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
