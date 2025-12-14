import { AlertTriangle, TrendingDown, Clock, XCircle } from 'lucide-react';
import Card, { CardHeader, CardContent } from '../../../components/ui/Card.jsx';
import Badge from '../../../components/ui/Badge.jsx';
import Button from '../../../components/ui/Button.jsx';

/**
 * SupplierAlertsWidget - Widget d'affichage des alertes fournisseurs
 */
export default function SupplierAlertsWidget({ suppliers = [], onSupplierClick }) {
  // Générer les alertes basées sur les scores
  const generateAlerts = () => {
    const alerts = [];

    suppliers.forEach((supplier) => {
      const score = (supplier.overall_score || 0) * 100;

      // Alerte score global faible
      if (score < 50) {
        alerts.push({
          id: `${supplier.name}-low-score`,
          supplier: supplier.name,
          severity: 'high',
          type: 'score',
          message: `Score global critique (${Math.round(score)}/100)`,
          icon: XCircle,
          color: 'rose',
        });
      } else if (score < 75) {
        alerts.push({
          id: `${supplier.name}-medium-score`,
          supplier: supplier.name,
          severity: 'medium',
          type: 'score',
          message: `Score global à surveiller (${Math.round(score)}/100)`,
          icon: AlertTriangle,
          color: 'amber',
        });
      }

      // Alerte tendance négative
      if (supplier.trend === 'declining') {
        alerts.push({
          id: `${supplier.name}-declining`,
          supplier: supplier.name,
          severity: 'medium',
          type: 'trend',
          message: 'Tendance en baisse',
          icon: TrendingDown,
          color: 'amber',
        });
      }

      // Alertes par dimension
      if ((supplier.price_stability_score || 0) * 100 < 50) {
        alerts.push({
          id: `${supplier.name}-price`,
          supplier: supplier.name,
          severity: 'high',
          type: 'dimension',
          message: 'Prix très instables',
          icon: AlertTriangle,
          color: 'rose',
        });
      }

      if ((supplier.delivery_reliability_score || 0) * 100 < 50) {
        alerts.push({
          id: `${supplier.name}-delivery`,
          supplier: supplier.name,
          severity: 'high',
          type: 'dimension',
          message: 'Livraisons non fiables',
          icon: Clock,
          color: 'rose',
        });
      }

      if ((supplier.invoice_accuracy_score || 0) * 100 < 50) {
        alerts.push({
          id: `${supplier.name}-invoice`,
          supplier: supplier.name,
          severity: 'medium',
          type: 'dimension',
          message: 'Erreurs fréquentes sur factures',
          icon: AlertTriangle,
          color: 'amber',
        });
      }
    });

    // Trier par sévérité
    return alerts.sort((a, b) => {
      const severityOrder = { high: 0, medium: 1, low: 2 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });
  };

  const alerts = generateAlerts();
  const criticalAlerts = alerts.filter((a) => a.severity === 'high');
  const warningAlerts = alerts.filter((a) => a.severity === 'medium');

  if (alerts.length === 0) {
    return (
      <Card padding="lg">
        <CardHeader
          title={
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-emerald-400" />
              <span>Alertes Fournisseurs</span>
            </div>
          }
        />
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mb-3">
              <svg
                className="h-6 w-6 text-emerald-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="font-medium text-white mb-1">Aucune alerte active</p>
            <p className="text-sm text-slate-400">
              Tous vos fournisseurs affichent de bonnes performances
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card padding="lg">
      <CardHeader
        title={
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            <span>Alertes Fournisseurs</span>
          </div>
        }
        action={
          <div className="flex items-center gap-2">
            {criticalAlerts.length > 0 && (
              <Badge variant="error-solid" size="sm">
                {criticalAlerts.length} critique{criticalAlerts.length > 1 ? 's' : ''}
              </Badge>
            )}
            {warningAlerts.length > 0 && (
              <Badge variant="warning-solid" size="sm">
                {warningAlerts.length} avertissement{warningAlerts.length > 1 ? 's' : ''}
              </Badge>
            )}
          </div>
        }
      />

      <CardContent>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {alerts.map((alert) => {
            const Icon = alert.icon;
            const bgColor =
              alert.color === 'rose'
                ? 'bg-rose-500/10'
                : alert.color === 'amber'
                  ? 'bg-amber-500/10'
                  : 'bg-blue-500/10';
            const borderColor =
              alert.color === 'rose'
                ? 'border-rose-500/20'
                : alert.color === 'amber'
                  ? 'border-amber-500/20'
                  : 'border-blue-500/20';
            const iconColor =
              alert.color === 'rose'
                ? 'text-rose-400'
                : alert.color === 'amber'
                  ? 'text-amber-400'
                  : 'text-blue-400';

            return (
              <div
                key={alert.id}
                className={`flex items-start gap-3 p-3 rounded-lg border ${bgColor} ${borderColor} hover:bg-white/5 transition-colors cursor-pointer`}
                onClick={() => {
                  const supplier = suppliers.find((s) => s.name === alert.supplier);
                  if (supplier) {
                    onSupplierClick?.(supplier);
                  }
                }}
              >
                <div className={`p-2 rounded-lg ${bgColor}`}>
                  <Icon className={`h-4 w-4 ${iconColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <p className="font-medium text-white text-sm">{alert.supplier}</p>
                    <Badge
                      variant={alert.severity === 'high' ? 'error' : 'warning'}
                      size="xs"
                    >
                      {alert.severity === 'high' ? 'Critique' : 'Attention'}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-400">{alert.message}</p>
                </div>
              </div>
            );
          })}
        </div>

        {alerts.length > 5 && (
          <div className="mt-4 pt-4 border-t border-white/10 text-center">
            <Button variant="ghost" size="sm">
              Voir toutes les alertes ({alerts.length})
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
