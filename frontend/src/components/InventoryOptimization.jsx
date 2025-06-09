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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useDispatch, useSelector } from 'react-redux';
import { formatCurrency, formatNumber } from '../utils/formatters';

const InventoryOptimization = () => {
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [optimization, setOptimization] = useState(null);
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

  const handleOptimize = async () => {
    try {
      setLoading(true);
      setError(null);

      // Mock API call - replace with actual API
      const response = await fetch('/api/optimize-inventory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: selectedProduct,
          location_id: selectedLocation,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to optimize inventory');
      }

      const data = await response.json();
      setOptimization(data.optimization);
      setMetrics(data.metrics);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = optimization
    ? [
        {
          name: 'Current Stock',
          value: optimization.current_stock,
        },
        {
          name: 'Safety Stock',
          value: optimization.safety_stock,
        },
        {
          name: 'Reorder Point',
          value: optimization.reorder_point,
        },
        {
          name: 'EOQ',
          value: optimization.economic_order_quantity,
        },
      ]
    : [];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Inventory Optimization
      </Typography>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={5}>
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
                <Grid item xs={12} sm={5}>
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
                <Grid item xs={12} sm={2}>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handleOptimize}
                    disabled={loading || !selectedProduct || !selectedLocation}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Optimize'}
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

        {/* Optimization Results */}
        {optimization && (
          <>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Optimization Results
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Metric</TableCell>
                          <TableCell align="right">Value</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Current Stock</TableCell>
                          <TableCell align="right">
                            {formatNumber(optimization.current_stock)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Safety Stock</TableCell>
                          <TableCell align="right">
                            {formatNumber(optimization.safety_stock)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Reorder Point</TableCell>
                          <TableCell align="right">
                            {formatNumber(optimization.reorder_point)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Economic Order Quantity</TableCell>
                          <TableCell align="right">
                            {formatNumber(optimization.economic_order_quantity)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Next Order Date</TableCell>
                          <TableCell align="right">
                            {optimization.next_order_date}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Suggested Order Quantity</TableCell>
                          <TableCell align="right">
                            {formatNumber(optimization.suggested_order_quantity)}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Stock Levels
                  </Typography>
                  <Box sx={{ height: 400 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar
                          dataKey="value"
                          fill="#2196f3"
                          name="Quantity"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Metrics */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Stockout Probability
                      </Typography>
                      <Typography variant="h6">
                        {formatNumber(metrics.stockout_probability)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Holding Cost Savings
                      </Typography>
                      <Typography variant="h6">
                        {formatCurrency(metrics.holding_cost_savings)}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
};

export default InventoryOptimization; 