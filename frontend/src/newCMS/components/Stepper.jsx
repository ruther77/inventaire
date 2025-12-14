export default function Stepper({ steps = [], active = 0 }) {
  return (
    <div className="flex items-center gap-3">
      {steps.map((step, idx) => {
        const done = idx < active;
        const current = idx === active;
        return (
          <div key={step} className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full border text-sm font-semibold ${
                done ? 'bg-emerald-500 text-white border-emerald-500' : current ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-300 border-white/10'
              }`}
            >
              {done ? '✓' : idx + 1}
            </div>
            <span className="text-sm text-white">{step}</span>
            {idx < steps.length - 1 && <div className="w-8 h-px bg-white/10" />}
          </div>
        );
      })}
    </div>
  );
}
