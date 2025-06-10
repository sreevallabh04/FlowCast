import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Async thunks
export const fetchInventory = createAsyncThunk(
  'inventory/fetchInventory',
  async (_, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/inventory`, {
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

export const addItem = createAsyncThunk(
  'inventory/addItem',
  async (itemData, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.post(`${API_URL}/inventory`, itemData, {
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

export const updateItem = createAsyncThunk(
  'inventory/updateItem',
  async ({ id, itemData }, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.put(`${API_URL}/inventory/${id}`, itemData, {
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

export const deleteItem = createAsyncThunk(
  'inventory/deleteItem',
  async (id, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      await axios.delete(`${API_URL}/inventory/${id}`, {
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

export const searchInventory = createAsyncThunk(
  'inventory/searchInventory',
  async (searchParams, { rejectWithValue, getState }) => {
    try {
      const { auth } = getState();
      const response = await axios.get(`${API_URL}/inventory/search`, {
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
  items: [],
  filteredItems: [],
  loading: false,
  error: null,
  searchParams: {
    query: '',
    category: '',
    status: '',
    sortBy: 'name',
    sortOrder: 'asc'
  }
};

const inventorySlice = createSlice({
  name: 'inventory',
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
      state.filteredItems = state.items;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch Inventory
      .addCase(fetchInventory.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInventory.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
        state.filteredItems = action.payload;
      })
      .addCase(fetchInventory.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Add Item
      .addCase(addItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addItem.fulfilled, (state, action) => {
        state.loading = false;
        state.items.push(action.payload);
        state.filteredItems.push(action.payload);
      })
      .addCase(addItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Update Item
      .addCase(updateItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateItem.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
          state.filteredItems[index] = action.payload;
        }
      })
      .addCase(updateItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Delete Item
      .addCase(deleteItem.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteItem.fulfilled, (state, action) => {
        state.loading = false;
        state.items = state.items.filter(item => item.id !== action.payload);
        state.filteredItems = state.filteredItems.filter(item => item.id !== action.payload);
      })
      .addCase(deleteItem.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Search Inventory
      .addCase(searchInventory.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchInventory.fulfilled, (state, action) => {
        state.loading = false;
        state.filteredItems = action.payload;
      })
      .addCase(searchInventory.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export const { clearError, setSearchParams, clearSearch } = inventorySlice.actions;
export default inventorySlice.reducer; 