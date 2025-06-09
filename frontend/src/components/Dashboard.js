import React, { useEffect, useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
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
} from 'recharts';
import { useDispatch, useSelector } from 'react-redux';
import { fetchDashboardData } from '../store/dashboardSlice';
import { formatCurrency, formatNumber } from '../utils/formatters';

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

function Dashboard() {
  const dispatch = useDispatch();
  const { data, loading, error } = useSelector((state) => state.dashboard);
  const [alerts, setAlerts] = useState([]);

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

  return (
    <Box>
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
      ))}

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard
            title="Total Revenue"
            value={formatCurrency(data?.revenue_metrics?.total_revenue)}
            icon={<TrendingUpIcon sx={{ color: '#4caf50' }} />}
            color="#4caf50"
            loading={loading}
            error={error}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard
            title="Inventory Value"
            value={formatCurrency(data?.inventory_metrics?.total_value)}
            icon={<InventoryIcon sx={{ color: '#2196f3' }} />}
            color="#2196f3"
            loading={loading}
            error={error}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard
            title="Active Deliveries"
            value={formatNumber(data?.routing_metrics?.active_deliveries)}
            icon={<LocalShippingIcon sx={{ color: '#ff9800' }} />}
            color="#ff9800"
            loading={loading}
            error={error}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard
            title="Waste Reduction"
            value={`${data?.expiry_metrics?.waste_reduction}%`}
            icon={<WarningIcon sx={{ color: '#f44336' }} />}
            color="#f44336"
            loading={loading}
            error={error}
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Demand Forecast"
            data={data?.demand_metrics?.forecast_data}
            loading={loading}
            error={error}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Inventory Levels"
            data={data?.inventory_metrics?.inventory_data}
            loading={loading}
            error={error}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Delivery Performance"
            data={data?.routing_metrics?.performance_data}
            loading={loading}
            error={error}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="Waste Reduction"
            data={data?.expiry_metrics?.waste_data}
            loading={loading}
            error={error}
          />
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard; 