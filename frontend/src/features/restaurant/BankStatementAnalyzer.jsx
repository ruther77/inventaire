import React, { useEffect, useMemo, useState } from 'react';
import { Download, Calendar, TrendingDown, Filter, Eye } from 'lucide-react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  useRestaurantBankStatements,
  useCreateRestaurantBankStatement,
  useUpdateRestaurantBankStatement,
  useImportRestaurantBankStatementsPdf,
  useRestaurantBankStatementSummary,
  useRestaurantBankAccountsOverview,
  useCreateExpenseFromBankStatement,
  useRestaurantCategories,
  useRestaurantCostCenters,
} from '../../hooks/useRestaurant.js';
import { aggregateTimeline, buildCategoryBuckets, roundAmount } from '../../utils/banking.js';

const SUMMARY_MONTH_OPTIONS = [
  { value: 'all', label: "Tout l'historique" },
  { value: '3', label: '3 mois' },
  { value: '6', label: '6 mois' },
  { value: '12', label: '12 mois' },
];

const SUMMARY_RESOLUTION_OPTIONS = [
  { value: 'monthly', label: 'Mensuel' },
  { value: 'weekly', label: 'Hebdomadaire' },
  { value: 'daily', label: 'Journalier' },
];

const ACCOUNT_STATUS_STYLES = {
  connected: 'bg-emerald-100 text-emerald-700',
  error: 'bg-rose-100 text-rose-700',
  warning: 'bg-amber-100 text-amber-700',
  disconnected: 'bg-slate-100 text-slate-500',
  disabled: 'bg-slate-100 text-slate-500',
};

const CATEGORY_COLOR_PALETTE = ['#2563eb', '#0ea5e9', '#10b981', '#f97316', '#ec4899', '#8b5cf6', '#94a3b8'];


const formatCurrency = (value) => {
  const amount = Math.abs(value || 0).toLocaleString('fr-FR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${value < 0 ? '-' : ''}${amount} €`;
};

const StatusBadge = ({ status, children }) => {
  const base = ACCOUNT_STATUS_STYLES[status] || 'bg-slate-100 text-slate-600';
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${base}`}>
      {children}
    </span>
  );
};

const GuidedTip = ({ title, description }) => (
  <div className="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-4 text-sm text-slate-700 shadow-sm">
    <p className="font-semibold text-slate-900">{title}</p>
    <p className="mt-1 text-slate-600">{description}</p>
  </div>
);

const KpiCard = ({ label, value, hint, accent = 'text-slate-900' }) => (
  <div className="rounded-2xl border border-slate-200 bg-white p-4">
    <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{label}</p>
    <p className={`text-2xl font-semibold ${accent}`}>{value}</p>
    {hint && <p className="text-xs text-slate-500">{hint}</p>}
  </div>
);

const CategoryTag = ({ label, color = '#cbd5f5' }) => (
  <span
    className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold text-white"
    style={{ backgroundColor: color }}
  >
    {label}
  </span>
);

const ACCOUNT_DATA = {
  incontournable: {
    label: 'Incontournable (restaurant)',
    provider: 'Crédit Agricole',
    status: 'connected',
    color: 'emerald',
    accounts: [
      { label: 'Compte courant', balance: 45001.58, currency: '€', status: 'connected' },
      { label: 'LDD', balance: 12000, currency: '€', status: 'connected' },
    ],
    transactions: [
      { date: '2024-06-28', libelle: 'VIR SEPA NOUTAM', categorie: 'Fournisseur', montant: 720.0, mois: '2024-06', type: 'Sortie' },
      { date: '2024-06-30', libelle: 'TRAIT.IRREG.FONCT.CTE', categorie: 'Frais bancaires', montant: 19.2, mois: '2024-06', type: 'Sortie' },
      { date: '2024-07-01', libelle: 'SFR FIXE ADSL', categorie: 'Télécom', montant: 48.99, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-01', libelle: 'PRLV SEPA METRO CASH CARRY', categorie: 'Fournisseur alimentaire', montant: 3629.11, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-01', libelle: 'VERSEMENT ALS', categorie: 'Encaissement', montant: 2745.0, mois: '2024-07', type: 'Entrée' },
      { date: '2024-07-01', libelle: 'VERSEMENT ALS', categorie: 'Encaissement', montant: 1200.0, mois: '2024-07', type: 'Entrée' },
      { date: '2024-07-04', libelle: 'PRLV SEPA CANALSAT', categorie: 'Abonnements', montant: 35.99, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-05', libelle: 'PRLV SEPA SPB', categorie: 'Services professionnels', montant: 4.41, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-05', libelle: 'PRLV SEPA HMD AUDIT ET CONSEIL', categorie: 'Services professionnels', montant: 316.5, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-09', libelle: 'PRLV SEPA ENGIE', categorie: 'Électricité', montant: 477.68, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-09', libelle: 'VIR SEPA ADOHINZIN AYABA (salaire)', categorie: 'Salaires', montant: 1437.39, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-10', libelle: 'PRLV SEPA METRO CASH CARRY', categorie: 'Fournisseur alimentaire', montant: 799.6, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-10', libelle: 'VERSEMENT ALS', categorie: 'Encaissement', montant: 1810.0, mois: '2024-07', type: 'Entrée' },
      { date: '2024-07-10', libelle: 'VERSEMENT ALS', categorie: 'Encaissement', montant: 170.0, mois: '2024-07', type: 'Entrée' },
      { date: '2024-07-11', libelle: 'PRLV SEPA GAZELENERGIE', categorie: 'Gaz', montant: 468.51, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-11', libelle: 'PRLV SEPA PREFILOC CAPITAL', categorie: 'Loyer/Location', montant: 18.6, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-12', libelle: 'PRLV SEPA METRO CASH CARRY', categorie: 'Fournisseur alimentaire', montant: 155.6, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-15', libelle: 'VIR SEPA residence St an (loyer)', categorie: 'Loyer/Location', montant: 2000.0, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-15', libelle: 'VERSEMENT ALS', categorie: 'Encaissement', montant: 7770.0, mois: '2024-07', type: 'Entrée' },
      { date: '2024-07-16', libelle: 'PRLV SEPA METRO CASH CARRY', categorie: 'Fournisseur alimentaire', montant: 1013.83, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-16', libelle: 'PRLV SEPA URSSAF', categorie: 'Charges sociales', montant: 436.0, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-16', libelle: 'VIR SEPA MASSA ANGELE (salaire)', categorie: 'Salaires', montant: 2079.13, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-17', libelle: 'PRLV SEPA METRO CASH CARRY', categorie: 'Fournisseur alimentaire', montant: 110.19, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-17', libelle: 'VERSEMENT ALS', categorie: 'Encaissement', montant: 806.2, mois: '2024-07', type: 'Entrée' },
      { date: '2024-07-17', libelle: 'PRLV SEPA B2B DGFIP (TVA)', categorie: 'Impôts et taxes', montant: 1415.0, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-18', libelle: 'VIR SEPA noutam sas (achat)', categorie: 'Fournisseur', montant: 3000.0, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-19', libelle: 'PRLV SEPA B2B DGFIP (TVA)', categorie: 'Impôts et taxes', montant: 4214.0, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-19', libelle: 'VERSEMENT ALS', categorie: 'Encaissement', montant: 3475.0, mois: '2024-07', type: 'Entrée' },
      { date: '2024-07-22', libelle: 'VIR SEPA noutam sas (achat)', categorie: 'Fournisseur', montant: 702.0, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-23', libelle: 'VIR INST gnanam exotique (achat)', categorie: 'Fournisseur', montant: 428.84, mois: '2024-07', type: 'Sortie' },
      { date: '2024-07-24', libelle: 'PRLV SEPA METRO CASH CARRY', categorie: 'Fournisseur alimentaire', montant: 130.21, mois: '2024-07', type: 'Sortie' },
    ],
  },
  noutam: {
    label: 'Noutam (épicerie)',
    provider: 'Revolut',
    status: 'error',
    color: 'sky',
    accounts: [
      { label: 'Compte courant $', balance: 0, currency: '$', status: 'disabled' },
      { label: 'Compte courant €', balance: 17.6, currency: '€', status: 'error' },
    ],
    transactions: [
      { date: '2024-08-01', libelle: 'FACTURE FOURNISSEUR A', categorie: 'Fournisseur alimentaire', montant: 2200.0, mois: '2024-08', type: 'Sortie' },
      { date: '2024-08-05', libelle: 'VERSEMENT CAF', categorie: 'Encaissement', montant: 3600.0, mois: '2024-08', type: 'Entrée' },
      { date: '2024-08-10', libelle: 'PRLV SEPA ENGIE', categorie: 'Électricité', montant: 320.45, mois: '2024-08', type: 'Sortie' },
      { date: '2024-08-15', libelle: 'PRLV SEPA URSSAF', categorie: 'Charges sociales', montant: 510.0, mois: '2024-08', type: 'Sortie' },
      { date: '2024-08-18', libelle: 'VIR SEPA GESTION STOCK', categorie: 'Fournisseur', montant: 1400.0, mois: '2024-08', type: 'Sortie' },
      { date: '2024-08-25', libelle: 'VERSEMENT NOUTAM', categorie: 'Encaissement', montant: 4200.0, mois: '2024-08', type: 'Entrée' },
    ],
  },
};

const FALLBACK_ACCOUNT_LIST = Object.entries(ACCOUNT_DATA).map(([key, meta]) => {
  const flux = (meta.transactions ?? []).reduce(
    (acc, tx) => {
      if (tx.type === 'Entrée') {
        acc.inflow += tx.montant || 0;
      } else {
        acc.outflow += tx.montant || 0;
      }
      acc.operations += 1;
      return acc;
    },
    { inflow: 0, outflow: 0, operations: 0 },
  );
  return {
    value: key,
    label: meta.label,
    provider: meta.provider,
    status: meta.status,
    balance: (meta.accounts ?? []).reduce((sum, account) => sum + (account.balance || 0), 0),
    currency: 'EUR',
    inflow: flux.inflow,
    outflow: flux.outflow,
    operations: flux.operations,
    subAccounts: meta.accounts ?? [],
  };
});

const STATUS_PRIORITY = {
  error: 4,
  warning: 3,
  disconnected: 2,
  connected: 1,
  disabled: 0,
};

const buildAggregatedAccount = (accounts) => {
  if (!accounts.length) {
    return null;
  }
  const aggregated = accounts.reduce(
    (acc, entry) => {
      acc.balance += entry.balance || 0;
      acc.inflow += entry.inflow || 0;
      acc.outflow += entry.outflow || 0;
      acc.operations += entry.operations || 0;
      if (entry.lastActivity) {
        const current = new Date(entry.lastActivity);
        if (!acc.lastActivity || current > acc.lastActivity) {
          acc.lastActivity = current;
        }
      }
      const weight = STATUS_PRIORITY[entry.status] ?? 0;
      if (weight > acc.statusWeight) {
        acc.status = entry.status;
        acc.statusWeight = weight;
      }
      return acc;
    },
    {
      value: 'all',
      label: 'Tous les comptes',
      provider: 'Consolidé',
      status: 'connected',
      statusWeight: STATUS_PRIORITY.connected,
      balance: 0,
      inflow: 0,
      outflow: 0,
      operations: 0,
      currency: 'EUR',
      subAccounts: [],
      lastActivity: null,
    },
  );
  if (aggregated.lastActivity instanceof Date) {
    aggregated.lastActivity = aggregated.lastActivity.toISOString().slice(0, 10);
  }
  delete aggregated.statusWeight;
  return aggregated;
};

const normalizeDateInput = (value) => {
  if (!value) return null;
  let cleaned = value.trim();
  if (!cleaned) return null;
  cleaned = cleaned.replace(/[.]/g, '/').replace(/-/g, '/');
  const segments = cleaned.split('/');
  if (segments.length === 3) {
    let [day, month, year] = segments;
    if (year.length === 2) {
      year = `20${year}`;
    }
    return `${year.padStart(4, '0')}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  }
  const parsed = new Date(cleaned);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toISOString().slice(0, 10);
  }
  return null;
};

const parserLine = (line) => {
  const parts = line.split(';').map(part => part.trim());
  if (parts.length < 5) return null;
  const normalizedDate = normalizeDateInput(parts[0]);
  return {
    date: normalizedDate,
    libelle: parts[1],
    categorie: parts[2] || 'Autres',
    montant: parseFloat(parts[3].replace(',', '.')) || 0,
    mois: parts[4] || (normalizedDate ? normalizedDate.slice(0, 7) : ''),
    type: (parts[5] || 'Sortie'),
  };
};

const BankStatementAnalyzer = ({ defaultAccount = 'incontournable' }) => {
  const [selectedMonth, setSelectedMonth] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('table');
  const [selectedAccount, setSelectedAccount] = useState(defaultAccount);
  const [manualInput, setManualInput] = useState('');
  const [fileError, setFileError] = useState('');
  const [pdfInfo, setPdfInfo] = useState('');
  const [editableTransaction, setEditableTransaction] = useState(null);
  const [summaryMonths, setSummaryMonths] = useState('all');
  const [summaryResolution, setSummaryResolution] = useState('monthly');
  const [groupingPreset, setGroupingPreset] = useState('default');
  const bankAccountsQuery = useRestaurantBankAccountsOverview();
  const serverAccountCards = useMemo(
    () =>
      (bankAccountsQuery.data ?? []).map((entry, index) => ({
        value: entry.account || entry.display_name || `compte-${index}`,
        label: entry.display_name || entry.account || `Compte ${index + 1}`,
        provider: entry.provider || 'Compte',
        status: entry.status || 'connected',
        balance: Number(entry.balance ?? 0),
        inflow: Number(entry.inflow ?? 0),
        outflow: Number(entry.outflow ?? 0),
        operations: Number(entry.operations ?? 0),
        currency: entry.currency || 'EUR',
        lastActivity: entry.last_activity || null,
        subAccounts: [],
      })),
    [bankAccountsQuery.data],
  );
  const hasServerAccounts = serverAccountCards.length > 0;
  const accountCards = hasServerAccounts ? serverAccountCards : FALLBACK_ACCOUNT_LIST;
  const aggregatedAccountMeta = useMemo(
    () => (hasServerAccounts ? buildAggregatedAccount(serverAccountCards) : null),
    [hasServerAccounts, serverAccountCards],
  );
  const allowAllAccounts = hasServerAccounts && serverAccountCards.length > 1;
  const accountMap = useMemo(() => {
    const entries = new Map();
    accountCards.forEach((card) => entries.set(card.value, card));
    if (aggregatedAccountMeta) {
      entries.set('all', aggregatedAccountMeta);
    }
    return entries;
  }, [accountCards, aggregatedAccountMeta]);

  useEffect(() => {
    if (!accountCards.length) {
      return;
    }
    if (selectedAccount === 'all' && !allowAllAccounts) {
      setSelectedAccount(accountCards[0].value);
      return;
    }
    const exists = selectedAccount && (selectedAccount === 'all' ? allowAllAccounts : accountMap.has(selectedAccount));
    if (!exists) {
      if (allowAllAccounts) {
        setSelectedAccount('all');
      } else {
        setSelectedAccount(accountCards[0].value);
      }
    }
  }, [accountCards, accountMap, allowAllAccounts, selectedAccount]);

  const selectedAccountQuery = selectedAccount === 'all' ? undefined : selectedAccount;
  const bankStatements = useRestaurantBankStatements(selectedAccountQuery);
  const createBankStatement = useCreateRestaurantBankStatement();
  const updateBankStatement = useUpdateRestaurantBankStatement();
  const importBankStatementsPdf = useImportRestaurantBankStatementsPdf();
  const categoriesQuery = useRestaurantCategories();
  const costCentersQuery = useRestaurantCostCenters();
  const createExpenseFromStatement = useCreateExpenseFromBankStatement();
  const [expenseModal, setExpenseModal] = useState(null);
  const [expenseError, setExpenseError] = useState('');
  const isAllWindow = summaryMonths === 'all';
  const summaryMonthsValue = isAllWindow ? 0 : Number(summaryMonths);
  const bankSummary = useRestaurantBankStatementSummary(selectedAccountQuery, summaryMonthsValue, groupingPreset);
  const summaryData = bankSummary.data;
  const groupingOptions = useMemo(() => {
    if (summaryData?.presets?.length) {
      return summaryData.presets;
    }
    return [{ name: 'default', label: 'Vue standard', groups: [] }];
  }, [summaryData]);
  const summaryLoading = bankSummary.isLoading || bankSummary.isFetching;
  const forecastValue = summaryData?.forecast_next_month ?? null;

  const showSampleData = import.meta.env.VITE_SHOW_SAMPLE_BANK_STATEMENTS === 'true';
  const allowSampleData = showSampleData && !hasServerAccounts;
  const fallbackTransactions = useMemo(() => {
    if (!allowSampleData) {
      return [];
    }
    const seedTransactions = ACCOUNT_DATA[selectedAccount]?.transactions ?? [];
    return seedTransactions.map((tx, index) => ({
      ...tx,
      uid: `${selectedAccount}-seed-${index}-${tx.date}-${tx.montant}`,
    }));
  }, [allowSampleData, selectedAccount]);
  const serverTransactions = bankStatements.data ?? [];
  const transactions = useMemo(() => {
    if (serverTransactions.length === 0) {
      return allowSampleData ? fallbackTransactions : [];
    }
    return serverTransactions.map((tx) => ({ ...tx, uid: `bank-${tx.id}` }));
  }, [serverTransactions, fallbackTransactions, allowSampleData]);
  const scopedTransactions = useMemo(() => {
    if (isAllWindow) {
      return transactions;
    }
    const now = new Date();
    const currentIndex = now.getUTCFullYear() * 12 + now.getUTCMonth();
    const minIndex = currentIndex - summaryMonthsValue + 1;
    return transactions.filter((tx) => {
      const rawMonth = tx.mois || (tx.date ? tx.date.slice(0, 7) : null);
      if (!rawMonth) return false;
      const [yearStr, monthStr] = rawMonth.split('-');
      const year = Number(yearStr);
      const month = Number(monthStr);
      if (Number.isNaN(year) || Number.isNaN(month)) {
        return false;
      }
      const idx = year * 12 + (month - 1);
      return idx >= minIndex;
    });
  }, [transactions, summaryMonthsValue, isAllWindow]);

  useEffect(() => {
    setEditableTransaction(null);
  }, [selectedAccount]);

  useEffect(() => {
    setSelectedAccount(defaultAccount);
  }, [defaultAccount]);

  useEffect(() => {
    if (!groupingOptions?.length) return;
    if (!groupingOptions.some((preset) => preset.name === groupingPreset)) {
      setGroupingPreset(groupingOptions[0].name);
    }
  }, [groupingOptions, groupingPreset]);

  const fallbackTimelines = useMemo(
    () => ({
      monthly: aggregateTimeline(scopedTransactions, 'monthly'),
      weekly: aggregateTimeline(scopedTransactions, 'weekly'),
      daily: aggregateTimeline(scopedTransactions, 'daily'),
    }),
    [scopedTransactions],
  );

  const timelineStats = useMemo(() => {
    if (summaryData) {
      const server = {
        monthly: summaryData.monthly ?? [],
        weekly: summaryData.weekly ?? [],
        daily: summaryData.daily ?? [],
      };
      if (server[summaryResolution]?.length) {
        return server[summaryResolution];
      }
    }
    return fallbackTimelines[summaryResolution] ?? [];
  }, [summaryData, summaryResolution, fallbackTimelines]);

  const availableCash = useMemo(
    () =>
      scopedTransactions.reduce(
        (sum, transaction) => sum + (transaction.type === 'Entrée' ? transaction.montant : -transaction.montant),
        0,
      ),
    [scopedTransactions],
  );

  const currentPeriod = timelineStats.length ? timelineStats[timelineStats.length - 1] : null;
  const inflowCurrent = currentPeriod?.entrees ?? 0;
  const outflowCurrent = currentPeriod?.sorties ?? 0;

  const vatBalance = useMemo(
    () =>
      scopedTransactions
        .filter((tx) => (tx.categorie || '').toLowerCase().includes('tva'))
        .reduce((sum, tx) => sum + (tx.type === 'Entrée' ? tx.montant : -tx.montant), 0),
    [scopedTransactions],
  );

  const resolutionLabel =
    SUMMARY_RESOLUTION_OPTIONS.find((option) => option.value === summaryResolution)?.label ?? 'Mensuel';

  const formatTimelineLabel = (stat) => {
    if (summaryResolution === 'weekly') {
      return stat.semaine;
    }
    if (summaryResolution === 'daily') {
      return stat.jour;
    }
    return stat.mois;
  };

  const formatTimelineSubLabel = (stat) => {
    if (summaryResolution === 'weekly' && stat.start_date && stat.end_date) {
      return `${stat.start_date} → ${stat.end_date}`;
    }
    return null;
  };

  const kpiCards = [
    {
      label: 'Trésorerie disponible',
      value: formatCurrency(availableCash),
      accent: availableCash >= 0 ? 'text-emerald-700' : 'text-rose-600',
    },
    {
      label: 'Encaissements du mois',
      value: formatCurrency(inflowCurrent),
      accent: 'text-emerald-700',
      hint: currentPeriod ? `Période ${formatTimelineLabel(currentPeriod)}` : undefined,
    },
    {
      label: 'Décaissements du mois',
      value: formatCurrency(outflowCurrent),
      accent: 'text-rose-600',
      hint: currentPeriod ? `Période ${formatTimelineLabel(currentPeriod)}` : undefined,
    },
    {
      label: 'Solde TVA',
      value: formatCurrency(vatBalance),
      accent: vatBalance >= 0 ? 'text-emerald-700' : 'text-rose-600',
      hint: 'Catégories contenant “TVA”',
    },
  ];

  const categoryTimelineMap = useMemo(
    () => buildCategoryBuckets(scopedTransactions, summaryResolution),
    [scopedTransactions, summaryResolution],
  );

  const topCategoryKeys = useMemo(() => {
    const totals = {};
    categoryTimelineMap.forEach((breakdown) => {
      Object.entries(breakdown).forEach(([category, amount]) => {
        totals[category] = (totals[category] || 0) + amount;
      });
    });
    return Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([category]) => category);
  }, [categoryTimelineMap]);

  const stackedCategoryKeys = useMemo(() => {
    const keys = [...topCategoryKeys];
    if (!keys.includes('Autres')) {
      keys.push('Autres');
    }
    return keys;
  }, [topCategoryKeys]);

  const timelineChartData = useMemo(
    () =>
      timelineStats.map((stat) => ({
        label: formatTimelineLabel(stat) ?? 'Période',
        entrees: roundAmount(stat.entrees ?? 0),
        sorties: roundAmount(stat.sorties ?? 0),
        net: roundAmount(stat.net ?? 0),
      })),
    [timelineStats, summaryResolution],
  );

  const categoryChartData = useMemo(() => {
    if (!timelineStats.length) return [];
    return timelineStats.map((stat) => {
      const label = formatTimelineLabel(stat) ?? 'Période';
      const breakdown = categoryTimelineMap.get(label) || {};
      const row = { label };
      let other = 0;
      Object.entries(breakdown).forEach(([category, amount]) => {
        if (topCategoryKeys.includes(category)) {
          row[category] = roundAmount(amount);
        } else {
          other += amount;
        }
      });
      row.Autres = roundAmount(other);
      return row;
    });
  }, [timelineStats, categoryTimelineMap, topCategoryKeys, summaryResolution]);

  const categoryCards = useMemo(
    () =>
      timelineStats.map((stat) => {
        const label = formatTimelineLabel(stat) ?? 'Période';
        const breakdown = categoryTimelineMap.get(label) || {};
        const total = Object.values(breakdown).reduce((sum, value) => sum + value, 0);
        const topEntries = Object.entries(breakdown)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([category, amount]) => ({ category, amount: roundAmount(amount) }));
        return {
          label,
          total: roundAmount(total),
          entries: topEntries,
        };
      }),
    [timelineStats, categoryTimelineMap, summaryResolution],
  );

  const categoryColorMap = useMemo(() => {
    const palette = CATEGORY_COLOR_PALETTE;
    const unique = [...new Set(scopedTransactions.map(t => t.categorie || 'Autres charges'))];
    return unique.reduce((acc, category, index) => {
      acc[category] = palette[index % palette.length];
      return acc;
    }, {});
  }, [scopedTransactions]);

  const fallbackCategoryStats = useMemo(() => {
    const stats = {};
    scopedTransactions.forEach(t => {
      if (t.type !== 'Sortie') return;
      const group = t.categorie || 'Autres charges';
      if (!stats[group]) stats[group] = { groupe: group, montant: 0 };
      stats[group].montant += t.montant;
    });
    return Object.values(stats).sort((a, b) => b.montant - a.montant);
  }, [scopedTransactions]);

  const categoryStats = useMemo(() => {
    if (summaryData?.groups?.length) {
      return summaryData.groups.map((group) => ({
        groupe: group.group,
        montant: group.sorties,
        entrees: group.entrees,
        net: group.net,
      }));
    }
    return fallbackCategoryStats;
  }, [summaryData, fallbackCategoryStats]);

  const selectedAccountMeta = selectedAccount ? accountMap.get(selectedAccount) : null;
  const asideAccountCards = useMemo(() => {
    if (allowAllAccounts && aggregatedAccountMeta) {
      return [aggregatedAccountMeta, ...accountCards];
    }
    return accountCards;
  }, [accountCards, allowAllAccounts, aggregatedAccountMeta]);
  const accountFilterOptions = useMemo(() => {
    const base = accountCards.map((card) => ({ value: card.value, label: card.label }));
    if (allowAllAccounts && aggregatedAccountMeta) {
      return [{ value: 'all', label: aggregatedAccountMeta.label }, ...base];
    }
    return base;
  }, [accountCards, allowAllAccounts, aggregatedAccountMeta]);

  const filteredTransactions = useMemo(() => {
    return scopedTransactions.filter(t => {
      if (selectedMonth !== 'all' && t.mois !== selectedMonth) return false;
      if (selectedCategory !== 'all' && t.categorie !== selectedCategory) return false;
      return true;
    });
  }, [scopedTransactions, selectedMonth, selectedCategory]);

  const persistEntries = async (entries) => {
    if (!selectedAccount || selectedAccount === 'all') {
      throw new Error('Sélectionnez un compte bancaire précis avant l’import.');
    }
    const payloads = entries
      .filter((entry) => entry.date && entry.mois)
      .map((entry) => ({
        account: selectedAccount,
        date: entry.date,
        libelle: entry.libelle,
        categorie: entry.categorie,
        montant: entry.montant,
        type: entry.type,
        mois: entry.mois || entry.date.slice(0, 7),
      }));
    if (!payloads.length) {
      throw new Error('Aucune ligne valide à enregistrer');
    }
    await Promise.all(payloads.map((payload) => createBankStatement.mutateAsync(payload)));
  };

  const handleManualSubmit = async (event) => {
    event.preventDefault();
    if (!selectedAccount || selectedAccount === 'all') {
      setFileError('Sélectionnez un compte précis avant d’enregistrer des lignes.');
      return;
    }
    const lines = manualInput.split('\n').map((line) => line.trim()).filter(Boolean);
    const parsed = lines.map(parserLine).filter(Boolean);
    if (!parsed.length) return;
    try {
      await persistEntries(parsed);
      setManualInput('');
      setFileError('');
      setPdfInfo('');
    } catch (error) {
      setFileError('Impossible d’enregistrer les relevés. Réessaye plus tard.');
    }
  };

const handleFileUpload = (event) => {
    setFileError('');
    if (!selectedAccount || selectedAccount === 'all') {
      setFileError('Sélectionnez un compte précis avant d’importer un fichier.');
      return;
    }
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const text = reader.result;
      if (typeof text !== 'string') {
        setFileError('Fichier introuvable ou illisible.');
        return;
      }
      const rows = text.split(/\r?\n/).map((row) => row.trim()).filter(Boolean);
      const parsed = rows.map(parserLine).filter(Boolean);
      if (!parsed.length) {
        setFileError('Aucune ligne valide détectée (format : date;libellé;categorie;montant;mois;type).');
        return;
      }
      try {
        await persistEntries(parsed);
        setPdfInfo('');
      } catch (error) {
        setFileError('Impossible d’enregistrer les relevés. Réessaye plus tard.');
      }
    };
  reader.onerror = () => setFileError('Impossible de lire le fichier.');
  reader.readAsText(file, 'utf-8');
};

  const handlePdfUpload = async (event) => {
    setPdfInfo('');
    if (!selectedAccount || selectedAccount === 'all') {
      setFileError('Sélectionnez un compte précis avant d’importer un PDF.');
      return;
    }
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const result = await importBankStatementsPdf.mutateAsync({ account: selectedAccount, file });
      setPdfInfo(`${result.inserted} mouvements ajoutés (${result.total} détectés${result.duplicates ? `, ${result.duplicates} doublon(s)` : ''}).`);
      setFileError('');
    } catch (error) {
      setFileError("Impossible d'importer le PDF. Vérifiez le format.");
    } finally {
      event.target.value = '';
    }
  };

  const handlePrepareEdit = (transaction) => {
    if (!transaction.id) return;
    setEditableTransaction({ ...transaction });
  };

  const handleEditChange = (field, value) => {
    setEditableTransaction((prev) => (prev ? { ...prev, [field]: value } : prev));
  };

  const handleEditSubmit = async (event) => {
    event.preventDefault();
    if (!editableTransaction?.id) return;
    try {
      await updateBankStatement.mutateAsync({
        entryId: editableTransaction.id,
        payload: {
          account: editableTransaction.account,
          date: editableTransaction.date,
          libelle: editableTransaction.libelle,
          categorie: editableTransaction.categorie,
          montant: Number(editableTransaction.montant),
          type: editableTransaction.type,
          mois: editableTransaction.mois,
        },
      });
      setEditableTransaction(null);
      setFileError('');
    } catch (error) {
      setFileError('Impossible de mettre à jour le relevé.');
    }
  };

  const handleEditCancel = () => {
    setEditableTransaction(null);
  };

  const handleOpenExpenseModal = (transaction) => {
    if (!transaction) return;
    setExpenseError('');
    setExpenseModal({
      entry: transaction,
      form: {
        libelle: transaction.libelle || '',
        date_operation: transaction.date || '',
        montant_ht: Math.abs(transaction.montant || 0),
        categorie_id: null,
        cost_center_id: null,
        fournisseur_id: null,
        tva_pct: 20,
      },
    });
  };

  const handleCloseExpenseModal = () => {
    setExpenseModal(null);
    setExpenseError('');
  };

  const handleExpenseFieldChange = (field, value) => {
    setExpenseModal((prev) => (prev ? { ...prev, form: { ...prev.form, [field]: value } } : prev));
  };

  const handleExpenseSubmit = async (event) => {
    event.preventDefault();
    if (!expenseModal?.entry) return;
    setExpenseError('');
    try {
      const payload = {
        ...expenseModal.form,
        libelle: expenseModal.form.libelle?.trim() || expenseModal.entry.libelle,
        montant_ht: expenseModal.form.montant_ht ? parseFloat(expenseModal.form.montant_ht) : undefined,
      };
      if (!payload.montant_ht) {
        payload.montant_ht = Math.abs(expenseModal.entry.montant || 0);
      }
      await createExpenseFromStatement.mutateAsync({
        entryId: expenseModal.entry.id,
        payload,
        account: selectedAccount,
      });
      handleCloseExpenseModal();
    } catch (error) {
      setExpenseError("Impossible de créer la dépense à partir du relevé.");
    }
  };

  const exportToCSV = () => {
    const headers = ['Date', 'Libellé', 'Catégorie', 'Montant', 'Type', 'Mois'];
    const rows = filteredTransactions.map(t => [
      t.date,
      t.libelle,
      t.categorie,
      t.montant.toFixed(2),
      t.type,
      t.mois,
    ]);
    const csv = [headers, ...rows].map(row => row.join(';')).join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `releves-${selectedMonth}.csv`;
    link.click();
  };

  const months = useMemo(() => [...new Set(scopedTransactions.map(t => t.mois))].sort(), [scopedTransactions]);
  const categoriesFilter = useMemo(() => [...new Set(scopedTransactions.map(t => t.categorie))].sort(), [scopedTransactions]);
  const categoryOptions = categoriesQuery.data ?? [];
  const costCenterOptions = costCentersQuery.data ?? [];

  const totalEntrées = filteredTransactions.filter(t => t.type === 'Entrée').reduce((sum, t) => sum + t.montant, 0);
  const totalSorties = filteredTransactions.filter(t => t.type === 'Sortie').reduce((sum, t) => sum + t.montant, 0);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <div className="grid gap-6 lg:grid-cols-[320px,1fr]">
          <aside className="flex flex-col gap-4">
            <Card className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Comptes bancaires</p>
                  <p className="text-sm text-slate-500">Centralisez vos flux et vos cartes</p>
                </div>
                {selectedAccountMeta && (
                  <StatusBadge status={selectedAccountMeta.status}>{selectedAccountMeta.status}</StatusBadge>
                )}
              </div>
              <div className="flex flex-col gap-3">
                {asideAccountCards.length ? (
                  asideAccountCards.map((meta) => {
                    const isActive = meta.value === selectedAccount;
                    const hasBreakdown = (meta.subAccounts ?? []).length > 0;
                    return (
                      <button
                        key={meta.value}
                        type="button"
                        onClick={() => setSelectedAccount(meta.value)}
                        className={`rounded-2xl border px-4 py-3 text-left transition ${
                          isActive ? 'border-slate-900 bg-white shadow-sm' : 'border-slate-200 bg-slate-50 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div>
                            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{meta.provider}</p>
                            <p className="text-sm font-semibold text-slate-900">{meta.label}</p>
                          </div>
                          {meta.status && <StatusBadge status={meta.status}>{meta.status}</StatusBadge>}
                        </div>
                        <p className="mt-3 text-xs uppercase tracking-[0.3em] text-slate-400">Solde agrégé</p>
                        <p className="text-lg font-semibold text-slate-900">{formatCurrency(meta.balance || 0)}</p>
                        <div className="mt-3 space-y-1 text-xs text-slate-600">
                          {hasBreakdown ? (
                            meta.subAccounts.map((account) => (
                              <div key={`${meta.value}-${account.label}`} className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span
                                    className={`inline-flex h-4 w-7 rounded-full border transition ${
                                      account.status === 'disabled'
                                        ? 'border-slate-200 bg-slate-100'
                                        : account.status === 'error'
                                          ? 'border-rose-200 bg-rose-100'
                                          : 'border-emerald-200 bg-emerald-100'
                                    }`}
                                  />
                                  {account.label}
                                </div>
                                <span className="font-semibold text-slate-900">{formatCurrency(account.balance || 0)}</span>
                              </div>
                            ))
                          ) : (
                            <>
                              {(meta.inflow || meta.outflow) && (
                                <p>
                                  Flux {formatCurrency(meta.inflow || 0)} / {formatCurrency(meta.outflow || 0)}
                                </p>
                              )}
                              {meta.operations ? <p>{meta.operations} opérations suivies</p> : null}
                              {meta.lastActivity && <p>Dernier mouvement {meta.lastActivity}</p>}
                            </>
                          )}
                        </div>
                      </button>
                    );
                  })
                ) : (
                  <p className="text-sm text-slate-500">Aucun compte relié pour l’instant.</p>
                )}
              </div>
              <div className="mt-4 flex gap-2">
                <Button variant="ghost" className="flex-1 justify-center text-sm">
                  Gérer les comptes
                </Button>
                <Button variant="brand" className="flex-1 justify-center text-sm">
                  Ajouter une banque
                </Button>
              </div>
            </Card>
            <GuidedTip
              title="Synchronisation temps réel"
              description="Connectez vos comptes et cartes pour alimenter automatiquement vos relevés et vos prévisions."
            />
            <GuidedTip
              title="Catégorisation intelligente"
              description="Modifiez vos catégories à tout moment : vos dashboards se mettent à jour instantanément."
            />
          </aside>
          <div className="space-y-6">
            <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-3">
                  <TrendingDown className="h-10 w-10 text-blue-600" />
                  <div>
                    <p className="text-xs uppercase tracking-[0.4em] text-slate-500">Restaurant HQ</p>
                    <h1 className="text-3xl font-semibold text-slate-900">Relevés bancaires détaillés</h1>
                    <p className="text-sm text-slate-500">
                      Compte sélectionné : {selectedAccountMeta?.label ?? selectedAccount}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" className="inline-flex items-center gap-2" onClick={exportToCSV}>
                  <Download className="h-4 w-4" />
                  Export CSV
                </Button>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                {kpiCards.map((kpi) => (
                  <KpiCard key={kpi.label} label={kpi.label} value={kpi.value} hint={kpi.hint} accent={kpi.accent} />
                ))}
              </div>
            </header>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex flex-col gap-4">
            <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-blue-600" />
              Chronologie & prévisions
              <span className="text-xs font-normal text-slate-400 uppercase tracking-wide">
                {resolutionLabel}
              </span>
            </h2>
            {summaryLoading && <p className="text-xs text-slate-400">Calcul en cours...</p>}
            {!summaryLoading && forecastValue !== null && (
              <p className="text-xs text-slate-500">
                Prévision prochaine période : <span className="font-semibold">{forecastValue.toFixed(2)} €</span>
              </p>
            )}
            {timelineChartData.length > 0 && (
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timelineChartData} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(value) => `${Number(value).toFixed(2)} €`} />
                    <Legend />
                    <Area type="monotone" dataKey="entrees" stroke="#22c55e" fill="#22c55e" fillOpacity={0.15} name="Entrées" />
                    <Area type="monotone" dataKey="sorties" stroke="#ef4444" fill="#ef4444" fillOpacity={0.1} name="Sorties" />
                    <Area type="monotone" dataKey="net" stroke="#0ea5e9" fill="url(#colorNet)" name="Résultat" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="space-y-3">
              {timelineStats.length === 0 && !summaryLoading && (
                <p className="text-sm text-slate-500">Aucune donnée sur la période sélectionnée.</p>
              )}
              {timelineStats.map((stat, index) => {
                const label = formatTimelineLabel(stat) ?? `periode-${index}`;
                const extra = formatTimelineSubLabel(stat);
                const scaleBase = summaryResolution === 'daily' ? 200 : summaryResolution === 'weekly' ? 800 : 1500;
                const progress = Math.min(Math.abs(stat.net || 0) / scaleBase, 1) * 100;
                return (
                  <div key={`${summaryResolution}-${label}-${index}`} className="space-y-1">
                    <div className="flex items-center justify-between text-sm text-slate-600">
                      <span>{label}</span>
                      <span>{stat.net.toFixed(2)} €</span>
                    </div>
                    {extra && <p className="text-xs text-slate-400">{extra}</p>}
                    <div className="h-2 rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-blue-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Filter className="w-4 h-4 text-blue-600" />
              Répartition par groupe
            </h2>
            {summaryLoading && <p className="text-xs text-slate-400">Calcul en cours...</p>}
            {categoryChartData.length > 0 && (
              <div className="h-64 w-full mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoryChartData} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(value) => `${Number(value).toFixed(2)} €`} />
                    <Legend />
                    {stackedCategoryKeys.map((key, idx) => (
                      <Bar
                        key={key}
                        dataKey={key}
                        stackId="categories"
                        fill={CATEGORY_COLOR_PALETTE[idx % CATEGORY_COLOR_PALETTE.length]}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="space-y-3">
              {categoryStats.length === 0 && !summaryLoading && (
                <p className="text-sm text-slate-500">Aucun groupe à afficher.</p>
              )}
              {categoryStats.map(group => (
                <div key={group.groupe} className="space-y-1">
                  <div className="flex items-center justify-between text-sm text-slate-600">
                    <span>{group.groupe}</span>
                    <span>{(group.montant ?? 0).toFixed(2)} €</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-rose-500 to-orange-500"
                      style={{ width: `${Math.min((group.montant ?? 0) / 5000, 1) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 grid gap-2">
              {categoryCards.length === 0 && !summaryLoading && (
                <p className="text-xs text-slate-400">Aucune dépense détectée sur cette période.</p>
              )}
              {categoryCards.slice(-6).reverse().map((card) => (
                <div key={`card-${card.label}`} className="rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center justify-between text-sm font-semibold text-slate-700">
                    <span>{card.label}</span>
                    <span>{card.total.toFixed(2)} €</span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {card.entries.length === 0 && (
                      <span className="text-xs text-slate-400">Aucune catégorie dominante</span>
                    )}
                    {card.entries.map((entry) => (
                      <span
                        key={`${card.label}-${entry.category}`}
                        className="inline-flex items-center rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600"
                      >
                        <span
                          className="mr-1 inline-block h-2 w-2 rounded-full"
                          style={{ backgroundColor: categoryColorMap[entry.category] || '#94a3b8' }}
                        />
                        {entry.category}: {entry.amount.toFixed(2)} €
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-[1.1fr,0.9fr]">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Eye className="w-4 h-4 text-blue-600" />
                Analyse détaillée
              </h2>
              <div className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                <button className={`mr-2 ${viewMode === 'table' ? 'text-slate-900' : 'text-slate-400'}`} onClick={() => setViewMode('table')}>
                  Table
                </button>
                |
                <button className={`ml-2 ${viewMode === 'summary' ? 'text-slate-900' : 'text-slate-400'}`} onClick={() => setViewMode('summary')}>
                  Résumé
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:flex-wrap">
              <label className="text-sm font-semibold text-slate-600">
                Mois
                <select
                  className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
                  value={selectedMonth}
                  onChange={e => setSelectedMonth(e.target.value)}
                >
                  <option value="all">Tous</option>
                  {months.map(month => (
                    <option key={month} value={month}>
                      {month}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-semibold text-slate-600">
                Catégorie
                <select
                  className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
                  value={selectedCategory}
                  onChange={e => setSelectedCategory(e.target.value)}
                >
                  <option value="all">Toutes</option>
                  {categoriesFilter.map(category => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                  </select>
                </label>
              <label className="text-sm font-semibold text-slate-600">
                Compte
                <select
                  className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
                  value={selectedAccount}
                  onChange={e => setSelectedAccount(e.target.value)}
                >
                  {accountFilterOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-semibold text-slate-600">
                Fenêtre
                <select
                  className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
                  value={summaryMonths}
                  onChange={e => setSummaryMonths(e.target.value)}
                >
                  {SUMMARY_MONTH_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-semibold text-slate-600">
                Granularité
                <select
                  className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
                  value={summaryResolution}
                  onChange={e => setSummaryResolution(e.target.value)}
                >
                  {SUMMARY_RESOLUTION_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-semibold text-slate-600">
                Regroupement
                <select
                  className="ml-3 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm"
                  value={groupingPreset}
                  onChange={e => setGroupingPreset(e.target.value)}
                  disabled={summaryLoading}
                >
                  {groupingOptions.map(option => (
                    <option key={option.name} value={option.name}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {viewMode === 'table' ? (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead>
                  <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Libellé</th>
                    <th className="px-3 py-2">Catégorie</th>
                    <th className="px-3 py-2">Montant</th>
                    <th className="px-3 py-2">Mois</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Action</th>
                  </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredTransactions.map((t) => (
                      <tr key={t.uid}>
                        <td className="px-3 py-2 text-slate-700">{t.date}</td>
                        <td className="px-3 py-2 text-slate-700">{t.libelle}</td>
                        <td className="px-3 py-2">
                          {t.categorie ? (
                            <CategoryTag label={t.categorie} color={categoryColorMap[t.categorie] || '#94a3b8'} />
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-slate-900 font-semibold">
                          {t.type === 'Entrée' ? '+' : '-'}
                          {t.montant.toFixed(2)} €
                        </td>
                        <td className="px-3 py-2 text-slate-600">{t.mois}</td>
                        <td className="px-3 py-2">
                          <span
                            className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                              t.type === 'Entrée' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {t.type}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-col gap-2">
                            <button
                              type="button"
                              disabled={!t.id}
                              onClick={() => handlePrepareEdit(t)}
                              className={`rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold ${
                                t.id ? 'text-slate-600 hover:border-slate-900 hover:text-slate-900' : 'text-slate-300 cursor-not-allowed'
                              }`}
                            >
                              Modifier
                            </button>
                            {t.depense_id ? (
                              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 text-center">
                                Charge #{t.depense_id}
                              </span>
                            ) : (
                              <button
                                type="button"
                                disabled={t.type !== 'Sortie'}
                                onClick={() => handleOpenExpenseModal(t)}
                                className={`rounded-full border border-amber-200 px-3 py-1 text-xs font-semibold ${
                                  t.type === 'Sortie'
                                    ? 'text-amber-700 hover:border-amber-500 hover:text-amber-900'
                                    : 'text-slate-300 cursor-not-allowed'
                                }`}
                              >
                                Créer charge
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="mt-4 space-y-2 text-sm text-slate-600">
                <p>Total entrées : {totalEntrées.toFixed(2)} €</p>
                <p>Total sorties : {totalSorties.toFixed(2)} €</p>
                <p>Solde net : {(totalEntrées - totalSorties).toFixed(2)} €</p>
              </div>
            )}
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Download className="w-4 h-4 text-blue-600" />
              Ajouter des relevés
            </h3>
            <form onSubmit={handleManualSubmit} className="space-y-3">
              <textarea
                value={manualInput}
                onChange={e => setManualInput(e.target.value)}
                placeholder="date;libellé;catégorie;montant;mois;type"
                rows={4}
                className="w-full rounded-xl border border-slate-200 p-3 text-sm"
              />
              {fileError && <p className="text-xs font-semibold text-rose-600">{fileError}</p>}
              <div className="flex flex-col gap-2">
                <input type="file" accept=".csv,.txt" onChange={handleFileUpload} className="text-sm text-slate-500" />
                <button
                  type="submit"
                  className="inline-flex items-center justify-center rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                >
                  Ajouter depuis le texte
                </button>
              </div>
            </form>
            <p className="mt-3 text-xs text-slate-500">
              Format CSV attendu: <span className="font-semibold">date;libellé;catégorie;montant;mois;type</span>. Valeur
              par défaut pour le `type` : Sortie.
            </p>
            <div className="mt-4 space-y-2">
              <label className="text-sm font-semibold text-slate-700">Importer un relevé PDF (LCL)</label>
              <input
                type="file"
                accept="application/pdf"
                onChange={handlePdfUpload}
                className="text-sm text-slate-500"
              />
              {importBankStatementsPdf.isLoading && (
                <p className="text-xs text-slate-500">Analyse du PDF en cours…</p>
              )}
              {pdfInfo && <p className="text-xs text-emerald-600">{pdfInfo}</p>}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Filter className="w-4 h-4 text-blue-600" />
              Moduler les relevés
            </h3>
            {editableTransaction ? (
              <form onSubmit={handleEditSubmit} className="space-y-3">
                <div className="grid gap-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Libellé</label>
                  <input
                    type="text"
                    value={editableTransaction.libelle}
                    onChange={(event) => handleEditChange('libelle', event.target.value)}
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div className="grid gap-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Catégorie</label>
                  <input
                    type="text"
                    value={editableTransaction.categorie}
                    onChange={(event) => handleEditChange('categorie', event.target.value)}
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div className="grid gap-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Montant</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editableTransaction.montant}
                    onChange={(event) => handleEditChange('montant', event.target.value)}
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div className="grid gap-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Type</label>
                  <select
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                    value={editableTransaction.type}
                    onChange={(event) => handleEditChange('type', event.target.value)}
                  >
                    <option value="Entrée">Entrée</option>
                    <option value="Sortie">Sortie</option>
                  </select>
                </div>
                <div className="grid gap-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Mois</label>
                  <input
                    type="text"
                    value={editableTransaction.mois}
                    onChange={(event) => handleEditChange('mois', event.target.value)}
                    className="rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleEditCancel}
                    className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 hover:text-slate-900"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="rounded-full bg-blue-600 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white hover:bg-blue-700"
                  >
                    Sauvegarder
                  </button>
                </div>
              </form>
            ) : (
              <p className="text-sm text-slate-500">Cliquez sur "Modifier" dans un relevé pour ajuster une ligne.</p>
            )}
          </div>
        </section>
          </div>
        </div>
      </div>
      {expenseModal && (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-900/30 px-4 py-8">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Créer une charge depuis le relevé</h3>
              <button type="button" onClick={handleCloseExpenseModal} className="text-slate-400 hover:text-slate-600 text-sm font-semibold">
                Fermer
              </button>
            </div>
            <form onSubmit={handleExpenseSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-500">Libellé</label>
                <input
                  type="text"
                  value={expenseModal.form.libelle}
                  onChange={(e) => handleExpenseFieldChange('libelle', e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-slate-500">Date</label>
                  <input
                    type="date"
                    value={expenseModal.form.date_operation}
                    onChange={(e) => handleExpenseFieldChange('date_operation', e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">Montant HT (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={expenseModal.form.montant_ht}
                    onChange={(e) => handleExpenseFieldChange('montant_ht', e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-slate-500">Catégorie</label>
                  <select
                    value={expenseModal.form.categorie_id || ''}
                    onChange={(e) => handleExpenseFieldChange('categorie_id', e.target.value ? Number(e.target.value) : null)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  >
                    <option value="">(Aucune)</option>
                    {categoryOptions.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.nom}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">Centre de coûts</label>
                  <select
                    value={expenseModal.form.cost_center_id || ''}
                    onChange={(e) => handleExpenseFieldChange('cost_center_id', e.target.value ? Number(e.target.value) : null)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  >
                    <option value="">(Aucun)</option>
                    {costCenterOptions.map((center) => (
                      <option key={center.id} value={center.id}>
                        {center.nom}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-slate-500">TVA (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={expenseModal.form.tva_pct}
                    onChange={(e) => handleExpenseFieldChange('tva_pct', e.target.value ? Number(e.target.value) : 0)}
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">Fournisseur</label>
                  <input
                    type="number"
                    min="1"
                    value={expenseModal.form.fournisseur_id || ''}
                    onChange={(e) => handleExpenseFieldChange('fournisseur_id', e.target.value ? Number(e.target.value) : null)}
                    placeholder="ID fournisseur"
                    className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              {expenseError && <p className="text-xs font-semibold text-rose-600">{expenseError}</p>}
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={handleCloseExpenseModal}
                  className="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={createExpenseFromStatement.isLoading}
                  className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-700 disabled:opacity-50"
                >
                  {createExpenseFromStatement.isLoading ? 'Création...' : 'Créer la charge'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BankStatementAnalyzer;
