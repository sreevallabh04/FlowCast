import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  CircularProgress,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import {
  Line,
  Bar,
  Pie,
  Doughnut
} from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { useNotification } from '../../contexts/NotificationContext';
import axios from 'axios';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const Analytics = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { showNotification } = useNotification();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    sales: [],
    inventory: [],
    deliveries: [],
    metrics: {}
  });
  const [filters, setFilters] = useState({
    dateRange: '30d',
    category: 'all',
    store: 'all'
  });

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/analytics', {
        params: filters
      });
      setData(response.data);
    } catch (error) {
      showNotification('Failed to fetch analytics data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [filters]);

  const handleExport = async (format) => {
    try {
      const response = await axios.get('/api/analytics/export', {
        params: {
          ...filters,
          format
        },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analytics_${filters.dateRange}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      showNotification('Failed to export analytics data', 'error');
    }
  };

  const SalesChart = () => {
    const chartData = {
      labels: data.sales.map(s => s.date),
      datasets: [{
        label: 'Sales',
        data: data.sales.map(s => s.value),
        borderColor: theme.palette.primary.main,
        backgroundColor: theme.palette.primary.main,
        fill: false
      }]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      }
    };

    return (
      <Box sx={{ height: 300 }}>
        <Line data={chartData} options={options} />
      </Box>
    );
  };

  const InventoryChart = () => {
    const chartData = {
      labels: data.inventory.map(i => i.category),
      datasets: [{
        label: 'Inventory Value',
        data: data.inventory.map(i => i.value),
        backgroundColor: [
          theme.palette.primary.main,
          theme.palette.secondary.main,
          theme.palette.success.main,
          theme.palette.warning.main,
          theme.palette.error.main
        ]
      }]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right'
        }
      }
    };

    return (
      <Box sx={{ height: 300 }}>
        <Doughnut data={chartData} options={options} />
      </Box>
    );
  };

  const DeliveryChart = () => {
    const chartData = {
      labels: data.deliveries.map(d => d.status),
      datasets: [{
        label: 'Deliveries',
        data: data.deliveries.map(d => d.count),
        backgroundColor: theme.palette.secondary.main
      }]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      }
    };

    return (
      <Box sx={{ height: 300 }}>
        <Bar data={chartData} options={options} />
      </Box>
    );
  };

  const MetricsCard = () => (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        height: '100%',
        bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'background.default'
      }}
    >
      <Typography variant="h6" color="text.secondary" gutterBottom>
        Key Metrics
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Total Sales
          </Typography>
          <Typography variant="h6">
            ${data.metrics.totalSales.toLocaleString()}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Average Order Value
          </Typography>
          <Typography variant="h6">
            ${data.metrics.averageOrderValue.toLocaleString()}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Delivery Success Rate
          </Typography>
          <Typography variant="h6">
            {data.metrics.deliverySuccessRate}%
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Inventory Turnover
          </Typography>
          <Typography variant="h6">
            {data.metrics.inventoryTurnover}x
          </Typography>
        </Grid>
      </Grid>
    </Paper>
  );

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '60vh'
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">
          Analytics Dashboard
        </Typography>
        <Box>
          <IconButton onClick={fetchAnalyticsData}>
            <RefreshIcon />
          </IconButton>
          <IconButton onClick={() => handleExport('csv')}>
            <DownloadIcon />
          </IconButton>
          <IconButton>
            <FilterIcon />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Filters */}
        <Grid item xs={12}>
          <Paper
            elevation={3}
            sx={{
              p: 2,
              mb: 3,
              bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'background.default'
            }}
          >
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Date Range</InputLabel>
                  <Select
                    value={filters.dateRange}
                    onChange={(e) => setFilters({
                      ...filters,
                      dateRange: e.target.value
                    })}
                    label="Date Range"
                  >
                    <MenuItem value="7d">Last 7 Days</MenuItem>
                    <MenuItem value="30d">Last 30 Days</MenuItem>
                    <MenuItem value="90d">Last 90 Days</MenuItem>
                    <MenuItem value="1y">Last Year</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={filters.category}
                    onChange={(e) => setFilters({
                      ...filters,
                      category: e.target.value
                    })}
                    label="Category"
                  >
                    <MenuItem value="all">All Categories</MenuItem>
                    <MenuItem value="electronics">Electronics</MenuItem>
                    <MenuItem value="clothing">Clothing</MenuItem>
                    <MenuItem value="food">Food</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Store</InputLabel>
                  <Select
                    value={filters.store}
                    onChange={(e) => setFilters({
                      ...filters,
                      store: e.target.value
                    })}
                    label="Store"
                  >
                    <MenuItem value="all">All Stores</MenuItem>
                    <MenuItem value="store1">Store 1</MenuItem>
                    <MenuItem value="store2">Store 2</MenuItem>
                    <MenuItem value="store3">Store 3</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Metrics */}
        <Grid item xs={12} md={4}>
          <MetricsCard />
        </Grid>

        {/* Charts */}
        <Grid item xs={12} md={8}>
          <Paper
            elevation={3}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'background.default'
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Sales Trend
            </Typography>
            <SalesChart />
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            elevation={3}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'background.default'
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Inventory Distribution
            </Typography>
            <InventoryChart />
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            elevation={3}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'background.default'
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Delivery Status
            </Typography>
            <DeliveryChart />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics; 