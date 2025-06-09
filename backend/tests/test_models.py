import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from models.arima import ARIMAModel
from models.prophet import ProphetModel
from models.lstm import LSTMModel
from models.xgboost import XGBoostModel

# Test data
@pytest.fixture
def sample_data():
    # Create sample time series data
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    values = np.random.normal(100, 10, len(dates))
    df = pd.DataFrame({'date': dates, 'value': values})
    return df

@pytest.fixture
def train_test_split(sample_data):
    # Split data into train and test sets
    train_size = int(len(sample_data) * 0.8)
    train_data = sample_data[:train_size]
    test_data = sample_data[train_size:]
    return train_data, test_data

class TestARIMAModel:
    def test_initialization(self):
        model = ARIMAModel()
        assert model is not None
        assert model.model is None
        
    def test_fit(self, train_test_split):
        train_data, _ = train_test_split
        model = ARIMAModel()
        model.fit(train_data)
        assert model.model is not None
        
    def test_predict(self, train_test_split):
        train_data, test_data = train_test_split
        model = ARIMAModel()
        model.fit(train_data)
        predictions = model.predict(test_data)
        assert len(predictions) == len(test_data)
        assert not np.isnan(predictions).any()
        
    def test_evaluate(self, train_test_split):
        train_data, test_data = train_test_split
        model = ARIMAModel()
        model.fit(train_data)
        metrics = model.evaluate(test_data)
        assert 'mse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert all(metric >= 0 for metric in metrics.values())
        
    def test_save_load(self, train_test_split, tmp_path):
        train_data, _ = train_test_split
        model = ARIMAModel()
        model.fit(train_data)
        
        # Save model
        model_path = tmp_path / "arima_model.pkl"
        model.save(model_path)
        assert model_path.exists()
        
        # Load model
        loaded_model = ARIMAModel()
        loaded_model.load(model_path)
        assert loaded_model.model is not None

class TestProphetModel:
    def test_initialization(self):
        model = ProphetModel()
        assert model is not None
        assert model.model is None
        
    def test_fit(self, train_test_split):
        train_data, _ = train_test_split
        model = ProphetModel()
        model.fit(train_data)
        assert model.model is not None
        
    def test_predict(self, train_test_split):
        train_data, test_data = train_test_split
        model = ProphetModel()
        model.fit(train_data)
        predictions = model.predict(test_data)
        assert len(predictions) == len(test_data)
        assert not np.isnan(predictions).any()
        
    def test_evaluate(self, train_test_split):
        train_data, test_data = train_test_split
        model = ProphetModel()
        model.fit(train_data)
        metrics = model.evaluate(test_data)
        assert 'mse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert all(metric >= 0 for metric in metrics.values())
        
    def test_save_load(self, train_test_split, tmp_path):
        train_data, _ = train_test_split
        model = ProphetModel()
        model.fit(train_data)
        
        # Save model
        model_path = tmp_path / "prophet_model.pkl"
        model.save(model_path)
        assert model_path.exists()
        
        # Load model
        loaded_model = ProphetModel()
        loaded_model.load(model_path)
        assert loaded_model.model is not None

class TestLSTMModel:
    def test_initialization(self):
        model = LSTMModel()
        assert model is not None
        assert model.model is None
        
    def test_fit(self, train_test_split):
        train_data, _ = train_test_split
        model = LSTMModel()
        model.fit(train_data)
        assert model.model is not None
        
    def test_predict(self, train_test_split):
        train_data, test_data = train_test_split
        model = LSTMModel()
        model.fit(train_data)
        predictions = model.predict(test_data)
        assert len(predictions) == len(test_data)
        assert not np.isnan(predictions).any()
        
    def test_evaluate(self, train_test_split):
        train_data, test_data = train_test_split
        model = LSTMModel()
        model.fit(train_data)
        metrics = model.evaluate(test_data)
        assert 'mse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert all(metric >= 0 for metric in metrics.values())
        
    def test_save_load(self, train_test_split, tmp_path):
        train_data, _ = train_test_split
        model = LSTMModel()
        model.fit(train_data)
        
        # Save model
        model_path = tmp_path / "lstm_model.h5"
        model.save(model_path)
        assert model_path.exists()
        
        # Load model
        loaded_model = LSTMModel()
        loaded_model.load(model_path)
        assert loaded_model.model is not None

class TestXGBoostModel:
    def test_initialization(self):
        model = XGBoostModel()
        assert model is not None
        assert model.model is None
        
    def test_fit(self, train_test_split):
        train_data, _ = train_test_split
        model = XGBoostModel()
        model.fit(train_data)
        assert model.model is not None
        
    def test_predict(self, train_test_split):
        train_data, test_data = train_test_split
        model = XGBoostModel()
        model.fit(train_data)
        predictions = model.predict(test_data)
        assert len(predictions) == len(test_data)
        assert not np.isnan(predictions).any()
        
    def test_evaluate(self, train_test_split):
        train_data, test_data = train_test_split
        model = XGBoostModel()
        model.fit(train_data)
        metrics = model.evaluate(test_data)
        assert 'mse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert all(metric >= 0 for metric in metrics.values())
        
    def test_save_load(self, train_test_split, tmp_path):
        train_data, _ = train_test_split
        model = XGBoostModel()
        model.fit(train_data)
        
        # Save model
        model_path = tmp_path / "xgboost_model.json"
        model.save(model_path)
        assert model_path.exists()
        
        # Load model
        loaded_model = XGBoostModel()
        loaded_model.load(model_path)
        assert loaded_model.model is not None

def test_model_comparison(train_test_split):
    train_data, test_data = train_test_split
    models = {
        'arima': ARIMAModel(),
        'prophet': ProphetModel(),
        'lstm': LSTMModel(),
        'xgboost': XGBoostModel()
    }
    
    results = {}
    for name, model in models.items():
        model.fit(train_data)
        predictions = model.predict(test_data)
        metrics = {
            'mse': mean_squared_error(test_data['value'], predictions),
            'mae': mean_absolute_error(test_data['value'], predictions),
            'r2': r2_score(test_data['value'], predictions)
        }
        results[name] = metrics
        
    # Compare model performance
    for metric in ['mse', 'mae', 'r2']:
        values = [results[model][metric] for model in models]
        assert len(set(values)) > 1  # Ensure models have different performance 