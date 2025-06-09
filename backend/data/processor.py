import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
import joblib
import os
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class DataProcessor:
    def __init__(self, data_dir: str = 'data/generated', output_dir: str = 'data/processed'):
        """Initialize the data processor with input and output directories."""
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.timezone = 'UTC'
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize data storage
        self.products = None
        self.locations = None
        self.suppliers = None
        self.vehicles = None
        self.events = None
        self.weather_data = None
        self.sales_data = None
        self.inventory_data = None
        self.delivery_data = None
        
        # Initialize transformers
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def load_data(self) -> None:
        """Load all data from CSV files."""
        try:
            # Load static data
            self.products = pd.read_csv(f'{self.data_dir}/products.csv')
            self.locations = pd.read_csv(f'{self.data_dir}/locations.csv')
            self.suppliers = pd.read_csv(f'{self.data_dir}/suppliers.csv')
            self.vehicles = pd.read_csv(f'{self.data_dir}/vehicles.csv')
            self.events = pd.read_csv(f'{self.data_dir}/events.csv')
            
            # Load time-series data
            self.weather_data = pd.read_csv(f'{self.data_dir}/weather.csv')
            self.sales_data = pd.read_csv(f'{self.data_dir}/sales.csv')
            self.inventory_data = pd.read_csv(f'{self.data_dir}/inventory.csv')
            self.delivery_data = pd.read_csv(f'{self.data_dir}/deliveries.csv')
            
            # Convert date columns to datetime
            for df in [self.events, self.weather_data, self.sales_data, 
                      self.inventory_data, self.delivery_data]:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                if 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at'])
            
            self.logger.info("All data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def clean_data(self) -> None:
        """Clean and preprocess all data."""
        try:
            # Clean products data
            self._clean_products()
            
            # Clean locations data
            self._clean_locations()
            
            # Clean suppliers data
            self._clean_suppliers()
            
            # Clean vehicles data
            self._clean_vehicles()
            
            # Clean events data
            self._clean_events()
            
            # Clean weather data
            self._clean_weather()
            
            # Clean sales data
            self._clean_sales()
            
            # Clean inventory data
            self._clean_inventory()
            
            # Clean delivery data
            self._clean_deliveries()
            
            self.logger.info("All data cleaned successfully")
            
        except Exception as e:
            self.logger.error(f"Error cleaning data: {str(e)}")
            raise

    def _clean_products(self) -> None:
        """Clean products data."""
        # Remove duplicates
        self.products = self.products.drop_duplicates()
        
        # Handle missing values
        numeric_cols = ['unit_price', 'unit_weight', 'shelf_life_days', 
                       'reorder_point', 'safety_stock', 'lead_time_days']
        for col in numeric_cols:
            self.products[col] = self.products[col].fillna(self.products[col].median())
        
        # Remove outliers
        for col in numeric_cols:
            z_scores = stats.zscore(self.products[col])
            self.products = self.products[abs(z_scores) < 3]
        
        # Ensure positive values
        for col in numeric_cols:
            self.products[col] = self.products[col].abs()

    def _clean_locations(self) -> None:
        """Clean locations data."""
        # Remove duplicates
        self.locations = self.locations.drop_duplicates()
        
        # Handle missing values
        numeric_cols = ['latitude', 'longitude', 'capacity']
        for col in numeric_cols:
            self.locations[col] = self.locations[col].fillna(self.locations[col].median())
        
        # Ensure valid coordinates
        self.locations['latitude'] = self.locations['latitude'].clip(-90, 90)
        self.locations['longitude'] = self.locations['longitude'].clip(-180, 180)
        
        # Ensure positive capacity
        self.locations['capacity'] = self.locations['capacity'].abs()

    def _clean_suppliers(self) -> None:
        """Clean suppliers data."""
        # Remove duplicates
        self.suppliers = self.suppliers.drop_duplicates()
        
        # Handle missing values
        numeric_cols = ['lead_time_days', 'minimum_order_quantity', 'payment_terms_days']
        for col in numeric_cols:
            self.suppliers[col] = self.suppliers[col].fillna(self.suppliers[col].median())
        
        # Ensure positive values
        for col in numeric_cols:
            self.suppliers[col] = self.suppliers[col].abs()

    def _clean_vehicles(self) -> None:
        """Clean vehicles data."""
        # Remove duplicates
        self.vehicles = self.vehicles.drop_duplicates()
        
        # Handle missing values
        numeric_cols = ['capacity', 'fuel_efficiency', 'maintenance_cost_per_km']
        for col in numeric_cols:
            self.vehicles[col] = self.vehicles[col].fillna(self.vehicles[col].median())
        
        # Ensure positive values
        for col in numeric_cols:
            self.vehicles[col] = self.vehicles[col].abs()

    def _clean_events(self) -> None:
        """Clean events data."""
        # Remove duplicates
        self.events = self.events.drop_duplicates()
        
        # Handle missing values
        self.events['impact_factor'] = self.events['impact_factor'].fillna(1.0)
        
        # Ensure valid dates
        self.events['start_date'] = pd.to_datetime(self.events['start_date'])
        self.events['end_date'] = pd.to_datetime(self.events['end_date'])
        
        # Ensure end_date is after start_date
        mask = self.events['end_date'] < self.events['start_date']
        self.events.loc[mask, 'end_date'] = self.events.loc[mask, 'start_date'] + timedelta(days=1)

    def _clean_weather(self) -> None:
        """Clean weather data."""
        # Remove duplicates
        self.weather_data = self.weather_data.drop_duplicates()
        
        # Handle missing values
        numeric_cols = ['temperature', 'humidity', 'precipitation', 'wind_speed']
        for col in numeric_cols:
            self.weather_data[col] = self.weather_data[col].fillna(self.weather_data[col].median())
        
        # Ensure valid ranges
        self.weather_data['temperature'] = self.weather_data['temperature'].clip(-50, 50)
        self.weather_data['humidity'] = self.weather_data['humidity'].clip(0, 100)
        self.weather_data['precipitation'] = self.weather_data['precipitation'].clip(0, 1000)
        self.weather_data['wind_speed'] = self.weather_data['wind_speed'].clip(0, 200)

    def _clean_sales(self) -> None:
        """Clean sales data."""
        # Remove duplicates
        self.sales_data = self.sales_data.drop_duplicates()
        
        # Handle missing values
        self.sales_data['quantity'] = self.sales_data['quantity'].fillna(0)
        self.sales_data['revenue'] = self.sales_data['revenue'].fillna(0)
        
        # Ensure non-negative values
        self.sales_data['quantity'] = self.sales_data['quantity'].abs()
        self.sales_data['revenue'] = self.sales_data['revenue'].abs()

    def _clean_inventory(self) -> None:
        """Clean inventory data."""
        # Remove duplicates
        self.inventory_data = self.inventory_data.drop_duplicates()
        
        # Handle missing values
        numeric_cols = ['inventory_level', 'reorder_point', 'safety_stock']
        for col in numeric_cols:
            self.inventory_data[col] = self.inventory_data[col].fillna(0)
        
        # Ensure non-negative values
        for col in numeric_cols:
            self.inventory_data[col] = self.inventory_data[col].abs()

    def _clean_deliveries(self) -> None:
        """Clean delivery data."""
        # Remove duplicates
        self.delivery_data = self.delivery_data.drop_duplicates()
        
        # Handle missing values
        numeric_cols = ['distance', 'duration']
        for col in numeric_cols:
            self.delivery_data[col] = self.delivery_data[col].fillna(0)
        
        # Ensure positive values
        for col in numeric_cols:
            self.delivery_data[col] = self.delivery_data[col].abs()

    def engineer_features(self) -> None:
        """Engineer features for all data."""
        try:
            # Engineer features for sales data
            self._engineer_sales_features()
            
            # Engineer features for inventory data
            self._engineer_inventory_features()
            
            # Engineer features for delivery data
            self._engineer_delivery_features()
            
            self.logger.info("All features engineered successfully")
            
        except Exception as e:
            self.logger.error(f"Error engineering features: {str(e)}")
            raise

    def _engineer_sales_features(self) -> None:
        """Engineer features for sales data."""
        # Add time-based features
        self.sales_data['year'] = self.sales_data['date'].dt.year
        self.sales_data['month'] = self.sales_data['date'].dt.month
        self.sales_data['day'] = self.sales_data['date'].dt.day
        self.sales_data['dayofweek'] = self.sales_data['date'].dt.dayofweek
        self.sales_data['quarter'] = self.sales_data['date'].dt.quarter
        
        # Add lag features
        self.sales_data = self.sales_data.sort_values(['product_id', 'location_id', 'date'])
        self.sales_data['quantity_lag_1'] = self.sales_data.groupby(['product_id', 'location_id'])['quantity'].shift(1)
        self.sales_data['quantity_lag_7'] = self.sales_data.groupby(['product_id', 'location_id'])['quantity'].shift(7)
        self.sales_data['quantity_lag_30'] = self.sales_data.groupby(['product_id', 'location_id'])['quantity'].shift(30)
        
        # Add rolling statistics
        self.sales_data['quantity_rolling_mean_7'] = self.sales_data.groupby(['product_id', 'location_id'])['quantity'].rolling(7).mean().reset_index(0, drop=True)
        self.sales_data['quantity_rolling_std_7'] = self.sales_data.groupby(['product_id', 'location_id'])['quantity'].rolling(7).std().reset_index(0, drop=True)
        
        # Add product and location features
        self.sales_data = self.sales_data.merge(
            self.products[['product_id', 'category', 'unit_price']], 
            on='product_id', 
            how='left'
        )
        
        # Add weather features
        self.sales_data = self.sales_data.merge(
            self.weather_data[['date', 'location_id', 'temperature', 'precipitation']],
            on=['date', 'location_id'],
            how='left'
        )
        
        # Add event features
        self.sales_data = self.sales_data.merge(
            self.events[['start_date', 'end_date', 'location_id', 'impact_factor']],
            left_on=['date', 'location_id'],
            right_on=['start_date', 'location_id'],
            how='left'
        )
        self.sales_data['has_event'] = self.sales_data['impact_factor'].notna().astype(int)
        self.sales_data['impact_factor'] = self.sales_data['impact_factor'].fillna(1.0)

    def _engineer_inventory_features(self) -> None:
        """Engineer features for inventory data."""
        # Add time-based features
        self.inventory_data['year'] = self.inventory_data['date'].dt.year
        self.inventory_data['month'] = self.inventory_data['date'].dt.month
        self.inventory_data['day'] = self.inventory_data['date'].dt.day
        
        # Add inventory metrics
        self.inventory_data['days_of_inventory'] = self.inventory_data['inventory_level'] / self.inventory_data['reorder_point']
        self.inventory_data['stockout_risk'] = (self.inventory_data['inventory_level'] < self.inventory_data['safety_stock']).astype(int)
        
        # Add lag features
        self.inventory_data = self.inventory_data.sort_values(['product_id', 'location_id', 'date'])
        self.inventory_data['inventory_lag_1'] = self.inventory_data.groupby(['product_id', 'location_id'])['inventory_level'].shift(1)
        self.inventory_data['inventory_lag_7'] = self.inventory_data.groupby(['product_id', 'location_id'])['inventory_level'].shift(7)
        
        # Add rolling statistics
        self.inventory_data['inventory_rolling_mean_7'] = self.inventory_data.groupby(['product_id', 'location_id'])['inventory_level'].rolling(7).mean().reset_index(0, drop=True)
        self.inventory_data['inventory_rolling_std_7'] = self.inventory_data.groupby(['product_id', 'location_id'])['inventory_level'].rolling(7).std().reset_index(0, drop=True)

    def _engineer_delivery_features(self) -> None:
        """Engineer features for delivery data."""
        # Add time-based features
        self.delivery_data['year'] = self.delivery_data['date'].dt.year
        self.delivery_data['month'] = self.delivery_data['date'].dt.month
        self.delivery_data['day'] = self.delivery_data['date'].dt.day
        self.delivery_data['dayofweek'] = self.delivery_data['date'].dt.dayofweek
        
        # Add delivery metrics
        self.delivery_data['speed'] = self.delivery_data['distance'] / self.delivery_data['duration']
        self.delivery_data['is_delayed'] = (self.delivery_data['status'] == 'Delayed').astype(int)
        
        # Add vehicle features
        self.delivery_data = self.delivery_data.merge(
            self.vehicles[['vehicle_id', 'type', 'capacity', 'fuel_efficiency']],
            on='vehicle_id',
            how='left'
        )
        
        # Add location features
        self.delivery_data = self.delivery_data.merge(
            self.locations[['location_id', 'type']],
            left_on='pickup_location_id',
            right_on='location_id',
            how='left',
            suffixes=('', '_pickup')
        )
        self.delivery_data = self.delivery_data.merge(
            self.locations[['location_id', 'type']],
            left_on='delivery_location_id',
            right_on='location_id',
            how='left',
            suffixes=('', '_delivery')
        )

    def transform_data(self) -> None:
        """Transform data for machine learning."""
        try:
            # Transform sales data
            self._transform_sales_data()
            
            # Transform inventory data
            self._transform_inventory_data()
            
            # Transform delivery data
            self._transform_delivery_data()
            
            self.logger.info("All data transformed successfully")
            
        except Exception as e:
            self.logger.error(f"Error transforming data: {str(e)}")
            raise

    def _transform_sales_data(self) -> None:
        """Transform sales data for machine learning."""
        # Select features for transformation
        numeric_features = ['quantity', 'unit_price', 'temperature', 'precipitation']
        categorical_features = ['category', 'dayofweek']
        
        # Scale numeric features
        for feature in numeric_features:
            if feature not in self.scalers:
                self.scalers[feature] = StandardScaler()
            self.sales_data[f'{feature}_scaled'] = self.scalers[feature].fit_transform(
                self.sales_data[feature].values.reshape(-1, 1)
            )
        
        # Encode categorical features
        for feature in categorical_features:
            if feature not in self.encoders:
                self.encoders[feature] = OneHotEncoder(sparse=False)
            encoded = self.encoders[feature].fit_transform(
                self.sales_data[feature].values.reshape(-1, 1)
            )
            for i, category in enumerate(self.encoders[feature].categories_[0]):
                self.sales_data[f'{feature}_{category}'] = encoded[:, i]

    def _transform_inventory_data(self) -> None:
        """Transform inventory data for machine learning."""
        # Select features for transformation
        numeric_features = ['inventory_level', 'reorder_point', 'safety_stock']
        
        # Scale numeric features
        for feature in numeric_features:
            if feature not in self.scalers:
                self.scalers[feature] = StandardScaler()
            self.inventory_data[f'{feature}_scaled'] = self.scalers[feature].fit_transform(
                self.inventory_data[feature].values.reshape(-1, 1)
            )

    def _transform_delivery_data(self) -> None:
        """Transform delivery data for machine learning."""
        # Select features for transformation
        numeric_features = ['distance', 'duration', 'speed']
        categorical_features = ['type', 'type_pickup', 'type_delivery']
        
        # Scale numeric features
        for feature in numeric_features:
            if feature not in self.scalers:
                self.scalers[feature] = StandardScaler()
            self.delivery_data[f'{feature}_scaled'] = self.scalers[feature].fit_transform(
                self.delivery_data[feature].values.reshape(-1, 1)
            )
        
        # Encode categorical features
        for feature in categorical_features:
            if feature not in self.encoders:
                self.encoders[feature] = OneHotEncoder(sparse=False)
            encoded = self.encoders[feature].fit_transform(
                self.delivery_data[feature].values.reshape(-1, 1)
            )
            for i, category in enumerate(self.encoders[feature].categories_[0]):
                self.delivery_data[f'{feature}_{category}'] = encoded[:, i]

    def save_processed_data(self) -> None:
        """Save processed data and transformers."""
        try:
            # Save processed data
            self.sales_data.to_csv(f'{self.output_dir}/sales_processed.csv', index=False)
            self.inventory_data.to_csv(f'{self.output_dir}/inventory_processed.csv', index=False)
            self.delivery_data.to_csv(f'{self.output_dir}/deliveries_processed.csv', index=False)
            
            # Save transformers
            joblib.dump(self.scalers, f'{self.output_dir}/scalers.joblib')
            joblib.dump(self.encoders, f'{self.output_dir}/encoders.joblib')
            
            self.logger.info("Processed data and transformers saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving processed data: {str(e)}")
            raise

    def load_processed_data(self) -> None:
        """Load processed data and transformers."""
        try:
            # Load processed data
            self.sales_data = pd.read_csv(f'{self.output_dir}/sales_processed.csv')
            self.inventory_data = pd.read_csv(f'{self.output_dir}/inventory_processed.csv')
            self.delivery_data = pd.read_csv(f'{self.output_dir}/deliveries_processed.csv')
            
            # Load transformers
            self.scalers = joblib.load(f'{self.output_dir}/scalers.joblib')
            self.encoders = joblib.load(f'{self.output_dir}/encoders.joblib')
            
            self.logger.info("Processed data and transformers loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading processed data: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create data processor
    processor = DataProcessor()
    
    # Load and process data
    processor.load_data()
    processor.clean_data()
    processor.engineer_features()
    processor.transform_data()
    processor.save_processed_data() 