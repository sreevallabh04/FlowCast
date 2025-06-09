import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import yaml
import json
import os
from dataclasses import dataclass
from pathlib import Path
import logging
import dotenv
from dotenv import load_dotenv
import configparser
import argparse
import sys
import shutil
import hashlib
import time

@dataclass
class DataConfig:
    """Configuration for the data system."""
    # Database configuration
    database_url: str
    database_pool_size: int
    database_max_overflow: int
    database_pool_timeout: int
    
    # Data processing configuration
    batch_size: int
    max_workers: int
    chunk_size: int
    timeout: int
    
    # Storage configuration
    data_dir: str
    backup_dir: str
    temp_dir: str
    cache_dir: str
    
    # Security configuration
    encryption_key: str
    jwt_secret: str
    api_key: str
    
    # Monitoring configuration
    metrics_port: int
    log_level: str
    alert_threshold: float
    
    # Feature flags
    enable_cache: bool
    enable_compression: bool
    enable_encryption: bool
    enable_validation: bool

class ConfigManager:
    def __init__(self, config_dir: str = 'config'):
        """Initialize the configuration manager."""
        self.config_dir = config_dir
        self.config = None
        self.env = {}
        self.secrets = {}
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Load configuration
        self._load_config()
        
        # Load environment variables
        self._load_env()
        
        # Load secrets
        self._load_secrets()

    def _load_config(self) -> None:
        """Load configuration from YAML files."""
        try:
            # Load main config
            with open(os.path.join(self.config_dir, 'config.yaml'), 'r') as f:
                config_dict = yaml.safe_load(f)
            
            # Load environment-specific config
            env = os.getenv('ENVIRONMENT', 'development')
            env_config_path = os.path.join(self.config_dir, f'config.{env}.yaml')
            
            if os.path.exists(env_config_path):
                with open(env_config_path, 'r') as f:
                    env_config = yaml.safe_load(f)
                    config_dict.update(env_config)
            
            # Create config object
            self.config = DataConfig(**config_dict)
            
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            raise

    def _load_env(self) -> None:
        """Load environment variables."""
        try:
            # Load .env file
            load_dotenv()
            
            # Store environment variables
            self.env = dict(os.environ)
            
        except Exception as e:
            print(f"Error loading environment variables: {str(e)}")
            raise

    def _load_secrets(self) -> None:
        """Load secrets from secure storage."""
        try:
            # Load secrets from file
            secrets_path = os.path.join(self.config_dir, 'secrets.yaml')
            
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    self.secrets = yaml.safe_load(f)
            
        except Exception as e:
            print(f"Error loading secrets: {str(e)}")
            raise

    def get_config(self) -> DataConfig:
        """Get the current configuration."""
        return self.config

    def get_env(self, key: str, default: Any = None) -> Any:
        """Get an environment variable."""
        return self.env.get(key, default)

    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get a secret value."""
        return self.secrets.get(key, default)

    def update_config(self, updates: Dict) -> None:
        """Update configuration values."""
        try:
            # Update config dictionary
            config_dict = self.config.__dict__
            config_dict.update(updates)
            
            # Create new config object
            self.config = DataConfig(**config_dict)
            
            # Save to file
            self._save_config()
            
        except Exception as e:
            print(f"Error updating configuration: {str(e)}")
            raise

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Convert config to dictionary
            config_dict = self.config.__dict__
            
            # Save to file
            with open(os.path.join(self.config_dir, 'config.yaml'), 'w') as f:
                yaml.dump(config_dict, f)
            
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
            raise

    def validate_config(self) -> bool:
        """Validate the current configuration."""
        try:
            # Check required fields
            required_fields = [
                'database_url',
                'data_dir',
                'encryption_key',
                'jwt_secret'
            ]
            
            for field in required_fields:
                if not getattr(self.config, field):
                    return False
            
            # Check directory permissions
            directories = [
                self.config.data_dir,
                self.config.backup_dir,
                self.config.temp_dir,
                self.config.cache_dir
            ]
            
            for directory in directories:
                if not os.access(directory, os.W_OK):
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating configuration: {str(e)}")
            return False

    def backup_config(self) -> None:
        """Create a backup of the current configuration."""
        try:
            # Create backup directory
            backup_dir = os.path.join(self.config_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'config_{timestamp}.yaml')
            
            shutil.copy2(
                os.path.join(self.config_dir, 'config.yaml'),
                backup_path
            )
            
        except Exception as e:
            print(f"Error backing up configuration: {str(e)}")
            raise

    def restore_config(self, backup_name: str) -> None:
        """Restore configuration from backup."""
        try:
            # Get backup path
            backup_path = os.path.join(self.config_dir, 'backups', backup_name)
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup {backup_name} not found")
            
            # Restore backup
            shutil.copy2(
                backup_path,
                os.path.join(self.config_dir, 'config.yaml')
            )
            
            # Reload configuration
            self._load_config()
            
        except Exception as e:
            print(f"Error restoring configuration: {str(e)}")
            raise

    def get_config_hash(self) -> str:
        """Get a hash of the current configuration."""
        try:
            # Convert config to string
            config_str = json.dumps(self.config.__dict__, sort_keys=True)
            
            # Calculate hash
            return hashlib.sha256(config_str.encode()).hexdigest()
            
        except Exception as e:
            print(f"Error calculating config hash: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Create config manager
    config_manager = ConfigManager()
    
    # Get configuration
    config = config_manager.get_config()
    print(f"Database URL: {config.database_url}")
    
    # Update configuration
    config_manager.update_config({
        'batch_size': 1000,
        'max_workers': 4
    })
    
    # Validate configuration
    if config_manager.validate_config():
        print("Configuration is valid")
    else:
        print("Configuration is invalid") 