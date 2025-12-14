export const formatCurrency = (value) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '—';
  return Number(value).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
};

export const formatPercent = (value, digits = 1) => {
  if (value === undefined || value === null || Number.isNaN(value)) return '—';
  return `${Number(value).toFixed(digits)}%`;
};

export const formatDate = (date) => {
  if (!date) return '—';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
};
