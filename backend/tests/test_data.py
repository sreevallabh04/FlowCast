import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data.generator import DataGenerator
from data.processor import DataProcessor
from data.validation import DataValidator
from data.metrics import MetricsCalculator
from data.cache import CacheManager
from data.queue import QueueManager
from data.scheduler import Scheduler
from data.notification import NotificationManager
from data.backup import DataBackup
from data.migration import DataMigration
from data.transformation import DataTransformation

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

class TestDataGenerator:
    def test_data_generation(self):
        generator = DataGenerator()
        data = generator.generate_data(
            num_records=1000,
            start_date='2020-01-01',
            end_date='2023-12-31'
        )
        assert len(data) == 1000
        assert all(col in data.columns for col in ['date', 'value'])
        assert data['date'].min() >= pd.Timestamp('2020-01-01')
        assert data['date'].max() <= pd.Timestamp('2023-12-31')
        
    def test_data_consistency(self):
        generator = DataGenerator()
        data1 = generator.generate_data(
            num_records=1000,
            start_date='2020-01-01',
            end_date='2023-12-31',
            seed=42
        )
        data2 = generator.generate_data(
            num_records=1000,
            start_date='2020-01-01',
            end_date='2023-12-31',
            seed=42
        )
        pd.testing.assert_frame_equal(data1, data2)
        
    def test_data_statistics(self):
        generator = DataGenerator()
        data = generator.generate_data(
            num_records=1000,
            start_date='2020-01-01',
            end_date='2023-12-31'
        )
        assert data['value'].mean() > 0
        assert data['value'].std() > 0
        assert not data['value'].isnull().any()

class TestDataProcessor:
    def test_data_processing(self, sample_data):
        processor = DataProcessor()
        processed_data = processor.process_data(sample_data)
        assert len(processed_data) > 0
        assert all(col in processed_data.columns for col in ['date', 'value'])
        assert not processed_data['value'].isnull().any()
        
    def test_data_cleaning(self, sample_data):
        # Add some invalid data
        sample_data.loc[0, 'value'] = np.nan
        sample_data.loc[1, 'value'] = -np.inf
        
        processor = DataProcessor()
        processed_data = processor.process_data(sample_data)
        assert not processed_data['value'].isnull().any()
        assert not np.isinf(processed_data['value']).any()
        
    def test_data_transformation(self, sample_data):
        processor = DataProcessor()
        processed_data = processor.process_data(sample_data)
        assert processed_data['date'].dtype == 'datetime64[ns]'
        assert processed_data['value'].dtype in ['float64', 'int64']

class TestDataValidator:
    def test_data_validation(self, processed_data):
        validator = DataValidator()
        validation_result = validator.validate_data(processed_data)
        assert validation_result['is_valid']
        assert len(validation_result['errors']) == 0
        
    def test_invalid_data_validation(self):
        # Create invalid data
        invalid_data = pd.DataFrame({
            'date': ['invalid_date'],
            'value': ['invalid_value']
        })
        
        validator = DataValidator()
        validation_result = validator.validate_data(invalid_data)
        assert not validation_result['is_valid']
        assert len(validation_result['errors']) > 0
        
    def test_missing_data_validation(self):
        # Create data with missing values
        missing_data = pd.DataFrame({
            'date': [None],
            'value': [None]
        })
        
        validator = DataValidator()
        validation_result = validator.validate_data(missing_data)
        assert not validation_result['is_valid']
        assert len(validation_result['errors']) > 0

class TestMetricsCalculator:
    def test_metrics_calculation(self, processed_data):
        metrics = MetricsCalculator()
        calculated_metrics = metrics.calculate_metrics(processed_data)
        assert all(metric >= 0 for metric in calculated_metrics.values())
        assert 'mean' in calculated_metrics
        assert 'std' in calculated_metrics
        assert 'min' in calculated_metrics
        assert 'max' in calculated_metrics
        
    def test_metrics_consistency(self, processed_data):
        metrics = MetricsCalculator()
        metrics1 = metrics.calculate_metrics(processed_data)
        metrics2 = metrics.calculate_metrics(processed_data)
        assert metrics1 == metrics2
        
    def test_metrics_edge_cases(self):
        # Test with empty data
        empty_data = pd.DataFrame(columns=['date', 'value'])
        metrics = MetricsCalculator()
        calculated_metrics = metrics.calculate_metrics(empty_data)
        assert all(metric == 0 for metric in calculated_metrics.values())

class TestCacheManager:
    def test_cache_operations(self, processed_data):
        cache = CacheManager()
        
        # Test setting and getting data
        cache.set('test_data', processed_data)
        cached_data = cache.get('test_data')
        pd.testing.assert_frame_equal(processed_data, cached_data)
        
        # Test cache invalidation
        cache.delete('test_data')
        assert cache.get('test_data') is None
        
    def test_cache_expiration(self, processed_data):
        cache = CacheManager()
        cache.set('test_data', processed_data, ttl=1)  # 1 second TTL
        import time
        time.sleep(2)
        assert cache.get('test_data') is None
        
    def test_cache_size_limit(self, processed_data):
        cache = CacheManager(max_size=1)  # 1 MB limit
        cache.set('test_data1', processed_data)
        cache.set('test_data2', processed_data)
        assert cache.get('test_data1') is None  # First item should be evicted
        assert cache.get('test_data2') is not None

class TestQueueManager:
    def test_queue_operations(self, processed_data):
        queue = QueueManager()
        
        # Test enqueue and dequeue
        queue.enqueue('test_task', processed_data)
        task = queue.dequeue('test_task')
        assert task is not None
        pd.testing.assert_frame_equal(processed_data, task)
        
        # Test queue status
        status = queue.get_status('test_task')
        assert status['pending'] >= 0
        assert status['processing'] >= 0
        assert status['completed'] >= 0
        
    def test_queue_priority(self, processed_data):
        queue = QueueManager()
        
        # Test priority queue
        queue.enqueue('test_task', processed_data, priority=2)
        queue.enqueue('test_task', processed_data, priority=1)
        task = queue.dequeue('test_task')
        assert task is not None
        
    def test_queue_cleanup(self, processed_data):
        queue = QueueManager()
        queue.enqueue('test_task', processed_data)
        queue.cleanup('test_task')
        assert queue.get_status('test_task')['pending'] == 0

class TestScheduler:
    def test_scheduler_operations(self):
        scheduler = Scheduler()
        
        # Test job scheduling
        job_id = scheduler.schedule_job(
            'test_job',
            '*/5 * * * *',  # Every 5 minutes
            {'param': 'value'}
        )
        assert job_id is not None
        
        # Test job status
        status = scheduler.get_job_status(job_id)
        assert status['status'] in ['pending', 'running', 'completed', 'failed']
        
    def test_scheduler_cleanup(self):
        scheduler = Scheduler()
        job_id = scheduler.schedule_job(
            'test_job',
            '*/5 * * * *',
            {'param': 'value'}
        )
        scheduler.cleanup_job(job_id)
        assert scheduler.get_job_status(job_id)['status'] == 'deleted'

class TestNotificationManager:
    def test_notification_operations(self):
        notifier = NotificationManager()
        
        # Test notification sending
        notification_id = notifier.send_notification(
            'test_user',
            'Test Notification',
            'This is a test notification',
            'info'
        )
        assert notification_id is not None
        
        # Test notification status
        status = notifier.get_notification_status(notification_id)
        assert status['status'] in ['sent', 'delivered', 'failed']
        
    def test_notification_cleanup(self):
        notifier = NotificationManager()
        notification_id = notifier.send_notification(
            'test_user',
            'Test Notification',
            'This is a test notification',
            'info'
        )
        notifier.cleanup_notification(notification_id)
        assert notifier.get_notification_status(notification_id)['status'] == 'deleted'

class TestDataBackup:
    def test_backup_operations(self, processed_data, tmp_path):
        backup = DataBackup()
        
        # Test backup creation
        backup_id = backup.create_backup(processed_data, 'test_backup')
        assert backup_id is not None
        
        # Test backup restoration
        restored_data = backup.restore_backup(backup_id)
        pd.testing.assert_frame_equal(processed_data, restored_data)
        
    def test_backup_cleanup(self, processed_data, tmp_path):
        backup = DataBackup()
        backup_id = backup.create_backup(processed_data, 'test_backup')
        backup.cleanup_backup(backup_id)
        assert backup.get_backup_status(backup_id)['status'] == 'deleted'

class TestDataMigration:
    def test_migration_operations(self, processed_data):
        migration = DataMigration()
        
        # Test data migration
        migration_id = migration.migrate_data(
            processed_data,
            'source_db',
            'target_db'
        )
        assert migration_id is not None
        
        # Test migration status
        status = migration.get_migration_status(migration_id)
        assert status['status'] in ['pending', 'running', 'completed', 'failed']
        
    def test_migration_cleanup(self, processed_data):
        migration = DataMigration()
        migration_id = migration.migrate_data(
            processed_data,
            'source_db',
            'target_db'
        )
        migration.cleanup_migration(migration_id)
        assert migration.get_migration_status(migration_id)['status'] == 'deleted'

class TestDataTransformation:
    def test_transformation_operations(self, processed_data):
        transformer = DataTransformation()
        
        # Test data transformation
        transformed_data = transformer.transform_data(processed_data)
        assert len(transformed_data) > 0
        assert all(col in transformed_data.columns for col in ['date', 'value'])
        
    def test_transformation_consistency(self, processed_data):
        transformer = DataTransformation()
        transformed_data1 = transformer.transform_data(processed_data)
        transformed_data2 = transformer.transform_data(processed_data)
        pd.testing.assert_frame_equal(transformed_data1, transformed_data2)
        
    def test_transformation_validation(self, processed_data):
        transformer = DataTransformation()
        transformed_data = transformer.transform_data(processed_data)
        assert not transformed_data['value'].isnull().any()
        assert not np.isinf(transformed_data['value']).any() 