import TableCard from './TableCard.jsx';

export default {
  title: 'newCMS/TableCard',
  component: TableCard,
};

const rows = [
  { plat: 'Burger Chef', marge: '71%', fc: '28%' },
  { plat: 'Risotto Truffe', marge: '50%', fc: '50%' },
];

export const Default = {
  render: () => (
    <TableCard
      title="Fiches techniques"
      description="Marge vs Food Cost"
      headers={['Plat', 'Marge', 'FC%']}
      rows={rows}
      renderRow={(row, idx) => (
        <tr key={idx} className="border-b border-white/5">
          <td className="py-3 text-sm text-white">{row.plat}</td>
          <td className="py-3 text-sm text-emerald-400">{row.marge}</td>
          <td className="py-3 text-sm text-amber-400">{row.fc}</td>
        </tr>
      )}
    />
  ),
};
