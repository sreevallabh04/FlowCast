import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Warning as WarningIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useDispatch, useSelector } from 'react-redux';
import { fetchInventory, updateInventory, deleteInventory, addInventory } from '../../redux/actions/inventoryActions';

const InventoryManagement = () => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const { inventory, loading, error } = useSelector(state => state.inventory);
  
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    category: '',
    price: '',
    quantity: '',
    reorderPoint: '',
    expiryDate: ''
  });

  useEffect(() => {
    dispatch(fetchInventory());
  }, [dispatch]);

  const handleOpenDialog = (item = null) => {
    if (item) {
      setSelectedItem(item);
      setFormData({
        sku: item.sku,
        name: item.name,
        category: item.category,
        price: item.price,
        quantity: item.quantity,
        reorderPoint: item.reorderPoint,
        expiryDate: item.expiryDate || ''
      });
    } else {
      setSelectedItem(null);
      setFormData({
        sku: '',
        name: '',
        category: '',
        price: '',
        quantity: '',
        reorderPoint: '',
        expiryDate: ''
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedItem(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = () => {
    if (selectedItem) {
      dispatch(updateInventory(selectedItem.id, formData));
    } else {
      dispatch(addInventory(formData));
    }
    handleCloseDialog();
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      dispatch(deleteInventory(id));
    }
  };

  const getStatusColor = (item) => {
    if (item.quantity <= item.reorderPoint) {
      return theme.palette.error.main;
    }
    if (item.expiryDate && new Date(item.expiryDate) < new Date()) {
      return theme.palette.warning.main;
    }
    return theme.palette.success.main;
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
                Total Inventory Value
              </Typography>
              <Typography variant="h4">
                ${inventory.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Low Stock Items
              </Typography>
              <Typography variant="h4">
                {inventory.filter(item => item.quantity <= item.reorderPoint).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Expiring Items
              </Typography>
              <Typography variant="h4">
                {inventory.filter(item => item.expiryDate && new Date(item.expiryDate) < new Date()).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Inventory Table */}
        <Grid item xs={12}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h5">Inventory Items</Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Add Item
            </Button>
          </Box>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>SKU</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Price</TableCell>
                  <TableCell>Quantity</TableCell>
                  <TableCell>Reorder Point</TableCell>
                  <TableCell>Expiry Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {inventory.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.sku}</TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.category}</TableCell>
                    <TableCell>${item.price.toFixed(2)}</TableCell>
                    <TableCell>{item.quantity}</TableCell>
                    <TableCell>{item.reorderPoint}</TableCell>
                    <TableCell>{item.expiryDate || 'N/A'}</TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {item.quantity <= item.reorderPoint && (
                          <WarningIcon color="error" style={{ marginRight: 8 }} />
                        )}
                        {item.expiryDate && new Date(item.expiryDate) < new Date() && (
                          <ErrorIcon color="warning" style={{ marginRight: 8 }} />
                        )}
                        <Typography
                          variant="body2"
                          style={{ color: getStatusColor(item) }}
                        >
                          {item.quantity <= item.reorderPoint
                            ? 'Low Stock'
                            : item.expiryDate && new Date(item.expiryDate) < new Date()
                            ? 'Expired'
                            : 'In Stock'}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <IconButton
                        color="primary"
                        onClick={() => handleOpenDialog(item)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        color="error"
                        onClick={() => handleDelete(item.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedItem ? 'Edit Inventory Item' : 'Add Inventory Item'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <TextField
              name="sku"
              label="SKU"
              value={formData.sku}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="name"
              label="Name"
              value={formData.name}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="category"
              label="Category"
              value={formData.category}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="price"
              label="Price"
              type="number"
              value={formData.price}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="quantity"
              label="Quantity"
              type="number"
              value={formData.quantity}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="reorderPoint"
              label="Reorder Point"
              type="number"
              value={formData.reorderPoint}
              onChange={handleInputChange}
              fullWidth
              required
            />
            <TextField
              name="expiryDate"
              label="Expiry Date"
              type="date"
              value={formData.expiryDate}
              onChange={handleInputChange}
              fullWidth
              InputLabelProps={{ shrink: true }}
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
            {selectedItem ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InventoryManagement; 