import React, { createContext, useContext, useState, useEffect } from 'react';
import { checkHealthDetails } from '../services/api';

const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [systemHealth, setSystemHealth] = useState({
    status: 'checking',
    environment: 'unknown',
    version: '0.1.0',
    database_connected: false,
    lastChecked: null,
    error: null,
  });

  const refreshHealth = async () => {
    try {
      const data = await checkHealthDetails();
      setSystemHealth({
        ...data,
        lastChecked: new Date().toLocaleTimeString(),
        error: null,
      });
    } catch (err) {
      setSystemHealth(prev => ({
        ...prev,
        status: 'disconnected',
        database_connected: false,
        lastChecked: new Date().toLocaleTimeString(),
        error: err.message || 'Unable to connect to backend',
      }));
    }
  };

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider
      value={{
        sidebarOpen,
        setSidebarOpen,
        systemHealth,
        refreshHealth,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
