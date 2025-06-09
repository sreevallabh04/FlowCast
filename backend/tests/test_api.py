import pytest
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app import app
from models.arima import ARIMAModel
from models.prophet import ProphetModel
from models.lstm import LSTMModel
from models.xgboost import XGBoostModel
from data.generator import DataGenerator
from data.processor import DataProcessor
from data.validation import DataValidator
from data.metrics import MetricsCalculator

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_data():
    # Generate sample data
    generator = DataGenerator()
    data = generator.generate_data(
        num_records=1000,
        start_date='2020-01-01',
        end_date='2023-12-31'
    )
    return data

@pytest.fixture
def processed_data(sample_data):
    # Process sample data
    processor = DataProcessor()
    processed = processor.process_data(sample_data)
    return processed

class TestForecastEndpoint:
    def test_forecast_success(self, client, processed_data):
        # Test successful forecast request
        response = client.post('/api/forecast', json={
            'data': processed_data.to_dict(orient='records'),
            'model': 'arima'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'forecast' in data
        assert 'metrics' in data
        assert len(data['forecast']) > 0
        assert all(metric >= 0 for metric in data['metrics'].values())
        
    def test_forecast_invalid_data(self, client):
        # Test forecast with invalid data
        response = client.post('/api/forecast', json={
            'data': [],
            'model': 'arima'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
    def test_forecast_invalid_model(self, client, processed_data):
        # Test forecast with invalid model
        response = client.post('/api/forecast', json={
            'data': processed_data.to_dict(orient='records'),
            'model': 'invalid_model'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
    def test_forecast_missing_parameters(self, client):
        # Test forecast with missing parameters
        response = client.post('/api/forecast', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
    def test_forecast_all_models(self, client, processed_data):
        # Test forecast with all available models
        models = ['arima', 'prophet', 'lstm', 'xgboost']
        for model in models:
            response = client.post('/api/forecast', json={
                'data': processed_data.to_dict(orient='records'),
                'model': model
            })
            assert response.status_code == 200
            data = response.get_json()
            assert 'forecast' in data
            assert 'metrics' in data

class TestMetricsEndpoint:
    def test_metrics_success(self, client, processed_data):
        # Test successful metrics request
        response = client.post('/api/metrics', json={
            'data': processed_data.to_dict(orient='records')
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data
        assert all(metric >= 0 for metric in data['metrics'].values())
        
    def test_metrics_invalid_data(self, client):
        # Test metrics with invalid data
        response = client.post('/api/metrics', json={
            'data': []
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
    def test_metrics_missing_parameters(self, client):
        # Test metrics with missing parameters
        response = client.post('/api/metrics', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

class TestValidationEndpoint:
    def test_validation_success(self, client, processed_data):
        # Test successful validation request
        response = client.post('/api/validate', json={
            'data': processed_data.to_dict(orient='records')
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'is_valid' in data
        assert 'errors' in data
        
    def test_validation_invalid_data(self, client):
        # Test validation with invalid data
        response = client.post('/api/validate', json={
            'data': []
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
    def test_validation_missing_parameters(self, client):
        # Test validation with missing parameters
        response = client.post('/api/validate', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

class TestProcessingEndpoint:
    def test_processing_success(self, client, sample_data):
        # Test successful processing request
        response = client.post('/api/process', json={
            'data': sample_data.to_dict(orient='records')
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'processed_data' in data
        assert len(data['processed_data']) > 0
        
    def test_processing_invalid_data(self, client):
        # Test processing with invalid data
        response = client.post('/api/process', json={
            'data': []
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
    def test_processing_missing_parameters(self, client):
        # Test processing with missing parameters
        response = client.post('/api/process', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

def test_error_handling(client):
    # Test invalid JSON
    response = client.post('/api/forecast', data='invalid json')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    
    # Test invalid content type
    response = client.post('/api/forecast', data='{"data": []}')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    
    # Test invalid endpoint
    response = client.get('/api/invalid')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_performance(client, processed_data):
    # Test response time for forecast endpoint
    start_time = datetime.now()
    response = client.post('/api/forecast', json={
        'data': processed_data.to_dict(orient='records'),
        'model': 'arima'
    })
    end_time = datetime.now()
    
    assert response.status_code == 200
    assert (end_time - start_time).total_seconds() < 5  # Response within 5 seconds
    
    # Test response time for metrics endpoint
    start_time = datetime.now()
    response = client.post('/api/metrics', json={
        'data': processed_data.to_dict(orient='records')
    })
    end_time = datetime.now()
    
    assert response.status_code == 200
    assert (end_time - start_time).total_seconds() < 2  # Response within 2 seconds

def test_data_consistency(client, processed_data):
    # Test data consistency across endpoints
    # First get metrics
    metrics_response = client.post('/api/metrics', json={
        'data': processed_data.to_dict(orient='records')
    })
    assert metrics_response.status_code == 200
    metrics_data = metrics_response.get_json()
    
    # Then get forecast
    forecast_response = client.post('/api/forecast', json={
        'data': processed_data.to_dict(orient='records'),
        'model': 'arima'
    })
    assert forecast_response.status_code == 200
    forecast_data = forecast_response.get_json()
    
    # Compare metrics
    assert metrics_data['metrics'] == forecast_data['metrics']

def test_concurrent_requests(client, processed_data):
    # Test handling of concurrent requests
    import threading
    
    def make_request():
        response = client.post('/api/forecast', json={
            'data': processed_data.to_dict(orient='records'),
            'model': 'arima'
        })
        assert response.status_code == 200
    
    # Create multiple threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join() 