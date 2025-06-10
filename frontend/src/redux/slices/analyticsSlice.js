import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Async thunks
export const fetchAnalytics = createAsyncThunk(
  'analytics/fetchAnalytics',
  async (timeRange, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/analytics`, {
        params: timeRange,
        headers: {
          Authorization: `Bearer ${auth.token}`
        }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data.message);
    }
  }
);

export const fetchInventoryAnalytics = createAsyncThunk(
  'analytics/fetchInventoryAnalytics',
  async (timeRange, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/analytics/inventory`, {
        params: timeRange,
        headers: {
          Authorization: `Bearer ${auth.token}`
        }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data.message);
    }
  }
);

export const fetchRouteAnalytics = createAsyncThunk(
  'analytics/fetchRouteAnalytics',
  async (timeRange, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/analytics/routes`, {
        params: timeRange,
        headers: {
          Authorization: `Bearer ${auth.token}`
        }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data.message);
    }
  }
);

export const fetchPerformanceMetrics = createAsyncThunk(
  'analytics/fetchPerformanceMetrics',
  async (timeRange, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/analytics/performance`, {
        params: timeRange,
        headers: {
          Authorization: `Bearer ${auth.token}`
        }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data.message);
    }
  }
);

const initialState = {
  overview: {
    totalItems: 0,
    activeRoutes: 0,
    pendingDeliveries: 0,
    lowStockItems: 0
  },
  inventory: {
    stockLevels: [],
    categoryDistribution: [],
    topItems: [],
    lowStockAlerts: []
  },
  routes: {
    routeEfficiency: [],
    deliveryTimes: [],
    routeUtilization: [],
    topRoutes: []
  },
  performance: {
    onTimeDelivery: 0,
    routeOptimization: 0,
    inventoryTurnover: 0,
    costSavings: 0
  },
  loading: false,
  error: null,
  timeRange: {
    start: new Date(new Date().setDate(new Date().getDate() - 30)),
    end: new Date()
  }
};

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setTimeRange: (state, action) => {
      state.timeRange = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch Analytics
      .addCase(fetchAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        state.overview = action.payload;
      })
      .addCase(fetchAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch Inventory Analytics
      .addCase(fetchInventoryAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInventoryAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        state.inventory = action.payload;
      })
      .addCase(fetchInventoryAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch Route Analytics
      .addCase(fetchRouteAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRouteAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        state.routes = action.payload;
      })
      .addCase(fetchRouteAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch Performance Metrics
      .addCase(fetchPerformanceMetrics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPerformanceMetrics.fulfilled, (state, action) => {
        state.loading = false;
        state.performance = action.payload;
      })
      .addCase(fetchPerformanceMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export const { clearError, setTimeRange } = analyticsSlice.actions;
export default analyticsSlice.reducer; 