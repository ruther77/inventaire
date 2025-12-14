export default function ErrorBanner({ message = 'Une erreur est survenue', dense = false }) {
  return (
    <div
      className={`rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-100 ${
        dense ? 'px-3 py-2 text-sm' : 'px-4 py-3 text-sm'
      }`}
    >
      {message}
    </div>
  );
}
