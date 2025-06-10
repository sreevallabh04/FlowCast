import React, { useEffect, useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Paper,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Inventory as InventoryIcon,
  LocalShipping as LocalShippingIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import { useDispatch, useSelector } from 'react-redux';
import { fetchDashboardData } from '../store/dashboardSlice';
import { formatCurrency, formatNumber } from '../utils/formatters';
import axios from 'axios';

const KpiCard = ({ title, value, icon, color, loading, error }) => {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box
            sx={{
              backgroundColor: `${color}20`,
              borderRadius: '50%',
              p: 1,
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
        {loading ? (
          <CircularProgress size={24} />
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <Typography variant="h4" component="div">
            {value}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

const ChartCard = ({ title, data, loading, error }) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" component="div" sx={{ mb: 2 }}>
          {title}
        </Typography>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#8884d8"
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const dispatch = useDispatch();
  const { data, loading, error } = useSelector((state) => state.dashboard);
  const [alerts, setAlerts] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [errorData, setErrorData] = useState(null);
  const [dataLocal, setDataLocal] = useState({
    demandMetrics: null,
    inventoryMetrics: null,
    routeMetrics: null
  });

  useEffect(() => {
    // Initial data fetch
    dispatch(fetchDashboardData());

    // Set up real-time updates
    const interval = setInterval(() => {
      dispatch(fetchDashboardData());
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [dispatch]);

  useEffect(() => {
    if (data) {
      // Process alerts
      const newAlerts = [];
      
      // Check for low inventory
      if (data.inventory_metrics?.low_stock_items > 0) {
        newAlerts.push({
          type: 'warning',
          message: `${data.inventory_metrics.low_stock_items} items are low in stock`,
        });
      }
      
      // Check for expiring products
      if (data.expiry_metrics?.expiring_soon > 0) {
        newAlerts.push({
          type: 'warning',
          message: `${data.expiry_metrics.expiring_soon} products are expiring soon`,
        });
      }
      
      // Check for delivery delays
      if (data.routing_metrics?.delayed_deliveries > 0) {
        newAlerts.push({
          type: 'error',
          message: `${data.routing_metrics.delayed_deliveries} deliveries are delayed`,
        });
      }
      
      setAlerts(newAlerts);
    }
  }, [data]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/analytics', {
          params: {
            product_id: 'PROD001', // Example product ID
            store_id: 'STORE001', // Example store ID
            start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            end_date: new Date().toISOString().split('T')[0]
          }
        });
        setDataLocal(response.data);
        setLoadingData(false);
      } catch (err) {
        setErrorData(err.message);
        setLoadingData(false);
      }
    };

    fetchData();
  }, []);

  if (loadingData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (errorData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <Typography color="error">{errorData}</Typography>
      </Box>
    );
  }

  const { demandMetrics, inventoryMetrics, routeMetrics } = dataLocal;

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Alerts */}
      {alerts.map((alert, index) => (
        <Alert
          key={index}
          severity={alert.type}
          sx={{ mb: 2 }}
          icon={alert.type === 'warning' ? <WarningIcon /> : undefined}
        >
          {alert.message}
        </Alert>
      )}

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              bgcolor: theme.palette.primary.main,
              color: 'white'
            }}
          >
            <Typography component="h2" variant="h6" gutterBottom>
              Total Demand
            </Typography>
            <Typography component="p" variant="h4">
              {demandMetrics?.total_demand || 0}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              bgcolor: theme.palette.secondary.main,
              color: 'white'
            }}
          >
            <Typography component="h2" variant="h6" gutterBottom>
              Current Stock
            </Typography>
            <Typography component="p" variant="h4">
              {inventoryMetrics?.current_stock || 0}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              bgcolor: theme.palette.success.main,
              color: 'white'
            }}
          >
            <Typography component="h2" variant="h6" gutterBottom>
              Service Level
            </Typography>
            <Typography component="p" variant="h4">
              {inventoryMetrics?.service_level || 0}%
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
              bgcolor: theme.palette.warning.main,
              color: 'white'
            }}
          >
            <Typography component="h2" variant="h6" gutterBottom>
              Total Distance
            </Typography>
            <Typography component="p" variant="h4">
              {routeMetrics?.total_distance || 0} km
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Demand Forecast Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Demand Forecast
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={demandMetrics?.forecast_data || []}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke={theme.palette.primary.main}
                  name="Predicted Demand"
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke={theme.palette.secondary.main}
                  name="Actual Demand"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Inventory Levels Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Inventory Levels
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={inventoryMetrics?.inventory_data || []}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="product" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="current"
                  fill={theme.palette.primary.main}
                  name="Current Stock"
                />
                <Bar
                  dataKey="safety"
                  fill={theme.palette.warning.main}
                  name="Safety Stock"
                />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Route Efficiency Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Route Efficiency
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={routeMetrics?.route_data || []}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="distance"
                  stroke={theme.palette.primary.main}
                  name="Distance (km)"
                />
                <Line
                  type="monotone"
                  dataKey="duration"
                  stroke={theme.palette.secondary.main}
                  name="Duration (min)"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 