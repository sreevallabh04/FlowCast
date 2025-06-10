import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
import joblib
import logging
from datetime import datetime, timedelta
import requests
from utils.config import Config
import os
from typing import Dict, List, Union, Optional
import json

logger = logging.getLogger(__name__)

class DemandModel:
    def __init__(self, n_estimators=100, random_state=42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.model_path = 'models/saved/demand_model.joblib'
        self.version = "1.0.0"
        self.last_trained = None
        self.feature_importance = {}
        self.metrics = {}
        self.feature_columns = None
        
        # Load model if exists
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self.train()  # Train new model if none exists

    def prepare_features(self, data):
        """Prepare features for the model."""
        # Convert dates to cyclical features
        data['day_of_week'] = pd.to_datetime(data['date']).dt.dayofweek
        data['month'] = pd.to_datetime(data['date']).dt.month
        data['day_of_year'] = pd.to_datetime(data['date']).dt.dayofyear
        
        # Create cyclical features
        data['day_sin'] = np.sin(2 * np.pi * data['day_of_week']/7)
        data['day_cos'] = np.cos(2 * np.pi * data['day_of_week']/7)
        data['month_sin'] = np.sin(2 * np.pi * data['month']/12)
        data['month_cos'] = np.cos(2 * np.pi * data['month']/12)
        
        # Add weather features
        data['temp_squared'] = data['temperature'] ** 2
        data['precip_squared'] = data['precipitation'] ** 2
        
        # Add economic features
        data['price_elasticity'] = data['price'] * data['gdp_growth']
        
        # Add event features
        data['is_holiday'] = data['is_holiday'].astype(int)
        data['is_event'] = data['is_event'].astype(int)
        
        # Add lag features
        for lag in [1, 7, 14, 30]:
            data[f'sales_lag_{lag}'] = data.groupby('product_id')['sales'].shift(lag)
        
        # Add rolling features
        for window in [7, 14, 30]:
            data[f'sales_rolling_mean_{window}'] = data.groupby('product_id')['sales'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )
            data[f'sales_rolling_std_{window}'] = data.groupby('product_id')['sales'].transform(
                lambda x: x.rolling(window=window, min_periods=1).std()
            )
        
        # Drop original date columns
        data = data.drop(['date', 'day_of_week', 'month', 'day_of_year'], axis=1)
        
        # Store feature columns
        self.feature_columns = [col for col in data.columns if col not in ['sales', 'product_id', 'store_id']]
        
        return data

    def generate_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data."""
        np.random.seed(42)
        n_samples = 10000
        
        # Generate dates
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # Generate product and location IDs
        product_ids = [f'P{i:03d}' for i in range(1, 21)]
        location_ids = [f'L{i:03d}' for i in range(1, 11)]
        
        # Generate base data
        data = []
        for date in dates:
            for product_id in product_ids:
                for location_id in location_ids:
                    # Base sales with seasonality
                    base_sales = 100 + 50 * np.sin(2 * np.pi * date.dayofyear / 365)
                    
                    # Add product and location effects
                    product_effect = hash(product_id) % 50
                    location_effect = hash(location_id) % 30
                    
                    # Add random noise
                    noise = np.random.normal(0, 20)
                    
                    # Calculate final sales
                    sales = max(0, int(base_sales + product_effect + location_effect + noise))
                    
                    data.append({
                        'date': date,
                        'product_id': product_id,
                        'location_id': location_id,
                        'sales': sales,
                        'price': np.random.uniform(10, 100),
                        'weather_condition': np.random.choice(['sunny', 'rainy', 'cloudy', 'snowy']),
                        'temperature': np.random.normal(20, 10),
                        'event_type': np.random.choice(['none', 'holiday', 'promotion', 'sport'], p=[0.7, 0.1, 0.1, 0.1])
                    })
        
        return pd.DataFrame(data)

    def train(self) -> None:
        """Train the demand prediction model."""
        try:
            # Generate or load training data
            data = self.generate_training_data()
            
            # Preprocess data
            processed_data = self.prepare_features(data)
            
            # Prepare features and target
            X = processed_data[self.feature_columns]
            y = processed_data['sales']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Calculate metrics
            y_pred = self.model.predict(X_test_scaled)
            self.metrics = {
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred)
            }
            
            # Calculate feature importance
            self.feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
            
            # Save model
            self.save_model()
            
            self.last_trained = datetime.utcnow()
            
            logging.info(f"Model trained successfully. Metrics: {self.metrics}")
            
        except Exception as e:
            logging.error(f"Error training model: {str(e)}")
            raise

    def predict(self, data, return_confidence=True):
        """Make predictions with confidence intervals."""
        try:
            # Prepare features
            processed_data = self.prepare_features(data)
            
            # Make predictions
            predictions = self.model.predict(processed_data[self.feature_columns])
            
            if return_confidence:
                # Get predictions from each tree
                predictions_all = np.array([tree.predict(processed_data[self.feature_columns]) 
                                          for tree in self.model.estimators_])
                
                # Calculate confidence intervals
                mean_pred = np.mean(predictions_all, axis=0)
                std_pred = np.std(predictions_all, axis=0)
                
                lower_bound = mean_pred - 1.96 * std_pred
                upper_bound = mean_pred + 1.96 * std_pred
                
                return {
                    'predictions': predictions.tolist(),
                    'confidence_intervals': {
                        'lower': lower_bound.tolist(),
                        'upper': upper_bound.tolist()
                    }
                }
            
            return {'predictions': predictions.tolist()}
            
        except Exception as e:
            logging.error(f"Error making predictions: {str(e)}")
            raise

    def get_metrics(self, start_date: datetime, end_date: datetime,
                   location_id: Optional[str] = None,
                   product_id: Optional[str] = None) -> Dict:
        """Get model performance metrics."""
        return {
            'accuracy': self.metrics.get('r2', 0),
            'mae': self.metrics.get('mae', 0),
            'rmse': self.metrics.get('rmse', 0),
            'feature_importance': self.feature_importance
        }

    def get_confidence_score(self) -> float:
        """Calculate model confidence score based on recent performance."""
        return min(1.0, max(0.0, self.metrics.get('r2', 0)))

    def save_model(self) -> None:
        """Save the trained model and scaler."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'version': self.version,
                'last_trained': self.last_trained,
                'metrics': self.metrics,
                'feature_importance': self.feature_importance
            }
            joblib.dump(model_data, self.model_path)
            logging.info(f"Model saved successfully to {self.model_path}")
        except Exception as e:
            logging.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self) -> None:
        """Load a trained model and scaler."""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.version = model_data['version']
            self.last_trained = model_data['last_trained']
            self.metrics = model_data['metrics']
            self.feature_importance = model_data['feature_importance']
            logging.info(f"Model loaded successfully from {self.model_path}")
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise

    def get_accuracy(self) -> float:
        """Get the model's accuracy score."""
        return self.metrics.get('r2', 0)

    def get_feature_importance(self):
        """Get feature importance scores."""
        if not self.model or not self.feature_columns:
            raise ValueError("Model not trained yet")
        
        importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

# Example usage
if __name__ == "__main__":
    # Create and train model
    model = DemandModel()
    metrics = model.train()
    
    # Generate test features
    test_features = pd.DataFrame({
        'product_id': [1, 2, 3],
        'store_id': [1, 1, 1],
        'temperature': [25, 20, 15],
        'precipitation': [0, 5, 10],
        'humidity': [60, 70, 80],
        'is_holiday': [0, 0, 1],
        'is_weekend': [1, 0, 0],
        'is_special_event': [0, 1, 0],
        'gdp_growth': [2.5, 2.0, 1.5],
        'inflation_rate': [3.0, 3.2, 3.5],
        'day_of_week': [5, 1, 3],
        'month': [6, 6, 6],
        'day_of_year': [180, 181, 182]
    })
    
    # Make predictions
    predictions = model.predict(test_features)
    
    print(f"Predictions: {predictions}")
    print(f"Model metrics: {metrics}") 