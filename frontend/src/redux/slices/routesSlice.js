import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Async thunks
export const fetchRoutes = createAsyncThunk(
  'routes/fetchRoutes',
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/routes`, {
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

export const addRoute = createAsyncThunk(
  'routes/addRoute',
  async (routeData, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.post(`${API_URL}/routes`, routeData, {
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

export const updateRoute = createAsyncThunk(
  'routes/updateRoute',
  async ({ id, routeData }, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.put(`${API_URL}/routes/${id}`, routeData, {
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

export const deleteRoute = createAsyncThunk(
  'routes/deleteRoute',
  async (id, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      await axios.delete(`${API_URL}/routes/${id}`, {
        headers: {
          Authorization: `Bearer ${auth.token}`
        }
      });
      return id;
    } catch (error) {
      return rejectWithValue(error.response.data.message);
    }
  }
);

export const optimizeRoute = createAsyncThunk(
  'routes/optimizeRoute',
  async ({ id, optimizationParams }, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.post(`${API_URL}/routes/${id}/optimize`, optimizationParams, {
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

export const searchRoutes = createAsyncThunk(
  'routes/searchRoutes',
  async (searchParams, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/routes/search`, {
        params: searchParams,
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
  routes: [],
  filteredRoutes: [],
  loading: false,
  error: null,
  searchParams: {
    query: '',
    status: '',
    dateRange: {
      start: null,
      end: null
    },
    sortBy: 'date',
    sortOrder: 'desc'
  }
};

const routesSlice = createSlice({
  name: 'routes',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setSearchParams: (state, action) => {
      state.searchParams = {
        ...state.searchParams,
        ...action.payload
      };
    },
    clearSearch: (state) => {
      state.searchParams = initialState.searchParams;
      state.filteredRoutes = state.routes;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch Routes
      .addCase(fetchRoutes.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRoutes.fulfilled, (state, action) => {
        state.loading = false;
        state.routes = action.payload;
        state.filteredRoutes = action.payload;
      })
      .addCase(fetchRoutes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Add Route
      .addCase(addRoute.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addRoute.fulfilled, (state, action) => {
        state.loading = false;
        state.routes.push(action.payload);
        state.filteredRoutes.push(action.payload);
      })
      .addCase(addRoute.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Update Route
      .addCase(updateRoute.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateRoute.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.routes.findIndex(route => route.id === action.payload.id);
        if (index !== -1) {
          state.routes[index] = action.payload;
          state.filteredRoutes[index] = action.payload;
        }
      })
      .addCase(updateRoute.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Delete Route
      .addCase(deleteRoute.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteRoute.fulfilled, (state, action) => {
        state.loading = false;
        state.routes = state.routes.filter(route => route.id !== action.payload);
        state.filteredRoutes = state.filteredRoutes.filter(route => route.id !== action.payload);
      })
      .addCase(deleteRoute.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Optimize Route
      .addCase(optimizeRoute.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(optimizeRoute.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.routes.findIndex(route => route.id === action.payload.id);
        if (index !== -1) {
          state.routes[index] = action.payload;
          state.filteredRoutes[index] = action.payload;
        }
      })
      .addCase(optimizeRoute.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Search Routes
      .addCase(searchRoutes.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchRoutes.fulfilled, (state, action) => {
        state.loading = false;
        state.filteredRoutes = action.payload;
      })
      .addCase(searchRoutes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export const { clearError, setSearchParams, clearSearch } = routesSlice.actions;
export default routesSlice.reducer; 