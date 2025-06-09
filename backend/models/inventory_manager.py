import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Union, Optional
import json
from scipy.optimize import minimize

class InventoryManager:
    def __init__(self, model_path: str = 'models/saved/inventory_model.joblib'):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.version = "1.0.0"
        self.last_trained = None
        self.feature_importance = {}
        self.metrics = {}
        
        # Load model if exists
        if os.path.exists(model_path):
            self.load_model()
        else:
            self.train()  # Train new model if none exists

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the input data for training or prediction."""
        # Convert dates to features
        data['year'] = data['date'].dt.year
        data['month'] = data['date'].dt.month
        data['day'] = data['date'].dt.day
        data['dayofweek'] = data['date'].dt.dayofweek
        data['is_weekend'] = data['dayofweek'].isin([5, 6]).astype(int)
        
        # Create demand features
        for lag in [1, 7, 14, 30]:
            data[f'demand_lag_{lag}'] = data.groupby('product_id')['demand'].shift(lag)
        
        # Create rolling statistics
        for window in [7, 14, 30]:
            data[f'demand_rolling_mean_{window}'] = data.groupby('product_id')['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )
            data[f'demand_rolling_std_{window}'] = data.groupby('product_id')['demand'].transform(
                lambda x: x.rolling(window=window, min_periods=1).std()
            )
        
        # Create inventory features
        data['inventory_turnover'] = data['demand'] / data['inventory_level']
        data['days_of_inventory'] = data['inventory_level'] / data['demand']
        data['stockout_risk'] = (data['inventory_level'] - data['demand']) / data['demand']
        
        # Handle categorical variables
        categorical_cols = ['product_id', 'location_id', 'supplier_id']
        data = pd.get_dummies(data, columns=categorical_cols, drop_first=True)
        
        # Fill missing values
        data = data.fillna(method='ffill').fillna(0)
        
        return data

    def generate_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data for inventory optimization."""
        np.random.seed(42)
        n_samples = 10000
        
        # Generate dates
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # Generate product, location, and supplier IDs
        product_ids = [f'P{i:03d}' for i in range(1, 21)]
        location_ids = [f'L{i:03d}' for i in range(1, 11)]
        supplier_ids = [f'S{i:03d}' for i in range(1, 6)]
        
        # Generate base data
        data = []
        for date in dates:
            for product_id in product_ids:
                for location_id in location_ids:
                    # Base demand with seasonality
                    base_demand = 100 + 50 * np.sin(2 * np.pi * date.dayofyear / 365)
                    
                    # Add product and location effects
                    product_effect = hash(product_id) % 50
                    location_effect = hash(location_id) % 30
                    
                    # Add random noise
                    noise = np.random.normal(0, 20)
                    
                    # Calculate final demand
                    demand = max(0, int(base_demand + product_effect + location_effect + noise))
                    
                    # Calculate inventory level (with some randomness)
                    inventory_level = max(0, int(demand * (1 + np.random.normal(0, 0.2))))
                    
                    data.append({
                        'date': date,
                        'product_id': product_id,
                        'location_id': location_id,
                        'supplier_id': np.random.choice(supplier_ids),
                        'demand': demand,
                        'inventory_level': inventory_level,
                        'lead_time': np.random.randint(1, 15),
                        'holding_cost': np.random.uniform(0.1, 1.0),
                        'ordering_cost': np.random.uniform(10, 100),
                        'unit_cost': np.random.uniform(5, 50),
                        'service_level': np.random.uniform(0.8, 0.99)
                    })
        
        return pd.DataFrame(data)

    def train(self) -> None:
        """Train the inventory optimization model."""
        try:
            # Generate or load training data
            data = self.generate_training_data()
            
            # Preprocess data
            processed_data = self.preprocess_data(data)
            
            # Prepare features and target
            feature_cols = [col for col in processed_data.columns 
                          if col not in ['date', 'optimal_order_quantity']]
            X = processed_data[feature_cols]
            y = processed_data['optimal_order_quantity']
            
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
            self.feature_importance = dict(zip(feature_cols, self.model.feature_importances_))
            
            # Save model
            self.save_model()
            
            self.last_trained = datetime.utcnow()
            
            logging.info(f"Model trained successfully. Metrics: {self.metrics}")
            
        except Exception as e:
            logging.error(f"Error training model: {str(e)}")
            raise

    def optimize(self, location_id: str, optimization_type: str,
                constraints: Optional[Dict] = None) -> Dict:
        """Optimize inventory levels and generate recommendations."""
        try:
            # Get current inventory data
            current_data = self._get_current_inventory_data(location_id)
            
            # Calculate optimal parameters
            optimal_params = self._calculate_optimal_parameters(current_data, constraints)
            
            # Generate recommendations based on optimization type
            if optimization_type == 'reorder_point':
                recommendations = self._generate_reorder_recommendations(
                    current_data, optimal_params
                )
            elif optimization_type == 'safety_stock':
                recommendations = self._generate_safety_stock_recommendations(
                    current_data, optimal_params
                )
            elif optimization_type == 'order_quantity':
                recommendations = self._generate_order_quantity_recommendations(
                    current_data, optimal_params
                )
            else:
                recommendations = self._generate_comprehensive_recommendations(
                    current_data, optimal_params
                )
            
            return {
                'recommendations': recommendations,
                'optimal_parameters': optimal_params,
                'metadata': {
                    'model_version': self.version,
                    'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                    'confidence': self.get_confidence_score()
                }
            }
            
        except Exception as e:
            logging.error(f"Error optimizing inventory: {str(e)}")
            raise

    def _get_current_inventory_data(self, location_id: str) -> pd.DataFrame:
        """Get current inventory data for a location."""
        # This would typically fetch from a database
        # For now, generate synthetic data
        data = self.generate_training_data()
        return data[data['location_id'] == location_id]

    def _calculate_optimal_parameters(self, data: pd.DataFrame,
                                   constraints: Optional[Dict] = None) -> Dict:
        """Calculate optimal inventory parameters."""
        constraints = constraints or {}
        
        # Calculate demand statistics
        demand_mean = data['demand'].mean()
        demand_std = data['demand'].std()
        
        # Calculate lead time statistics
        lead_time_mean = data['lead_time'].mean()
        lead_time_std = data['lead_time'].std()
        
        # Calculate costs
        holding_cost = data['holding_cost'].mean()
        ordering_cost = data['ordering_cost'].mean()
        unit_cost = data['unit_cost'].mean()
        
        # Calculate service level
        service_level = data['service_level'].mean()
        z_score = self._get_z_score(service_level)
        
        # Calculate optimal parameters
        optimal_order_quantity = self._calculate_economic_order_quantity(
            demand_mean, ordering_cost, holding_cost, unit_cost
        )
        
        safety_stock = self._calculate_safety_stock(
            demand_mean, demand_std,
            lead_time_mean, lead_time_std,
            z_score
        )
        
        reorder_point = self._calculate_reorder_point(
            demand_mean, lead_time_mean,
            safety_stock
        )
        
        return {
            'optimal_order_quantity': optimal_order_quantity,
            'safety_stock': safety_stock,
            'reorder_point': reorder_point,
            'service_level': service_level,
            'z_score': z_score
        }

    def _calculate_economic_order_quantity(self, demand: float,
                                         ordering_cost: float,
                                         holding_cost: float,
                                         unit_cost: float) -> float:
        """Calculate Economic Order Quantity (EOQ)."""
        return np.sqrt((2 * demand * ordering_cost) / (holding_cost * unit_cost))

    def _calculate_safety_stock(self, demand_mean: float, demand_std: float,
                              lead_time_mean: float, lead_time_std: float,
                              z_score: float) -> float:
        """Calculate safety stock level."""
        return z_score * np.sqrt(
            (lead_time_mean * demand_std ** 2) +
            (demand_mean ** 2 * lead_time_std ** 2)
        )

    def _calculate_reorder_point(self, demand_mean: float,
                               lead_time_mean: float,
                               safety_stock: float) -> float:
        """Calculate reorder point."""
        return (demand_mean * lead_time_mean) + safety_stock

    def _get_z_score(self, service_level: float) -> float:
        """Get z-score for a given service level."""
        # Simplified z-score lookup
        z_scores = {
            0.80: 0.84,
            0.85: 1.04,
            0.90: 1.28,
            0.95: 1.64,
            0.99: 2.33
        }
        return z_scores.get(round(service_level, 2), 1.64)

    def _generate_reorder_recommendations(self, data: pd.DataFrame,
                                        optimal_params: Dict) -> List[Dict]:
        """Generate reorder point recommendations."""
        recommendations = []
        
        for _, row in data.iterrows():
            current_level = row['inventory_level']
            reorder_point = optimal_params['reorder_point']
            
            if current_level <= reorder_point:
                recommendations.append({
                    'type': 'reorder',
                    'product_id': row['product_id'],
                    'current_level': current_level,
                    'reorder_point': reorder_point,
                    'recommended_order_quantity': optimal_params['optimal_order_quantity'],
                    'urgency': 'high' if current_level < reorder_point * 0.5 else 'medium'
                })
        
        return recommendations

    def _generate_safety_stock_recommendations(self, data: pd.DataFrame,
                                             optimal_params: Dict) -> List[Dict]:
        """Generate safety stock recommendations."""
        recommendations = []
        
        for _, row in data.iterrows():
            current_level = row['inventory_level']
            safety_stock = optimal_params['safety_stock']
            
            if current_level < safety_stock:
                recommendations.append({
                    'type': 'safety_stock',
                    'product_id': row['product_id'],
                    'current_level': current_level,
                    'recommended_safety_stock': safety_stock,
                    'shortage_amount': safety_stock - current_level,
                    'urgency': 'high' if current_level < safety_stock * 0.5 else 'medium'
                })
        
        return recommendations

    def _generate_order_quantity_recommendations(self, data: pd.DataFrame,
                                               optimal_params: Dict) -> List[Dict]:
        """Generate order quantity recommendations."""
        recommendations = []
        
        for _, row in data.iterrows():
            current_level = row['inventory_level']
            optimal_quantity = optimal_params['optimal_order_quantity']
            
            if current_level <= optimal_params['reorder_point']:
                recommendations.append({
                    'type': 'order_quantity',
                    'product_id': row['product_id'],
                    'current_level': current_level,
                    'recommended_quantity': optimal_quantity,
                    'expected_cost': optimal_quantity * row['unit_cost'],
                    'urgency': 'high' if current_level < optimal_params['safety_stock'] else 'medium'
                })
        
        return recommendations

    def _generate_comprehensive_recommendations(self, data: pd.DataFrame,
                                              optimal_params: Dict) -> List[Dict]:
        """Generate comprehensive inventory recommendations."""
        recommendations = []
        
        for _, row in data.iterrows():
            current_level = row['inventory_level']
            
            # Check multiple conditions
            if current_level <= optimal_params['reorder_point']:
                recommendations.append({
                    'type': 'comprehensive',
                    'product_id': row['product_id'],
                    'current_level': current_level,
                    'recommendations': {
                        'reorder_point': optimal_params['reorder_point'],
                        'safety_stock': optimal_params['safety_stock'],
                        'order_quantity': optimal_params['optimal_order_quantity']
                    },
                    'actions': [
                        {
                            'type': 'order',
                            'quantity': optimal_params['optimal_order_quantity'],
                            'urgency': 'high' if current_level < optimal_params['safety_stock'] else 'medium'
                        },
                        {
                            'type': 'monitor',
                            'message': 'Monitor demand patterns and adjust parameters if needed'
                        }
                    ]
                })
        
        return recommendations

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