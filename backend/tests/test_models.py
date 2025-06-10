import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models.demand_model import DemandModel
from models.expiry_model import ExpiryModel
from models.inventory_model import InventoryModel
from models.routing_model import RoutingModel

class TestDemandModel(unittest.TestCase):
    def setUp(self):
        self.model = DemandModel()
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        self.data = pd.DataFrame([
            {
                'date': date,
                'product_id': 'PROD001',
                'store_id': 'STORE001',
                'sales': np.random.normal(100, 20),
                'temperature': np.random.normal(20, 5),
                'precipitation': np.random.uniform(0, 50),
                'is_holiday': np.random.choice([0, 1], p=[0.9, 0.1]),
                'is_event': np.random.choice([0, 1], p=[0.8, 0.2]),
                'price': np.random.uniform(10, 100),
                'gdp_growth': np.random.normal(2, 0.5)
            }
            for date in dates
        ])

    def test_train(self):
        """Test model training."""
        metrics = self.model.train(self.data)
        
        self.assertIn('r2_score', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('feature_importance', metrics)
        
        self.assertGreater(metrics['r2_score'], 0)
        self.assertGreater(metrics['mae'], 0)

    def test_predict(self):
        """Test model prediction."""
        # Train model first
        self.model.train(self.data)
        
        # Make predictions
        predictions = self.model.predict(self.data)
        
        self.assertIn('predictions', predictions)
        self.assertIn('confidence_intervals', predictions)
        
        self.assertEqual(len(predictions['predictions']), len(self.data))
        self.assertEqual(len(predictions['confidence_intervals']['lower']), len(self.data))
        self.assertEqual(len(predictions['confidence_intervals']['upper']), len(self.data))

class TestExpiryModel(unittest.TestCase):
    def setUp(self):
        self.model = ExpiryModel()
        
        # Add test product
        self.model.add_product_shelf_life(
            product_id="PROD001",
            shelf_life_days=14,
            decay_rate=0.1,
            min_quality_threshold=0.7,
            donation_threshold=0.5
        )
        
        # Add test donation partner
        self.model.add_donation_partner(
            partner_id="PART001",
            name="Test Food Bank",
            accepted_product_types=["PROD001"],
            pickup_lead_time_hours=24
        )
        
        # Create sample inventory data
        self.inventory_data = pd.DataFrame([
            {
                'product_id': 'PROD001',
                'production_date': '2024-01-01',
                'current_date': '2024-01-10',
                'temperature': 4,
                'humidity': 60
            }
        ])

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        quality = self.model.calculate_quality_score(
            product_id="PROD001",
            days_since_production=5,
            storage_conditions={'temperature': 4, 'humidity': 60}
        )
        
        self.assertGreaterEqual(quality, 0)
        self.assertLessEqual(quality, 1)

    def test_predict_expiry(self):
        """Test expiry prediction."""
        predictions = self.model.predict_expiry(self.inventory_data)
        
        self.assertIn('current_quality', predictions.columns)
        self.assertIn('days_until_expiry', predictions.columns)
        self.assertIn('expiry_date', predictions.columns)
        self.assertIn('donation_recommendation', predictions.columns)

    def test_optimize_waste_reduction(self):
        """Test waste reduction optimization."""
        recommendations = self.model.optimize_waste_reduction(self.inventory_data)
        
        self.assertIn('immediate_actions', recommendations)
        self.assertIn('short_term_actions', recommendations)
        self.assertIn('long_term_actions', recommendations)

class TestInventoryModel(unittest.TestCase):
    def setUp(self):
        self.model = InventoryModel(service_level=0.95)
        
        # Create sample data
        self.historical_data = pd.DataFrame([
            {
                'product_id': 'PROD001',
                'date': '2024-01-01',
                'demand': np.random.normal(100, 20)
            }
            for _ in range(30)
        ])
        
        self.current_inventory = {
            'PROD001': 500
        }
        
        self.lead_times = {
            'PROD001': 7
        }
        
        self.costs = {
            'PROD001': {
                'order_cost': 100,
                'holding_cost': 10
            }
        }

    def test_calculate_safety_stock(self):
        """Test safety stock calculation."""
        safety_stock = self.model.calculate_safety_stock(
            lead_time_days=7,
            demand_mean=100,
            demand_std=20
        )
        
        self.assertGreaterEqual(safety_stock, 0)

    def test_calculate_reorder_point(self):
        """Test reorder point calculation."""
        reorder_point = self.model.calculate_reorder_point(
            safety_stock=100,
            lead_time_days=7,
            demand_mean=100
        )
        
        self.assertGreaterEqual(reorder_point, 0)

    def test_optimize_inventory(self):
        """Test inventory optimization."""
        results = self.model.optimize_inventory(
            historical_data=self.historical_data,
            current_inventory=self.current_inventory,
            lead_times=self.lead_times,
            costs=self.costs
        )
        
        self.assertIn('PROD001', results)
        self.assertIn('safety_stock', results['PROD001'])
        self.assertIn('reorder_point', results['PROD001'])
        self.assertIn('recommendations', results['PROD001'])

class TestRoutingModel(unittest.TestCase):
    def setUp(self):
        self.model = RoutingModel()
        
        # Create sample locations
        self.locations = [
            {'lat': 40.7128, 'lng': -74.0060},  # New York
            {'lat': 40.7589, 'lng': -73.9851},  # Times Square
            {'lat': 40.7829, 'lng': -73.9654},  # Central Park
            {'lat': 40.7527, 'lng': -73.9772},  # Empire State
            {'lat': 40.7484, 'lng': -73.9857}   # Madison Square
        ]
        
        self.demands = [0, 100, 150, 200, 120]  # First location is depot

    def test_create_distance_matrix(self):
        """Test distance matrix creation."""
        distance_matrix, duration_matrix = self.model.create_distance_matrix(
            locations=self.locations,
            mode='driving'
        )
        
        self.assertEqual(distance_matrix.shape, (len(self.locations), len(self.locations)))
        self.assertEqual(duration_matrix.shape, (len(self.locations), len(self.locations)))

    def test_optimize_route(self):
        """Test route optimization."""
        route_data = self.model.optimize_route(
            locations=self.locations,
            demands=self.demands,
            vehicle_capacity=500,
            num_vehicles=2
        )
        
        self.assertIn('routes', route_data)
        self.assertIn('total_distance', route_data)
        self.assertIn('total_duration', route_data)
        self.assertIn('metrics', route_data)

if __name__ == '__main__':
    unittest.main() 