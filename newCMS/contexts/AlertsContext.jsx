import { createContext, useContext, useMemo, useState } from 'react';

const AlertsContext = createContext(null);

const seedAlerts = [
  { id: 'alt-001', level: 'critical', title: 'Rupture Tomates', category: 'Stock', time: 'Il y a 15 min' },
  { id: 'alt-002', level: 'warning', title: 'Factures Metro en attente', category: 'Finance', time: 'Il y a 2h' },
  { id: 'alt-003', level: 'info', title: 'Prévision cash demain', category: 'Cockpit', time: 'Aujourd’hui' },
];

export function AlertsProvider({ children, initialAlerts = seedAlerts }) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [acknowledged, setAcknowledged] = useState(new Set());

  const value = useMemo(() => {
    const unread = alerts.filter((alert) => !acknowledged.has(alert.id));
    return {
      alerts,
      unreadCount: unread.length,
      acknowledge: (id) =>
        setAcknowledged((prev) => {
          const next = new Set(prev);
          next.add(id);
          return next;
        }),
      pushAlert: (alert) => setAlerts((prev) => [{ ...alert }, ...prev]),
    };
  }, [alerts, acknowledged]);

  return <AlertsContext.Provider value={value}>{children}</AlertsContext.Provider>;
}

export function useAlerts() {
  const ctx = useContext(AlertsContext);
  if (!ctx) {
    throw new Error('useAlerts must be used within an AlertsProvider');
  }
  return ctx;
}
