const Inventory = require('../models/Inventory');

// @desc    Get all inventory items
// @route   GET /api/v1/inventory
// @access  Private
exports.getInventory = async (req, res, next) => {
  try {
    let query;

    // Copy req.query
    const reqQuery = { ...req.query };

    // Fields to exclude
    const removeFields = ['select', 'sort', 'page', 'limit'];

    // Loop over removeFields and delete them from reqQuery
    removeFields.forEach(param => delete reqQuery[param]);

    // Create query string
    let queryStr = JSON.stringify(reqQuery);

    // Create operators ($gt, $gte, etc)
    queryStr = queryStr.replace(/\b(gt|gte|lt|lte|in)\b/g, match => `$${match}`);

    // Finding resource
    query = Inventory.find(JSON.parse(queryStr)).populate({
      path: 'user',
      select: 'name email'
    });

    // Select Fields
    if (req.query.select) {
      const fields = req.query.select.split(',').join(' ');
      query = query.select(fields);
    }

    // Sort
    if (req.query.sort) {
      const sortBy = req.query.sort.split(',').join(' ');
      query = query.sort(sortBy);
    } else {
      query = query.sort('-createdAt');
    }

    // Pagination
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 25;
    const startIndex = (page - 1) * limit;
    const endIndex = page * limit;
    const total = await Inventory.countDocuments();

    query = query.skip(startIndex).limit(limit);

    // Executing query
    const inventory = await query;

    // Pagination result
    const pagination = {};

    if (endIndex < total) {
      pagination.next = {
        page: page + 1,
        limit
      };
    }

    if (startIndex > 0) {
      pagination.prev = {
        page: page - 1,
        limit
      };
    }

    res.status(200).json({
      success: true,
      count: inventory.length,
      pagination,
      data: inventory
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Get single inventory item
// @route   GET /api/v1/inventory/:id
// @access  Private
exports.getInventoryItem = async (req, res, next) => {
  try {
    const inventory = await Inventory.findById(req.params.id).populate({
      path: 'user',
      select: 'name email'
    });

    if (!inventory) {
      return res.status(404).json({
        success: false,
        message: `Inventory item not found with id of ${req.params.id}`
      });
    }

    res.status(200).json({
      success: true,
      data: inventory
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Create new inventory item
// @route   POST /api/v1/inventory
// @access  Private
exports.createInventoryItem = async (req, res, next) => {
  try {
    // Add user to req.body
    req.body.user = req.user.id;

    const inventory = await Inventory.create(req.body);

    res.status(201).json({
      success: true,
      data: inventory
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Update inventory item
// @route   PUT /api/v1/inventory/:id
// @access  Private
exports.updateInventoryItem = async (req, res, next) => {
  try {
    let inventory = await Inventory.findById(req.params.id);

    if (!inventory) {
      return res.status(404).json({
        success: false,
        message: `Inventory item not found with id of ${req.params.id}`
      });
    }

    // Make sure user is inventory owner
    if (inventory.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to update this inventory item`
      });
    }

    inventory = await Inventory.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true
    });

    res.status(200).json({
      success: true,
      data: inventory
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Delete inventory item
// @route   DELETE /api/v1/inventory/:id
// @access  Private
exports.deleteInventoryItem = async (req, res, next) => {
  try {
    const inventory = await Inventory.findById(req.params.id);

    if (!inventory) {
      return res.status(404).json({
        success: false,
        message: `Inventory item not found with id of ${req.params.id}`
      });
    }

    // Make sure user is inventory owner
    if (inventory.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to delete this inventory item`
      });
    }

    await inventory.remove();

    res.status(200).json({
      success: true,
      data: {}
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Get inventory statistics
// @route   GET /api/v1/inventory/stats
// @access  Private
exports.getInventoryStats = async (req, res, next) => {
  try {
    const stats = await Inventory.aggregate([
      {
        $match: { user: req.user.id }
      },
      {
        $group: {
          _id: '$category',
          totalItems: { $sum: 1 },
          totalValue: { $sum: { $multiply: ['$price', '$quantity'] } },
          averagePrice: { $avg: '$price' },
          lowStock: {
            $sum: {
              $cond: [{ $lte: ['$quantity', '$reorderPoint'] }, 1, 0]
            }
          }
        }
      },
      {
        $sort: { totalValue: -1 }
      }
    ]);

    res.status(200).json({
      success: true,
      data: stats
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Get low stock items
// @route   GET /api/v1/inventory/lowstock
// @access  Private
exports.getLowStockItems = async (req, res, next) => {
  try {
    const lowStockItems = await Inventory.find({
      user: req.user.id,
      $expr: { $lte: ['$quantity', '$reorderPoint'] }
    });

    res.status(200).json({
      success: true,
      count: lowStockItems.length,
      data: lowStockItems
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Get expiring items
// @route   GET /api/v1/inventory/expiring
// @access  Private
exports.getExpiringItems = async (req, res, next) => {
  try {
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

    const expiringItems = await Inventory.find({
      user: req.user.id,
      expiryDate: { $exists: true, $lte: thirtyDaysFromNow }
    });

    res.status(200).json({
      success: true,
      count: expiringItems.length,
      data: expiringItems
    });
  } catch (err) {
    next(err);
  }
}; 