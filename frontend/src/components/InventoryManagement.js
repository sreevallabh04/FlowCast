import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import axios from 'axios';

const InventoryManagement = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState({
    product_id: '',
    store_id: '',
    current_stock: 0,
    safety_stock: 0,
    reorder_point: 0
  });

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await axios.get('/api/inventory');
      setInventory(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch inventory data');
      setLoading(false);
    }
  };

  const handleOpenDialog = (item = null) => {
    if (item) {
      setSelectedItem(item);
      setFormData({
        product_id: item.product_id,
        store_id: item.store_id,
        current_stock: item.current_stock,
        safety_stock: item.safety_stock,
        reorder_point: item.reorder_point
      });
    } else {
      setSelectedItem(null);
      setFormData({
        product_id: '',
        store_id: '',
        current_stock: 0,
        safety_stock: 0,
        reorder_point: 0
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedItem(null);
  };

  const handleSubmit = async () => {
    try {
      if (selectedItem) {
        await axios.put(`/api/inventory/${selectedItem.id}`, formData);
      } else {
        await axios.post('/api/inventory', formData);
      }
      fetchInventory();
      handleCloseDialog();
    } catch (err) {
      setError('Failed to save inventory item');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        await axios.delete(`/api/inventory/${id}`);
        fetchInventory();
      } catch (err) {
        setError('Failed to delete inventory item');
      }
    }
  };

  const getStockStatus = (current, safety) => {
    if (current <= 0) return { label: 'Out of Stock', color: 'error' };
    if (current <= safety) return { label: 'Low Stock', color: 'warning' };
    return { label: 'In Stock', color: 'success' };
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Inventory Management</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Item
        </Button>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell>Store</TableCell>
              <TableCell align="right">Current Stock</TableCell>
              <TableCell align="right">Safety Stock</TableCell>
              <TableCell align="right">Reorder Point</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {inventory.map((item) => {
              const status = getStockStatus(item.current_stock, item.safety_stock);
              return (
                <TableRow key={item.id}>
                  <TableCell>{item.product_name}</TableCell>
                  <TableCell>{item.store_name}</TableCell>
                  <TableCell align="right">{item.current_stock}</TableCell>
                  <TableCell align="right">{item.safety_stock}</TableCell>
                  <TableCell align="right">{item.reorder_point}</TableCell>
                  <TableCell>
                    <Chip
                      label={status.label}
                      color={status.color}
                      size="small"
                      icon={status.color === 'warning' ? <WarningIcon /> : null}
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(item)}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(item.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedItem ? 'Edit Inventory Item' : 'Add Inventory Item'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Product ID"
                value={formData.product_id}
                onChange={(e) =>
                  setFormData({ ...formData, product_id: e.target.value })
                }
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Store ID"
                value={formData.store_id}
                onChange={(e) =>
                  setFormData({ ...formData, store_id: e.target.value })
                }
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Current Stock"
                value={formData.current_stock}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    current_stock: parseInt(e.target.value)
                  })
                }
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Safety Stock"
                value={formData.safety_stock}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    safety_stock: parseInt(e.target.value)
                  })
                }
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Reorder Point"
                value={formData.reorder_point}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    reorder_point: parseInt(e.target.value)
                  })
                }
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            {selectedItem ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InventoryManagement; 