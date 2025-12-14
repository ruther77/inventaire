export default function ConfirmationModal({ open, title, message, onConfirm, onCancel }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-5 shadow-2xl">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="mt-2 text-sm text-slate-300">{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onCancel} className="rounded-lg px-3 py-2 text-sm text-slate-200 bg-white/10 hover:bg-white/20">
            Annuler
          </button>
          <button onClick={onConfirm} className="rounded-lg px-3 py-2 text-sm font-medium text-white bg-rose-500 hover:bg-rose-600">
            Confirmer
          </button>
        </div>
      </div>
    </div>
  );
}
