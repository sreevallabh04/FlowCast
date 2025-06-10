import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Alert,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Map as MapIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchRoutes,
  addRoute,
  updateRoute,
  deleteRoute,
  optimizeRoute,
  searchRoutes
} from '../../redux/slices/routesSlice';

const statuses = ['Pending', 'In Progress', 'Completed', 'Cancelled'];
const priorities = ['Low', 'Medium', 'High', 'Urgent'];

const Routes = () => {
  const dispatch = useDispatch();
  const { routes, filteredRoutes, loading, error } = useSelector(state => state.routes);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [searchParams, setSearchParams] = useState({
    query: '',
    status: '',
    dateRange: {
      start: null,
      end: null
    }
  });

  const [formData, setFormData] = useState({
    name: '',
    startLocation: '',
    endLocation: '',
    stops: [],
    priority: '',
    status: '',
    estimatedTime: '',
    distance: '',
    notes: ''
  });

  useEffect(() => {
    dispatch(fetchRoutes());
  }, [dispatch]);

  const handleOpenDialog = (route = null) => {
    if (route) {
      setSelectedRoute(route);
      setFormData({
        name: route.name,
        startLocation: route.startLocation,
        endLocation: route.endLocation,
        stops: route.stops,
        priority: route.priority,
        status: route.status,
        estimatedTime: route.estimatedTime,
        distance: route.distance,
        notes: route.notes
      });
    } else {
      setSelectedRoute(null);
      setFormData({
        name: '',
        startLocation: '',
        endLocation: '',
        stops: [],
        priority: '',
        status: '',
        estimatedTime: '',
        distance: '',
        notes: ''
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
      dispatch(updateRoute({ id: selectedRoute.id, routeData: formData }));
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

  const handleOptimize = (id) => {
    dispatch(optimizeRoute({ id, optimizationParams: {} }));
  };

  const handleSearch = () => {
    dispatch(searchRoutes(searchParams));
  };

  const columns = [
    { field: 'name', headerName: 'Route Name', flex: 1 },
    { field: 'startLocation', headerName: 'Start', flex: 1 },
    { field: 'endLocation', headerName: 'End', flex: 1 },
    { field: 'priority', headerName: 'Priority', flex: 1 },
    { field: 'status', headerName: 'Status', flex: 1 },
    {
      field: 'stops',
      headerName: 'Stops',
      flex: 1,
      renderCell: (params) => (
        <Box>
          {params.row.stops.map((stop, index) => (
            <Chip
              key={index}
              label={stop}
              size="small"
              sx={{ mr: 0.5 }}
            />
          ))}
        </Box>
      )
    },
    {
      field: 'actions',
      headerName: 'Actions',
      flex: 1,
      renderCell: (params) => (
        <Box>
          <IconButton
            color="primary"
            onClick={() => handleOpenDialog(params.row)}
          >
            <EditIcon />
          </IconButton>
          <IconButton
            color="success"
            onClick={() => handleOptimize(params.row.id)}
          >
            <TimelineIcon />
          </IconButton>
          <IconButton
            color="error"
            onClick={() => handleDelete(params.row.id)}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      )
    }
  ];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Search"
                value={searchParams.query}
                onChange={(e) => setSearchParams(prev => ({ ...prev, query: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Status"
                value={searchParams.status}
                onChange={(e) => setSearchParams(prev => ({ ...prev, status: e.target.value }))}
              >
                <MenuItem value="">All</MenuItem>
                {statuses.map(status => (
                  <MenuItem key={status} value={status}>
                    {status}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <DatePicker
                label="Start Date"
                value={searchParams.dateRange.start}
                onChange={(date) => setSearchParams(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange, start: date }
                }))}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={handleSearch}
              >
                Search
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Routes</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Add Route
            </Button>
          </Box>

          <Box height={400}>
            <DataGrid
              rows={filteredRoutes}
              columns={columns}
              pageSize={5}
              rowsPerPageOptions={[5, 10, 20]}
              checkboxSelection
              disableSelectionOnClick
            />
          </Box>
        </CardContent>
      </Card>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedRoute ? 'Edit Route' : 'Add New Route'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <TextField
              fullWidth
              label="Route Name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
            />
            <TextField
              fullWidth
              label="Start Location"
              name="startLocation"
              value={formData.startLocation}
              onChange={handleInputChange}
              required
            />
            <TextField
              fullWidth
              label="End Location"
              name="endLocation"
              value={formData.endLocation}
              onChange={handleInputChange}
              required
            />
            <TextField
              fullWidth
              select
              label="Priority"
              name="priority"
              value={formData.priority}
              onChange={handleInputChange}
              required
            >
              {priorities.map(priority => (
                <MenuItem key={priority} value={priority}>
                  {priority}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              select
              label="Status"
              name="status"
              value={formData.status}
              onChange={handleInputChange}
              required
            >
              {statuses.map(status => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              label="Estimated Time (hours)"
              name="estimatedTime"
              type="number"
              value={formData.estimatedTime}
              onChange={handleInputChange}
              required
            />
            <TextField
              fullWidth
              label="Distance (km)"
              name="distance"
              type="number"
              value={formData.distance}
              onChange={handleInputChange}
              required
            />
            <TextField
              fullWidth
              label="Notes"
              name="notes"
              multiline
              rows={4}
              value={formData.notes}
              onChange={handleInputChange}
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

export default Routes; 