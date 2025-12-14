export default function ActionBar({ primary, secondary, children }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-slate-800/50 px-4 py-3">
      <div className="flex items-center gap-2">{children}</div>
      <div className="flex gap-2">
        {secondary}
        {primary}
      </div>
    </div>
  );
}
