export default function DrawerShell({ open, onClose, title, children, footer }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end lg:items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="w-full max-w-4xl rounded-t-3xl lg:rounded-2xl border border-white/10 bg-slate-900 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="rounded-lg px-2 py-1 text-slate-400 hover:bg-white/10">
            ✕
          </button>
        </div>
        <div className="max-h-[70vh] overflow-auto px-4 py-4 space-y-4">{children}</div>
        {footer && <div className="border-t border-white/10 px-4 py-3">{footer}</div>}
      </div>
    </div>
  );
}
