import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import psutil
import threading
import time
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import requests
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import schedule

@dataclass
class MonitorConfig:
    """Configuration for the data monitor."""
    metrics_port: int
    influxdb_url: str
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str
    alert_thresholds: Dict[str, float]
    check_interval: int
    retention_days: int

class DataMonitor:
    def __init__(self, config_path: str = 'config/monitor_config.yaml'):
        """Initialize the data monitor with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize metrics
        self._init_metrics()
        
        # Initialize InfluxDB client
        self._init_influxdb()
        
        # Initialize monitoring state
        self.is_monitoring = False
        self.last_check = {}
        self.alerts = []
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Start Prometheus metrics server
        start_http_server(self.config.metrics_port)

    def _load_config(self) -> MonitorConfig:
        """Load monitor configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return MonitorConfig(**config_dict)
        except Exception as e:
            self.logger.error(f"Error loading monitor configuration: {str(e)}")
            raise

    def _init_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        # Pipeline metrics
        self.pipeline_duration = Histogram(
            'pipeline_duration_seconds',
            'Time taken by pipeline steps',
            ['step']
        )
        self.pipeline_errors = Counter(
            'pipeline_errors_total',
            'Number of pipeline errors',
            ['step', 'error_type']
        )
        self.pipeline_batch_size = Gauge(
            'pipeline_batch_size',
            'Current batch size being processed'
        )
        
        # Data quality metrics
        self.data_quality_score = Gauge(
            'data_quality_score',
            'Overall data quality score',
            ['dataset']
        )
        self.missing_values = Gauge(
            'missing_values_total',
            'Number of missing values',
            ['dataset', 'column']
        )
        self.outliers = Gauge(
            'outliers_total',
            'Number of outliers',
            ['dataset', 'column']
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )
        self.memory_usage = Gauge(
            'memory_usage_percent',
            'Memory usage percentage'
        )
        self.disk_usage = Gauge(
            'disk_usage_percent',
            'Disk usage percentage'
        )
        self.network_io = Gauge(
            'network_io_bytes',
            'Network I/O in bytes',
            ['direction']
        )

    def _init_influxdb(self) -> None:
        """Initialize InfluxDB client."""
        try:
            self.influx_client = InfluxDBClient(
                url=self.config.influxdb_url,
                token=self.config.influxdb_token,
                org=self.config.influxdb_org
            )
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.influx_client.query_api()
            
        except Exception as e:
            self.logger.error(f"Error initializing InfluxDB client: {str(e)}")
            raise

    def start_monitoring(self) -> None:
        """Start the monitoring system."""
        try:
            self.is_monitoring = True
            self.logger.info("Starting data monitoring")
            
            # Start system metrics collection
            threading.Thread(target=self._collect_system_metrics, daemon=True).start()
            
            # Schedule regular checks
            schedule.every(self.config.check_interval).seconds.do(self._check_data_quality)
            schedule.every(self.config.check_interval).seconds.do(self._check_system_health)
            schedule.every(self.config.check_interval).seconds.do(self._cleanup_old_data)
            
            # Run the scheduler
            while self.is_monitoring:
                schedule.run_pending()
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in monitoring system: {str(e)}")
            raise
        finally:
            self.is_monitoring = False

    def _collect_system_metrics(self) -> None:
        """Collect system metrics."""
        try:
            while self.is_monitoring:
                # CPU usage
                cpu_percent = psutil.cpu_percent()
                self.cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                self.disk_usage.set(disk.percent)
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.network_io.labels('sent').set(net_io.bytes_sent)
                self.network_io.labels('recv').set(net_io.bytes_recv)
                
                # Write to InfluxDB
                point = Point("system_metrics")\
                    .field("cpu_usage", cpu_percent)\
                    .field("memory_usage", memory.percent)\
                    .field("disk_usage", disk.percent)\
                    .field("network_sent", net_io.bytes_sent)\
                    .field("network_recv", net_io.bytes_recv)\
                    .time(datetime.utcnow())
                
                self.write_api.write(bucket=self.config.influxdb_bucket, record=point)
                
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
            raise

    def _check_data_quality(self) -> None:
        """Check data quality metrics."""
        try:
            # Load latest data
            data_dir = 'data/processed'
            for dataset in ['sales', 'inventory', 'delivery']:
                file_path = f'{data_dir}/{dataset}_processed.csv'
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    
                    # Calculate quality metrics
                    missing_count = df.isnull().sum()
                    for col in df.columns:
                        self.missing_values.labels(dataset, col).set(missing_count[col])
                    
                    # Calculate outliers using IQR method
                    for col in df.select_dtypes(include=[np.number]).columns:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
                        self.outliers.labels(dataset, col).set(len(outliers))
                    
                    # Calculate overall quality score
                    quality_score = 1 - (missing_count.sum() / (df.shape[0] * df.shape[1]))
                    self.data_quality_score.labels(dataset).set(quality_score)
                    
                    # Write to InfluxDB
                    point = Point("data_quality")\
                        .tag("dataset", dataset)\
                        .field("quality_score", quality_score)\
                        .field("missing_values", missing_count.sum())\
                        .field("outliers", len(outliers))\
                        .time(datetime.utcnow())
                    
                    self.write_api.write(bucket=self.config.influxdb_bucket, record=point)
                    
                    # Check thresholds and generate alerts
                    self._check_quality_thresholds(dataset, quality_score)
            
        except Exception as e:
            self.logger.error(f"Error checking data quality: {str(e)}")
            raise

    def _check_system_health(self) -> None:
        """Check system health metrics."""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > self.config.alert_thresholds['cpu']:
                self._generate_alert('system', 'high_cpu', cpu_percent)
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.config.alert_thresholds['memory']:
                self._generate_alert('system', 'high_memory', memory.percent)
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > self.config.alert_thresholds['disk']:
                self._generate_alert('system', 'high_disk', disk.percent)
            
            # Check network connectivity
            try:
                requests.get('https://www.google.com', timeout=5)
            except requests.RequestException:
                self._generate_alert('system', 'network_error', None)
            
        except Exception as e:
            self.logger.error(f"Error checking system health: {str(e)}")
            raise

    def _check_quality_thresholds(self, dataset: str, quality_score: float) -> None:
        """Check data quality thresholds and generate alerts."""
        if quality_score < self.config.alert_thresholds['data_quality']:
            self._generate_alert('data', 'low_quality', quality_score, dataset)

    def _generate_alert(self, category: str, alert_type: str, value: Optional[float], dataset: Optional[str] = None) -> None:
        """Generate an alert."""
        alert = {
            'timestamp': datetime.utcnow(),
            'category': category,
            'type': alert_type,
            'value': value,
            'dataset': dataset
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"Alert generated: {alert}")
        
        # Write to InfluxDB
        point = Point("alerts")\
            .tag("category", category)\
            .tag("type", alert_type)\
            .field("value", value if value is not None else 0)\
            .time(alert['timestamp'])
        
        if dataset:
            point = point.tag("dataset", dataset)
        
        self.write_api.write(bucket=self.config.influxdb_bucket, record=point)

    def _cleanup_old_data(self) -> None:
        """Clean up old monitoring data."""
        try:
            # Calculate cutoff time
            cutoff = datetime.utcnow() - timedelta(days=self.config.retention_days)
            
            # Delete old data from InfluxDB
            delete_api = self.influx_client.delete_api()
            delete_api.delete(
                cutoff,
                f'_measurement="system_metrics" OR _measurement="data_quality" OR _measurement="alerts"',
                bucket=self.config.influxdb_bucket
            )
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            raise

    def generate_dashboard(self, output_path: str = 'monitoring/dashboard.html') -> None:
        """Generate an interactive monitoring dashboard."""
        try:
            # Create subplots
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'System Metrics', 'Data Quality',
                    'Pipeline Performance', 'Alerts',
                    'Network I/O', 'Resource Usage'
                )
            )
            
            # Query data from InfluxDB
            query = f'''
                from(bucket: "{self.config.influxdb_bucket}")
                    |> range(start: -24h)
                    |> filter(fn: (r) => r._measurement == "system_metrics")
            '''
            result = self.query_api.query(query)
            
            # Add system metrics
            for table in result:
                for record in table.records:
                    fig.add_trace(
                        go.Scatter(
                            x=[record.get_time()],
                            y=[record.get_value()],
                            name=record.get_field()
                        ),
                        row=1, col=1
                    )
            
            # Add data quality metrics
            query = f'''
                from(bucket: "{self.config.influxdb_bucket}")
                    |> range(start: -24h)
                    |> filter(fn: (r) => r._measurement == "data_quality")
            '''
            result = self.query_api.query(query)
            
            for table in result:
                for record in table.records:
                    fig.add_trace(
                        go.Scatter(
                            x=[record.get_time()],
                            y=[record.get_value()],
                            name=f"{record.get_field()} - {record.get_tag('dataset')}"
                        ),
                        row=1, col=2
                    )
            
            # Add alerts
            query = f'''
                from(bucket: "{self.config.influxdb_bucket}")
                    |> range(start: -24h)
                    |> filter(fn: (r) => r._measurement == "alerts")
            '''
            result = self.query_api.query(query)
            
            for table in result:
                for record in table.records:
                    fig.add_trace(
                        go.Scatter(
                            x=[record.get_time()],
                            y=[record.get_value()],
                            name=f"{record.get_tag('type')} - {record.get_tag('category')}"
                        ),
                        row=2, col=2
                    )
            
            # Update layout
            fig.update_layout(
                title='FlowCast Monitoring Dashboard',
                height=1200,
                showlegend=True
            )
            
            # Save dashboard
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.write_html(output_path)
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard: {str(e)}")
            raise

    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status."""
        return {
            'is_monitoring': self.is_monitoring,
            'last_check': self.last_check,
            'active_alerts': len(self.alerts),
            'metrics_port': self.config.metrics_port
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start monitor
    monitor = DataMonitor()
    monitor.start_monitoring() 