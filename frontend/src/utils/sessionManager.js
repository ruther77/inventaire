/**
 * Session Manager - Gestion du session_id pour grouper les imports
 *
 * Le session_id est:
 * - Généré au premier import de la session browser
 * - Stocké en sessionStorage (disparaît à la fermeture de l'onglet)
 * - Utilisé pour grouper tous les imports d'une même session de travail
 */

const SESSION_ID_KEY = 'import_session_id';

/**
 * Génère un UUID v4 simple
 */
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Récupère le session_id courant ou en génère un nouveau
 */
export function getSessionId() {
  try {
    let sessionId = sessionStorage.getItem(SESSION_ID_KEY);
    if (!sessionId) {
      sessionId = generateUUID();
      sessionStorage.setItem(SESSION_ID_KEY, sessionId);
      console.log('🆕 Nouvelle session d\'import créée:', sessionId);
    }
    return sessionId;
  } catch (error) {
    // Fallback si sessionStorage n'est pas disponible
    console.warn('sessionStorage indisponible, génération d\'un session_id temporaire');
    return generateUUID();
  }
}

/**
 * Efface le session_id courant (démarre une nouvelle session)
 */
export function clearSessionId() {
  try {
    sessionStorage.removeItem(SESSION_ID_KEY);
    console.log('🧹 Session d\'import effacée');
  } catch (error) {
    console.warn('Impossible d\'effacer le session_id');
  }
}

/**
 * Vérifie si une session est active
 */
export function hasActiveSession() {
  try {
    return sessionStorage.getItem(SESSION_ID_KEY) !== null;
  } catch (error) {
    return false;
  }
}

/**
 * Récupère l'ID de la session courante (sans en créer une nouvelle)
 */
export function getCurrentSessionId() {
  try {
    return sessionStorage.getItem(SESSION_ID_KEY);
  } catch (error) {
    return null;
  }
}

/**
 * Démarre explicitement une nouvelle session
 */
export function startNewSession() {
  clearSessionId();
  return getSessionId();
}
