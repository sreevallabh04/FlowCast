import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  TextField,
  CircularProgress,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { GoogleMap, LoadScript, Marker, Polyline } from '@react-google-maps/api';
import axios from 'axios';

const RouteOptimization = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [mapCenter, setMapCenter] = useState({ lat: 40.7128, lng: -74.0060 });
  const [mapZoom, setMapZoom] = useState(12);
  const mapRef = useRef(null);

  const mapContainerStyle = {
    width: '100%',
    height: isMobile ? '300px' : '600px'
  };

  const mapOptions = {
    disableDefaultUI: true,
    zoomControl: true,
    styles: [
      {
        featureType: 'poi',
        elementType: 'labels',
        stylers: [{ visibility: 'off' }]
      }
    ]
  };

  const optimizeRoutes = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/optimize-routes', {
        locations: routes.map(route => ({
          lat: route.lat,
          lng: route.lng
        })),
        demands: routes.map(route => route.demand),
        vehicle_capacity: 500,
        num_vehicles: 2
      });

      setRoutes(response.data.routes);
      setSelectedRoute(response.data.routes[0]);

      // Center map on first route
      if (response.data.routes[0]?.locations?.[0]) {
        setMapCenter(response.data.routes[0].locations[0]);
      }
    } catch (err) {
      setError('Failed to optimize routes');
    } finally {
      setLoading(false);
    }
  };

  const handleMapClick = (event) => {
    const newLocation = {
      lat: event.latLng.lat(),
      lng: event.latLng.lng(),
      demand: 100 // Default demand
    };

    setRoutes([...routes, newLocation]);
  };

  const handleRouteSelect = (route) => {
    setSelectedRoute(route);
    if (route.locations?.[0]) {
      setMapCenter(route.locations[0]);
    }
  };

  const getRouteColor = (index) => {
    const colors = [
      theme.palette.primary.main,
      theme.palette.secondary.main,
      theme.palette.success.main,
      theme.palette.warning.main,
      theme.palette.error.main
    ];
    return colors[index % colors.length];
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Route Optimization
      </Typography>

      <Grid container spacing={3}>
        {/* Map */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <LoadScript
              googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}
            >
              <GoogleMap
                mapContainerStyle={mapContainerStyle}
                center={mapCenter}
                zoom={mapZoom}
                onClick={handleMapClick}
                options={mapOptions}
                onLoad={map => {
                  mapRef.current = map;
                }}
              >
                {/* Markers for all locations */}
                {routes.map((location, index) => (
                  <Marker
                    key={index}
                    position={{ lat: location.lat, lng: location.lng }}
                    label={`${index + 1}`}
                  />
                ))}

                {/* Polylines for optimized routes */}
                {routes.map((route, index) => (
                  <Polyline
                    key={index}
                    path={route.locations}
                    options={{
                      strokeColor: getRouteColor(index),
                      strokeOpacity: 1.0,
                      strokeWeight: 3
                    }}
                  />
                ))}
              </GoogleMap>
            </LoadScript>
          </Paper>
        </Grid>

        {/* Controls and Route Details */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Controls
            </Typography>
            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={optimizeRoutes}
              disabled={loading || routes.length < 2}
              sx={{ mb: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Optimize Routes'}
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              fullWidth
              onClick={() => setRoutes([])}
              disabled={loading}
            >
              Clear Routes
            </Button>
          </Paper>

          {selectedRoute && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Route Details
              </Typography>
              <Typography variant="body2" gutterBottom>
                Distance: {selectedRoute.distance.toFixed(2)} km
              </Typography>
              <Typography variant="body2" gutterBottom>
                Duration: {Math.round(selectedRoute.duration / 60)} minutes
              </Typography>
              <Typography variant="body2" gutterBottom>
                Stops: {selectedRoute.locations.length}
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* Error Message */}
      {error && (
        <Typography color="error" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}

      {/* Route List */}
      {routes.length > 0 && (
        <Paper sx={{ p: 2, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Routes
          </Typography>
          <Grid container spacing={2}>
            {routes.map((route, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Paper
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    bgcolor:
                      selectedRoute === route
                        ? theme.palette.action.selected
                        : 'inherit'
                  }}
                  onClick={() => handleRouteSelect(route)}
                >
                  <Typography variant="subtitle1">
                    Route {index + 1}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Distance: {route.distance.toFixed(2)} km
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Duration: {Math.round(route.duration / 60)} minutes
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default RouteOptimization; 