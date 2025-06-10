import React, { createContext, useContext, useState } from 'react';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    type: 'info'
  });

  const showNotification = (message, type = 'info') => {
    setNotification({
      open: true,
      message,
      type
    });
  };

  const hideNotification = () => {
    setNotification(prev => ({
      ...prev,
      open: false
    }));
  };

  const value = {
    notification,
    showNotification,
    hideNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}; 