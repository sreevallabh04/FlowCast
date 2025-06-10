const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Please add a name'],
    trim: true,
    maxlength: [50, 'Name cannot be more than 50 characters']
  },
  email: {
    type: String,
    required: [true, 'Please add an email'],
    unique: true,
    match: [
      /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/,
      'Please add a valid email'
    ]
  },
  password: {
    type: String,
    required: [true, 'Please add a password'],
    minlength: [6, 'Password must be at least 6 characters'],
    select: false
  },
  role: {
    type: String,
    enum: ['user', 'admin'],
    default: 'user'
  },
  settings: {
    notifications: {
      email: { type: Boolean, default: true },
      push: { type: Boolean, default: true },
      lowStock: { type: Boolean, default: true },
      expiringItems: { type: Boolean, default: true },
      deliveryUpdates: { type: Boolean, default: true }
    },
    display: {
      darkMode: { type: Boolean, default: false },
      compactView: { type: Boolean, default: false },
      showCharts: { type: Boolean, default: true },
      itemsPerPage: { type: Number, default: 10 }
    },
    data: {
      autoBackup: { type: Boolean, default: true },
      backupFrequency: { type: String, default: 'daily' },
      retentionPeriod: { type: Number, default: 30 },
      exportFormat: { type: String, default: 'csv' }
    }
  },
  apiKeys: [{
    name: String,
    key: String,
    permissions: [String],
    createdAt: { type: Date, default: Date.now }
  }],
  resetPasswordToken: String,
  resetPasswordExpire: Date,
  createdAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Encrypt password using bcrypt
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    next();
  }

  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
});

// Sign JWT and return
userSchema.methods.getSignedJwtToken = function() {
  return jwt.sign({ id: this._id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRE
  });
};

// Match user entered password to hashed password in database
userSchema.methods.matchPassword = async function(enteredPassword) {
  return await bcrypt.compare(enteredPassword, this.password);
};

// Create indexes
userSchema.index({ email: 1 });
userSchema.index({ 'apiKeys.key': 1 });

module.exports = mongoose.model('User', userSchema); 