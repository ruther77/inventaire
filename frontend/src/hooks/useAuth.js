/**
 * Hook d'authentification pour accéder au contexte utilisateur.
 *
 * Fournit l'accès aux informations de l'utilisateur connecté et aux méthodes
 * de connexion/déconnexion depuis n'importe quel composant de l'application.
 *
 * @returns {Object} Contexte d'authentification contenant:
 * @property {Object|null} user - Informations de l'utilisateur connecté
 * @property {Function} login - Fonction de connexion
 * @property {Function} logout - Fonction de déconnexion
 * @property {boolean} isAuthenticated - Indique si l'utilisateur est connecté
 * @property {boolean} isLoading - Indique si l'authentification est en cours de chargement
 *
 * @example
 * const { user, isAuthenticated, logout } = useAuth();
 *
 * if (!isAuthenticated) {
 *   return <LoginPage />;
 * }
 *
 * return <div>Bonjour {user.username}</div>;
 */
import { useContext } from 'react';
import AuthContext from '../context/AuthContext.jsx';

const useAuth = () => useContext(AuthContext);

export default useAuth;
export { useAuth };
