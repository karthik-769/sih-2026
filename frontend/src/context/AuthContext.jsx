import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginApi, getMeApi } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('auth_token'));
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('auth_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [sessionExpiredNotice, setSessionExpiredNotice] = useState(false);

  // Validate token on mount
  useEffect(() => {
    const verifySession = async () => {
      if (token) {
        try {
          const userData = await getMeApi();
          setUser(userData);
          localStorage.setItem('auth_user', JSON.stringify(userData));
        } catch (err) {
          console.warn('Session verification failed:', err);
          logout();
          setSessionExpiredNotice(true);
        }
      }
      setIsLoading(false);
    };

    verifySession();

    // Listen to 401 session-expired custom events from API interceptor
    const handleExpired = () => {
      setToken(null);
      setUser(null);
      setSessionExpiredNotice(true);
    };
    window.addEventListener('session-expired', handleExpired);
    return () => window.removeEventListener('session-expired', handleExpired);
  }, []);

  const login = async (email, password) => {
    setSessionExpiredNotice(false);
    const data = await loginApi(email, password);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('auth_user', JSON.stringify(data.user));
    return data.user;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  const clearSessionNotice = () => setSessionExpiredNotice(false);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        sessionExpiredNotice,
        clearSessionNotice,
        login,
        logout,
        role: user?.role || null,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
