import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Union, Optional
import json

class ExpiryOptimizer:
    def __init__(self, model_path: str = 'models/saved/expiry_model.joblib'):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
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
        data['days_until_expiry'] = (data['expiry_date'] - data['current_date']).dt.days
        data['year'] = data['current_date'].dt.year
        data['month'] = data['current_date'].dt.month
        data['day'] = data['current_date'].dt.day
        
        # Create storage condition features
        data['temperature_deviation'] = data['storage_temperature'] - data['optimal_temperature']
        data['humidity_deviation'] = data['storage_humidity'] - data['optimal_humidity']
        
        # Create product age features
        data['product_age_days'] = (data['current_date'] - data['manufacturing_date']).dt.days
        data['shelf_life_remaining'] = data['days_until_expiry'] / data['shelf_life_days']
        
        # Create handling features
        data['handling_score'] = data['handling_quality'].map({
            'excellent': 1.0,
            'good': 0.8,
            'average': 0.5,
            'poor': 0.2
        })
        
        # Handle categorical variables
        categorical_cols = ['product_id', 'location_id', 'storage_condition', 'handling_quality']
        for col in categorical_cols:
            if col in data.columns:
                data[col] = self.label_encoder.fit_transform(data[col])
        
        # Fill missing values
        data = data.fillna(method='ffill').fillna(0)
        
        return data

    def generate_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data for expiry prediction."""
        np.random.seed(42)
        n_samples = 10000
        
        # Generate dates
        current_dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        manufacturing_dates = [date - timedelta(days=np.random.randint(1, 180)) for date in current_dates]
        expiry_dates = [date + timedelta(days=np.random.randint(1, 365)) for date in current_dates]
        
        # Generate product and location IDs
        product_ids = [f'P{i:03d}' for i in range(1, 21)]
        location_ids = [f'L{i:03d}' for i in range(1, 11)]
        
        # Generate base data
        data = []
        for i in range(n_samples):
            current_date = np.random.choice(current_dates)
            manufacturing_date = current_date - timedelta(days=np.random.randint(1, 180))
            expiry_date = current_date + timedelta(days=np.random.randint(1, 365))
            
            # Base shelf life
            shelf_life_days = np.random.randint(30, 365)
            
            # Storage conditions
            optimal_temperature = np.random.uniform(2, 8)
            optimal_humidity = np.random.uniform(30, 70)
            storage_temperature = optimal_temperature + np.random.normal(0, 2)
            storage_humidity = optimal_humidity + np.random.normal(0, 10)
            
            # Handling quality
            handling_quality = np.random.choice(
                ['excellent', 'good', 'average', 'poor'],
                p=[0.3, 0.4, 0.2, 0.1]
            )
            
            # Calculate expiry probability
            days_until_expiry = (expiry_date - current_date).days
            temperature_effect = np.exp(-0.1 * abs(storage_temperature - optimal_temperature))
            humidity_effect = np.exp(-0.05 * abs(storage_humidity - optimal_humidity))
            handling_effect = {
                'excellent': 1.0,
                'good': 0.9,
                'average': 0.7,
                'poor': 0.5
            }[handling_quality]
            
            base_probability = days_until_expiry / shelf_life_days
            expiry_probability = base_probability * temperature_effect * humidity_effect * handling_effect
            
            # Determine if product will expire
            will_expire = np.random.random() < expiry_probability
            
            data.append({
                'current_date': current_date,
                'manufacturing_date': manufacturing_date,
                'expiry_date': expiry_date,
                'product_id': np.random.choice(product_ids),
                'location_id': np.random.choice(location_ids),
                'shelf_life_days': shelf_life_days,
                'optimal_temperature': optimal_temperature,
                'optimal_humidity': optimal_humidity,
                'storage_temperature': storage_temperature,
                'storage_humidity': storage_humidity,
                'handling_quality': handling_quality,
                'will_expire': will_expire
            })
        
        return pd.DataFrame(data)

    def train(self) -> None:
        """Train the expiry prediction model."""
        try:
            # Generate or load training data
            data = self.generate_training_data()
            
            # Preprocess data
            processed_data = self.preprocess_data(data)
            
            # Prepare features and target
            feature_cols = [col for col in processed_data.columns 
                          if col not in ['current_date', 'manufacturing_date', 'expiry_date', 'will_expire']]
            X = processed_data[feature_cols]
            y = processed_data['will_expire']
            
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
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1': f1_score(y_test, y_pred)
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

    def predict_expiry(self, product_id: str, location_id: str, 
                      current_date: datetime, manufacturing_date: datetime,
                      expiry_date: datetime, shelf_life_days: int,
                      storage_conditions: Dict) -> Dict:
        """Predict expiry probability for a product."""
        try:
            # Create prediction data
            pred_data = pd.DataFrame([{
                'current_date': current_date,
                'manufacturing_date': manufacturing_date,
                'expiry_date': expiry_date,
                'product_id': product_id,
                'location_id': location_id,
                'shelf_life_days': shelf_life_days,
                'optimal_temperature': storage_conditions.get('optimal_temperature', 5),
                'optimal_humidity': storage_conditions.get('optimal_humidity', 50),
                'storage_temperature': storage_conditions.get('storage_temperature', 5),
                'storage_humidity': storage_conditions.get('storage_humidity', 50),
                'handling_quality': storage_conditions.get('handling_quality', 'good')
            }])
            
            # Preprocess data
            processed_data = self.preprocess_data(pred_data)
            
            # Prepare features
            feature_cols = [col for col in processed_data.columns 
                          if col not in ['current_date', 'manufacturing_date', 'expiry_date']]
            X = processed_data[feature_cols]
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Generate predictions
            expiry_probability = self.model.predict_proba(X_scaled)[0][1]
            
            # Calculate days until expiry
            days_until_expiry = (expiry_date - current_date).days
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                expiry_probability,
                days_until_expiry,
                storage_conditions
            )
            
            return {
                'expiry_probability': float(expiry_probability),
                'days_until_expiry': days_until_expiry,
                'recommendations': recommendations,
                'metadata': {
                    'model_version': self.version,
                    'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                    'confidence': self.get_confidence_score()
                }
            }
            
        except Exception as e:
            logging.error(f"Error predicting expiry: {str(e)}")
            raise

    def _generate_recommendations(self, expiry_probability: float,
                                days_until_expiry: int,
                                storage_conditions: Dict) -> List[Dict]:
        """Generate recommendations based on expiry probability and conditions."""
        recommendations = []
        
        # High expiry probability recommendations
        if expiry_probability > 0.7:
            recommendations.append({
                'type': 'urgent',
                'action': 'discount',
                'message': 'High risk of expiry. Consider immediate discounting.',
                'priority': 'high'
            })
            recommendations.append({
                'type': 'storage',
                'action': 'adjust_conditions',
                'message': 'Optimize storage conditions to extend shelf life.',
                'priority': 'high'
            })
        
        # Medium expiry probability recommendations
        elif expiry_probability > 0.4:
            recommendations.append({
                'type': 'inventory',
                'action': 'redistribute',
                'message': 'Consider redistributing inventory to locations with higher demand.',
                'priority': 'medium'
            })
        
        # Storage condition recommendations
        if abs(storage_conditions.get('storage_temperature', 0) - 
               storage_conditions.get('optimal_temperature', 0)) > 2:
            recommendations.append({
                'type': 'storage',
                'action': 'temperature',
                'message': 'Adjust storage temperature to optimal range.',
                'priority': 'medium'
            })
        
        if abs(storage_conditions.get('storage_humidity', 0) - 
               storage_conditions.get('optimal_humidity', 0)) > 10:
            recommendations.append({
                'type': 'storage',
                'action': 'humidity',
                'message': 'Adjust storage humidity to optimal range.',
                'priority': 'medium'
            })
        
        return recommendations

    def get_metrics(self, start_date: datetime, end_date: datetime,
                   location_id: Optional[str] = None,
                   product_id: Optional[str] = None) -> Dict:
        """Get model performance metrics."""
        return {
            'accuracy': self.metrics.get('accuracy', 0),
            'precision': self.metrics.get('precision', 0),
            'recall': self.metrics.get('recall', 0),
            'f1_score': self.metrics.get('f1', 0),
            'feature_importance': self.feature_importance
        }

    def get_confidence_score(self) -> float:
        """Calculate model confidence score based on recent performance."""
        return min(1.0, max(0.0, self.metrics.get('accuracy', 0)))

    def save_model(self) -> None:
        """Save the trained model and scaler."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'label_encoder': self.label_encoder,
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
            self.label_encoder = model_data['label_encoder']
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
        return self.metrics.get('accuracy', 0) 