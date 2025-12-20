# Exemples d'Intégration Frontend - newCMS Cockpit

Guide pratique pour intégrer les endpoints `/newcms/cockpit` dans votre frontend (React, Vue, Angular, etc.).

---

## 📦 Installation & Configuration

### 1. Client HTTP (Axios)
```javascript
// src/api/client.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor pour ajouter le token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor pour gérer les erreurs
apiClient.interceptors.response.use(
  (response) => response.data, // Retourne directement les données
  (error) => {
    if (error.response?.status === 401) {
      // Rediriger vers login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 🎣 React Hooks

### Hook: useMorningBrief
```javascript
// src/hooks/useMorningBrief.js
import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

export const useMorningBrief = (options = {}) => {
  const {
    daysForecast = 7,
    topAnomaliesLimit = 5,
    autoRefresh = true,
    refreshInterval = 60000, // 60s
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchBrief = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/newcms/cockpit', {
        params: {
          days_forecast: daysForecast,
          top_anomalies_limit: topAnomaliesLimit,
        },
      });

      if (response.success) {
        setData(response.data);
        setLastUpdate(new Date());
        setError(null);
      } else {
        throw new Error(response.error?.message || 'Erreur inconnue');
      }
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetch Morning Brief:', err);
    } finally {
      setLoading(false);
    }
  }, [daysForecast, topAnomaliesLimit]);

  // Fetch initial
  useEffect(() => {
    fetchBrief();
  }, [fetchBrief]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchBrief, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchBrief]);

  return {
    data,
    loading,
    error,
    lastUpdate,
    refetch: fetchBrief,
  };
};
```

### Hook: useCockpitActions
```javascript
// src/hooks/useCockpitActions.js
import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

export const useCockpitActions = (category = null) => {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchActions = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/newcms/cockpit/actions', {
        params: category ? { category } : {},
      });

      if (response.success) {
        setActions(response.data.actions || []);
        setError(null);
      } else {
        throw new Error(response.error?.message || 'Erreur inconnue');
      }
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetch actions:', err);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    fetchActions();
  }, [fetchActions]);

  return {
    actions,
    loading,
    error,
    refetch: fetchActions,
  };
};
```

---

## 🎨 Composants React

### Dashboard Morning Brief
```javascript
// src/components/MorningBriefDashboard.jsx
import React from 'react';
import { useMorningBrief } from '../hooks/useMorningBrief';
import KPICard from './KPICard';
import AlertsList from './AlertsList';
import AnomaliesList from './AnomaliesList';
import ForecastChart from './ForecastChart';
import SuggestionsList from './SuggestionsList';
import HealthScore from './HealthScore';

const MorningBriefDashboard = () => {
  const { data, loading, error, lastUpdate, refetch } = useMorningBrief({
    autoRefresh: true,
    refreshInterval: 60000, // 60s
  });

  if (loading && !data) {
    return <div className="loading">Chargement du Morning Brief...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>Erreur: {error}</p>
        <button onClick={refetch}>Réessayer</button>
      </div>
    );
  }

  return (
    <div className="morning-brief-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <h1>Morning Brief - {data.tenant_name}</h1>
        <div className="last-update">
          Dernière mise à jour: {lastUpdate?.toLocaleTimeString()}
        </div>
        <button onClick={refetch} className="btn-refresh">
          Actualiser
        </button>
      </header>

      {/* Health Score */}
      <HealthScore
        score={data.health_score}
        status={data.health_status}
      />

      {/* KPIs Grid */}
      <section className="kpis-grid">
        <KPICard kpi={data.kpis.stock_value} />
        <KPICard kpi={data.kpis.stock_alerts} />
        <KPICard kpi={data.kpis.margin_avg} />
        <KPICard kpi={data.kpis.cash_flow_7d} />
        <KPICard kpi={data.kpis.anomalies_count} />
        <KPICard kpi={data.kpis.match_rate} />
      </section>

      {/* Alerts */}
      <section className="alerts-section">
        <h2>
          Alertes ({data.alerts_summary.critical} critiques,{' '}
          {data.alerts_summary.warning} warnings)
        </h2>
        <AlertsList alerts={data.alerts} />
      </section>

      {/* Anomalies */}
      <section className="anomalies-section">
        <h2>Top Anomalies</h2>
        <AnomaliesList anomalies={data.top_anomalies} />
      </section>

      {/* Forecasts */}
      <section className="forecasts-section">
        <div className="forecast-grid">
          <div className="cashflow-forecast">
            <h2>Prévision Trésorerie (7j)</h2>
            <ForecastChart data={data.cash_flow_forecast_7d} />
          </div>
          <div className="stock-forecast">
            <h2>Stock en Épuisement</h2>
            <table>
              <thead>
                <tr>
                  <th>Produit</th>
                  <th>Stock</th>
                  <th>Jours restants</th>
                  <th>Recommandation</th>
                </tr>
              </thead>
              <tbody>
                {data.stock_depletion_forecast.map((item) => (
                  <tr key={item.product_id}>
                    <td>{item.product_name}</td>
                    <td>{item.current_stock}</td>
                    <td className="text-danger">
                      {item.days_until_depletion?.toFixed(1)}j
                    </td>
                    <td>
                      {new Date(item.recommended_reorder_date).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* AI Suggestions */}
      <section className="suggestions-section">
        <h2>Suggestions IA</h2>
        <SuggestionsList suggestions={data.ai_suggestions} />
      </section>
    </div>
  );
};

export default MorningBriefDashboard;
```

### KPI Card Component
```javascript
// src/components/KPICard.jsx
import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const KPICard = ({ kpi }) => {
  const getStatusColor = (status) => {
    const colors = {
      success: 'bg-green-100 text-green-800 border-green-300',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      error: 'bg-red-100 text-red-800 border-red-300',
      info: 'bg-blue-100 text-blue-800 border-blue-300',
    };
    return colors[status] || colors.info;
  };

  const getTrendIcon = (direction) => {
    if (direction === 'up') return <TrendingUp size={16} />;
    if (direction === 'down') return <TrendingDown size={16} />;
    return <Minus size={16} />;
  };

  return (
    <div className={`kpi-card border-l-4 p-4 rounded-lg ${getStatusColor(kpi.status)}`}>
      <div className="kpi-header flex justify-between items-start">
        <h3 className="text-sm font-medium">{kpi.label}</h3>
        {kpi.icon && <span className="kpi-icon">{/* Icône */}</span>}
      </div>

      <div className="kpi-value mt-2">
        <span className="text-3xl font-bold">
          {kpi.value.toLocaleString()}
        </span>
        {kpi.unit && <span className="text-lg ml-1">{kpi.unit}</span>}
      </div>

      {kpi.trend !== null && (
        <div className="kpi-trend flex items-center mt-2 text-sm">
          {getTrendIcon(kpi.trend_direction)}
          <span className="ml-1">
            {kpi.trend > 0 ? '+' : ''}{kpi.trend.toFixed(1)}%
          </span>
        </div>
      )}

      {kpi.description && (
        <p className="kpi-description text-xs mt-2 opacity-75">
          {kpi.description}
        </p>
      )}
    </div>
  );
};

export default KPICard;
```

### Actions Panel Component
```javascript
// src/components/ActionsPanel.jsx
import React from 'react';
import { useCockpitActions } from '../hooks/useCockpitActions';
import { AlertTriangle, AlertCircle, Lightbulb } from 'lucide-react';

const ActionsPanel = () => {
  const { actions, loading, error } = useCockpitActions();

  if (loading) return <div>Chargement...</div>;
  if (error) return <div>Erreur: {error}</div>;

  const getCategoryIcon = (category) => {
    const icons = {
      urgent: <AlertTriangle className="text-red-600" size={20} />,
      important: <AlertCircle className="text-orange-600" size={20} />,
      suggested: <Lightbulb className="text-blue-600" size={20} />,
    };
    return icons[category];
  };

  const groupedActions = {
    urgent: actions.filter((a) => a.category === 'urgent'),
    important: actions.filter((a) => a.category === 'important'),
    suggested: actions.filter((a) => a.category === 'suggested'),
  };

  return (
    <div className="actions-panel">
      <h2>Actions à Traiter</h2>

      {/* Urgent */}
      {groupedActions.urgent.length > 0 && (
        <section className="actions-section urgent">
          <h3 className="text-red-600 font-semibold">
            Urgent ({groupedActions.urgent.length})
          </h3>
          {groupedActions.urgent.map((action) => (
            <ActionCard key={action.id} action={action} />
          ))}
        </section>
      )}

      {/* Important */}
      {groupedActions.important.length > 0 && (
        <section className="actions-section important">
          <h3 className="text-orange-600 font-semibold">
            Important ({groupedActions.important.length})
          </h3>
          {groupedActions.important.map((action) => (
            <ActionCard key={action.id} action={action} />
          ))}
        </section>
      )}

      {/* Suggested */}
      {groupedActions.suggested.length > 0 && (
        <section className="actions-section suggested">
          <h3 className="text-blue-600 font-semibold">
            Suggestions ({groupedActions.suggested.length})
          </h3>
          {groupedActions.suggested.map((action) => (
            <ActionCard key={action.id} action={action} />
          ))}
        </section>
      )}

      {actions.length === 0 && (
        <div className="no-actions text-center py-8">
          <p className="text-gray-500">Aucune action en attente</p>
        </div>
      )}
    </div>
  );
};

const ActionCard = ({ action }) => {
  const handleAction = () => {
    // Rediriger vers l'URL d'action
    window.location.href = action.action_url;
  };

  return (
    <div className="action-card border rounded-lg p-4 mb-3 hover:shadow-md transition">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h4 className="font-semibold text-lg">{action.title}</h4>
          <p className="text-gray-600 text-sm mt-1">{action.description}</p>

          <div className="flex gap-4 mt-2 text-xs text-gray-500">
            {action.deadline && (
              <span>
                Deadline: {new Date(action.deadline).toLocaleDateString()}
              </span>
            )}
            {action.estimated_duration && (
              <span>Durée: {action.estimated_duration}</span>
            )}
          </div>
        </div>

        <button
          onClick={handleAction}
          className="btn btn-primary ml-4"
        >
          {action.action_label}
        </button>
      </div>
    </div>
  );
};

export default ActionsPanel;
```

---

## 🔄 Vue.js Composables

### Composable: useMorningBrief
```javascript
// src/composables/useMorningBrief.js
import { ref, onMounted, onUnmounted } from 'vue';
import apiClient from '../api/client';

export function useMorningBrief(options = {}) {
  const {
    daysForecast = 7,
    topAnomaliesLimit = 5,
    autoRefresh = true,
    refreshInterval = 60000,
  } = options;

  const data = ref(null);
  const loading = ref(true);
  const error = ref(null);
  const lastUpdate = ref(null);

  let intervalId = null;

  const fetchBrief = async () => {
    try {
      loading.value = true;
      const response = await apiClient.get('/newcms/cockpit', {
        params: {
          days_forecast: daysForecast,
          top_anomalies_limit: topAnomaliesLimit,
        },
      });

      if (response.success) {
        data.value = response.data;
        lastUpdate.value = new Date();
        error.value = null;
      } else {
        throw new Error(response.error?.message || 'Erreur inconnue');
      }
    } catch (err) {
      error.value = err.message;
      console.error('Erreur fetch Morning Brief:', err);
    } finally {
      loading.value = false;
    }
  };

  onMounted(() => {
    fetchBrief();

    if (autoRefresh) {
      intervalId = setInterval(fetchBrief, refreshInterval);
    }
  });

  onUnmounted(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });

  return {
    data,
    loading,
    error,
    lastUpdate,
    refetch: fetchBrief,
  };
}
```

---

## 📱 Exemple Vanilla JavaScript

### Fetch Simple
```javascript
// Authentification
async function login(username, password) {
  const response = await fetch('http://localhost:8000/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password }),
  });

  const data = await response.json();
  if (data.success) {
    localStorage.setItem('access_token', data.data.access_token);
    return data.data.access_token;
  }
  throw new Error(data.error?.message || 'Authentification échouée');
}

// Fetch Morning Brief
async function fetchMorningBrief() {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/newcms/cockpit', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  const result = await response.json();

  if (result.success) {
    return result.data;
  }
  throw new Error(result.error?.message || 'Erreur inconnue');
}

// Utilisation
(async () => {
  try {
    const data = await fetchMorningBrief();
    console.log('Morning Brief:', data);

    // Afficher les KPIs
    console.log('KPIs:', {
      stock_value: data.kpis.stock_value.value,
      alerts: data.kpis.stock_alerts.value,
      margin: data.kpis.margin_avg.value,
    });

    // Afficher les alertes critiques
    const criticalAlerts = data.alerts.filter(a => a.severity === 'critical');
    console.log('Alertes critiques:', criticalAlerts);
  } catch (err) {
    console.error('Erreur:', err);
  }
})();
```

---

## 🎯 Patterns d'Utilisation

### 1. Dashboard Principal
```javascript
// Afficher le Morning Brief complet au chargement
const MorningBriefPage = () => {
  const { data } = useMorningBrief({ autoRefresh: true });

  return <MorningBriefDashboard data={data} />;
};
```

### 2. Widget KPIs
```javascript
// Widget compact avec KPIs uniquement
const KPIsWidget = () => {
  const { data } = useMorningBrief({ autoRefresh: false });

  if (!data) return null;

  return (
    <div className="kpis-widget">
      {Object.values(data.kpis).map((kpi) => (
        <KPICard key={kpi.key} kpi={kpi} compact />
      ))}
    </div>
  );
};
```

### 3. Notification d'Alertes
```javascript
// Notifier l'utilisateur des alertes critiques
const AlertsNotifier = () => {
  const { data } = useMorningBrief();

  useEffect(() => {
    if (!data) return;

    const critical = data.alerts.filter(a => a.severity === 'critical');
    if (critical.length > 0) {
      // Afficher notification
      showNotification({
        title: `${critical.length} alerte(s) critique(s)`,
        message: critical[0].message,
        type: 'error',
      });
    }
  }, [data]);

  return null;
};
```

---

## 🔔 Exemples de Notifications

### Browser Notifications
```javascript
// Demander permission
if ('Notification' in window) {
  Notification.requestPermission();
}

// Notifier lors d'une alerte critique
useEffect(() => {
  if (!data?.alerts) return;

  const critical = data.alerts.filter(a => a.severity === 'critical');

  if (critical.length > 0 && Notification.permission === 'granted') {
    new Notification('Morning Brief - Alerte Critique', {
      body: critical[0].message,
      icon: '/icon-alert.png',
      tag: 'morning-brief',
    });
  }
}, [data]);
```

---

## 📊 Exemples de Graphiques

### Chart.js - Cash Flow Forecast
```javascript
import { Line } from 'react-chartjs-2';

const CashFlowChart = ({ forecast }) => {
  const data = {
    labels: forecast.predictions.map(p => p.date),
    datasets: [
      {
        label: 'Flux Net',
        data: forecast.predictions.map(p => p.value),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
      },
      {
        label: 'Intervalle de confiance',
        data: forecast.predictions.map(p => p.upper_bound),
        borderColor: 'rgba(59, 130, 246, 0.3)',
        borderDash: [5, 5],
        fill: false,
      },
    ],
  };

  return <Line data={data} options={{ responsive: true }} />;
};
```

---

## 🧪 Tests Unitaires

### Jest + React Testing Library
```javascript
// MorningBriefDashboard.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import MorningBriefDashboard from './MorningBriefDashboard';
import { useMorningBrief } from '../hooks/useMorningBrief';

jest.mock('../hooks/useMorningBrief');

describe('MorningBriefDashboard', () => {
  it('affiche les KPIs', async () => {
    const mockData = {
      kpis: {
        stock_value: { key: 'stock_value', label: 'Valeur Stock', value: 15234.50 },
        // ... autres KPIs
      },
      alerts: [],
      // ... autres données
    };

    useMorningBrief.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
    });

    render(<MorningBriefDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Valeur Stock')).toBeInTheDocument();
      expect(screen.getByText('15234.50')).toBeInTheDocument();
    });
  });
});
```

---

**Fichiers à créer dans votre frontend:**
- `src/api/client.js` - Client HTTP
- `src/hooks/useMorningBrief.js` - Hook React
- `src/hooks/useCockpitActions.js` - Hook actions
- `src/components/MorningBriefDashboard.jsx` - Dashboard principal
- `src/components/KPICard.jsx` - Card KPI
- `src/components/ActionsPanel.jsx` - Panel actions

**Documentation complète:** `backend/api/newcms/COCKPIT_ENDPOINTS.md`
