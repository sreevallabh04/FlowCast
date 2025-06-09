import os
import yaml
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from dotenv import load_dotenv

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False

@dataclass
class MLConfig:
    """Machine learning model configuration."""
    model_dir: str
    batch_size: int
    epochs: int
    learning_rate: float
    validation_split: float
    early_stopping_patience: int
    model_checkpoint: bool = True
    tensorboard_logs: bool = True

@dataclass
class APIConfig:
    """API configuration settings."""
    host: str
    port: int
    debug: bool
    workers: int
    timeout: int
    cors_origins: list
    rate_limit: int
    jwt_secret: str
    jwt_expiry: int

@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str
    format: str
    file: str
    max_size: int
    backup_count: int
    console: bool = True

@dataclass
class CacheConfig:
    """Cache configuration settings."""
    type: str
    host: str
    port: int
    password: str
    db: int
    ttl: int
    max_size: int

@dataclass
class StorageConfig:
    """Storage configuration settings."""
    type: str
    bucket: str
    region: str
    access_key: str
    secret_key: str
    endpoint: Optional[str] = None

@dataclass
class AppConfig:
    """Main application configuration."""
    env: str
    debug: bool
    secret_key: str
    database: DatabaseConfig
    ml: MLConfig
    api: APIConfig
    logging: LoggingConfig
    cache: CacheConfig
    storage: StorageConfig

class ConfigManager:
    """Configuration manager for loading and accessing application settings."""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to the main configuration file
        """
        self.config_path = config_path
        self.config: Optional[AppConfig] = None
        self._load_environment()
        self._load_config()
        
    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(env_path)
            
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            
            # Override with environment variables if present
            config_dict = self._override_from_env(config_dict)
            
            # Create configuration objects
            self.config = AppConfig(
                env=config_dict['env'],
                debug=config_dict['debug'],
                secret_key=config_dict['secret_key'],
                database=DatabaseConfig(**config_dict['database']),
                ml=MLConfig(**config_dict['ml']),
                api=APIConfig(**config_dict['api']),
                logging=LoggingConfig(**config_dict['logging']),
                cache=CacheConfig(**config_dict['cache']),
                storage=StorageConfig(**config_dict['storage'])
            )
            
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            raise
            
    def _override_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration values with environment variables.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Updated configuration dictionary
        """
        env_mappings = {
            'DB_HOST': ('database', 'host'),
            'DB_PORT': ('database', 'port'),
            'DB_NAME': ('database', 'database'),
            'DB_USER': ('database', 'user'),
            'DB_PASSWORD': ('database', 'password'),
            'API_HOST': ('api', 'host'),
            'API_PORT': ('api', 'port'),
            'API_DEBUG': ('api', 'debug'),
            'JWT_SECRET': ('api', 'jwt_secret'),
            'STORAGE_ACCESS_KEY': ('storage', 'access_key'),
            'STORAGE_SECRET_KEY': ('storage', 'secret_key'),
            'CACHE_HOST': ('cache', 'host'),
            'CACHE_PORT': ('cache', 'port'),
            'CACHE_PASSWORD': ('cache', 'password'),
        }
        
        for env_var, config_path in env_mappings.items():
            if env_var in os.environ:
                current = config
                for key in config_path[:-1]:
                    current = current[key]
                current[config_path[-1]] = os.environ[env_var]
                
        return config
    
    def get_config(self) -> AppConfig:
        """Get the current configuration.
        
        Returns:
            AppConfig object containing all settings
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config
    
    def reload(self) -> None:
        """Reload configuration from file and environment."""
        self._load_environment()
        self._load_config()
        
    def validate(self) -> bool:
        """Validate the current configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if not self.config:
                return False
                
            # Validate required directories exist
            os.makedirs(self.config.ml.model_dir, exist_ok=True)
            os.makedirs(os.path.dirname(self.config.logging.file), exist_ok=True)
            
            # Validate database connection
            if self.config.database.type == 'postgresql':
                import psycopg2
                conn = psycopg2.connect(
                    host=self.config.database.host,
                    port=self.config.database.port,
                    database=self.config.database.database,
                    user=self.config.database.user,
                    password=self.config.database.password
                )
                conn.close()
                
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation failed: {str(e)}")
            return False
            
    def export(self, format: str = 'yaml') -> str:
        """Export configuration to string format.
        
        Args:
            format: Output format ('yaml' or 'json')
            
        Returns:
            Configuration as string
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded")
            
        config_dict = {
            'env': self.config.env,
            'debug': self.config.debug,
            'secret_key': self.config.secret_key,
            'database': self.config.database.__dict__,
            'ml': self.config.ml.__dict__,
            'api': self.config.api.__dict__,
            'logging': self.config.logging.__dict__,
            'cache': self.config.cache.__dict__,
            'storage': self.config.storage.__dict__
        }
        
        if format == 'yaml':
            return yaml.dump(config_dict)
        elif format == 'json':
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

# Example usage
if __name__ == '__main__':
    config_manager = ConfigManager()
    config = config_manager.get_config()
    print(f"Environment: {config.env}")
    print(f"Database host: {config.database.host}")
    print(f"API port: {config.api.port}")
    print(f"Logging level: {config.logging.level}")

# Server Configuration
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'flowcast')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# API Keys
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
FRED_API_KEY = os.getenv('FRED_API_KEY')

# Model Configuration
DEMAND_MODEL_PATH = os.getenv('DEMAND_MODEL_PATH', 'models/saved/demand_model.pkl')
INVENTORY_MODEL_PATH = os.getenv('INVENTORY_MODEL_PATH', 'models/saved/inventory_model.pkl')
ROUTING_MODEL_PATH = os.getenv('ROUTING_MODEL_PATH', 'models/saved/routing_model.pkl')
EXPIRY_MODEL_PATH = os.getenv('EXPIRY_MODEL_PATH', 'models/saved/expiry_model.pkl')

# Cache Configuration
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))  # 5 minutes

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/flowcast.log')

# Feature Engineering
WEATHER_FEATURES = ['temperature', 'precipitation', 'humidity', 'wind_speed']
ECONOMIC_FEATURES = ['gdp_growth', 'unemployment_rate', 'inflation_rate']
EVENT_FEATURES = ['holidays', 'sports_events', 'concerts', 'festivals']

# Model Parameters
DEMAND_FORECAST_HORIZON = int(os.getenv('DEMAND_FORECAST_HORIZON', 7))
INVENTORY_SAFETY_STOCK_MULTIPLIER = float(os.getenv('INVENTORY_SAFETY_STOCK_MULTIPLIER', 1.5))
ROUTING_TIME_WINDOW = int(os.getenv('ROUTING_TIME_WINDOW', 30))  # minutes

# API Rate Limits
GOOGLE_MAPS_RATE_LIMIT = int(os.getenv('GOOGLE_MAPS_RATE_LIMIT', 1000))  # requests per day
OPENWEATHER_RATE_LIMIT = int(os.getenv('OPENWEATHER_RATE_LIMIT', 1000))  # requests per day
FRED_RATE_LIMIT = int(os.getenv('FRED_RATE_LIMIT', 120))  # requests per minute 