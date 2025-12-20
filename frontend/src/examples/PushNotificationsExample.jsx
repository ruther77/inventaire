import React, { useEffect } from 'react';
import { usePushNotifications } from '../hooks';
import { NotificationPermissionButton } from '../components/pwa';

/**
 * Exemple d'intégration des notifications push dans l'application
 *
 * Ce fichier montre plusieurs cas d'usage pratiques pour l'application
 * Inventaire Épicerie.
 */

/**
 * Exemple 1: Intégration dans une page de paramètres
 */
export function SettingsPageExample() {
  const handleSubscriptionChange = async (subscription) => {
    if (subscription) {
      try {
        // Envoyer la souscription au backend
        const response = await fetch('/api/push/subscribe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(subscription),
        });

        if (response.ok) {
          console.log('Souscription sauvegardée avec succès');
        }
      } catch (error) {
        console.error('Erreur lors de la sauvegarde de la souscription:', error);
      }
    } else {
      // L'utilisateur s'est désabonné
      console.log('Utilisateur désabonné');
    }
  };

  return (
    <div className="settings-page">
      <h1>Paramètres</h1>

      <section className="settings-section">
        <h2>Notifications</h2>
        <p className="description">
          Recevez des alertes pour les anomalies, nouvelles factures, et rappels importants.
        </p>

        <NotificationPermissionButton
          variant="full"
          onSubscriptionChange={handleSubscriptionChange}
        />
      </section>
    </div>
  );
}

/**
 * Exemple 2: Bouton compact dans la barre de navigation
 */
export function NavbarWithNotifications() {
  const { isSubscribed } = usePushNotifications();

  return (
    <nav className="navbar">
      <div className="navbar-brand">Inventaire Épicerie</div>

      <div className="navbar-actions">
        {/* Autres boutons de navigation */}
        <button className="nav-button">Tableau de bord</button>
        <button className="nav-button">Factures</button>

        {/* Bouton de notifications */}
        <NotificationPermissionButton variant="compact" />

        {/* Indicateur visuel si souscrit */}
        {isSubscribed && (
          <span className="notification-badge">Notifications ON</span>
        )}
      </div>
    </nav>
  );
}

/**
 * Exemple 3: Auto-souscription pour les utilisateurs premium
 */
export function PremiumUserAutoSubscribe({ user }) {
  const { isSubscribed, subscribe, permission } = usePushNotifications();

  useEffect(() => {
    // Si l'utilisateur est premium et n'est pas encore souscrit
    if (user.isPremium && !isSubscribed && permission !== 'denied') {
      // Proposer automatiquement les notifications
      const timer = setTimeout(() => {
        showNotificationPrompt();
      }, 5000); // Attendre 5 secondes après le chargement

      return () => clearTimeout(timer);
    }
  }, [user.isPremium, isSubscribed, permission]);

  const showNotificationPrompt = async () => {
    if (window.confirm('Activer les notifications pour ne rien manquer ?')) {
      const result = await subscribe();
      if (result.success) {
        // Envoyer au backend
        await fetch('/api/push/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(result.subscription),
        });
      }
    }
  };

  return null; // Ce composant ne rend rien visuellement
}

/**
 * Exemple 4: Gestion conditionnelle des notifications par type
 */
export function NotificationPreferencesForm() {
  const { isSubscribed, subscribe, unsubscribe } = usePushNotifications();
  const [preferences, setPreferences] = React.useState({
    anomalies: true,
    invoices: true,
    stock: false,
    reminders: true,
  });

  const handlePreferenceChange = async (type, enabled) => {
    setPreferences(prev => ({ ...prev, [type]: enabled }));

    // Envoyer les préférences au backend
    await fetch('/api/push/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [type]: enabled }),
    });
  };

  return (
    <div className="notification-preferences">
      <h3>Types de notifications</h3>

      {!isSubscribed ? (
        <div className="subscribe-prompt">
          <p>Activez les notifications pour personnaliser vos préférences</p>
          <button onClick={subscribe}>Activer</button>
        </div>
      ) : (
        <div className="preferences-list">
          <label>
            <input
              type="checkbox"
              checked={preferences.anomalies}
              onChange={(e) => handlePreferenceChange('anomalies', e.target.checked)}
            />
            Anomalies financières
          </label>

          <label>
            <input
              type="checkbox"
              checked={preferences.invoices}
              onChange={(e) => handlePreferenceChange('invoices', e.target.checked)}
            />
            Nouvelles factures
          </label>

          <label>
            <input
              type="checkbox"
              checked={preferences.stock}
              onChange={(e) => handlePreferenceChange('stock', e.target.checked)}
            />
            Alertes de stock
          </label>

          <label>
            <input
              type="checkbox"
              checked={preferences.reminders}
              onChange={(e) => handlePreferenceChange('reminders', e.target.checked)}
            />
            Rappels
          </label>

          <button onClick={unsubscribe} className="unsubscribe-button">
            Désactiver toutes les notifications
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Exemple 5: Notification lors d'événements spécifiques
 */
export function useNotifyOnAnomaly() {
  const { isSubscribed, sendTestNotification } = usePushNotifications();

  const notifyAnomaly = async (anomaly) => {
    if (!isSubscribed) {
      console.log('Utilisateur non souscrit aux notifications');
      return;
    }

    // En production, le backend enverrait la vraie notification
    // Ici, on utilise une notification de test pour la démo
    await sendTestNotification();

    // En production :
    // await fetch('/api/push/send', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     title: 'Anomalie détectée',
    //     body: `${anomaly.type}: ${anomaly.description}`,
    //     url: `/intelligence/anomalies/${anomaly.id}`,
    //     tag: `anomaly-${anomaly.id}`,
    //     data: { anomalyId: anomaly.id },
    //   }),
    // });
  };

  return { notifyAnomaly };
}

/**
 * Exemple 6: Hook personnalisé pour gérer les notifications de l'app
 */
export function useAppNotifications() {
  const push = usePushNotifications();

  const notifyNewInvoice = async (invoice) => {
    if (!push.isSubscribed) return;

    await fetch('/api/push/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Nouvelle facture',
        body: `Facture ${invoice.number} - ${invoice.amount}€`,
        url: `/invoices/${invoice.id}`,
        tag: `invoice-${invoice.id}`,
      }),
    });
  };

  const notifyLowStock = async (ingredient) => {
    if (!push.isSubscribed) return;

    await fetch('/api/push/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Stock faible',
        body: `${ingredient.name}: ${ingredient.quantity} unités restantes`,
        url: '/restaurant/ingredients',
        tag: `stock-${ingredient.id}`,
        requireInteraction: true,
      }),
    });
  };

  const notifyReminder = async (reminder) => {
    if (!push.isSubscribed) return;

    await fetch('/api/push/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: reminder.title,
        body: reminder.message,
        url: reminder.url || '/',
        tag: `reminder-${reminder.id}`,
      }),
    });
  };

  return {
    ...push,
    notifyNewInvoice,
    notifyLowStock,
    notifyReminder,
  };
}

/**
 * Exemple 7: Composant avec toast pour confirmer la souscription
 */
export function NotificationButtonWithToast() {
  const [showToast, setShowToast] = React.useState(false);
  const [toastMessage, setToastMessage] = React.useState('');

  const handleSubscriptionChange = (subscription) => {
    if (subscription) {
      setToastMessage('Notifications activées avec succès!');
    } else {
      setToastMessage('Notifications désactivées');
    }
    setShowToast(true);

    // Auto-hide après 3 secondes
    setTimeout(() => setShowToast(false), 3000);
  };

  return (
    <>
      <NotificationPermissionButton
        variant="full"
        onSubscriptionChange={handleSubscriptionChange}
      />

      {showToast && (
        <div className="toast-notification">
          {toastMessage}
        </div>
      )}

      <style jsx>{`
        .toast-notification {
          position: fixed;
          bottom: 24px;
          right: 24px;
          padding: 16px 24px;
          background: #10b981;
          color: white;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
}

/**
 * Exemple 8: Intégration dans le Dashboard
 */
export function DashboardWithNotifications() {
  const { isSupported, isSubscribed, subscribe } = usePushNotifications();

  return (
    <div className="dashboard">
      <h1>Tableau de bord</h1>

      {/* Banner pour encourager l'activation des notifications */}
      {isSupported && !isSubscribed && (
        <div className="notification-banner">
          <div className="banner-content">
            <span className="banner-icon">🔔</span>
            <div className="banner-text">
              <strong>Restez informé</strong>
              <p>Activez les notifications pour recevoir des alertes en temps réel</p>
            </div>
          </div>
          <button onClick={subscribe} className="banner-button">
            Activer
          </button>
        </div>
      )}

      {/* Reste du dashboard */}
      <div className="dashboard-content">
        {/* ... */}
      </div>

      <style jsx>{`
        .notification-banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 12px;
          margin-bottom: 24px;
        }

        .banner-content {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .banner-icon {
          font-size: 32px;
        }

        .banner-text strong {
          display: block;
          font-size: 18px;
          margin-bottom: 4px;
        }

        .banner-text p {
          margin: 0;
          opacity: 0.9;
          font-size: 14px;
        }

        .banner-button {
          padding: 10px 24px;
          background: white;
          color: #667eea;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .banner-button:hover {
          transform: scale(1.05);
        }
      `}</style>
    </div>
  );
}

// Exports pour utilisation dans l'app
export default {
  SettingsPageExample,
  NavbarWithNotifications,
  PremiumUserAutoSubscribe,
  NotificationPreferencesForm,
  useNotifyOnAnomaly,
  useAppNotifications,
  NotificationButtonWithToast,
  DashboardWithNotifications,
};
