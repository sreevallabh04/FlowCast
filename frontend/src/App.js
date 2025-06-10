import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './redux/store';
import theme from './theme';

// Components
import Navigation from './components/layout/Navigation';
import Dashboard from './components/dashboard/Dashboard';
import Inventory from './components/inventory/Inventory';
import Routes from './components/routes/Routes';
import Analytics from './components/analytics/Analytics';
import Settings from './components/settings/Settings';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import PrivateRoute from './components/auth/PrivateRoute';

// Layout wrapper for authenticated routes
const AuthenticatedLayout = ({ children }) => (
  <>
    <Navigation />
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        mt: '64px',
        backgroundColor: 'background.default',
        minHeight: 'calc(100vh - 64px)'
      }}
    >
      {children}
    </Box>
  </>
);

const App = () => {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected Routes */}
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <AuthenticatedLayout>
                      <Dashboard />
                    </AuthenticatedLayout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/inventory"
                element={
                  <PrivateRoute>
                    <AuthenticatedLayout>
                      <Inventory />
                    </AuthenticatedLayout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/routes"
                element={
                  <PrivateRoute>
                    <AuthenticatedLayout>
                      <Routes />
                    </AuthenticatedLayout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/analytics"
                element={
                  <PrivateRoute>
                    <AuthenticatedLayout>
                      <Analytics />
                    </AuthenticatedLayout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <PrivateRoute>
                    <AuthenticatedLayout>
                      <Settings />
                    </AuthenticatedLayout>
                  </PrivateRoute>
                }
              />

              {/* Fallback Route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Router>
        </ThemeProvider>
      </PersistGate>
    </Provider>
  );
};

export default App; 