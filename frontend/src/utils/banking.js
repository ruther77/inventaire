const roundAmount = (value) => Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100;

const parseIsoDateToUtc = (value) => {
  if (!value) return null;
  const segments = value.split('-').map(Number);
  if (segments.length !== 3 || segments.some(Number.isNaN)) return null;
  return new Date(Date.UTC(segments[0], segments[1] - 1, segments[2]));
};

const formatUtcDate = (dateObj) => dateObj.toISOString().slice(0, 10);

const getIsoWeekInfo = (dateObj) => {
  const tmp = new Date(dateObj.getTime());
  const dayNum = tmp.getUTCDay() || 7;
  tmp.setUTCDate(tmp.getUTCDate() + 4 - dayNum);
  const year = tmp.getUTCFullYear();
  const yearStart = new Date(Date.UTC(year, 0, 1));
  const week = Math.ceil((((tmp - yearStart) / 86400000) + 1) / 7);

  const monday = new Date(dateObj.getTime());
  const shift = (dateObj.getUTCDay() || 7) - 1;
  monday.setUTCDate(monday.getUTCDate() - shift);
  const sunday = new Date(monday.getTime());
  sunday.setUTCDate(sunday.getUTCDate() + 6);

  return {
    year,
    week,
    start: monday,
    end: sunday,
  };
};

const aggregateTimeline = (transactions, granularity) => {
  if (!transactions?.length) return [];
  const buckets = new Map();

  const getBucket = (key, factory) => {
    if (!buckets.has(key)) {
      buckets.set(key, factory());
    }
    return buckets.get(key);
  };

  transactions.forEach((tx) => {
    if (!tx) return;
    const amount = Number(tx.montant);
    if (Number.isNaN(amount)) return;
    const entryType = tx.type === 'Entrée' ? 'Entrée' : 'Sortie';
    if (granularity === 'monthly') {
      const monthKey = tx.mois || (tx.date ? tx.date.slice(0, 7) : null);
      if (!monthKey) return;
      const bucket = getBucket(monthKey, () => ({
        sortKey: monthKey,
        mois: monthKey,
        entrees: 0,
        sorties: 0,
      }));
      bucket[entryType === 'Entrée' ? 'entrees' : 'sorties'] += amount;
      return;
    }

    const parsedDate = parseIsoDateToUtc(tx.date);
    if (!parsedDate) return;

    if (granularity === 'weekly') {
      const info = getIsoWeekInfo(parsedDate);
      const weekKey = `${info.year}-W${String(info.week).padStart(2, '0')}`;
      const bucket = getBucket(weekKey, () => ({
        sortKey: `${info.year}-${String(info.week).padStart(2, '0')}`,
        semaine: weekKey,
        start_date: formatUtcDate(info.start),
        end_date: formatUtcDate(info.end),
        entrees: 0,
        sorties: 0,
      }));
      bucket[entryType === 'Entrée' ? 'entrees' : 'sorties'] += amount;
      return;
    }

    if (granularity === 'daily') {
      const dayKey = formatUtcDate(parsedDate);
      const bucket = getBucket(dayKey, () => ({
        sortKey: dayKey,
        jour: dayKey,
        entrees: 0,
        sorties: 0,
      }));
      bucket[entryType === 'Entrée' ? 'entrees' : 'sorties'] += amount;
    }
  });

  return Array.from(buckets.values())
    .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
    .map((bucket) => {
      const { sortKey, ...rest } = bucket;
      const net = roundAmount((rest.entrees || 0) - (rest.sorties || 0));
      return {
        ...rest,
        entrees: roundAmount(rest.entrees || 0),
        sorties: roundAmount(rest.sorties || 0),
        net,
      };
    });
};

const getBucketLabelForResolution = (transaction, resolution) => {
  if (resolution === 'monthly') {
    return transaction.mois || (transaction.date ? transaction.date.slice(0, 7) : null);
  }
  const parsedDate = parseIsoDateToUtc(transaction.date);
  if (!parsedDate) return null;
  if (resolution === 'weekly') {
    const info = getIsoWeekInfo(parsedDate);
    return `${info.year}-W${String(info.week).padStart(2, '0')}`;
  }
  return formatUtcDate(parsedDate);
};

const buildCategoryBuckets = (transactions, resolution) => {
  const bucketMap = new Map();
  transactions?.forEach((tx) => {
    if (!tx || tx.type !== 'Sortie') return;
    const label = getBucketLabelForResolution(tx, resolution);
    if (!label) return;
    const category = tx.categorie || 'Autres charges';
    const current = bucketMap.get(label) || {};
    current[category] = (current[category] || 0) + Math.abs(Number(tx.montant) || 0);
    bucketMap.set(label, current);
  });
  return bucketMap;
};

export {
  roundAmount,
  parseIsoDateToUtc,
  formatUtcDate,
  getIsoWeekInfo,
  aggregateTimeline,
  buildCategoryBuckets,
};
