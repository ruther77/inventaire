/**
 * Fonctions utilitaires diverses
 */

/**
 * Clone profond d'un objet
 * @param {*} obj - Objet à cloner
 * @returns {*} Clone de l'objet
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (obj instanceof Object) {
    const clonedObj = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
  return obj;
}

/**
 * Debounce : retarde l'exécution d'une fonction
 * @param {Function} fn - Fonction à exécuter
 * @param {number} delay - Délai en millisecondes
 * @returns {Function} Fonction debounced
 */
export function debounce(fn, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Throttle : limite l'exécution d'une fonction
 * @param {Function} fn - Fonction à exécuter
 * @param {number} limit - Intervalle minimum en millisecondes
 * @returns {Function} Fonction throttled
 */
export function throttle(fn, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Génère un identifiant unique
 * @param {string} prefix - Préfixe optionnel
 * @returns {string} Identifiant unique
 */
export function generateId(prefix = '') {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 9);
  return prefix ? `${prefix}_${timestamp}${randomPart}` : `${timestamp}${randomPart}`;
}

/**
 * Groupe les éléments d'un tableau par une clé
 * @param {Array} array - Tableau à grouper
 * @param {string|Function} key - Clé ou fonction pour grouper
 * @returns {Object} Objet avec les groupes
 */
export function groupBy(array, key) {
  if (!Array.isArray(array)) return {};
  return array.reduce((result, item) => {
    const groupKey = typeof key === 'function' ? key(item) : item[key];
    if (!result[groupKey]) result[groupKey] = [];
    result[groupKey].push(item);
    return result;
  }, {});
}

/**
 * Trie un tableau d'objets par une clé
 * @param {Array} array - Tableau à trier
 * @param {string|Function} key - Clé ou fonction pour trier
 * @param {string} order - Ordre de tri ('asc' ou 'desc')
 * @returns {Array} Nouveau tableau trié
 */
export function sortBy(array, key, order = 'asc') {
  if (!Array.isArray(array)) return [];
  return [...array].sort((a, b) => {
    const valueA = typeof key === 'function' ? key(a) : a[key];
    const valueB = typeof key === 'function' ? key(b) : b[key];
    if (valueA === valueB) return 0;
    let comparison = valueA > valueB ? 1 : -1;
    return order === 'desc' ? -comparison : comparison;
  });
}

/**
 * Vérifie si une valeur est vide
 * @param {*} value - Valeur à vérifier
 * @returns {boolean} True si vide
 */
export function isEmpty(value) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}
