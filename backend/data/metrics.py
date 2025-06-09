import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import json
import yaml
import os
from dataclasses import dataclass
import time
from datetime import datetime, timedelta
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, Summary
import influxdb_client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import psutil
import threading
import logging
import hashlib
import requests
from requests.exceptions import RequestException
import socket
import platform
import subprocess
import re

@dataclass
class MetricsConfig:
    """Configuration for the metrics system."""
    metrics_port: int
    influxdb_url: str
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str
    collection_interval: int
    retention_days: int
    alert_threshold: float
    enable_prometheus: bool
    enable_influxdb: bool
    enable_alerting: bool

class DataMetrics:
    def __init__(self, config_path: str = 'config/metrics_config.yaml'):
        """Initialize the metrics system."""
        self.config_path = config_path
        self.config = self._load_config()
        self.metrics = {}
        self.is_collecting = False
        self.collection_thread = None
        
        # Initialize metrics
        self._init_metrics()
        
        # Initialize external services
        self._init_external_services()
        
        # Start collection
        self.start_collection()

    def _load_config(self) -> MetricsConfig:
        """Load metrics configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return MetricsConfig(**config_dict)
        except Exception as e:
            print(f"Error loading metrics configuration: {str(e)}")
            raise

    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        try:
            # System metrics
            self.metrics['cpu_usage'] = Gauge('cpu_usage_percent', 'CPU usage percentage')
            self.metrics['memory_usage'] = Gauge('memory_usage_percent', 'Memory usage percentage')
            self.metrics['disk_usage'] = Gauge('disk_usage_percent', 'Disk usage percentage')
            self.metrics['network_io'] = Gauge('network_io_bytes', 'Network I/O in bytes')
            
            # Application metrics
            self.metrics['request_count'] = Counter('request_total', 'Total number of requests')
            self.metrics['request_latency'] = Histogram('request_latency_seconds', 'Request latency in seconds')
            self.metrics['error_count'] = Counter('error_total', 'Total number of errors')
            self.metrics['data_processed'] = Counter('data_processed_bytes', 'Total data processed in bytes')
            
            # Business metrics
            self.metrics['sales_count'] = Counter('sales_total', 'Total number of sales')
            self.metrics['inventory_level'] = Gauge('inventory_level', 'Current inventory level')
            self.metrics['delivery_time'] = Histogram('delivery_time_seconds', 'Delivery time in seconds')
            self.metrics['customer_satisfaction'] = Gauge('customer_satisfaction', 'Customer satisfaction score')
            
        except Exception as e:
            print(f"Error initializing metrics: {str(e)}")
            raise

    def _init_external_services(self) -> None:
        """Initialize external metrics services."""
        try:
            # Initialize InfluxDB client
            if self.config.enable_influxdb:
                self.influxdb = InfluxDBClient(
                    url=self.config.influxdb_url,
                    token=self.config.influxdb_token,
                    org=self.config.influxdb_org
                )
                self.write_api = self.influxdb.write_api(write_options=SYNCHRONOUS)
            
        except Exception as e:
            print(f"Error initializing external services: {str(e)}")
            raise

    def start_collection(self) -> None:
        """Start metrics collection."""
        try:
            if not self.is_collecting:
                self.is_collecting = True
                self.collection_thread = threading.Thread(target=self._collect_metrics)
                self.collection_thread.daemon = True
                self.collection_thread.start()
            
        except Exception as e:
            print(f"Error starting metrics collection: {str(e)}")
            raise

    def stop_collection(self) -> None:
        """Stop metrics collection."""
        try:
            self.is_collecting = False
            if self.collection_thread:
                self.collection_thread.join()
            
        except Exception as e:
            print(f"Error stopping metrics collection: {str(e)}")
            raise

    def _collect_metrics(self) -> None:
        """Collect system and application metrics."""
        try:
            while self.is_collecting:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Collect application metrics
                self._collect_application_metrics()
                
                # Collect business metrics
                self._collect_business_metrics()
                
                # Store metrics in InfluxDB
                if self.config.enable_influxdb:
                    self._store_metrics_influxdb()
                
                # Sleep for collection interval
                time.sleep(self.config.collection_interval)
            
        except Exception as e:
            print(f"Error collecting metrics: {str(e)}")
            raise

    def _collect_system_metrics(self) -> None:
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics['disk_usage'].set(disk.percent)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.metrics['network_io'].set(net_io.bytes_sent + net_io.bytes_recv)
            
        except Exception as e:
            print(f"Error collecting system metrics: {str(e)}")
            raise

    def _collect_application_metrics(self) -> None:
        """Collect application-level metrics."""
        try:
            # Get process information
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            self.metrics['data_processed'].inc(memory_info.rss)
            
            # Thread count
            self.metrics['thread_count'] = Gauge('thread_count', 'Number of threads')
            self.metrics['thread_count'].set(process.num_threads())
            
            # File descriptors
            if hasattr(process, 'num_fds'):
                self.metrics['file_descriptors'] = Gauge('file_descriptors', 'Number of file descriptors')
                self.metrics['file_descriptors'].set(process.num_fds())
            
        except Exception as e:
            print(f"Error collecting application metrics: {str(e)}")
            raise

    def _collect_business_metrics(self) -> None:
        """Collect business-level metrics."""
        try:
            # Example business metrics collection
            # In a real application, these would be collected from your business logic
            
            # Sales count
            self.metrics['sales_count'].inc()
            
            # Inventory level
            self.metrics['inventory_level'].set(100)  # Example value
            
            # Delivery time
            self.metrics['delivery_time'].observe(30)  # Example value
            
            # Customer satisfaction
            self.metrics['customer_satisfaction'].set(4.5)  # Example value
            
        except Exception as e:
            print(f"Error collecting business metrics: {str(e)}")
            raise

    def _store_metrics_influxdb(self) -> None:
        """Store metrics in InfluxDB."""
        try:
            if not self.config.enable_influxdb:
                return
            
            # Create data points
            points = []
            
            for metric_name, metric in self.metrics.items():
                if isinstance(metric, (Gauge, Counter, Histogram)):
                    point = Point(metric_name)
                    
                    # Add metric value
                    if isinstance(metric, Gauge):
                        point.field('value', metric._value.get())
                    elif isinstance(metric, Counter):
                        point.field('value', metric._value.get())
                    elif isinstance(metric, Histogram):
                        point.field('sum', metric._sum.get())
                        point.field('count', metric._count.get())
                    
                    # Add timestamp
                    point.time(datetime.utcnow())
                    
                    points.append(point)
            
            # Write points to InfluxDB
            self.write_api.write(
                bucket=self.config.influxdb_bucket,
                record=points
            )
            
        except Exception as e:
            print(f"Error storing metrics in InfluxDB: {str(e)}")
            raise

    def get_metrics_summary(self) -> Dict:
        """Get a summary of current metrics."""
        try:
            summary = {}
            
            for metric_name, metric in self.metrics.items():
                if isinstance(metric, Gauge):
                    summary[metric_name] = metric._value.get()
                elif isinstance(metric, Counter):
                    summary[metric_name] = metric._value.get()
                elif isinstance(metric, Histogram):
                    summary[metric_name] = {
                        'sum': metric._sum.get(),
                        'count': metric._count.get(),
                        'mean': metric._sum.get() / metric._count.get() if metric._count.get() > 0 else 0
                    }
            
            return summary
            
        except Exception as e:
            print(f"Error getting metrics summary: {str(e)}")
            raise

    def check_alerts(self) -> List[Dict]:
        """Check for metric alerts."""
        try:
            alerts = []
            
            # Check CPU usage
            if self.metrics['cpu_usage']._value.get() > self.config.alert_threshold:
                alerts.append({
                    'metric': 'cpu_usage',
                    'value': self.metrics['cpu_usage']._value.get(),
                    'threshold': self.config.alert_threshold,
                    'message': 'CPU usage above threshold'
                })
            
            # Check memory usage
            if self.metrics['memory_usage']._value.get() > self.config.alert_threshold:
                alerts.append({
                    'metric': 'memory_usage',
                    'value': self.metrics['memory_usage']._value.get(),
                    'threshold': self.config.alert_threshold,
                    'message': 'Memory usage above threshold'
                })
            
            # Check disk usage
            if self.metrics['disk_usage']._value.get() > self.config.alert_threshold:
                alerts.append({
                    'metric': 'disk_usage',
                    'value': self.metrics['disk_usage']._value.get(),
                    'threshold': self.config.alert_threshold,
                    'message': 'Disk usage above threshold'
                })
            
            return alerts
            
        except Exception as e:
            print(f"Error checking alerts: {str(e)}")
            raise

    def cleanup_old_metrics(self) -> None:
        """Clean up old metrics data."""
        try:
            if not self.config.enable_influxdb:
                return
            
            # Calculate retention time
            retention_time = datetime.utcnow() - timedelta(days=self.config.retention_days)
            
            # Delete old data
            delete_api = self.influxdb.delete_api()
            delete_api.delete(
                retention_time,
                f'_measurement=*',
                bucket=self.config.influxdb_bucket,
                org=self.config.influxdb_org
            )
            
        except Exception as e:
            print(f"Error cleaning up old metrics: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Create metrics instance
    metrics = DataMetrics()
    
    # Get metrics summary
    summary = metrics.get_metrics_summary()
    print(f"Metrics summary: {summary}")
    
    # Check alerts
    alerts = metrics.check_alerts()
    print(f"Alerts: {alerts}")
    
    # Clean up old metrics
    metrics.cleanup_old_metrics() 