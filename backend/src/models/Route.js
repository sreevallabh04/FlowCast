const mongoose = require('mongoose');

const routeSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Please add a name'],
    trim: true,
    maxlength: [100, 'Name cannot be more than 100 characters']
  },
  startLocation: {
    type: String,
    required: [true, 'Please add a start location']
  },
  endLocation: {
    type: String,
    required: [true, 'Please add an end location']
  },
  stops: [{
    location: String,
    order: Number,
    estimatedTime: Number,
    status: {
      type: String,
      enum: ['Pending', 'Completed', 'Skipped'],
      default: 'Pending'
    }
  }],
  priority: {
    type: String,
    enum: ['Low', 'Medium', 'High', 'Urgent'],
    default: 'Medium'
  },
  status: {
    type: String,
    enum: ['Pending', 'In Progress', 'Completed', 'Cancelled'],
    default: 'Pending'
  },
  estimatedTime: {
    type: Number,
    required: [true, 'Please add estimated time in hours']
  },
  distance: {
    type: Number,
    required: [true, 'Please add distance in kilometers']
  },
  notes: {
    type: String,
    trim: true,
    maxlength: [500, 'Notes cannot be more than 500 characters']
  },
  assignedTo: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  items: [{
    item: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Inventory'
    },
    quantity: Number
  }],
  optimizationParams: {
    fuelEfficiency: { type: Number, default: 0 },
    timeEfficiency: { type: Number, default: 0 },
    costEfficiency: { type: Number, default: 0 }
  },
  actualTime: Number,
  actualDistance: Number,
  startTime: Date,
  endTime: Date,
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Create indexes
routeSchema.index({ name: 1 });
routeSchema.index({ status: 1 });
routeSchema.index({ priority: 1 });
routeSchema.index({ user: 1 });
routeSchema.index({ assignedTo: 1 });
routeSchema.index({ 'stops.location': 1 });

// Virtual for route efficiency
routeSchema.virtual('efficiency').get(function() {
  if (!this.actualTime || !this.actualDistance) return null;
  
  const timeEfficiency = (this.estimatedTime / this.actualTime) * 100;
  const distanceEfficiency = (this.distance / this.actualDistance) * 100;
  
  return (timeEfficiency + distanceEfficiency) / 2;
});

// Update status based on stops
routeSchema.methods.updateStatus = function() {
  const allCompleted = this.stops.every(stop => stop.status === 'Completed');
  const anySkipped = this.stops.some(stop => stop.status === 'Skipped');
  
  if (allCompleted) {
    this.status = 'Completed';
    this.endTime = new Date();
  } else if (anySkipped) {
    this.status = 'In Progress';
  }
};

module.exports = mongoose.model('Route', routeSchema); 