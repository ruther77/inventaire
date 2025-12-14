export default function InlineTag({ label, tone = 'info' }) {
  const tones = {
    info: 'bg-blue-500/10 text-blue-200 border-blue-500/30',
    success: 'bg-emerald-500/10 text-emerald-200 border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-200 border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-200 border-rose-500/30',
    neutral: 'bg-white/5 text-slate-200 border-white/10',
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${tones[tone] || tones.neutral}`}>
      {label}
    </span>
  );
}
