import { createContext, useContext, useMemo, useState } from 'react';
import { useNewCMSQuery } from '../hooks/useNewCMSQuery.js';
import { fetchOperationsOverview } from '../../api/newcms.js';

const TenantContext = createContext(null);

const DEFAULT_TENANTS = [
  { id: 1, name: 'Épicerie', slug: 'epicerie', color: 'emerald' },
  { id: 2, name: 'Restaurant', slug: 'restaurant', color: 'orange' },
  { id: 3, name: 'Intelligence', slug: 'intelligence', color: 'pink' },
];

export function TenantProvider({ children, initialTenantId = 2 }) {
  // On tente de récupérer les tenants depuis le backend (fallback sur défaut).
  const { data: tenantData } = useNewCMSQuery(
    ['newcms-tenants'],
    async () => {
      // Pas d'endpoint dédié : on réutilise l'overview opérations pour extraire les meta.tenants si présents.
      const data = await fetchOperationsOverview();
      return data?.meta?.tenants || [];
    },
    { staleTime: 5 * 60 * 1000, retry: 0 }
  );

  const [activeTenantId, setActiveTenantId] = useState(initialTenantId);

  const tenants = useMemo(() => {
    if (tenantData && tenantData.length > 0) {
      return tenantData.map((t) => ({
        id: t.id ?? t.tenant_id ?? t.tenantId,
        name: t.name ?? t.label ?? t.slug ?? `Tenant ${t.id}`,
        slug: t.slug ?? t.name?.toLowerCase?.().replace(/\s+/g, '-') ?? `tenant-${t.id}`,
        color: t.color ?? 'blue',
      }));
    }
    return DEFAULT_TENANTS;
  }, [tenantData]);

  const value = useMemo(() => {
    const activeTenant = tenants.find((t) => t.id === activeTenantId) || tenants[0];

    return {
      tenants,
      activeTenant,
      activeTenantId,
      switchTenant: setActiveTenantId,
    };
  }, [activeTenantId, tenants]);

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant() {
  const ctx = useContext(TenantContext);
  if (!ctx) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return ctx;
}
