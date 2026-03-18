import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/authApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Verify token is still valid on mount
    if (token) {
      authApi
        .verifyToken()
        .then(() => setIsLoading(false))
        .catch(() => {
          // Token invalid / expired — clear it
          localStorage.removeItem('token');
          setToken(null);
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    navigate('/dashboard');
    return data;
  }, [navigate]);

  const register = useCallback(async (username, email, password) => {
    await authApi.register(username, email, password);
    // Auto-login after successful registration
    const data = await authApi.login(email, password);
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    navigate('/dashboard');
    return data;
  }, [navigate]);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
    navigate('/login');
  }, [navigate]);

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ token, login, register, logout, isAuthenticated, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
