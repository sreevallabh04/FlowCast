import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models.demand_model import DemandModel

class TestDemandModel(unittest.TestCase):
    def setUp(self):
        """Set up test data and model."""
        self.model = DemandModel()
        
        # Generate test data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        self.test_data = pd.DataFrame({
            'date': dates,
            'product_id': ['P001'] * len(dates),
            'location_id': ['L001'] * len(dates),
            'demand': np.random.randint(10, 100, size=len(dates)),
            'price': np.random.uniform(10, 100, size=len(dates)),
            'temperature': np.random.uniform(0, 30, size=len(dates)),
            'precipitation': np.random.uniform(0, 50, size=len(dates)),
            'is_holiday': np.random.choice([0, 1], size=len(dates)),
            'is_weekend': np.random.choice([0, 1], size=len(dates))
        })
        
        # Add some seasonality
        self.test_data['demand'] = self.test_data['demand'] * (1 + 0.2 * np.sin(2 * np.pi * self.test_data['date'].dt.dayofyear / 365))
        
        # Add some trend
        self.test_data['demand'] = self.test_data['demand'] * (1 + 0.001 * np.arange(len(self.test_data)))
    
    def test_data_preprocessing(self):
        """Test data preprocessing functionality."""
        processed_data = self.model._preprocess_data(self.test_data)
        
        self.assertIsInstance(processed_data, pd.DataFrame)
        self.assertTrue('date' in processed_data.columns)
        self.assertTrue('demand' in processed_data.columns)
        self.assertTrue('price' in processed_data.columns)
        self.assertTrue('temperature' in processed_data.columns)
        self.assertTrue('precipitation' in processed_data.columns)
        self.assertTrue('is_holiday' in processed_data.columns)
        self.assertTrue('is_weekend' in processed_data.columns)
    
    def test_feature_engineering(self):
        """Test feature engineering functionality."""
        processed_data = self.model._preprocess_data(self.test_data)
        features = self.model._engineer_features(processed_data)
        
        self.assertIsInstance(features, pd.DataFrame)
        self.assertTrue('day_of_week' in features.columns)
        self.assertTrue('month' in features.columns)
        self.assertTrue('year' in features.columns)
        self.assertTrue('day_of_year' in features.columns)
        self.assertTrue('rolling_mean_7d' in features.columns)
        self.assertTrue('rolling_std_7d' in features.columns)
    
    def test_model_training(self):
        """Test model training functionality."""
        # Split data into train and test
        train_data = self.test_data[self.test_data['date'] < '2023-11-01']
        test_data = self.test_data[self.test_data['date'] >= '2023-11-01']
        
        # Train model
        self.model.train(train_data)
        
        # Test predictions
        predictions = self.model.predict(test_data)
        
        self.assertIsInstance(predictions, pd.DataFrame)
        self.assertTrue('date' in predictions.columns)
        self.assertTrue('predicted_demand' in predictions.columns)
        self.assertTrue('confidence_interval_lower' in predictions.columns)
        self.assertTrue('confidence_interval_upper' in predictions.columns)
    
    def test_model_evaluation(self):
        """Test model evaluation functionality."""
        # Split data into train and test
        train_data = self.test_data[self.test_data['date'] < '2023-11-01']
        test_data = self.test_data[self.test_data['date'] >= '2023-11-01']
        
        # Train model
        self.model.train(train_data)
        
        # Evaluate model
        metrics = self.model.evaluate(test_data)
        
        self.assertIsInstance(metrics, dict)
        self.assertTrue('mse' in metrics)
        self.assertTrue('rmse' in metrics)
        self.assertTrue('mae' in metrics)
        self.assertTrue('r2' in metrics)
        
        # Check metric values are reasonable
        self.assertGreaterEqual(metrics['r2'], 0)
        self.assertLessEqual(metrics['r2'], 1)
        self.assertGreaterEqual(metrics['mse'], 0)
        self.assertGreaterEqual(metrics['rmse'], 0)
        self.assertGreaterEqual(metrics['mae'], 0)
    
    def test_model_persistence(self):
        """Test model saving and loading functionality."""
        # Train model
        self.model.train(self.test_data)
        
        # Save model
        self.model.save('test_model.pkl')
        
        # Load model
        loaded_model = DemandModel()
        loaded_model.load('test_model.pkl')
        
        # Compare predictions
        original_predictions = self.model.predict(self.test_data)
        loaded_predictions = loaded_model.predict(self.test_data)
        
        pd.testing.assert_frame_equal(original_predictions, loaded_predictions)
    
    def test_feature_importance(self):
        """Test feature importance calculation."""
        # Train model
        self.model.train(self.test_data)
        
        # Get feature importance
        importance = self.model.get_feature_importance()
        
        self.assertIsInstance(importance, pd.DataFrame)
        self.assertTrue('feature' in importance.columns)
        self.assertTrue('importance' in importance.columns)
        
        # Check importance values
        self.assertTrue(all(importance['importance'] >= 0))
        self.assertTrue(all(importance['importance'] <= 1))
        self.assertAlmostEqual(importance['importance'].sum(), 1.0, places=5)

if __name__ == '__main__':
    unittest.main() 