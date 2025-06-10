import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton
} from '@mui/material';
import {
  Save as SaveIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchSettings,
  updateSettings,
  addApiKey,
  deleteApiKey,
  updateApiKey
} from '../../redux/actions/settingsActions';

const Settings = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const { settings, loading, error } = useSelector(state => state.settings);
  
  const [formData, setFormData] = useState({
    notifications: {
      email: true,
      push: true,
      lowStock: true,
      expiringItems: true,
      deliveryUpdates: true
    },
    display: {
      darkMode: false,
      compactView: false,
      showCharts: true,
      itemsPerPage: 10
    },
    data: {
      autoBackup: true,
      backupFrequency: 'daily',
      retentionPeriod: 30,
      exportFormat: 'csv'
    }
  });

  const [openApiKeyDialog, setOpenApiKeyDialog] = useState(false);
  const [selectedApiKey, setSelectedApiKey] = useState(null);
  const [apiKeyData, setApiKeyData] = useState({
    name: '',
    key: '',
    permissions: []
  });

  useEffect(() => {
    dispatch(fetchSettings());
  }, [dispatch]);

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleSave = () => {
    dispatch(updateSettings(formData));
  };

  const handleOpenApiKeyDialog = (apiKey = null) => {
    if (apiKey) {
      setSelectedApiKey(apiKey);
      setApiKeyData({
        name: apiKey.name,
        key: apiKey.key,
        permissions: apiKey.permissions
      });
    } else {
      setSelectedApiKey(null);
      setApiKeyData({
        name: '',
        key: '',
        permissions: []
      });
    }
    setOpenApiKeyDialog(true);
  };

  const handleCloseApiKeyDialog = () => {
    setOpenApiKeyDialog(false);
    setSelectedApiKey(null);
  };

  const handleSaveApiKey = () => {
    if (selectedApiKey) {
      dispatch(updateApiKey(selectedApiKey.id, apiKeyData));
    } else {
      dispatch(addApiKey(apiKeyData));
    }
    handleCloseApiKeyDialog();
  };

  const handleDeleteApiKey = (id) => {
    if (window.confirm('Are you sure you want to delete this API key?')) {
      dispatch(deleteApiKey(id));
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
        {/* Notifications Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notifications
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.notifications.email}
                      onChange={(e) => handleInputChange('notifications', 'email', e.target.checked)}
                    />
                  }
                  label="Email Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.notifications.push}
                      onChange={(e) => handleInputChange('notifications', 'push', e.target.checked)}
                    />
                  }
                  label="Push Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.notifications.lowStock}
                      onChange={(e) => handleInputChange('notifications', 'lowStock', e.target.checked)}
                    />
                  }
                  label="Low Stock Alerts"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.notifications.expiringItems}
                      onChange={(e) => handleInputChange('notifications', 'expiringItems', e.target.checked)}
                    />
                  }
                  label="Expiring Items Alerts"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.notifications.deliveryUpdates}
                      onChange={(e) => handleInputChange('notifications', 'deliveryUpdates', e.target.checked)}
                    />
                  }
                  label="Delivery Updates"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Display Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Display
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.display.darkMode}
                      onChange={(e) => handleInputChange('display', 'darkMode', e.target.checked)}
                    />
                  }
                  label="Dark Mode"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.display.compactView}
                      onChange={(e) => handleInputChange('display', 'compactView', e.target.checked)}
                    />
                  }
                  label="Compact View"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.display.showCharts}
                      onChange={(e) => handleInputChange('display', 'showCharts', e.target.checked)}
                    />
                  }
                  label="Show Charts"
                />
                <TextField
                  select
                  label="Items Per Page"
                  value={formData.display.itemsPerPage}
                  onChange={(e) => handleInputChange('display', 'itemsPerPage', e.target.value)}
                  fullWidth
                >
                  <MenuItem value={10}>10</MenuItem>
                  <MenuItem value={25}>25</MenuItem>
                  <MenuItem value={50}>50</MenuItem>
                  <MenuItem value={100}>100</MenuItem>
                </TextField>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Data Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Management
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.data.autoBackup}
                      onChange={(e) => handleInputChange('data', 'autoBackup', e.target.checked)}
                    />
                  }
                  label="Automatic Backup"
                />
                <TextField
                  select
                  label="Backup Frequency"
                  value={formData.data.backupFrequency}
                  onChange={(e) => handleInputChange('data', 'backupFrequency', e.target.value)}
                  fullWidth
                >
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                </TextField>
                <TextField
                  type="number"
                  label="Retention Period (days)"
                  value={formData.data.retentionPeriod}
                  onChange={(e) => handleInputChange('data', 'retentionPeriod', e.target.value)}
                  fullWidth
                />
                <TextField
                  select
                  label="Export Format"
                  value={formData.data.exportFormat}
                  onChange={(e) => handleInputChange('data', 'exportFormat', e.target.value)}
                  fullWidth
                >
                  <MenuItem value="csv">CSV</MenuItem>
                  <MenuItem value="json">JSON</MenuItem>
                  <MenuItem value="excel">Excel</MenuItem>
                </TextField>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* API Keys */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">API Keys</Typography>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={() => handleOpenApiKeyDialog()}
                >
                  Add Key
                </Button>
              </Box>
              <List>
                {settings.apiKeys?.map(apiKey => (
                  <ListItem key={apiKey.id}>
                    <ListItemText
                      primary={apiKey.name}
                      secondary={`Created: ${new Date(apiKey.createdAt).toLocaleDateString()}`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        color="primary"
                        onClick={() => handleOpenApiKeyDialog(apiKey)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        color="error"
                        onClick={() => handleDeleteApiKey(apiKey.id)}
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

      {/* Save Button */}
      <Box display="flex" justifyContent="flex-end" mt={3}>
        <Button
          variant="contained"
          color="primary"
          startIcon={<SaveIcon />}
          onClick={handleSave}
        >
          Save Changes
        </Button>
      </Box>

      {/* API Key Dialog */}
      <Dialog open={openApiKeyDialog} onClose={handleCloseApiKeyDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedApiKey ? 'Edit API Key' : 'Add API Key'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <TextField
              label="Name"
              value={apiKeyData.name}
              onChange={(e) => setApiKeyData(prev => ({ ...prev, name: e.target.value }))}
              fullWidth
              required
            />
            <TextField
              label="Key"
              value={apiKeyData.key}
              onChange={(e) => setApiKeyData(prev => ({ ...prev, key: e.target.value }))}
              fullWidth
              required
            />
            <TextField
              select
              label="Permissions"
              value={apiKeyData.permissions}
              onChange={(e) => setApiKeyData(prev => ({ ...prev, permissions: e.target.value }))}
              fullWidth
              SelectProps={{
                multiple: true
              }}
            >
              <MenuItem value="read">Read</MenuItem>
              <MenuItem value="write">Write</MenuItem>
              <MenuItem value="delete">Delete</MenuItem>
              <MenuItem value="admin">Admin</MenuItem>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseApiKeyDialog}>Cancel</Button>
          <Button
            onClick={handleSaveApiKey}
            variant="contained"
            color="primary"
          >
            {selectedApiKey ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings; 