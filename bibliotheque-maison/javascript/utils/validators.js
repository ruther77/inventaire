/**
 * Utilitaires de validation
 */

/**
 * Valide une adresse email
 * @param {string} email - Email à valider
 * @returns {boolean} True si valide
 */
export function isValidEmail(email) {
  if (!email || typeof email !== 'string') return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}

/**
 * Valide un numéro SIRET (14 chiffres) avec l'algorithme de Luhn
 * @param {string} siret - Numéro SIRET à valider
 * @returns {boolean} True si valide
 */
export function isValidSiret(siret) {
  if (!siret || typeof siret !== 'string') return false;
  const cleaned = siret.replace(/\s/g, '');
  if (!/^\d{14}$/.test(cleaned)) return false;

  let sum = 0;
  for (let i = 0; i < 14; i++) {
    let digit = parseInt(cleaned[i], 10);
    if (i % 2 === 0) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
  }
  return sum % 10 === 0;
}

/**
 * Valide un numéro de TVA intracommunautaire français
 * @param {string} tva - Numéro de TVA à valider
 * @returns {boolean} True si valide
 */
export function isValidTVA(tva) {
  if (!tva || typeof tva !== 'string') return false;
  const cleaned = tva.replace(/\s/g, '').toUpperCase();
  const tvaRegex = /^FR[A-Z0-9]{2}\d{9}$/;
  return tvaRegex.test(cleaned);
}

/**
 * Valide un IBAN
 * @param {string} iban - IBAN à valider
 * @returns {boolean} True si valide
 */
export function isValidIBAN(iban) {
  if (!iban || typeof iban !== 'string') return false;
  const cleaned = iban.replace(/\s/g, '').toUpperCase();
  if (!/^[A-Z]{2}\d{2}[A-Z0-9]+$/.test(cleaned)) return false;
  if (cleaned.length < 15 || cleaned.length > 34) return false;

  const rearranged = cleaned.substring(4) + cleaned.substring(0, 4);
  const numericString = rearranged.split('').map(char => {
    const code = char.charCodeAt(0);
    if (code >= 65 && code <= 90) return (code - 55).toString();
    return char;
  }).join('');

  let remainder = numericString;
  while (remainder.length > 2) {
    const block = remainder.substring(0, 9);
    remainder = (parseInt(block, 10) % 97).toString() + remainder.substring(block.length);
  }
  return parseInt(remainder, 10) % 97 === 1;
}

/**
 * Vérifie qu'une valeur est renseignée
 * @param {*} value - Valeur à vérifier
 * @returns {boolean} True si la valeur est renseignée
 */
export function isRequired(value) {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === 'object') return Object.keys(value).length > 0;
  return true;
}
