import unittest
import json
from app import app
import pandas as pd
from datetime import datetime, timedelta
from models.demand_model import DemandModel
from models.expiry_model import ExpiryModel
from models.inventory_model import InventoryModel
from models.routing_model import RoutingModel
from data.generator import DataGenerator

class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Initialize models
        self.demand_model = DemandModel()
        self.expiry_model = ExpiryModel()
        self.inventory_model = InventoryModel()
        self.routing_model = RoutingModel()
        
        # Generate test data
        self.generator = DataGenerator()
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=365*2)
        
        self.data = self.generator.generate_all_data(
            self.start_date,
            self.end_date,
            self.end_date
        )

    def test_end_to_end_demand_prediction(self):
        """Test end-to-end demand prediction flow."""
        # 1. Prepare data
        product_id = 'PROD001'
        store_id = 'STORE001'
        
        # 2. Train demand model
        self.demand_model.train(self.data['transactions'])
        
        # 3. Make prediction through API
        response = self.app.post(
            '/predict-demand',
            data=json.dumps({
                'product_id': product_id,
                'store_id': store_id,
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat()
            }),
            content_type='application/json'
        )
        
        # 4. Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('predictions', data)
        self.assertIn('confidence_intervals', data)

    def test_end_to_end_inventory_optimization(self):
        """Test end-to-end inventory optimization flow."""
        # 1. Prepare data
        product_id = 'PROD001'
        store_id = 'STORE001'
        
        # 2. Get current inventory
        current_inventory = self.data['inventory'][
            (self.data['inventory']['product_id'] == product_id) &
            (self.data['inventory']['store_id'] == store_id)
        ]
        
        # 3. Optimize inventory through API
        response = self.app.post(
            '/optimize-inventory',
            data=json.dumps({
                'product_id': product_id,
                'store_id': store_id,
                'current_inventory': current_inventory.to_dict('records')[0]
            }),
            content_type='application/json'
        )
        
        # 4. Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('safety_stock', data)
        self.assertIn('reorder_point', data)
        self.assertIn('recommendations', data)

    def test_end_to_end_route_optimization(self):
        """Test end-to-end route optimization flow."""
        # 1. Prepare data
        store_locations = self.data['stores'][['lat', 'lng']].to_dict('records')
        demands = [0] + [100] * (len(store_locations) - 1)  # First location is depot
        
        # 2. Optimize routes through API
        response = self.app.post(
            '/optimize-routes',
            data=json.dumps({
                'locations': store_locations,
                'demands': demands,
                'vehicle_capacity': 500,
                'num_vehicles': 2
            }),
            content_type='application/json'
        )
        
        # 3. Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('routes', data)
        self.assertIn('total_distance', data)
        self.assertIn('total_duration', data)

    def test_end_to_end_analytics(self):
        """Test end-to-end analytics flow."""
        # 1. Prepare data
        product_id = 'PROD001'
        store_id = 'STORE001'
        
        # 2. Get analytics through API
        response = self.app.get(
            '/analytics',
            query_string={
                'product_id': product_id,
                'store_id': store_id,
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat()
            }
        )
        
        # 3. Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('demand_metrics', data)
        self.assertIn('inventory_metrics', data)
        self.assertIn('route_metrics', data)

    def test_data_consistency(self):
        """Test data consistency across the system."""
        # 1. Generate data
        data = self.generator.generate_all_data(
            self.start_date,
            self.end_date,
            self.end_date
        )
        
        # 2. Verify product consistency
        product_ids = set(data['products']['product_id'])
        transaction_product_ids = set(data['transactions']['product_id'])
        inventory_product_ids = set(data['inventory']['product_id'])
        
        self.assertTrue(product_ids.issuperset(transaction_product_ids))
        self.assertTrue(product_ids.issuperset(inventory_product_ids))
        
        # 3. Verify store consistency
        store_ids = set(data['stores']['store_id'])
        transaction_store_ids = set(data['transactions']['store_id'])
        inventory_store_ids = set(data['inventory']['store_id'])
        
        self.assertTrue(store_ids.issuperset(transaction_store_ids))
        self.assertTrue(store_ids.issuperset(inventory_store_ids))

    def test_model_integration(self):
        """Test integration between different models."""
        # 1. Get demand prediction
        demand_prediction = self.demand_model.predict(self.data['transactions'])
        
        # 2. Use demand prediction for inventory optimization
        inventory_optimization = self.inventory_model.optimize_inventory(
            historical_data=self.data['transactions'],
            current_inventory=self.data['inventory'].set_index('product_id')['current_stock'].to_dict(),
            lead_times={'PROD001': 7},
            costs={'PROD001': {'order_cost': 100, 'holding_cost': 10}}
        )
        
        # 3. Use inventory optimization for route optimization
        route_optimization = self.routing_model.optimize_route(
            locations=self.data['stores'][['lat', 'lng']].to_dict('records'),
            demands=[inventory_optimization['PROD001']['reorder_point']],
            vehicle_capacity=500,
            num_vehicles=2
        )
        
        # 4. Verify all models produced valid results
        self.assertIn('predictions', demand_prediction)
        self.assertIn('PROD001', inventory_optimization)
        self.assertIn('routes', route_optimization)

    def test_error_handling(self):
        """Test error handling across the system."""
        # 1. Test invalid product ID
        response = self.app.post(
            '/predict-demand',
            data=json.dumps({
                'product_id': 'INVALID',
                'store_id': 'STORE001',
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat()
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # 2. Test invalid date range
        response = self.app.post(
            '/predict-demand',
            data=json.dumps({
                'product_id': 'PROD001',
                'store_id': 'STORE001',
                'start_date': self.end_date.isoformat(),
                'end_date': self.start_date.isoformat()  # End date before start date
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # 3. Test missing required fields
        response = self.app.post(
            '/predict-demand',
            data=json.dumps({
                'product_id': 'PROD001'
                # Missing store_id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main() 