export default function FilterChip({ label, active, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
        active
          ? 'bg-blue-500/20 text-blue-100 border-blue-500/40'
          : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'
      }`}
    >
      {label}
    </button>
  );
}
