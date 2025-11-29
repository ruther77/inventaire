import clsx from 'clsx';

export default function Modal({ open, title, description, children, actions, onClose }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur">
      <div className="glass-panel w-full max-w-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </div>
          <button
            type="button"
            className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-800"
            onClick={onClose}
          >
            ✕
          </button>
        </div>
        <div className="mt-4 flex flex-col gap-4">{children}</div>
        {actions && (
          <div className="mt-6 flex justify-end gap-2">
            {actions.map(({ label, variant = 'subtle', onClick, type = 'button', disabled }) => (
              <button
                key={label}
                type={type}
                onClick={onClick}
                disabled={disabled}
                className={clsx(
                  'inline-flex items-center rounded-2xl px-4 py-2 text-sm font-semibold transition',
                  variant === 'primary'
                    ? 'bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-700/50'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 disabled:opacity-50',
                )}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
