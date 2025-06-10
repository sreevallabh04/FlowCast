const Route = require('../models/Route');

// @desc    Get all routes
// @route   GET /api/v1/routes
// @access  Private
exports.getRoutes = async (req, res, next) => {
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
    query = Route.find(JSON.parse(queryStr)).populate({
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
    const total = await Route.countDocuments();

    query = query.skip(startIndex).limit(limit);

    // Executing query
    const routes = await query;

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
      count: routes.length,
      pagination,
      data: routes
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Get single route
// @route   GET /api/v1/routes/:id
// @access  Private
exports.getRoute = async (req, res, next) => {
  try {
    const route = await Route.findById(req.params.id).populate({
      path: 'user',
      select: 'name email'
    });

    if (!route) {
      return res.status(404).json({
        success: false,
        message: `Route not found with id of ${req.params.id}`
      });
    }

    res.status(200).json({
      success: true,
      data: route
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Create new route
// @route   POST /api/v1/routes
// @access  Private
exports.createRoute = async (req, res, next) => {
  try {
    // Add user to req.body
    req.body.user = req.user.id;

    const route = await Route.create(req.body);

    res.status(201).json({
      success: true,
      data: route
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Update route
// @route   PUT /api/v1/routes/:id
// @access  Private
exports.updateRoute = async (req, res, next) => {
  try {
    let route = await Route.findById(req.params.id);

    if (!route) {
      return res.status(404).json({
        success: false,
        message: `Route not found with id of ${req.params.id}`
      });
    }

    // Make sure user is route owner
    if (route.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to update this route`
      });
    }

    route = await Route.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true
    });

    res.status(200).json({
      success: true,
      data: route
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Delete route
// @route   DELETE /api/v1/routes/:id
// @access  Private
exports.deleteRoute = async (req, res, next) => {
  try {
    const route = await Route.findById(req.params.id);

    if (!route) {
      return res.status(404).json({
        success: false,
        message: `Route not found with id of ${req.params.id}`
      });
    }

    // Make sure user is route owner
    if (route.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to delete this route`
      });
    }

    await route.remove();

    res.status(200).json({
      success: true,
      data: {}
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Optimize route
// @route   POST /api/v1/routes/:id/optimize
// @access  Private
exports.optimizeRoute = async (req, res, next) => {
  try {
    const route = await Route.findById(req.params.id);

    if (!route) {
      return res.status(404).json({
        success: false,
        message: `Route not found with id of ${req.params.id}`
      });
    }

    // Make sure user is route owner
    if (route.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to optimize this route`
      });
    }

    // TODO: Implement route optimization algorithm
    // This is a placeholder for the actual optimization logic
    const optimizedStops = [...route.stops].sort((a, b) => a.order - b.order);
    
    route.stops = optimizedStops;
    await route.save();

    res.status(200).json({
      success: true,
      data: route
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Update route status
// @route   PUT /api/v1/routes/:id/status
// @access  Private
exports.updateRouteStatus = async (req, res, next) => {
  try {
    const route = await Route.findById(req.params.id);

    if (!route) {
      return res.status(404).json({
        success: false,
        message: `Route not found with id of ${req.params.id}`
      });
    }

    // Make sure user is route owner
    if (route.user.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(401).json({
        success: false,
        message: `User ${req.user.id} is not authorized to update this route`
      });
    }

    route.status = req.body.status;
    
    if (req.body.status === 'In Progress' && !route.startTime) {
      route.startTime = new Date();
    } else if (req.body.status === 'Completed' && !route.endTime) {
      route.endTime = new Date();
    }

    await route.save();

    res.status(200).json({
      success: true,
      data: route
    });
  } catch (err) {
    next(err);
  }
};

// @desc    Get route statistics
// @route   GET /api/v1/routes/stats
// @access  Private
exports.getRouteStats = async (req, res, next) => {
  try {
    const stats = await Route.aggregate([
      {
        $match: { user: req.user.id }
      },
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 },
          totalDistance: { $sum: '$distance' },
          totalTime: { $sum: '$estimatedTime' },
          averageEfficiency: { $avg: '$efficiency' }
        }
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