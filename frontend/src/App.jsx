import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import DemandForecast from './components/DemandForecast';
import InventoryOptimization from './components/InventoryOptimization';
import RouteOptimization from './components/RouteOptimization';
import Analytics from './components/Analytics';

// Theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex' }}>
          <Navbar />
          <Sidebar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              mt: 8,
              backgroundColor: 'background.default',
              minHeight: '100vh',
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/demand" element={<DemandForecast />} />
              <Route path="/inventory" element={<InventoryOptimization />} />
              <Route path="/routes" element={<RouteOptimization />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App; 