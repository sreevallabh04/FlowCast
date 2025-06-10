import unittest
import json
from app import app
import pandas as pd
from datetime import datetime, timedelta

class TestAPI(unittest.TestCase):
    def setUp(self):
        """Set up test client and test data."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Create sample data
        self.sample_data = {
            'product_id': 'PROD001',
            'store_id': 'STORE001',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.app.get('/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')

    def test_predict_demand(self):
        """Test demand prediction endpoint."""
        response = self.app.post(
            '/predict-demand',
            data=json.dumps(self.sample_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('predictions', data)
        self.assertIn('confidence_intervals', data)

    def test_optimize_inventory(self):
        """Test inventory optimization endpoint."""
        response = self.app.post(
            '/optimize-inventory',
            data=json.dumps(self.sample_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('safety_stock', data)
        self.assertIn('reorder_point', data)
        self.assertIn('recommendations', data)

    def test_optimize_routes(self):
        """Test route optimization endpoint."""
        route_data = {
            'locations': [
                {'lat': 40.7128, 'lng': -74.0060},
                {'lat': 40.7589, 'lng': -73.9851},
                {'lat': 40.7829, 'lng': -73.9654}
            ],
            'demands': [0, 100, 150],
            'vehicle_capacity': 500,
            'num_vehicles': 2
        }
        
        response = self.app.post(
            '/optimize-routes',
            data=json.dumps(route_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('routes', data)
        self.assertIn('total_distance', data)
        self.assertIn('total_duration', data)

    def test_analytics(self):
        """Test analytics endpoint."""
        response = self.app.get(
            '/analytics',
            query_string=self.sample_data
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('demand_metrics', data)
        self.assertIn('inventory_metrics', data)
        self.assertIn('route_metrics', data)

    def test_invalid_input(self):
        """Test invalid input handling."""
        # Test missing required fields
        invalid_data = {
            'product_id': 'PROD001'
            # Missing store_id
        }
        
        response = self.app.post(
            '/predict-demand',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.data))

    def test_error_handling(self):
        """Test error handling."""
        # Test invalid date format
        invalid_data = {
            'product_id': 'PROD001',
            'store_id': 'STORE001',
            'start_date': 'invalid-date',
            'end_date': '2024-01-31'
        }
        
        response = self.app.post(
            '/predict-demand',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', json.loads(response.data))

    def test_rate_limiting(self):
        """Test rate limiting."""
        # Make multiple requests in quick succession
        for _ in range(10):
            response = self.app.post(
                '/predict-demand',
                data=json.dumps(self.sample_data),
                content_type='application/json'
            )
        
        # The last request should be rate limited
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', json.loads(response.data))

    def test_caching(self):
        """Test response caching."""
        # First request
        response1 = self.app.post(
            '/predict-demand',
            data=json.dumps(self.sample_data),
            content_type='application/json'
        )
        
        # Second request with same data
        response2 = self.app.post(
            '/predict-demand',
            data=json.dumps(self.sample_data),
            content_type='application/json'
        )
        
        # Check if response times are different (cached response should be faster)
        self.assertLess(
            response2.elapsed.total_seconds(),
            response1.elapsed.total_seconds()
        )

if __name__ == '__main__':
    unittest.main() 