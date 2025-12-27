/**
 * Utilitaires de formatage - Format français
 */

/**
 * Formate un montant en devise
 * @param {number} amount - Montant à formater
 * @param {string} currency - Code devise ISO (EUR par défaut)
 * @returns {string} Montant formaté
 */
export function formatCurrency(amount, currency = 'EUR') {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '-';
  }
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * Formate une date selon le format français
 * @param {Date|string|number} date - Date à formater
 * @param {Object} options - Options de formatage
 * @returns {string} Date formatée
 */
export function formatDate(date, options = {}) {
  if (!date) return '-';
  const dateObj = date instanceof Date ? date : new Date(date);
  if (isNaN(dateObj.getTime())) return '-';

  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    ...options
  };
  return new Intl.DateTimeFormat('fr-FR', defaultOptions).format(dateObj);
}

/**
 * Formate un pourcentage
 * @param {number} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales
 * @returns {string} Pourcentage formaté
 */
export function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined || isNaN(value)) return '-';
  const percentValue = value > 1 ? value : value * 100;
  return new Intl.NumberFormat('fr-FR', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(percentValue / 100);
}

/**
 * Formate un nombre avec séparateurs français
 * @param {number} value - Nombre à formater
 * @param {number} decimals - Nombre de décimales
 * @returns {string} Nombre formaté
 */
export function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return '-';
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
}
