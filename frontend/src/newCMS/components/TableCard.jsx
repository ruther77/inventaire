export default function TableCard({ title, description, headers = [], rows = [], renderRow, actions }) {
  return (
    <div className="p-6 rounded-2xl bg-slate-800/50 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-white">{title}</h3>
          {description && <p className="text-sm text-slate-400">{description}</p>}
        </div>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              {headers.map((h) => (
                <th key={h} className="text-left py-2 text-xs text-slate-400">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>{rows.map((row, idx) => (renderRow ? renderRow(row, idx) : null))}</tbody>
        </table>
      </div>
    </div>
  );
}
