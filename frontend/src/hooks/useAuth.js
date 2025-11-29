import { useContext } from 'react';
import AuthContext from '../context/AuthContext.jsx';

const useAuth = () => useContext(AuthContext);

export default useAuth;
export { useAuth };
