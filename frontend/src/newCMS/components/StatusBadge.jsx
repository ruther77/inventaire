const COLORS = {
  success: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  warning: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  danger: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
  info: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
};

export default function StatusBadge({ label, tone = 'info' }) {
  const styles = COLORS[tone] || COLORS.info;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${styles}`}>
      {label}
    </span>
  );
}
