const express = require('express');
const {
  getInventory,
  getInventoryItem,
  createInventoryItem,
  updateInventoryItem,
  deleteInventoryItem,
  getInventoryStats,
  getLowStockItems,
  getExpiringItems
} = require('../controllers/inventoryController');

const router = express.Router();

const { protect, authorize } = require('../middleware/auth');

router
  .route('/')
  .get(protect, getInventory)
  .post(protect, createInventoryItem);

router
  .route('/:id')
  .get(protect, getInventoryItem)
  .put(protect, updateInventoryItem)
  .delete(protect, deleteInventoryItem);

router.get('/stats', protect, getInventoryStats);
router.get('/lowstock', protect, getLowStockItems);
router.get('/expiring', protect, getExpiringItems);

module.exports = router; 