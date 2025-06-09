import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any, Callable
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import pytest
from hypothesis import given, strategies as st
import great_expectations as ge
from great_expectations.dataset import PandasDataset
import unittest
from unittest.mock import Mock, patch
import tempfile
import shutil
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
import time

@dataclass
class TestConfig:
    """Configuration for the testing system."""
    test_data_dir: str
    expectations_dir: str
    results_dir: str
    database_url: str
    test_timeout: int
    retry_count: int
    parallel_tests: bool
    max_workers: int
    coverage_threshold: float

class DataTesting:
    def __init__(self, config_path: str = 'config/test_config.yaml'):
        """Initialize the testing system with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize testing state
        self.is_testing = False
        self.test_results = []
        self.coverage_report = {}
        
        # Set up database connection
        self.engine = create_engine(self.config.database_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Create necessary directories
        os.makedirs(self.config.test_data_dir, exist_ok=True)
        os.makedirs(self.config.expectations_dir, exist_ok=True)
        os.makedirs(self.config.results_dir, exist_ok=True)

    def _load_config(self) -> TestConfig:
        """Load test configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return TestConfig(**config_dict)
        except Exception as e:
            self.logger.error(f"Error loading test configuration: {str(e)}")
            raise

    def run_tests(self, test_type: str = 'all') -> Dict:
        """Run data tests."""
        try:
            self.is_testing = True
            self.logger.info(f"Running {test_type} tests")
            
            start_time = time.time()
            results = {
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'errors': []
            }
            
            if test_type in ['all', 'data_quality']:
                self._run_data_quality_tests(results)
            
            if test_type in ['all', 'schema']:
                self._run_schema_tests(results)
            
            if test_type in ['all', 'integration']:
                self._run_integration_tests(results)
            
            if test_type in ['all', 'performance']:
                self._run_performance_tests(results)
            
            # Calculate coverage
            self._calculate_coverage()
            
            # Save results
            self._save_test_results(results)
            
            duration = time.time() - start_time
            self.logger.info(f"Tests completed in {duration:.2f} seconds")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error running tests: {str(e)}")
            raise
        finally:
            self.is_testing = False

    def _run_data_quality_tests(self, results: Dict) -> None:
        """Run data quality tests using Great Expectations."""
        try:
            # Load expectations
            expectations = self._load_expectations()
            
            # Test each dataset
            for dataset_name, dataset_expectations in expectations.items():
                # Load dataset
                dataset_path = os.path.join(self.config.test_data_dir, f'{dataset_name}.csv')
                if not os.path.exists(dataset_path):
                    self.logger.warning(f"Dataset {dataset_name} not found")
                    continue
                
                df = pd.read_csv(dataset_path)
                ge_df = PandasDataset(df)
                
                # Run expectations
                for expectation in dataset_expectations:
                    try:
                        result = ge_df.expectation(expectation)
                        if result.success:
                            results['passed'] += 1
                        else:
                            results['failed'] += 1
                            results['errors'].append({
                                'dataset': dataset_name,
                                'expectation': expectation,
                                'error': result.error
                            })
                    except Exception as e:
                        results['errors'].append({
                            'dataset': dataset_name,
                            'expectation': expectation,
                            'error': str(e)
                        })
            
        except Exception as e:
            self.logger.error(f"Error running data quality tests: {str(e)}")
            raise

    def _run_schema_tests(self, results: Dict) -> None:
        """Run database schema tests."""
        try:
            # Get database inspector
            inspector = sa.inspect(self.engine)
            
            # Test required tables
            required_tables = ['products', 'locations', 'suppliers', 'vehicles', 'events',
                             'weather_data', 'sales_data', 'inventory_data', 'delivery_data']
            
            for table in required_tables:
                try:
                    # Check if table exists
                    if not inspector.has_table(table):
                        results['failed'] += 1
                        results['errors'].append({
                            'test': 'schema',
                            'table': table,
                            'error': 'Table does not exist'
                        })
                        continue
                    
                    # Check columns
                    columns = inspector.get_columns(table)
                    if not columns:
                        results['failed'] += 1
                        results['errors'].append({
                            'test': 'schema',
                            'table': table,
                            'error': 'Table has no columns'
                        })
                        continue
                    
                    # Check constraints
                    constraints = inspector.get_unique_constraints(table)
                    foreign_keys = inspector.get_foreign_keys(table)
                    indexes = inspector.get_indexes(table)
                    
                    results['passed'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': 'schema',
                        'table': table,
                        'error': str(e)
                    })
            
        except Exception as e:
            self.logger.error(f"Error running schema tests: {str(e)}")
            raise

    def _run_integration_tests(self, results: Dict) -> None:
        """Run integration tests."""
        try:
            # Test data flow
            self._test_data_flow(results)
            
            # Test API endpoints
            self._test_api_endpoints(results)
            
            # Test external integrations
            self._test_external_integrations(results)
            
        except Exception as e:
            self.logger.error(f"Error running integration tests: {str(e)}")
            raise

    def _run_performance_tests(self, results: Dict) -> None:
        """Run performance tests."""
        try:
            # Test query performance
            self._test_query_performance(results)
            
            # Test data processing performance
            self._test_processing_performance(results)
            
            # Test API response times
            self._test_api_performance(results)
            
        except Exception as e:
            self.logger.error(f"Error running performance tests: {str(e)}")
            raise

    def _test_data_flow(self, results: Dict) -> None:
        """Test data flow through the system."""
        try:
            # Test data generation
            with patch('data.generator.DataGenerator') as mock_generator:
                mock_generator.generate_all_data.return_value = pd.DataFrame()
                self._run_data_generation_test(results)
            
            # Test data processing
            with patch('data.processor.DataProcessor') as mock_processor:
                mock_processor.process_data.return_value = pd.DataFrame()
                self._run_data_processing_test(results)
            
            # Test data validation
            with patch('data.validator.DataValidator') as mock_validator:
                mock_validator.validate_data.return_value = True
                self._run_data_validation_test(results)
            
        except Exception as e:
            self.logger.error(f"Error testing data flow: {str(e)}")
            raise

    def _test_api_endpoints(self, results: Dict) -> None:
        """Test API endpoints."""
        try:
            # Test endpoints
            endpoints = [
                '/api/products',
                '/api/locations',
                '/api/suppliers',
                '/api/vehicles',
                '/api/events',
                '/api/weather',
                '/api/sales',
                '/api/inventory',
                '/api/deliveries'
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f'http://localhost:8000{endpoint}')
                    if response.status_code == 200:
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'test': 'api',
                            'endpoint': endpoint,
                            'error': f'Status code: {response.status_code}'
                        })
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': 'api',
                        'endpoint': endpoint,
                        'error': str(e)
                    })
            
        except Exception as e:
            self.logger.error(f"Error testing API endpoints: {str(e)}")
            raise

    def _test_external_integrations(self, results: Dict) -> None:
        """Test external system integrations."""
        try:
            # Test database connection
            try:
                with self.engine.connect() as conn:
                    conn.execute("SELECT 1")
                results['passed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'test': 'integration',
                    'system': 'database',
                    'error': str(e)
                })
            
            # Test S3 connection
            try:
                s3 = boto3.client('s3')
                s3.list_buckets()
                results['passed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'test': 'integration',
                    'system': 's3',
                    'error': str(e)
                })
            
        except Exception as e:
            self.logger.error(f"Error testing external integrations: {str(e)}")
            raise

    def _test_query_performance(self, results: Dict) -> None:
        """Test database query performance."""
        try:
            # Test complex queries
            queries = [
                "SELECT * FROM sales_data WHERE date >= NOW() - INTERVAL '30 days'",
                "SELECT product_id, SUM(quantity) FROM sales_data GROUP BY product_id",
                "SELECT location_id, AVG(temperature) FROM weather_data GROUP BY location_id"
            ]
            
            for query in queries:
                try:
                    start_time = time.time()
                    with self.engine.connect() as conn:
                        conn.execute(query)
                    duration = time.time() - start_time
                    
                    if duration < 1.0:  # 1 second threshold
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'test': 'performance',
                            'query': query,
                            'error': f'Query took {duration:.2f} seconds'
                        })
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': 'performance',
                        'query': query,
                        'error': str(e)
                    })
            
        except Exception as e:
            self.logger.error(f"Error testing query performance: {str(e)}")
            raise

    def _test_processing_performance(self, results: Dict) -> None:
        """Test data processing performance."""
        try:
            # Test data processing
            data_sizes = [1000, 10000, 100000]
            
            for size in data_sizes:
                try:
                    # Generate test data
                    df = pd.DataFrame({
                        'id': range(size),
                        'value': np.random.rand(size)
                    })
                    
                    # Test processing
                    start_time = time.time()
                    df['processed'] = df['value'].apply(lambda x: x * 2)
                    duration = time.time() - start_time
                    
                    if duration < 1.0:  # 1 second threshold
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'test': 'performance',
                            'size': size,
                            'error': f'Processing took {duration:.2f} seconds'
                        })
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': 'performance',
                        'size': size,
                        'error': str(e)
                    })
            
        except Exception as e:
            self.logger.error(f"Error testing processing performance: {str(e)}")
            raise

    def _test_api_performance(self, results: Dict) -> None:
        """Test API performance."""
        try:
            # Test endpoints
            endpoints = [
                '/api/products',
                '/api/locations',
                '/api/suppliers'
            ]
            
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f'http://localhost:8000{endpoint}')
                    duration = time.time() - start_time
                    
                    if duration < 0.5:  # 500ms threshold
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'test': 'performance',
                            'endpoint': endpoint,
                            'error': f'Response took {duration:.2f} seconds'
                        })
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': 'performance',
                        'endpoint': endpoint,
                        'error': str(e)
                    })
            
        except Exception as e:
            self.logger.error(f"Error testing API performance: {str(e)}")
            raise

    def _load_expectations(self) -> Dict:
        """Load Great Expectations configurations."""
        try:
            expectations = {}
            
            for file in os.listdir(self.config.expectations_dir):
                if file.endswith('.yaml'):
                    with open(os.path.join(self.config.expectations_dir, file), 'r') as f:
                        dataset_expectations = yaml.safe_load(f)
                        expectations[file[:-5]] = dataset_expectations
            
            return expectations
            
        except Exception as e:
            self.logger.error(f"Error loading expectations: {str(e)}")
            raise

    def _calculate_coverage(self) -> None:
        """Calculate test coverage."""
        try:
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['status'] == 'passed')
            
            coverage = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.coverage_report = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'coverage': coverage,
                'threshold': self.config.coverage_threshold,
                'meets_threshold': coverage >= self.config.coverage_threshold
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating coverage: {str(e)}")
            raise

    def _save_test_results(self, results: Dict) -> None:
        """Save test results to file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_path = os.path.join(self.config.results_dir, f'test_results_{timestamp}.json')
            
            results['timestamp'] = datetime.now().isoformat()
            results['coverage'] = self.coverage_report
            
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving test results: {str(e)}")
            raise

    def get_test_status(self) -> Dict:
        """Get current test status."""
        return {
            'is_testing': self.is_testing,
            'total_tests': len(self.test_results),
            'coverage': self.coverage_report.get('coverage', 0),
            'last_run': self.test_results[-1] if self.test_results else None
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run tests
    testing = DataTesting()
    results = testing.run_tests() 