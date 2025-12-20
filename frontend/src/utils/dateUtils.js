/**
 * Date utilities - Formatage des dates pour l'interface
 */

/**
 * Formate une date ISO en format lisible "JJ/MM/AAAA HH:MM"
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return dateStr;
  }
}

/**
 * Formate une date ISO en format lisible "JJ/MM/AAAA"
 */
export function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch (error) {
    return dateStr;
  }
}

/**
 * Formate une date ISO en format relatif ("Il y a 2h", "Hier", etc.)
 */
export function formatRelativeDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'À l\'instant';
    if (diffMin < 60) return `Il y a ${diffMin} min`;
    if (diffHour < 24) return `Il y a ${diffHour}h`;
    if (diffDay === 1) return 'Hier';
    if (diffDay < 7) return `Il y a ${diffDay} jours`;
    return formatDate(dateStr);
  } catch (error) {
    return dateStr;
  }
}
