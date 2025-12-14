import { AlertTriangle, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardContent, Badge } from '@/components/ui';

/**
 * RestaurantAlertsWidget - Widget d'alertes restaurant
 *
 * Props:
 * - alerts: Array<{
 *     id, type, severity, title, description, plat_id, ingredient_id, value
 *   }>
 * - isLoading: boolean
 */
export default function RestaurantAlertsWidget({ alerts = [], isLoading = false }) {
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-rose-600" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-amber-600" />;
      case 'info':
        return <CheckCircle className="w-4 h-4 text-blue-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'rose';
      case 'warning':
        return 'amber';
      case 'info':
        return 'blue';
      default:
        return 'slate';
    }
  };

  const getAlertTypeLabel = (type) => {
    switch (type) {
      case 'low_margin':
        return 'Marge faible';
      case 'high_food_cost':
        return 'Food cost élevé';
      case 'price_increase':
        return 'Hausse prix';
      case 'stock_alert':
        return 'Stock critique';
      case 'rupture':
        return 'Rupture prévue';
      default:
        return 'Alerte';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-semibold text-slate-900">Alertes en temps réel</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-500" />
            <h3 className="text-lg font-semibold text-slate-900">Alertes en temps réel</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center gap-3 py-8 text-center">
            <CheckCircle className="w-12 h-12 text-emerald-500" />
            <p className="text-sm text-slate-600">Aucune alerte pour le moment</p>
            <p className="text-xs text-slate-400">Tout fonctionne normalement</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Grouper les alertes par sévérité
  const criticalAlerts = alerts.filter(a => a.severity === 'critical');
  const warningAlerts = alerts.filter(a => a.severity === 'warning');
  const infoAlerts = alerts.filter(a => a.severity === 'info');

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-semibold text-slate-900">Alertes en temps réel</h3>
          </div>
          <div className="flex items-center gap-2">
            {criticalAlerts.length > 0 && (
              <Badge variant="danger" size="sm">
                {criticalAlerts.length} critique{criticalAlerts.length > 1 ? 's' : ''}
              </Badge>
            )}
            {warningAlerts.length > 0 && (
              <Badge variant="warning" size="sm">
                {warningAlerts.length}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {alerts.map((alert) => {
            const color = getSeverityColor(alert.severity);
            return (
              <div
                key={alert.id}
                className={`rounded-lg border border-${color}-200 bg-${color}-50/30 p-3 transition-all hover:shadow-sm`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {getSeverityIcon(alert.severity)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-sm font-semibold text-slate-900">{alert.title}</p>
                      <Badge variant={alert.severity === 'critical' ? 'danger' : 'warning'} size="xs">
                        {getAlertTypeLabel(alert.type)}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 mb-2">{alert.description}</p>
                    {alert.value && (
                      <div className="flex items-center gap-2">
                        <TrendingUp className={`w-3 h-3 text-${color}-600`} />
                        <p className={`text-xs font-semibold text-${color}-700`}>{alert.value}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
