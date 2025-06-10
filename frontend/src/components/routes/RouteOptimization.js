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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Directions as DirectionsIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useDispatch, useSelector } from 'react-redux';
import { GoogleMap, LoadScript, Marker, DirectionsRenderer } from '@react-google-maps/api';
import {
  fetchRoutes,
  optimizeRoutes,
  updateRoute,
  deleteRoute,
  addRoute
} from '../../redux/actions/routeActions';

const RouteOptimization = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const { routes, loading, error } = useSelector(state => state.routes);
  
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [directions, setDirections] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [formData, setFormData] = useState({
    storeId: '',
    maxDistance: 100,
    maxTime: 120,
    vehicleCapacity: 1000
  });

  const mapContainerStyle = {
    width: '100%',
    height: '500px'
  };

  const center = {
    lat: 0,
    lng: 0
  };

  useEffect(() => {
    dispatch(fetchRoutes());
  }, [dispatch]);

  const handleOpenDialog = (route = null) => {
    if (route) {
      setSelectedRoute(route);
      setFormData({
        storeId: route.storeId,
        maxDistance: route.maxDistance,
        maxTime: route.maxTime,
        vehicleCapacity: route.vehicleCapacity
      });
    } else {
      setSelectedRoute(null);
      setFormData({
        storeId: '',
        maxDistance: 100,
        maxTime: 120,
        vehicleCapacity: 1000
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedRoute(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = () => {
    if (selectedRoute) {
      dispatch(updateRoute(selectedRoute.id, formData));
    } else {
      dispatch(addRoute(formData));
    }
    handleCloseDialog();
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this route?')) {
      dispatch(deleteRoute(id));
    }
  };

  const handleOptimize = () => {
    dispatch(optimizeRoutes());
  };

  const handleGetDirections = async (route) => {
    try {
      const response = await fetch(`/api/routes/${route.id}/directions`);
      const data = await response.json();
      setDirections(data);
      setSelectedRoute(route);
    } catch (error) {
      console.error('Error fetching directions:', error);
    }
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
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Routes
              </Typography>
              <Typography variant="h4">
                {routes.filter(route => route.status === 'active').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Deliveries
              </Typography>
              <Typography variant="h4">
                {routes.reduce((sum, route) => sum + route.deliveries.length, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Average Route Time
              </Typography>
              <Typography variant="h4">
                {routes.length > 0
                  ? `${Math.round(
                      routes.reduce((sum, route) => sum + route.duration, 0) / routes.length
                    )} mins`
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Map and Routes List */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Route Map
              </Typography>
              <LoadScript googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}>
                <GoogleMap
                  mapContainerStyle={mapContainerStyle}
                  center={center}
                  zoom={12}
                >
                  {routes.map(route => (
                    <Marker
                      key={route.id}
                      position={{
                        lat: route.store.latitude,
                        lng: route.store.longitude
                      }}
                    />
                  ))}
                  {directions && <DirectionsRenderer directions={directions} />}
                </GoogleMap>
              </LoadScript>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Routes</Typography>
                <Box>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<AddIcon />}
                    onClick={() => handleOpenDialog()}
                    style={{ marginRight: 8 }}
                  >
                    Add
                  </Button>
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<RefreshIcon />}
                    onClick={handleOptimize}
                  >
                    Optimize
                  </Button>
                </Box>
              </Box>
              <List>
                {routes.map(route => (
                  <ListItem key={route.id}>
                    <ListItemText
                      primary={`Route ${route.id}`}
                      secondary={`${route.deliveries.length} deliveries`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        color="primary"
                        onClick={() => handleGetDirections(route)}
                      >
                        <DirectionsIcon />
                      </IconButton>
                      <IconButton
                        color="primary"
                        onClick={() => handleOpenDialog(route)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        color="error"
                        onClick={() => handleDelete(route.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedRoute ? 'Edit Route' : 'Add Route'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <TextField
              name="storeId"
              label="Store"
              value={formData.storeId}
              onChange={handleInputChange}
              select
              fullWidth
              required
            >
              {stores.map(store => (
                <MenuItem key={store.id} value={store.id}>
                  {store.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              name="maxDistance"
              label="Max Distance (km)"
              type="number"
              value={formData.maxDistance}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="maxTime"
              label="Max Time (mins)"
              type="number"
              value={formData.maxTime}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="vehicleCapacity"
              label="Vehicle Capacity (kg)"
              type="number"
              value={formData.vehicleCapacity}
              onChange={handleInputChange}
              fullWidth
              required
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="primary"
          >
            {selectedRoute ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RouteOptimization; 