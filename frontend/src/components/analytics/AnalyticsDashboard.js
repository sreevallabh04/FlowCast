import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchAnalytics,
  exportAnalytics
} from '../../redux/actions/analyticsActions';

const AnalyticsDashboard = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const { analytics, loading, error } = useSelector(state => state.analytics);
  
  const [dateRange, setDateRange] = useState('30d');
  const [category, setCategory] = useState('all');
  const [store, setStore] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  const COLORS = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.error.main
  ];

  useEffect(() => {
    dispatch(fetchAnalytics(dateRange, category, store));
  }, [dispatch, dateRange, category, store]);

  const handleExport = (format) => {
    dispatch(exportAnalytics(dateRange, category, store, format));
  };

  const handleRefresh = () => {
    dispatch(fetchAnalytics(dateRange, category, store));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Analytics Dashboard</Typography>
        <Box>
          <IconButton
            color="primary"
            onClick={() => setShowFilters(!showFilters)}
            style={{ marginRight: 8 }}
          >
            <FilterIcon />
          </IconButton>
          <IconButton
            color="primary"
            onClick={handleRefresh}
            style={{ marginRight: 8 }}
          >
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            color="primary"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('csv')}
          >
            Export
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      {showFilters && (
        <Card style={{ marginBottom: 24 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  label="Date Range"
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  fullWidth
                >
                  <MenuItem value="7d">Last 7 Days</MenuItem>
                  <MenuItem value="30d">Last 30 Days</MenuItem>
                  <MenuItem value="90d">Last 90 Days</MenuItem>
                  <MenuItem value="365d">Last Year</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  label="Category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  fullWidth
                >
                  <MenuItem value="all">All Categories</MenuItem>
                  {analytics.categories?.map(cat => (
                    <MenuItem key={cat} value={cat}>
                      {cat}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  label="Store"
                  value={store}
                  onChange={(e) => setStore(e.target.value)}
                  fullWidth
                >
                  <MenuItem value="all">All Stores</MenuItem>
                  {analytics.stores?.map(s => (
                    <MenuItem key={s.id} value={s.id}>
                      {s.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        {/* Sales Trend */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sales Trend
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.salesTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="sales"
                    stroke={theme.palette.primary.main}
                    name="Sales"
                  />
                  <Line
                    type="monotone"
                    dataKey="ma7"
                    stroke={theme.palette.secondary.main}
                    name="7-day MA"
                  />
                  <Line
                    type="monotone"
                    dataKey="ma30"
                    stroke={theme.palette.success.main}
                    name="30-day MA"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Category Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sales by Category
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.categoryDistribution}
                    dataKey="value"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {analytics.categoryDistribution?.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Store Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Store Performance
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.storePerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="store" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Bar
                    dataKey="sales"
                    fill={theme.palette.primary.main}
                    name="Sales"
                  />
                  <Bar
                    dataKey="orders"
                    fill={theme.palette.secondary.main}
                    name="Orders"
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Key Metrics */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Sales
              </Typography>
              <Typography variant="h4">
                ${analytics.metrics?.totalSales.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Average Order Value
              </Typography>
              <Typography variant="h4">
                ${analytics.metrics?.averageOrderValue.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Delivery Success Rate
              </Typography>
              <Typography variant="h4">
                {analytics.metrics?.deliverySuccessRate.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Inventory Turnover
              </Typography>
              <Typography variant="h4">
                {analytics.metrics?.inventoryTurnover.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AnalyticsDashboard; 