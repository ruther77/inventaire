export default function TagPill({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
        active
          ? 'bg-blue-500/20 text-blue-100 border-blue-500/40'
          : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'
      }`}
    >
      {label}
    </button>
  );
}
