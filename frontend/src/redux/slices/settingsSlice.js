import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Async thunks
export const fetchSettings = createAsyncThunk(
  'settings/fetchSettings',
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/settings`, {
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

export const updateSettings = createAsyncThunk(
  'settings/updateSettings',
  async (settings, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.put(`${API_URL}/settings`, settings, {
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

export const addApiKey = createAsyncThunk(
  'settings/addApiKey',
  async (apiKeyData, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.post(`${API_URL}/settings/api-keys`, apiKeyData, {
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

export const updateApiKey = createAsyncThunk(
  'settings/updateApiKey',
  async ({ id, apiKeyData }, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.put(`${API_URL}/settings/api-keys/${id}`, apiKeyData, {
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

export const deleteApiKey = createAsyncThunk(
  'settings/deleteApiKey',
  async (id, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      await axios.delete(`${API_URL}/settings/api-keys/${id}`, {
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

const initialState = {
  settings: {
    notifications: {
      email: true,
      push: true,
      lowStock: true,
      expiringItems: true,
      deliveryUpdates: true
    },
    display: {
      darkMode: false,
      compactView: false,
      showCharts: true,
      itemsPerPage: 10
    },
    data: {
      autoBackup: true,
      backupFrequency: 'daily',
      retentionPeriod: 30,
      exportFormat: 'csv'
    },
    apiKeys: []
  },
  loading: false,
  error: null
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch Settings
      .addCase(fetchSettings.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSettings.fulfilled, (state, action) => {
        state.loading = false;
        state.settings = action.payload;
      })
      .addCase(fetchSettings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Update Settings
      .addCase(updateSettings.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateSettings.fulfilled, (state, action) => {
        state.loading = false;
        state.settings = action.payload;
      })
      .addCase(updateSettings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Add API Key
      .addCase(addApiKey.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addApiKey.fulfilled, (state, action) => {
        state.loading = false;
        state.settings.apiKeys.push(action.payload);
      })
      .addCase(addApiKey.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Update API Key
      .addCase(updateApiKey.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateApiKey.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.settings.apiKeys.findIndex(key => key.id === action.payload.id);
        if (index !== -1) {
          state.settings.apiKeys[index] = action.payload;
        }
      })
      .addCase(updateApiKey.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Delete API Key
      .addCase(deleteApiKey.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteApiKey.fulfilled, (state, action) => {
        state.loading = false;
        state.settings.apiKeys = state.settings.apiKeys.filter(key => key.id !== action.payload);
      })
      .addCase(deleteApiKey.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export const { clearError } = settingsSlice.actions;
export default settingsSlice.reducer; 