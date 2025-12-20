import React from 'react';
import { NotificationPermissionButton } from './NotificationPermissionButton.jsx';
import { usePushNotifications } from '../../hooks';

/**
 * Composant de démonstration pour les notifications push
 *
 * Ce composant montre comment utiliser le hook usePushNotifications
 * et le composant NotificationPermissionButton dans votre application.
 *
 * Fonctionnalités démontrées:
 * - Affichage du statut des notifications
 * - Boutons compacts et complets
 * - Gestion de la souscription
 * - Envoi de notifications de test
 * - Affichage des informations de souscription
 */
export function PushNotificationsDemo() {
  const {
    permission,
    isSupported,
    isSubscribed,
    isLoading,
    error,
    getSubscriptionInfo,
  } = usePushNotifications();

  const handleSubscriptionChange = (subscription) => {
    console.log('Souscription changée:', subscription);
    // Ici, vous pourriez envoyer la souscription à votre backend
    // await api.savePushSubscription(subscription);
  };

  return (
    <div className="push-notifications-demo">
      <h1>Démonstration des Notifications Push</h1>

      <div className="demo-section">
        <h2>Statut actuel</h2>
        <div className="status-grid">
          <div className="status-item">
            <span className="status-label">Support:</span>
            <span className={`status-value ${isSupported ? 'success' : 'error'}`}>
              {isSupported ? 'Supporté' : 'Non supporté'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Permission:</span>
            <span className={`status-value ${permission === 'granted' ? 'success' : permission === 'denied' ? 'error' : 'warning'}`}>
              {permission}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Souscription:</span>
            <span className={`status-value ${isSubscribed ? 'success' : 'warning'}`}>
              {isSubscribed ? 'Actif' : 'Inactif'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Chargement:</span>
            <span className={`status-value ${isLoading ? 'warning' : ''}`}>
              {isLoading ? 'En cours...' : 'Prêt'}
            </span>
          </div>
        </div>

        {error && (
          <div className="error-message">
            Erreur: {error.message || String(error)}
          </div>
        )}
      </div>

      <div className="demo-section">
        <h2>Bouton compact</h2>
        <p className="section-description">
          Idéal pour les barres d'outils et les menus
        </p>
        <NotificationPermissionButton
          variant="compact"
          onSubscriptionChange={handleSubscriptionChange}
        />
      </div>

      <div className="demo-section">
        <h2>Bouton complet</h2>
        <p className="section-description">
          Avec détails et options avancées
        </p>
        <NotificationPermissionButton
          variant="full"
          onSubscriptionChange={handleSubscriptionChange}
        />
      </div>

      {isSubscribed && getSubscriptionInfo() && (
        <div className="demo-section">
          <h2>Informations de souscription</h2>
          <div className="subscription-info">
            <pre>{JSON.stringify(getSubscriptionInfo(), null, 2)}</pre>
          </div>
          <p className="info-note">
            Ces informations doivent être envoyées à votre backend pour pouvoir
            envoyer des notifications push à cet utilisateur.
          </p>
        </div>
      )}

      <div className="demo-section">
        <h2>Exemple d'utilisation dans le code</h2>
        <div className="code-example">
          <pre>{`import React from 'react';
import { NotificationPermissionButton } from '@/components/pwa';
import { usePushNotifications } from '@/hooks';

function MyComponent() {
  const { isSubscribed, subscribe } = usePushNotifications();

  const handleSubscriptionChange = async (subscription) => {
    if (subscription) {
      // Envoyer au backend
      await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription),
      });
    }
  };

  return (
    <div>
      {/* Bouton compact */}
      <NotificationPermissionButton
        variant="compact"
        onSubscriptionChange={handleSubscriptionChange}
      />

      {/* Ou bouton complet */}
      <NotificationPermissionButton
        variant="full"
        onSubscriptionChange={handleSubscriptionChange}
      />

      {/* Ou utilisation directe du hook */}
      {!isSubscribed && (
        <button onClick={subscribe}>
          Activer les notifications
        </button>
      )}
    </div>
  );
}`}</pre>
        </div>
      </div>

      <div className="demo-section">
        <h2>Configuration backend requise</h2>
        <div className="backend-info">
          <h3>1. Générer les clés VAPID</h3>
          <pre>npm install web-push --save-dev
npx web-push generate-vapid-keys</pre>

          <h3>2. Configurer la clé publique</h3>
          <p>
            Remplacez la clé VAPID_PUBLIC_KEY dans{' '}
            <code>/frontend/src/hooks/usePushNotifications.js</code> par votre
            clé publique générée.
          </p>

          <h3>3. Endpoint backend pour recevoir les souscriptions</h3>
          <pre>{`POST /api/push/subscribe
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}`}</pre>

          <h3>4. Endpoint backend pour envoyer des notifications</h3>
          <pre>{`// Exemple Node.js avec web-push
const webpush = require('web-push');

webpush.setVapidDetails(
  'mailto:your-email@example.com',
  process.env.VAPID_PUBLIC_KEY,
  process.env.VAPID_PRIVATE_KEY
);

// Envoyer une notification
await webpush.sendNotification(
  subscription,
  JSON.stringify({
    title: 'Nouvelle facture',
    body: 'Une nouvelle facture a été créée',
    icon: '/icon-192.png',
    url: '/invoices/123',
    tag: 'invoice-123'
  })
);`}</pre>
        </div>
      </div>

      <style jsx>{`
        .push-notifications-demo {
          max-width: 1200px;
          margin: 0 auto;
          padding: 40px 20px;
        }

        h1 {
          font-size: 32px;
          font-weight: 700;
          margin-bottom: 40px;
          color: var(--text-primary, #1a1a1a);
        }

        h2 {
          font-size: 24px;
          font-weight: 600;
          margin-bottom: 16px;
          color: var(--text-primary, #1a1a1a);
        }

        h3 {
          font-size: 18px;
          font-weight: 600;
          margin: 24px 0 12px 0;
          color: var(--text-primary, #1a1a1a);
        }

        .demo-section {
          background: var(--card-bg, white);
          border: 1px solid var(--border-color, #e0e0e0);
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 24px;
        }

        .section-description {
          color: var(--text-secondary, #666);
          margin-bottom: 16px;
        }

        .status-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 16px;
        }

        .status-item {
          display: flex;
          justify-content: space-between;
          padding: 12px 16px;
          background: var(--bg-secondary, #f9fafb);
          border-radius: 8px;
        }

        .status-label {
          font-weight: 500;
          color: var(--text-secondary, #666);
        }

        .status-value {
          font-weight: 600;
        }

        .status-value.success {
          color: #059669;
        }

        .status-value.error {
          color: #dc2626;
        }

        .status-value.warning {
          color: #d97706;
        }

        .error-message {
          padding: 12px 16px;
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fca5a5;
          border-radius: 8px;
          font-size: 14px;
        }

        .subscription-info {
          background: var(--bg-secondary, #f9fafb);
          border-radius: 8px;
          padding: 16px;
          overflow-x: auto;
        }

        .subscription-info pre {
          margin: 0;
          font-size: 12px;
          font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
          color: var(--text-primary, #1a1a1a);
        }

        .info-note {
          margin-top: 12px;
          padding: 12px 16px;
          background: #dbeafe;
          border: 1px solid #3b82f6;
          border-radius: 8px;
          font-size: 14px;
          color: #1e40af;
        }

        .code-example {
          background: #1e293b;
          border-radius: 8px;
          padding: 20px;
          overflow-x: auto;
        }

        .code-example pre {
          margin: 0;
          font-size: 14px;
          font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
          color: #e2e8f0;
          line-height: 1.6;
        }

        .backend-info {
          background: var(--bg-secondary, #f9fafb);
          border-radius: 8px;
          padding: 20px;
        }

        .backend-info pre {
          background: #1e293b;
          color: #e2e8f0;
          padding: 16px;
          border-radius: 6px;
          overflow-x: auto;
          font-size: 13px;
          font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
          line-height: 1.5;
        }

        .backend-info code {
          background: #1e293b;
          color: #e2e8f0;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 13px;
          font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
        }

        .backend-info p {
          color: var(--text-secondary, #666);
          line-height: 1.6;
        }
      `}</style>
    </div>
  );
}

export default PushNotificationsDemo;
