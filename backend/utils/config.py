import os
from dotenv import load_dotenv

load_dotenv()

class Config:
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