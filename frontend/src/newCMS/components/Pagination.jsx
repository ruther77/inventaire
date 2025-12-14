export default function Pagination({ page = 1, totalPages = 1, onChange }) {
  if (totalPages <= 1) return null;
  const prev = () => onChange?.(Math.max(1, page - 1));
  const next = () => onChange?.(Math.min(totalPages, page + 1));
  return (
    <div className="flex items-center gap-2 text-sm text-slate-300">
      <button
        onClick={prev}
        className="rounded-lg border border-white/10 px-2 py-1 hover:bg-white/10 disabled:opacity-50"
        disabled={page <= 1}
      >
        ←
      </button>
      <span>
        Page {page} / {totalPages}
      </span>
      <button
        onClick={next}
        className="rounded-lg border border-white/10 px-2 py-1 hover:bg-white/10 disabled:opacity-50"
        disabled={page >= totalPages}
      >
        →
      </button>
    </div>
  );
}
