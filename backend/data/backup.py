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
    def __init__(self, config_path: str = 'config/backup_config.yaml'):
        """Initialize the backup system."""
        self.config_path = config_path
        self.config = self._load_config()
        self.backup_queue = queue.Queue()
        self.processing = False
        self.processing_thread = None
        self.storage_client = None
        
        # Initialize storage
        self._init_storage()
        
        # Start processing
        self.start_processing()

    def _load_config(self) -> BackupConfig:
        """Load backup configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return BackupConfig(**config_dict)
        except Exception as e:
            print(f"Error loading backup configuration: {str(e)}")
            raise

    def _init_storage(self) -> None:
        """Initialize storage client."""
        try:
            if self.config.enable_cloud:
                if self.config.storage_type == 's3':
                    self.storage_client = boto3.client('s3', **self.config.storage_config)
                elif self.config.storage_type == 'azure':
                    self.storage_client = azure.storage.blob.BlobServiceClient(**self.config.storage_config)
                elif self.config.storage_type == 'gcs':
                    self.storage_client = google.cloud.storage.Client(**self.config.storage_config)
                elif self.config.storage_type == 'dropbox':
                    self.storage_client = dropbox.Dropbox(**self.config.storage_config)
                elif self.config.storage_type == 'onedrive':
                    self.storage_client = onedrive.OneDriveClient(**self.config.storage_config)
                elif self.config.storage_type == 'gdrive':
                    self.storage_client = gdrive.GoogleDriveClient(**self.config.storage_config)
                elif self.config.storage_type == 'box':
                    self.storage_client = boxsdk.Client(**self.config.storage_config)
                elif self.config.storage_type == 'b2':
                    self.storage_client = b2sdk.B2Api(**self.config.storage_config)
                elif self.config.storage_type == 'backblaze':
                    self.storage_client = backblaze.BackblazeClient(**self.config.storage_config)
                elif self.config.storage_type == 'wasabi':
                    self.storage_client = wasabi.WasabiClient(**self.config.storage_config)
                elif self.config.storage_type == 'minio':
                    self.storage_client = minio.MinioClient(**self.config.storage_config)
            
        except Exception as e:
            print(f"Error initializing storage client: {str(e)}")
            raise

    def start_processing(self) -> None:
        """Start backup processing."""
        try:
            if not self.processing:
                self.processing = True
                self.processing_thread = threading.Thread(target=self._process_backups)
                self.processing_thread.daemon = True
                self.processing_thread.start()
            
        except Exception as e:
            print(f"Error starting backup processing: {str(e)}")
            raise

    def stop_processing(self) -> None:
        """Stop backup processing."""
        try:
            self.processing = False
            if self.processing_thread:
                self.processing_thread.join()
            
        except Exception as e:
            print(f"Error stopping backup processing: {str(e)}")
            raise

    def _process_backups(self) -> None:
        """Process backups from the queue."""
        try:
            while self.processing:
                try:
                    # Get backup from queue
                    backup = self.backup_queue.get(timeout=1)
                    
                    # Process backup
                    self._create_backup(backup)
                    
                    # Mark task as done
                    self.backup_queue.task_done()
                    
                except queue.Empty:
                    continue
                
        except Exception as e:
            print(f"Error processing backups: {str(e)}")
            raise

    def _create_backup(self, backup: Dict) -> None:
        """Create a backup."""
        try:
            # Get backup type
            backup_type = backup.get('type', 'full')
            
            # Create backup directory
            backup_dir = os.path.join(self.config.backup_dir, backup_type)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup file
            backup_file = os.path.join(backup_dir, f"{backup['id']}.tar.gz")
            
            # Create tar file
            with tarfile.open(backup_file, 'w:gz') as tar:
                # Add files to tar
                for file in backup['files']:
                    tar.add(file)
            
            # Upload to cloud storage if enabled
            if self.config.enable_cloud:
                self._upload_backup(backup_file)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            raise

    def _upload_backup(self, backup_file: str) -> None:
        """Upload backup to cloud storage."""
        try:
            if self.config.storage_type == 's3':
                self.storage_client.upload_file(
                    backup_file,
                    self.config.storage_config['bucket'],
                    os.path.basename(backup_file)
                )
            elif self.config.storage_type == 'azure':
                with open(backup_file, 'rb') as f:
                    self.storage_client.upload_blob(
                        self.config.storage_config['container'],
                        os.path.basename(backup_file),
                        f
                    )
            elif self.config.storage_type == 'gcs':
                bucket = self.storage_client.bucket(self.config.storage_config['bucket'])
                blob = bucket.blob(os.path.basename(backup_file))
                blob.upload_from_filename(backup_file)
            
        except Exception as e:
            print(f"Error uploading backup: {str(e)}")
            raise

    def _cleanup_old_backups(self) -> None:
        """Clean up old backups."""
        try:
            # Get backup directory
            backup_dir = self.config.backup_dir
            
            # Get all backup files
            backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.endswith('.tar.gz'):
                        backup_files.append(os.path.join(root, file))
            
            # Sort by modification time
            backup_files.sort(key=os.path.getmtime)
            
            # Remove old backups
            while len(backup_files) > self.config.max_backups:
                os.remove(backup_files.pop(0))
            
        except Exception as e:
            print(f"Error cleaning up old backups: {str(e)}")
            raise

    def create_backup(self, files: List[str], backup_type: str = 'full') -> str:
        """Create a new backup."""
        try:
            # Generate backup ID
            backup_id = str(uuid.uuid4())
            
            # Create backup
            backup = {
                'id': backup_id,
                'type': backup_type,
                'files': files,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add to queue
            self.backup_queue.put(backup)
            
            return backup_id
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            raise

    def restore_backup(self, backup_id: str, restore_dir: str) -> None:
        """Restore a backup."""
        try:
            # Find backup file
            backup_file = None
            for root, dirs, files in os.walk(self.config.backup_dir):
                for file in files:
                    if file.startswith(backup_id) and file.endswith('.tar.gz'):
                        backup_file = os.path.join(root, file)
                        break
                if backup_file:
                    break
            
            if not backup_file:
                raise FileNotFoundError(f"Backup {backup_id} not found")
            
            # Download from cloud storage if enabled
            if self.config.enable_cloud:
                self._download_backup(backup_file)
            
            # Extract backup
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(restore_dir)
            
        except Exception as e:
            print(f"Error restoring backup: {str(e)}")
            raise

    def _download_backup(self, backup_file: str) -> None:
        """Download backup from cloud storage."""
        try:
            if self.config.storage_type == 's3':
                self.storage_client.download_file(
                    self.config.storage_config['bucket'],
                    os.path.basename(backup_file),
                    backup_file
                )
            elif self.config.storage_type == 'azure':
                with open(backup_file, 'wb') as f:
                    self.storage_client.download_blob(
                        self.config.storage_config['container'],
                        os.path.basename(backup_file),
                        f
                    )
            elif self.config.storage_type == 'gcs':
                bucket = self.storage_client.bucket(self.config.storage_config['bucket'])
                blob = bucket.blob(os.path.basename(backup_file))
                blob.download_to_filename(backup_file)
            
        except Exception as e:
            print(f"Error downloading backup: {str(e)}")
            raise

    def get_backup_stats(self) -> Dict:
        """Get backup statistics."""
        try:
            stats = {
                'queue_size': self.backup_queue.qsize(),
                'processing': self.processing,
                'backup_count': len(self._get_backup_files()),
                'storage_used': self._get_storage_used(),
                'last_backup': self._get_last_backup_time()
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting backup stats: {str(e)}")
            raise

    def _get_backup_files(self) -> List[str]:
        """Get list of backup files."""
        try:
            backup_files = []
            for root, dirs, files in os.walk(self.config.backup_dir):
                for file in files:
                    if file.endswith('.tar.gz'):
                        backup_files.append(os.path.join(root, file))
            return backup_files
            
        except Exception as e:
            print(f"Error getting backup files: {str(e)}")
            raise

    def _get_storage_used(self) -> int:
        """Get total storage used by backups."""
        try:
            total_size = 0
            for backup_file in self._get_backup_files():
                total_size += os.path.getsize(backup_file)
            return total_size
            
        except Exception as e:
            print(f"Error getting storage used: {str(e)}")
            raise

    def _get_last_backup_time(self) -> Optional[str]:
        """Get timestamp of last backup."""
        try:
            backup_files = self._get_backup_files()
            if not backup_files:
                return None
            
            # Sort by modification time
            backup_files.sort(key=os.path.getmtime)
            
            # Get last backup time
            return datetime.fromtimestamp(os.path.getmtime(backup_files[-1])).isoformat()
            
        except Exception as e:
            print(f"Error getting last backup time: {str(e)}")
            raise

    def clear_backups(self) -> None:
        """Clear all backups."""
        try:
            # Clear queue
            while not self.backup_queue.empty():
                self.backup_queue.get()
                self.backup_queue.task_done()
            
            # Remove backup files
            for backup_file in self._get_backup_files():
                os.remove(backup_file)
            
        except Exception as e:
            print(f"Error clearing backups: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Create backup instance
    backup = DataBackup()
    
    # Create backup
    backup_id = backup.create_backup(
        files=['data/sales.csv', 'data/inventory.csv'],
        backup_type='full'
    )
    
    # Get backup stats
    stats = backup.get_backup_stats()
    print(f"Backup stats: {stats}")
    
    # Restore backup
    backup.restore_backup(backup_id, 'restore')
    
    # Clear backups
    backup.clear_backups() 