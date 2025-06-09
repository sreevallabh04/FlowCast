import { configureStore } from '@reduxjs/toolkit';
import appReducer from './appSlice';
import dashboardReducer from './dashboardSlice';

const store = configureStore({
  reducer: {
    app: appReducer,
    dashboard: dashboardReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export default store; 