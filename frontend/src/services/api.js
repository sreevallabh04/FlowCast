import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Demand prediction
  predictDemand: (data) => api.post('/predict-demand', data),
  
  // Inventory optimization
  optimizeInventory: (data) => api.post('/optimize-inventory', data),
  
  // Route optimization
  optimizeRoutes: (data) => api.post('/optimize-routes', data),
  
  // Analytics
  getAnalytics: () => api.get('/analytics'),
  
  // Data management
  getData: (params) => api.get('/data', { params }),
  updateData: (id, data) => api.put(`/data/${id}`, data),
  deleteData: (id) => api.delete(`/data/${id}`),
  
  // User management
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),
  
  // Settings
  getSettings: () => api.get('/settings'),
  updateSettings: (data) => api.put('/settings', data),
};

// Error handling
export const handleApiError = (error) => {
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    console.error('API Error:', error.response.data);
    return error.response.data;
  } else if (error.request) {
    // The request was made but no response was received
    console.error('API Error: No response received');
    return { error: 'No response received from server' };
  } else {
    // Something happened in setting up the request that triggered an Error
    console.error('API Error:', error.message);
    return { error: error.message };
  }
};

// Cache management
const cache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export const cachedApiCall = async (key, apiCall) => {
  const cachedData = cache.get(key);
  if (cachedData && Date.now() - cachedData.timestamp < CACHE_DURATION) {
    return cachedData.data;
  }

  try {
    const response = await apiCall();
    cache.set(key, {
      data: response.data,
      timestamp: Date.now(),
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

// Batch requests
export const batchApiCalls = async (calls) => {
  try {
    const responses = await Promise.all(calls);
    return responses.map(response => response.data);
  } catch (error) {
    throw handleApiError(error);
  }
};

export default api; 