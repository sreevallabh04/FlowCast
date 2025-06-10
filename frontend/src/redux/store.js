import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { combineReducers } from 'redux';

// Import reducers
import authReducer from './slices/authSlice';
import inventoryReducer from './slices/inventorySlice';
import routesReducer from './slices/routesSlice';
import analyticsReducer from './slices/analyticsSlice';
import settingsReducer from './slices/settingsSlice';

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['auth', 'settings'] // Only persist these reducers
};

const rootReducer = combineReducers({
  auth: authReducer,
  inventory: inventoryReducer,
  routes: routesReducer,
  analytics: analyticsReducer,
  settings: settingsReducer
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE']
      }
    })
});

export const persistor = persistStore(store); 