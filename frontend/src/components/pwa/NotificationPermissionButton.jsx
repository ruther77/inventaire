import React, { useState } from 'react';
import { usePushNotifications } from '../../hooks';

/**
 * Composant bouton pour gérer les permissions et souscriptions aux notifications push
 *
 * Fonctionnalités:
 * - Affiche l'état actuel de la permission et de la souscription
 * - Permet de demander la permission
 * - Permet de s'abonner/se désabonner
 * - Affiche une notification de test
 * - Gère les états de chargement et d'erreur
 *
 * @param {Object} props - Props du composant
 * @param {string} props.variant - Variante de style ('compact' | 'full')
 * @param {Function} props.onSubscriptionChange - Callback appelé quand la souscription change
 */
export function NotificationPermissionButton({
  variant = 'full',
  onSubscriptionChange,
  className = '',
}) {
  const {
    permission,
    isLoading,
    error,
    isSupported,
    isSubscribed,
    requestPermission,
    subscribe,
    unsubscribe,
    sendTestNotification,
    getSubscriptionInfo,
  } = usePushNotifications();

  const [showDetails, setShowDetails] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  /**
   * Gère le clic sur le bouton principal
   */
  const handleMainAction = async () => {
    setActionMessage('');

    if (!isSupported) {
      setActionMessage('Les notifications push ne sont pas supportées sur cet appareil');
      return;
    }

    if (permission === 'denied') {
      setActionMessage('Permission refusée. Veuillez l\'activer dans les paramètres du navigateur.');
      return;
    }

    if (!isSubscribed) {
      // Demande permission et souscription
      const result = await subscribe();
      if (result.success) {
        setActionMessage('Notifications activées avec succès');
        onSubscriptionChange?.(result.subscription);
      } else {
        setActionMessage(`Erreur: ${result.error}`);
      }
    } else {
      // Désabonnement
      const result = await unsubscribe();
      if (result.success) {
        setActionMessage('Notifications désactivées');
        onSubscriptionChange?.(null);
      } else {
        setActionMessage(`Erreur: ${result.error}`);
      }
    }
  };

  /**
   * Envoie une notification de test
   */
  const handleTestNotification = async () => {
    setActionMessage('');
    const result = await sendTestNotification();
    if (result.success) {
      setActionMessage('Notification de test envoyée');
    } else {
      setActionMessage(`Erreur: ${result.error}`);
    }
  };

  /**
   * Obtient le texte du bouton principal selon l'état
   */
  const getButtonText = () => {
    if (isLoading) return 'Chargement...';
    if (!isSupported) return 'Non supporté';
    if (permission === 'denied') return 'Permission refusée';
    if (isSubscribed) return 'Désactiver les notifications';
    if (permission === 'granted') return 'Activer les notifications';
    return 'Autoriser les notifications';
  };

  /**
   * Obtient l'icône selon l'état
   */
  const getIcon = () => {
    if (!isSupported) return '🚫';
    if (permission === 'denied') return '🔕';
    if (isSubscribed) return '🔔';
    if (permission === 'granted') return '🔔';
    return '🔔';
  };

  /**
   * Obtient le statut en texte
   */
  const getStatusText = () => {
    if (!isSupported) return 'Non supporté';
    if (permission === 'denied') return 'Refusée';
    if (isSubscribed) return 'Activées';
    if (permission === 'granted') return 'Autorisées (non souscrit)';
    if (permission === 'default') return 'Non demandée';
    return 'Inconnu';
  };

  // Rendu compact
  if (variant === 'compact') {
    return (
      <div className={`notification-permission-compact ${className}`}>
        <button
          onClick={handleMainAction}
          disabled={isLoading || !isSupported || permission === 'denied'}
          className="notification-button-compact"
          title={getStatusText()}
        >
          <span className="notification-icon">{getIcon()}</span>
        </button>

        {actionMessage && (
          <div className="notification-message-compact">{actionMessage}</div>
        )}

        <style jsx>{`
          .notification-permission-compact {
            display: inline-flex;
            align-items: center;
            gap: 8px;
          }

          .notification-button-compact {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 2px solid var(--border-color, #e0e0e0);
            background: var(--bg-color, white);
            cursor: pointer;
            transition: all 0.2s ease;
          }

          .notification-button-compact:hover:not(:disabled) {
            background: var(--hover-bg, #f5f5f5);
            border-color: var(--primary-color, #2563eb);
            transform: scale(1.05);
          }

          .notification-button-compact:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .notification-icon {
            font-size: 20px;
          }

          .notification-message-compact {
            font-size: 12px;
            color: var(--text-secondary, #666);
            max-width: 200px;
          }
        `}</style>
      </div>
    );
  }

  // Rendu complet
  return (
    <div className={`notification-permission-full ${className}`}>
      <div className="notification-header">
        <div className="notification-status">
          <span className="notification-icon-large">{getIcon()}</span>
          <div className="notification-info">
            <h3>Notifications Push</h3>
            <p className="status-text">Statut: {getStatusText()}</p>
          </div>
        </div>
      </div>

      <div className="notification-actions">
        <button
          onClick={handleMainAction}
          disabled={isLoading || !isSupported || permission === 'denied'}
          className="notification-button-primary"
        >
          {getButtonText()}
        </button>

        {isSubscribed && (
          <button
            onClick={handleTestNotification}
            disabled={isLoading}
            className="notification-button-secondary"
          >
            Tester
          </button>
        )}

        <button
          onClick={() => setShowDetails(!showDetails)}
          className="notification-button-details"
        >
          {showDetails ? 'Masquer les détails' : 'Voir les détails'}
        </button>
      </div>

      {actionMessage && (
        <div className={`notification-message ${error ? 'error' : 'success'}`}>
          {actionMessage}
        </div>
      )}

      {showDetails && (
        <div className="notification-details">
          <div className="detail-row">
            <span className="detail-label">Support:</span>
            <span className="detail-value">{isSupported ? 'Oui' : 'Non'}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Permission:</span>
            <span className="detail-value">{permission}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Souscrit:</span>
            <span className="detail-value">{isSubscribed ? 'Oui' : 'Non'}</span>
          </div>
          {isSubscribed && getSubscriptionInfo() && (
            <>
              <div className="detail-row">
                <span className="detail-label">Endpoint:</span>
                <span className="detail-value truncate">
                  {getSubscriptionInfo().endpoint}
                </span>
              </div>
            </>
          )}
        </div>
      )}

      {permission === 'denied' && (
        <div className="notification-help">
          Pour activer les notifications, vous devez modifier les paramètres de votre
          navigateur. Consultez l'aide de votre navigateur pour plus d'informations.
        </div>
      )}

      <style jsx>{`
        .notification-permission-full {
          background: var(--card-bg, white);
          border: 1px solid var(--border-color, #e0e0e0);
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .notification-header {
          margin-bottom: 20px;
        }

        .notification-status {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .notification-icon-large {
          font-size: 48px;
        }

        .notification-info h3 {
          margin: 0 0 4px 0;
          font-size: 20px;
          font-weight: 600;
          color: var(--text-primary, #1a1a1a);
        }

        .status-text {
          margin: 0;
          font-size: 14px;
          color: var(--text-secondary, #666);
        }

        .notification-actions {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .notification-button-primary,
        .notification-button-secondary,
        .notification-button-details {
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          border: none;
        }

        .notification-button-primary {
          background: var(--primary-color, #2563eb);
          color: white;
          flex: 1;
          min-width: 200px;
        }

        .notification-button-primary:hover:not(:disabled) {
          background: var(--primary-hover, #1d4ed8);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .notification-button-primary:disabled {
          background: var(--disabled-bg, #e0e0e0);
          color: var(--disabled-text, #999);
          cursor: not-allowed;
        }

        .notification-button-secondary {
          background: var(--secondary-bg, #f3f4f6);
          color: var(--text-primary, #1a1a1a);
        }

        .notification-button-secondary:hover:not(:disabled) {
          background: var(--secondary-hover, #e5e7eb);
        }

        .notification-button-details {
          background: transparent;
          color: var(--primary-color, #2563eb);
          border: 1px solid var(--border-color, #e0e0e0);
        }

        .notification-button-details:hover {
          background: var(--hover-bg, #f9fafb);
        }

        .notification-message {
          margin-top: 16px;
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 14px;
        }

        .notification-message.success {
          background: #d1fae5;
          color: #065f46;
          border: 1px solid #6ee7b7;
        }

        .notification-message.error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fca5a5;
        }

        .notification-details {
          margin-top: 20px;
          padding: 16px;
          background: var(--bg-secondary, #f9fafb);
          border-radius: 8px;
          font-size: 14px;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid var(--border-color, #e5e7eb);
        }

        .detail-row:last-child {
          border-bottom: none;
        }

        .detail-label {
          font-weight: 500;
          color: var(--text-secondary, #666);
        }

        .detail-value {
          color: var(--text-primary, #1a1a1a);
          max-width: 60%;
          text-align: right;
        }

        .detail-value.truncate {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .notification-help {
          margin-top: 16px;
          padding: 12px 16px;
          background: #fef3c7;
          border: 1px solid #fbbf24;
          border-radius: 8px;
          font-size: 14px;
          color: #92400e;
        }
      `}</style>
    </div>
  );
}

export default NotificationPermissionButton;
