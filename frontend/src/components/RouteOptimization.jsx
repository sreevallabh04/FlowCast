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
  Chip,
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

const RouteOptimization = () => {
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [selectedVehicles, setSelectedVehicles] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [metrics, setMetrics] = useState(null);

  // Mock data - replace with actual API calls
  const locations = [
    { id: 'L001', name: 'New York Store', address: '123 Main St, NY' },
    { id: 'L002', name: 'Los Angeles Store', address: '456 Oak Ave, LA' },
    { id: 'L003', name: 'Chicago Store', address: '789 Pine Rd, CH' },
  ];

  const vehicles = [
    { id: 'V001', name: 'Truck 1', capacity: 1000, type: 'Delivery' },
    { id: 'V002', name: 'Van 1', capacity: 500, type: 'Delivery' },
    { id: 'V003', name: 'Car 1', capacity: 200, type: 'Express' },
  ];

  const handleOptimize = async () => {
    try {
      setLoading(true);
      setError(null);

      // Mock API call - replace with actual API
      const response = await fetch('/api/optimize-routes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          locations: selectedLocations,
          vehicles: selectedVehicles,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to optimize routes');
      }

      const data = await response.json();
      setRoutes(data.routes);
      setMetrics(data.metrics);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = routes.map((route) => ({
    name: route.vehicle_id,
    distance: route.total_distance,
    duration: route.total_duration,
  }));

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Route Optimization
      </Typography>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={5}>
                  <TextField
                    select
                    fullWidth
                    label="Locations"
                    value={selectedLocations}
                    onChange={(e) => setSelectedLocations(e.target.value)}
                    SelectProps={{
                      multiple: true,
                      renderValue: (selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip
                              key={value}
                              label={locations.find((l) => l.id === value)?.name}
                            />
                          ))}
                        </Box>
                      ),
                    }}
                  >
                    {locations.map((location) => (
                      <MenuItem key={location.id} value={location.id}>
                        {location.name}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={12} sm={5}>
                  <TextField
                    select
                    fullWidth
                    label="Vehicles"
                    value={selectedVehicles}
                    onChange={(e) => setSelectedVehicles(e.target.value)}
                    SelectProps={{
                      multiple: true,
                      renderValue: (selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip
                              key={value}
                              label={vehicles.find((v) => v.id === value)?.name}
                            />
                          ))}
                        </Box>
                      ),
                    }}
                  >
                    {vehicles.map((vehicle) => (
                      <MenuItem key={vehicle.id} value={vehicle.id}>
                        {vehicle.name} ({vehicle.type})
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={12} sm={2}>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handleOptimize}
                    disabled={
                      loading ||
                      selectedLocations.length === 0 ||
                      selectedVehicles.length === 0
                    }
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

        {/* Routes */}
        {routes.length > 0 && (
          <>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Optimized Routes
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Vehicle</TableCell>
                          <TableCell>Route</TableCell>
                          <TableCell align="right">Distance (km)</TableCell>
                          <TableCell align="right">Duration (hrs)</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {routes.map((route) => (
                          <TableRow key={route.vehicle_id}>
                            <TableCell>{route.vehicle_id}</TableCell>
                            <TableCell>
                              {route.route
                                .map((stop) => stop.location_id)
                                .join(' → ')}
                            </TableCell>
                            <TableCell align="right">
                              {formatNumber(route.total_distance)}
                            </TableCell>
                            <TableCell align="right">
                              {formatNumber(route.total_duration)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>

            {/* Chart */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Route Performance
                  </Typography>
                  <Box sx={{ height: 400 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis yAxisId="left" />
                        <YAxis yAxisId="right" orientation="right" />
                        <Tooltip />
                        <Legend />
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="distance"
                          stroke="#2196f3"
                          name="Distance (km)"
                        />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="duration"
                          stroke="#f50057"
                          name="Duration (hrs)"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Metrics */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Total Distance
                      </Typography>
                      <Typography variant="h6">
                        {formatNumber(metrics.total_distance)} km
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Total Duration
                      </Typography>
                      <Typography variant="h6">
                        {formatNumber(metrics.total_duration)} hrs
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Fuel Savings
                      </Typography>
                      <Typography variant="h6">
                        {formatCurrency(metrics.fuel_savings)}
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

export default RouteOptimization; 