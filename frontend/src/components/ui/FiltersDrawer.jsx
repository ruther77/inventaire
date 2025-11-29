import clsx from 'clsx';

export default function FiltersDrawer({ open, onClose, title, children }) {
  return (
    <div
      className={clsx(
        'fixed inset-0 z-50 flex transition-opacity duration-300',
        open ? 'visible opacity-100' : 'pointer-events-none opacity-0',
      )}
    >
      <div
        className="absolute inset-0 bg-slate-900/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        className={clsx(
          'relative ml-auto h-full max-w-md border-l border-slate-200 bg-white shadow-2xl transition-transform duration-300',
          open ? 'translate-x-0' : 'translate-x-full',
        )}
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-600">{title}</h3>
          <button onClick={onClose} className="text-sm font-semibold text-slate-500">
            Fermer
          </button>
        </div>
        <div className="p-5 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
