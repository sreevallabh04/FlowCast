import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  CircularProgress,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import axios from 'axios';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

const Analytics = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedStore, setSelectedStore] = useState('');
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);

  const COLORS = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.error.main
  ];

  useEffect(() => {
    fetchOptions();
  }, []);

  const fetchOptions = async () => {
    try {
      const [productsRes, storesRes] = await Promise.all([
        axios.get('/api/products'),
        axios.get('/api/stores')
      ]);
      setProducts(productsRes.data);
      setStores(storesRes.data);
    } catch (err) {
      setError('Failed to load options');
    }
  };

  const fetchAnalytics = async () => {
    if (!selectedProduct || !selectedStore) {
      setError('Please select both product and store');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get('/api/analytics', {
        params: {
          product_id: selectedProduct,
          store_id: selectedStore,
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0]
        }
      });
      setData(response.data);
    } catch (err) {
      setError('Failed to fetch analytics data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Analytics
      </Typography>

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              select
              fullWidth
              label="Product"
              value={selectedProduct}
              onChange={(e) => setSelectedProduct(e.target.value)}
            >
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              select
              fullWidth
              label="Store"
              value={selectedStore}
              onChange={(e) => setSelectedStore(e.target.value)}
            >
              {stores.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name}
                </option>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={setStartDate}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </LocalizationProvider>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={setEndDate}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </LocalizationProvider>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={fetchAnalytics}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Analyze'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {data && (
        <Grid container spacing={3}>
          {/* Demand Metrics */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Demand Trends
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={data.demand_metrics.trends}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="demand"
                    stroke={theme.palette.primary.main}
                    name="Demand"
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast"
                    stroke={theme.palette.secondary.main}
                    name="Forecast"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Inventory Metrics */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Inventory Levels
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.inventory_metrics.levels}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
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

          {/* Route Metrics */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Route Efficiency
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={data.route_metrics.efficiency}
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

          {/* Distribution Metrics */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Demand Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.demand_metrics.distribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {data.demand_metrics.distribution.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Summary Metrics */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Summary Metrics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Total Demand
                    </Typography>
                    <Typography variant="h6">
                      {data.demand_metrics.total_demand}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Service Level
                    </Typography>
                    <Typography variant="h6">
                      {data.inventory_metrics.service_level}%
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Average Route Distance
                    </Typography>
                    <Typography variant="h6">
                      {data.route_metrics.avg_distance.toFixed(2)} km
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Average Route Duration
                    </Typography>
                    <Typography variant="h6">
                      {Math.round(data.route_metrics.avg_duration / 60)} min
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Analytics; 