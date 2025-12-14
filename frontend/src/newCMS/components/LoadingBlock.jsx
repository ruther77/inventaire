export default function LoadingBlock({ rows = 3, height = 14 }) {
  return (
    <div className="space-y-2">
      {[...Array(rows)].map((_, idx) => (
        <div
          key={idx}
          className="w-full animate-pulse rounded-lg bg-white/5"
          style={{ height: `${height}px` }}
        />
      ))}
    </div>
  );
}
