import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import shutil
import tarfile
import gzip
import boto3
from botocore.exceptions import ClientError
import hashlib
import schedule
import time
import threading
from pathlib import Path
import tempfile
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import azure.storage.blob
import google.cloud.storage
import uuid
import queue
import pytz
import psutil
import requests
import paramiko
import ftplib
import smb.SMBConnection
import dropbox
import onedrive
import gdrive
import boxsdk
import pysftp
import b2sdk
import backblaze
import wasabi
import minio
import s3fs
import gcsfs
import adlfs
import azurefs
import ossfs
import swiftfs
import hdfs
import webhdfs
import sftpfs
import ftpfs
import smbfs
import dropboxfs
import onedrivefs
import gdrivefs
import boxfs
import b2fs
import backblazefs
import wasabifs
import miniofs
from models import db, User, Product, Store, Transaction, Weather, Route, Forecast, Log

@dataclass
class BackupConfig:
    """Configuration for the backup system."""
    backup_dir: str
    temp_dir: str
    retention_days: int
    compression: bool
    encryption: bool
    encryption_key: str
    max_backups: int
    backup_interval: int
    storage_type: str
    storage_config: Dict
    enable_cloud: bool
    enable_local: bool
    enable_incremental: bool
    enable_differential: bool
    enable_full: bool
    enable_compression: bool
    enable_encryption: bool
    enable_verification: bool
    enable_notification: bool
    enable_logging: bool
    enable_monitoring: bool
    enable_scheduling: bool
    enable_retention: bool
    enable_cleanup: bool
    enable_restore: bool
    enable_verify: bool
    enable_compress: bool
    enable_encrypt: bool
    enable_upload: bool
    enable_download: bool
    enable_sync: bool
    enable_mirror: bool
    enable_replication: bool
    enable_archiving: bool
    enable_versioning: bool
    enable_snapshotting: bool
    enable_cloning: bool
    enable_migration: bool
    enable_consolidation: bool
    enable_deduplication: bool

class DataBackup:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('flowcast')
        self.backup_dir = 'backups'
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, format='json'):
        """Create a backup of the database."""
        try:
            with self.app.app_context():
                # Generate timestamp
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                backup_file = f'{self.backup_dir}/backup_{timestamp}.{format}'
                
                # Get all data
                data = {
                    'users': self._get_table_data(User),
                    'products': self._get_table_data(Product),
                    'stores': self._get_table_data(Store),
                    'transactions': self._get_table_data(Transaction),
                    'weather': self._get_table_data(Weather),
                    'routes': self._get_table_data(Route),
                    'forecasts': self._get_table_data(Forecast),
                    'logs': self._get_table_data(Log)
                }
                
                # Save data based on format
                if format == 'json':
                    self._save_json(data, backup_file)
                elif format == 'csv':
                    self._save_csv(data, backup_file)
                else:
                    raise ValueError(f'Unsupported backup format: {format}')
                
                self.logger.info(f'Backup created successfully: {backup_file}')
                return backup_file
        except Exception as e:
            self.logger.error(f'Failed to create backup: {str(e)}')
            raise
    
    def restore_backup(self, backup_file):
        """Restore database from backup."""
        try:
            with self.app.app_context():
                # Determine backup format
                format = backup_file.split('.')[-1]
                
                # Load data based on format
                if format == 'json':
                    data = self._load_json(backup_file)
                elif format == 'csv':
                    data = self._load_csv(backup_file)
                else:
                    raise ValueError(f'Unsupported backup format: {format}')
                
                # Restore data
                self._restore_table_data(User, data['users'])
                self._restore_table_data(Product, data['products'])
                self._restore_table_data(Store, data['stores'])
                self._restore_table_data(Transaction, data['transactions'])
                self._restore_table_data(Weather, data['weather'])
                self._restore_table_data(Route, data['routes'])
                self._restore_table_data(Forecast, data['forecasts'])
                self._restore_table_data(Log, data['logs'])
                
                self.logger.info(f'Backup restored successfully: {backup_file}')
        except Exception as e:
            self.logger.error(f'Failed to restore backup: {str(e)}')
            raise
    
    def list_backups(self):
        """List all available backups."""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('backup_') and (file.endswith('.json') or file.endswith('.csv')):
                    file_path = os.path.join(self.backup_dir, file)
                    backups.append({
                        'filename': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'created_at': datetime.fromtimestamp(os.path.getctime(file_path))
                    })
            
            return sorted(backups, key=lambda x: x['created_at'], reverse=True)
        except Exception as e:
            self.logger.error(f'Failed to list backups: {str(e)}')
            raise
    
    def delete_backup(self, backup_file):
        """Delete a backup file."""
        try:
            file_path = os.path.join(self.backup_dir, backup_file)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f'Backup deleted successfully: {backup_file}')
            else:
                raise FileNotFoundError(f'Backup file not found: {backup_file}')
        except Exception as e:
            self.logger.error(f'Failed to delete backup: {str(e)}')
            raise
    
    def _get_table_data(self, model):
        """Get all data from a table."""
        return [self._model_to_dict(record) for record in model.query.all()]
    
    def _model_to_dict(self, model):
        """Convert a model instance to a dictionary."""
        return {
            column.name: getattr(model, column.name)
            for column in model.__table__.columns
        }
    
    def _save_json(self, data, file_path):
        """Save data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, default=str)
    
    def _save_csv(self, data, file_path):
        """Save data to a CSV file."""
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['table', 'data'])
            
            # Write data
            for table, records in data.items():
                for record in records:
                    writer.writerow([table, json.dumps(record, default=str)])
    
    def _load_json(self, file_path):
        """Load data from a JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _load_csv(self, file_path):
        """Load data from a CSV file."""
        data = {
            'users': [],
            'products': [],
            'stores': [],
            'transactions': [],
            'weather': [],
            'routes': [],
            'forecasts': [],
            'logs': []
        }
        
        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
                table, record = row
                data[table].append(json.loads(record))
        
        return data
    
    def _restore_table_data(self, model, data):
        """Restore data to a table."""
        # Clear existing data
        model.query.delete()
        
        # Insert new data
        for record in data:
            instance = model()
            for key, value in record.items():
                setattr(instance, key, value)
            db.session.add(instance)
        
        db.session.commit()
    
    def create_incremental_backup(self, last_backup_time):
        """Create an incremental backup since the last backup."""
        try:
            with self.app.app_context():
                # Generate timestamp
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                backup_file = f'{self.backup_dir}/incremental_backup_{timestamp}.json'
                
                # Get changed data
                data = {
                    'users': self._get_changed_data(User, last_backup_time),
                    'products': self._get_changed_data(Product, last_backup_time),
                    'stores': self._get_changed_data(Store, last_backup_time),
                    'transactions': self._get_changed_data(Transaction, last_backup_time),
                    'weather': self._get_changed_data(Weather, last_backup_time),
                    'routes': self._get_changed_data(Route, last_backup_time),
                    'forecasts': self._get_changed_data(Forecast, last_backup_time),
                    'logs': self._get_changed_data(Log, last_backup_time)
                }
                
                # Save data
                self._save_json(data, backup_file)
                
                self.logger.info(f'Incremental backup created successfully: {backup_file}')
                return backup_file
        except Exception as e:
            self.logger.error(f'Failed to create incremental backup: {str(e)}')
            raise
    
    def _get_changed_data(self, model, since_time):
        """Get data that has changed since the specified time."""
        return [
            self._model_to_dict(record)
            for record in model.query.filter(
                model.updated_at >= since_time
            ).all()
        ]
    
    def compress_backup(self, backup_file):
        """Compress a backup file."""
        try:
            file_path = os.path.join(self.backup_dir, backup_file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f'Backup file not found: {backup_file}')
            
            # Create compressed file
            compressed_file = f'{file_path}.gz'
            with open(file_path, 'rb') as f_in:
                with open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            os.remove(file_path)
            
            self.logger.info(f'Backup compressed successfully: {compressed_file}')
            return compressed_file
        except Exception as e:
            self.logger.error(f'Failed to compress backup: {str(e)}')
            raise
    
    def decompress_backup(self, compressed_file):
        """Decompress a backup file."""
        try:
            file_path = os.path.join(self.backup_dir, compressed_file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f'Compressed file not found: {compressed_file}')
            
            # Create decompressed file
            decompressed_file = file_path[:-3]  # Remove .gz extension
            with open(file_path, 'rb') as f_in:
                with open(decompressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove compressed file
            os.remove(file_path)
            
            self.logger.info(f'Backup decompressed successfully: {decompressed_file}')
            return decompressed_file
        except Exception as e:
            self.logger.error(f'Failed to decompress backup: {str(e)}')
            raise

# Example usage
if __name__ == "__main__":
    # Create backup instance
    backup = DataBackup()
    
    # Create backup
    backup_id = backup.create_backup(
        format='json'
    )
    
    # Get backup stats
    stats = backup.list_backups()
    print(f"Backup stats: {stats}")
    
    # Restore backup
    backup.restore_backup(backup_id)
    
    # Clear backups
    for backup_file in backup.list_backups():
        backup.delete_backup(backup_file['filename']) 