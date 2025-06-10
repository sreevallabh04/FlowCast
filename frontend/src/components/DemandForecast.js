import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  TextField,
  Button,
  Grid,
  MenuItem,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import axios from 'axios';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

const DemandForecast = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedStore, setSelectedStore] = useState('');
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000));

  useEffect(() => {
    // Fetch products and stores
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

    fetchOptions();
  }, []);

  const handleForecast = async () => {
    if (!selectedProduct || !selectedStore) {
      setError('Please select both product and store');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/predict-demand', {
        product_id: selectedProduct,
        store_id: selectedStore,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0]
      });
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch forecast');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Demand Forecast
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
                <MenuItem key={product.id} value={product.id}>
                  {product.name}
                </MenuItem>
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
                <MenuItem key={store.id} value={store.id}>
                  {store.name}
                </MenuItem>
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
              onClick={handleForecast}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Forecast'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Message */}
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {/* Forecast Chart */}
      {data && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Forecast Results
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart
              data={data.predictions}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="predicted_demand"
                stroke={theme.palette.primary.main}
                fill={theme.palette.primary.light}
                name="Predicted Demand"
              />
              <Area
                type="monotone"
                dataKey="upper_bound"
                stroke={theme.palette.secondary.main}
                fill={theme.palette.secondary.light}
                name="Upper Bound"
              />
              <Area
                type="monotone"
                dataKey="lower_bound"
                stroke={theme.palette.secondary.main}
                fill={theme.palette.secondary.light}
                name="Lower Bound"
              />
            </AreaChart>
          </ResponsiveContainer>

          {/* Metrics */}
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="subtitle2" color="textSecondary">
                  R² Score
                </Typography>
                <Typography variant="h6">
                  {data.metrics.r2_score.toFixed(3)}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="subtitle2" color="textSecondary">
                  MAE
                </Typography>
                <Typography variant="h6">
                  {data.metrics.mae.toFixed(2)}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="subtitle2" color="textSecondary">
                  RMSE
                </Typography>
                <Typography variant="h6">
                  {data.metrics.rmse.toFixed(2)}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="subtitle2" color="textSecondary">
                  MAPE
                </Typography>
                <Typography variant="h6">
                  {data.metrics.mape.toFixed(2)}%
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default DemandForecast; 