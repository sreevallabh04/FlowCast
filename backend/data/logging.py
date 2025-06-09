import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import logging.handlers
import structlog
from structlog import get_logger
import loguru
from loguru import logger
import elasticsearch
from elasticsearch import Elasticsearch
import redis
from redis import Redis
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
import time

@dataclass
class LoggingConfig:
    """Configuration for the logging system."""
    log_dir: str
    log_level: str
    log_format: str
    log_rotation: str
    log_retention: int
    elasticsearch_url: str
    redis_url: str
    sentry_dsn: str
    enable_metrics: bool
    enable_tracing: bool
    enable_alerting: bool

class DataLogging:
    def __init__(self, config_path: str = 'config/logging_config.yaml'):
        """Initialize the logging system with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize logging state
        self.is_logging = False
        self.log_status = {}
        
        # Set up database connection
        self.engine = create_engine(self.config.database_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        
        # Set up logging
        self._setup_logging()
        
        # Set up external services
        self._setup_external_services()
        
        # Set up metrics
        if self.config.enable_metrics:
            self._setup_metrics()

    def _load_config(self) -> LoggingConfig:
        """Load logging configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return LoggingConfig(**config_dict)
        except Exception as e:
            print(f"Error loading logging configuration: {str(e)}")
            raise

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        try:
            # Create log directory
            os.makedirs(self.config.log_dir, exist_ok=True)
            
            # Set up structlog
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory(),
                wrapper_class=structlog.BoundLogger,
                cache_logger_on_first_use=True
            )
            
            # Set up loguru
            logger.add(
                os.path.join(self.config.log_dir, "app.log"),
                rotation=self.config.log_rotation,
                retention=self.config.log_retention,
                level=self.config.log_level,
                format=self.config.log_format
            )
            
            # Set up Sentry
            if self.config.sentry_dsn:
                sentry_sdk.init(
                    dsn=self.config.sentry_dsn,
                    integrations=[LoggingIntegration()],
                    traces_sample_rate=1.0
                )
            
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")
            raise

    def _setup_external_services(self) -> None:
        """Set up external logging services."""
        try:
            # Set up Elasticsearch
            if self.config.elasticsearch_url:
                self.es = Elasticsearch([self.config.elasticsearch_url])
            
            # Set up Redis
            if self.config.redis_url:
                self.redis = Redis.from_url(self.config.redis_url)
            
        except Exception as e:
            print(f"Error setting up external services: {str(e)}")
            raise

    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics."""
        try:
            # Define metrics
            self.log_counter = Counter(
                'log_entries_total',
                'Total number of log entries',
                ['level', 'module']
            )
            
            self.log_latency = Histogram(
                'log_latency_seconds',
                'Log processing latency',
                ['level']
            )
            
            self.log_size = Gauge(
                'log_size_bytes',
                'Current log file size',
                ['file']
            )
            
        except Exception as e:
            print(f"Error setting up metrics: {str(e)}")
            raise

    def log_event(self, level: str, message: str, **kwargs) -> None:
        """Log an event with the specified level and message."""
        try:
            # Get logger
            logger = get_logger()
            
            # Add context
            logger = logger.bind(**kwargs)
            
            # Log event
            if level == 'DEBUG':
                logger.debug(message)
            elif level == 'INFO':
                logger.info(message)
            elif level == 'WARNING':
                logger.warning(message)
            elif level == 'ERROR':
                logger.error(message)
            elif level == 'CRITICAL':
                logger.critical(message)
            
            # Update metrics
            if self.config.enable_metrics:
                self.log_counter.labels(level=level, module=kwargs.get('module', 'unknown')).inc()
            
            # Store in Elasticsearch
            if hasattr(self, 'es'):
                self._store_in_elasticsearch(level, message, **kwargs)
            
            # Store in Redis
            if hasattr(self, 'redis'):
                self._store_in_redis(level, message, **kwargs)
            
        except Exception as e:
            print(f"Error logging event: {str(e)}")
            raise

    def _store_in_elasticsearch(self, level: str, message: str, **kwargs) -> None:
        """Store log entry in Elasticsearch."""
        try:
            # Create document
            doc = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                **kwargs
            }
            
            # Index document
            self.es.index(
                index=f"logs-{datetime.now().strftime('%Y.%m.%d')}",
                body=doc
            )
            
        except Exception as e:
            print(f"Error storing in Elasticsearch: {str(e)}")
            raise

    def _store_in_redis(self, level: str, message: str, **kwargs) -> None:
        """Store log entry in Redis."""
        try:
            # Create log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                **kwargs
            }
            
            # Store in Redis
            self.redis.lpush(
                f"logs:{level}",
                json.dumps(log_entry)
            )
            
            # Set expiration
            self.redis.expire(
                f"logs:{level}",
                self.config.log_retention * 86400  # Convert days to seconds
            )
            
        except Exception as e:
            print(f"Error storing in Redis: {str(e)}")
            raise

    def get_logs(self, level: Optional[str] = None, start_time: Optional[datetime] = None,
                end_time: Optional[datetime] = None, **filters) -> List[Dict]:
        """Retrieve logs with optional filtering."""
        try:
            logs = []
            
            # Query Elasticsearch
            if hasattr(self, 'es'):
                query = {
                    'query': {
                        'bool': {
                            'must': []
                        }
                    }
                }
                
                # Add filters
                if level:
                    query['query']['bool']['must'].append({'term': {'level': level}})
                
                if start_time:
                    query['query']['bool']['must'].append({
                        'range': {'timestamp': {'gte': start_time.isoformat()}}
                    })
                
                if end_time:
                    query['query']['bool']['must'].append({
                        'range': {'timestamp': {'lte': end_time.isoformat()}}
                    })
                
                for key, value in filters.items():
                    query['query']['bool']['must'].append({'term': {key: value}})
                
                # Execute query
                response = self.es.search(
                    index=f"logs-{datetime.now().strftime('%Y.%m.%d')}",
                    body=query
                )
                
                # Process results
                for hit in response['hits']['hits']:
                    logs.append(hit['_source'])
            
            # Query Redis
            if hasattr(self, 'redis'):
                if level:
                    keys = [f"logs:{level}"]
                else:
                    keys = self.redis.keys("logs:*")
                
                for key in keys:
                    entries = self.redis.lrange(key, 0, -1)
                    for entry in entries:
                        log_entry = json.loads(entry)
                        
                        # Apply filters
                        if start_time and datetime.fromisoformat(log_entry['timestamp']) < start_time:
                            continue
                        
                        if end_time and datetime.fromisoformat(log_entry['timestamp']) > end_time:
                            continue
                        
                        for key, value in filters.items():
                            if log_entry.get(key) != value:
                                break
                        else:
                            logs.append(log_entry)
            
            return logs
            
        except Exception as e:
            print(f"Error retrieving logs: {str(e)}")
            raise

    def analyze_logs(self, level: Optional[str] = None, start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> Dict:
        """Analyze logs and generate statistics."""
        try:
            # Get logs
            logs = self.get_logs(level, start_time, end_time)
            
            # Initialize statistics
            stats = {
                'total_logs': len(logs),
                'level_distribution': {},
                'module_distribution': {},
                'error_rate': 0,
                'average_response_time': 0,
                'peak_times': []
            }
            
            # Calculate statistics
            for log in logs:
                # Level distribution
                level = log['level']
                stats['level_distribution'][level] = stats['level_distribution'].get(level, 0) + 1
                
                # Module distribution
                module = log.get('module', 'unknown')
                stats['module_distribution'][module] = stats['module_distribution'].get(module, 0) + 1
                
                # Error rate
                if level in ['ERROR', 'CRITICAL']:
                    stats['error_rate'] += 1
                
                # Response time
                if 'response_time' in log:
                    stats['average_response_time'] += log['response_time']
            
            # Calculate averages
            if stats['total_logs'] > 0:
                stats['error_rate'] = stats['error_rate'] / stats['total_logs']
                stats['average_response_time'] = stats['average_response_time'] / stats['total_logs']
            
            # Find peak times
            if logs:
                df = pd.DataFrame(logs)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
                peak_hours = df['hour'].value_counts().nlargest(5)
                stats['peak_times'] = peak_hours.index.tolist()
            
            return stats
            
        except Exception as e:
            print(f"Error analyzing logs: {str(e)}")
            raise

    def rotate_logs(self) -> None:
        """Rotate log files."""
        try:
            # Get current log files
            log_files = [f for f in os.listdir(self.config.log_dir) if f.endswith('.log')]
            
            for log_file in log_files:
                file_path = os.path.join(self.config.log_dir, log_file)
                
                # Check file size
                if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
                    # Create backup
                    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.rename(file_path, backup_path)
                    
                    # Create new log file
                    open(file_path, 'a').close()
                    
                    # Update metrics
                    if self.config.enable_metrics:
                        self.log_size.labels(file=log_file).set(0)
            
        except Exception as e:
            print(f"Error rotating logs: {str(e)}")
            raise

    def cleanup_logs(self) -> None:
        """Clean up old log files."""
        try:
            # Get all log files
            log_files = [f for f in os.listdir(self.config.log_dir) if f.endswith('.log')]
            
            for log_file in log_files:
                file_path = os.path.join(self.config.log_dir, log_file)
                
                # Check file age
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path))
                if file_age.days > self.config.log_retention:
                    # Remove old file
                    os.remove(file_path)
                    
                    # Update metrics
                    if self.config.enable_metrics:
                        self.log_size.labels(file=log_file).set(0)
            
        except Exception as e:
            print(f"Error cleaning up logs: {str(e)}")
            raise

    def get_logging_status(self) -> Dict:
        """Get current logging status."""
        return {
            'is_logging': self.is_logging,
            'log_files': [f for f in os.listdir(self.config.log_dir) if f.endswith('.log')],
            'log_size': sum(os.path.getsize(os.path.join(self.config.log_dir, f))
                          for f in os.listdir(self.config.log_dir) if f.endswith('.log')),
            'last_rotation': self.log_status.get('last_rotation'),
            'last_cleanup': self.log_status.get('last_cleanup')
        }

# Example usage
if __name__ == "__main__":
    # Create logging instance
    logging = DataLogging()
    
    # Example logging operations
    logging.log_event(
        level='INFO',
        message='Application started',
        module='main',
        user='admin'
    )
    
    # Analyze logs
    stats = logging.analyze_logs(
        start_time=datetime.now() - timedelta(days=1),
        end_time=datetime.now()
    )
    print(f"Log statistics: {stats}") 