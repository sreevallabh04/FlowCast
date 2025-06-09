import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import os
import csv
import xlsxwriter
from sqlalchemy import create_engine, text
import boto3
from google.cloud import bigquery
import requests
import yaml
import xml.etree.ElementTree as ET
from dataclasses import dataclass
import hashlib
import hmac
import base64
import time

@dataclass
class ExportConfig:
    """Configuration for data export."""
    format: str
    destination: str
    credentials: Optional[Dict] = None
    options: Optional[Dict] = None

class DataExporter:
    def __init__(self, data_dir: str = 'data/processed', output_dir: str = 'data/export'):
        """Initialize the data exporter with input and output directories."""
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize data storage
        self.sales_data = None
        self.inventory_data = None
        self.delivery_data = None
        
        # Initialize export configurations
        self.export_configs = {}
        
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def load_data(self) -> None:
        """Load processed data from CSV files."""
        try:
            # Load time-series data
            self.sales_data = pd.read_csv(f'{self.data_dir}/sales_processed.csv')
            self.inventory_data = pd.read_csv(f'{self.data_dir}/inventory_processed.csv')
            self.delivery_data = pd.read_csv(f'{self.data_dir}/deliveries_processed.csv')
            
            # Convert date columns to datetime
            for df in [self.sales_data, self.inventory_data, self.delivery_data]:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            
            self.logger.info("All data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def load_export_config(self, config_path: str) -> None:
        """Load export configurations from a YAML file."""
        try:
            with open(config_path, 'r') as f:
                configs = yaml.safe_load(f)
            
            for name, config in configs.items():
                self.export_configs[name] = ExportConfig(**config)
            
            self.logger.info("Export configurations loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading export configurations: {str(e)}")
            raise

    def export_data(self, data_name: str, config_name: str) -> None:
        """Export data using the specified configuration."""
        try:
            if config_name not in self.export_configs:
                raise ValueError(f"Export configuration '{config_name}' not found")
            
            config = self.export_configs[config_name]
            data = getattr(self, f"{data_name}_data")
            
            if data is None:
                raise ValueError(f"Data '{data_name}' not found")
            
            # Export based on format
            if config.format == 'csv':
                self._export_csv(data, config)
            elif config.format == 'excel':
                self._export_excel(data, config)
            elif config.format == 'json':
                self._export_json(data, config)
            elif config.format == 'xml':
                self._export_xml(data, config)
            elif config.format == 'sql':
                self._export_sql(data, config)
            elif config.format == 'bigquery':
                self._export_bigquery(data, config)
            elif config.format == 's3':
                self._export_s3(data, config)
            elif config.format == 'api':
                self._export_api(data, config)
            else:
                raise ValueError(f"Unsupported export format: {config.format}")
            
            self.logger.info(f"Data '{data_name}' exported successfully using configuration '{config_name}'")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
            raise

    def _export_csv(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data to CSV format."""
        try:
            output_path = os.path.join(self.output_dir, f"{config.destination}.csv")
            data.to_csv(output_path, index=False)
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    def _export_excel(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data to Excel format."""
        try:
            output_path = os.path.join(self.output_dir, f"{config.destination}.xlsx")
            
            # Create Excel writer
            writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
            
            # Write data
            data.to_excel(writer, sheet_name='Data', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Data']
            
            # Add formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Write header with formatting
            for col_num, value in enumerate(data.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Save the file
            writer.close()
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {str(e)}")
            raise

    def _export_json(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data to JSON format."""
        try:
            output_path = os.path.join(self.output_dir, f"{config.destination}.json")
            
            # Convert DataFrame to JSON
            json_data = data.to_dict(orient='records')
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {str(e)}")
            raise

    def _export_xml(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data to XML format."""
        try:
            output_path = os.path.join(self.output_dir, f"{config.destination}.xml")
            
            # Create root element
            root = ET.Element("data")
            
            # Add records
            for _, row in data.iterrows():
                record = ET.SubElement(root, "record")
                for col in data.columns:
                    field = ET.SubElement(record, col)
                    field.text = str(row[col])
            
            # Create tree and write to file
            tree = ET.ElementTree(root)
            tree.write(output_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting to XML: {str(e)}")
            raise

    def _export_sql(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data to SQL database."""
        try:
            # Create database engine
            engine = create_engine(config.destination)
            
            # Export data
            data.to_sql(
                config.options.get('table_name', 'data'),
                engine,
                if_exists=config.options.get('if_exists', 'replace'),
                index=False
            )
            
        except Exception as e:
            self.logger.error(f"Error exporting to SQL: {str(e)}")
            raise

    def _export_bigquery(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data to BigQuery."""
        try:
            # Initialize BigQuery client
            client = bigquery.Client(credentials=config.credentials)
            
            # Define table reference
            table_ref = client.dataset(config.options['dataset']).table(config.options['table'])
            
            # Export data
            job_config = bigquery.LoadJobConfig(
                write_disposition=config.options.get('write_disposition', 'WRITE_TRUNCATE')
            )
            
            job = client.load_table_from_dataframe(
                data,
                table_ref,
                job_config=job_config
            )
            job.result()
            
        except Exception as e:
            self.logger.error(f"Error exporting to BigQuery: {str(e)}")
            raise

    def _export_s3(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data to S3."""
        try:
            # Initialize S3 client
            s3 = boto3.client(
                's3',
                aws_access_key_id=config.credentials['access_key'],
                aws_secret_access_key=config.credentials['secret_key']
            )
            
            # Convert DataFrame to CSV
            csv_buffer = data.to_csv(index=False)
            
            # Upload to S3
            s3.put_object(
                Bucket=config.options['bucket'],
                Key=config.options['key'],
                Body=csv_buffer
            )
            
        except Exception as e:
            self.logger.error(f"Error exporting to S3: {str(e)}")
            raise

    def _export_api(self, data: pd.DataFrame, config: ExportConfig) -> None:
        """Export data via API."""
        try:
            # Convert DataFrame to JSON
            json_data = data.to_dict(orient='records')
            
            # Generate signature if required
            headers = {}
            if config.credentials.get('api_key') and config.credentials.get('api_secret'):
                timestamp = str(int(time.time()))
                signature = self._generate_api_signature(
                    config.credentials['api_secret'],
                    timestamp,
                    json_data
                )
                headers = {
                    'X-API-Key': config.credentials['api_key'],
                    'X-Timestamp': timestamp,
                    'X-Signature': signature
                }
            
            # Send data to API
            response = requests.post(
                config.destination,
                json=json_data,
                headers=headers
            )
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Error exporting via API: {str(e)}")
            raise

    def _generate_api_signature(self, secret: str, timestamp: str, data: List[Dict]) -> str:
        """Generate API signature for authentication."""
        # Convert data to string
        data_str = json.dumps(data, sort_keys=True)
        
        # Create message
        message = f"{timestamp}{data_str}"
        
        # Generate signature
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        # Return base64 encoded signature
        return base64.b64encode(signature).decode()

    def export_all(self) -> None:
        """Export all data using all configurations."""
        try:
            for data_name in ['sales', 'inventory', 'delivery']:
                for config_name in self.export_configs:
                    self.export_data(data_name, config_name)
            
            self.logger.info("All data exported successfully")
            
        except Exception as e:
            self.logger.error(f"Error exporting all data: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create data exporter
    exporter = DataExporter()
    
    # Load data and configurations
    exporter.load_data()
    exporter.load_export_config('config/export_config.yaml')
    
    # Export all data
    exporter.export_all() 