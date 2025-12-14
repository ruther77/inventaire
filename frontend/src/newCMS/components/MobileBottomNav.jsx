export default function MobileBottomNav({ items = [] }) {
  return (
    <div className="flex justify-around p-3 bg-slate-900/90 backdrop-blur-lg border-t border-white/10">
      {items.map((item, idx) => (
        <button
          key={idx}
          className={`flex flex-col items-center gap-1 ${
            item.active ? 'text-blue-400' : 'text-slate-500'
          }`}
        >
          <span className="text-xl">{item.icon}</span>
          <span className="text-[10px]">{item.label}</span>
        </button>
      ))}
    </div>
  );
}
