import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  TextField,
  Button,
  MenuItem,
  CircularProgress,
  Alert,
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
} from 'recharts';
import { useDispatch, useSelector } from 'react-redux';
import { formatCurrency, formatNumber } from '../utils/formatters';

const DemandForecast = () => {
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [forecastDays, setForecastDays] = useState(7);
  const [predictions, setPredictions] = useState([]);
  const [metrics, setMetrics] = useState(null);

  // Mock data - replace with actual API calls
  const products = [
    { id: 'P001', name: 'Product 1' },
    { id: 'P002', name: 'Product 2' },
    { id: 'P003', name: 'Product 3' },
  ];

  const locations = [
    { id: 'L001', name: 'New York Store' },
    { id: 'L002', name: 'Los Angeles Store' },
    { id: 'L003', name: 'Chicago Store' },
  ];

  const handlePredict = async () => {
    try {
      setLoading(true);
      setError(null);

      // Mock API call - replace with actual API
      const response = await fetch('/api/predict-demand', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: selectedProduct,
          location_id: selectedLocation,
          forecast_days: forecastDays,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get predictions');
      }

      const data = await response.json();
      setPredictions(data.predictions);
      setMetrics(data.metrics);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = predictions.map((pred) => ({
    date: pred.date,
    predicted: pred.predicted_demand,
    lower: pred.confidence_interval.lower,
    upper: pred.confidence_interval.upper,
  }));

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Demand Forecasting
      </Typography>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={3}>
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
                <Grid item xs={12} sm={3}>
                  <TextField
                    select
                    fullWidth
                    label="Location"
                    value={selectedLocation}
                    onChange={(e) => setSelectedLocation(e.target.value)}
                  >
                    {locations.map((location) => (
                      <MenuItem key={location.id} value={location.id}>
                        {location.name}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    type="number"
                    fullWidth
                    label="Forecast Days"
                    value={forecastDays}
                    onChange={(e) => setForecastDays(Number(e.target.value))}
                    inputProps={{ min: 1, max: 30 }}
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handlePredict}
                    disabled={loading || !selectedProduct || !selectedLocation}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Predict'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Alert */}
        {error && (
          <Grid item xs={12}>
            <Alert severity="error">{error}</Alert>
          </Grid>
        )}

        {/* Metrics */}
        {metrics && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="subtitle2" color="textSecondary">
                      MAPE
                    </Typography>
                    <Typography variant="h6">
                      {formatNumber(metrics.mape)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="subtitle2" color="textSecondary">
                      RMSE
                    </Typography>
                    <Typography variant="h6">
                      {formatNumber(metrics.rmse)}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Chart */}
        {chartData.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Demand Forecast
                </Typography>
                <Box sx={{ height: 400 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="predicted"
                        stroke="#2196f3"
                        name="Predicted Demand"
                      />
                      <Line
                        type="monotone"
                        dataKey="lower"
                        stroke="#f50057"
                        strokeDasharray="5 5"
                        name="Lower Bound"
                      />
                      <Line
                        type="monotone"
                        dataKey="upper"
                        stroke="#f50057"
                        strokeDasharray="5 5"
                        name="Upper Bound"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default DemandForecast; 