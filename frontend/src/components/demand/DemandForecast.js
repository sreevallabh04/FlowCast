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
  CircularProgress,
  Slider,
  Button,
  IconButton,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { useNotification } from '../../contexts/NotificationContext';
import axios from 'axios';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const DemandForecast = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { showNotification } = useNotification();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    products: [],
    forecasts: [],
    confidenceBands: [],
    metrics: {}
  });
  const [selectedProduct, setSelectedProduct] = useState('');
  const [confidenceLevel, setConfidenceLevel] = useState(95);
  const [forecastPeriod, setForecastPeriod] = useState(30);

  const fetchForecastData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/forecast', {
        params: {
          product: selectedProduct,
          confidence: confidenceLevel,
          period: forecastPeriod
        }
      });
      setData(response.data);
    } catch (error) {
      showNotification('Failed to fetch forecast data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProduct) {
      fetchForecastData();
    }
  }, [selectedProduct, confidenceLevel, forecastPeriod]);

  const handleExport = async (format) => {
    try {
      const response = await axios.get('/api/forecast/export', {
        params: {
          product: selectedProduct,
          format
        },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `forecast_${selectedProduct}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      showNotification('Failed to export forecast data', 'error');
    }
  };

  const ForecastChart = () => {
    const chartData = {
      labels: data.forecasts.map(f => f.date),
      datasets: [
        {
          label: 'Historical Demand',
          data: data.forecasts.map(f => f.historical),
          borderColor: theme.palette.primary.main,
          backgroundColor: theme.palette.primary.main,
          fill: false
        },
        {
          label: 'Forecast',
          data: data.forecasts.map(f => f.forecast),
          borderColor: theme.palette.secondary.main,
          backgroundColor: theme.palette.secondary.main,
          fill: false
        },
        {
          label: 'Upper Confidence Band',
          data: data.confidenceBands.map(b => b.upper),
          borderColor: theme.palette.success.main,
          backgroundColor: theme.palette.success.main,
          fill: '+1',
          pointRadius: 0
        },
        {
          label: 'Lower Confidence Band',
          data: data.confidenceBands.map(b => b.lower),
          borderColor: theme.palette.success.main,
          backgroundColor: theme.palette.success.main,
          fill: false,
          pointRadius: 0
        }
      ]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'day'
          }
        },
        y: {
          beginAtZero: true
        }
      }
    };

    return (
      <Box sx={{ height: 400 }}>
        <Line data={chartData} options={options} />
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
        Forecast Metrics
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            MAPE
          </Typography>
          <Typography variant="h6">
            {data.metrics.mape}%
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            RMSE
          </Typography>
          <Typography variant="h6">
            {data.metrics.rmse}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            R² Score
          </Typography>
          <Typography variant="h6">
            {data.metrics.r2}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Forecast Horizon
          </Typography>
          <Typography variant="h6">
            {forecastPeriod} days
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
          Demand Forecast
        </Typography>
        <Box>
          <IconButton onClick={fetchForecastData}>
            <RefreshIcon />
          </IconButton>
          <IconButton onClick={() => handleExport('csv')}>
            <DownloadIcon />
          </IconButton>
          <IconButton>
            <SettingsIcon />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12} md={4}>
          <Paper
            elevation={3}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'background.default'
            }}
          >
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Product</InputLabel>
              <Select
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
                label="Product"
              >
                {data.products.map((product) => (
                  <MenuItem key={product.id} value={product.id}>
                    {product.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Typography gutterBottom>
              Confidence Level: {confidenceLevel}%
            </Typography>
            <Slider
              value={confidenceLevel}
              onChange={(_, value) => setConfidenceLevel(value)}
              min={80}
              max={99}
              step={1}
              marks
              valueLabelDisplay="auto"
            />

            <Typography gutterBottom sx={{ mt: 2 }}>
              Forecast Period: {forecastPeriod} days
            </Typography>
            <Slider
              value={forecastPeriod}
              onChange={(_, value) => setForecastPeriod(value)}
              min={7}
              max={90}
              step={7}
              marks
              valueLabelDisplay="auto"
            />
          </Paper>
        </Grid>

        {/* Chart */}
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
              Forecast Visualization
            </Typography>
            <ForecastChart />
          </Paper>
        </Grid>

        {/* Metrics */}
        <Grid item xs={12}>
          <MetricsCard />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DemandForecast; 