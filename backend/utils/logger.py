import logging
import logging.handlers
import os
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    if log_file is None:
        log_file = f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log'
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create loggers for different components
app_logger = setup_logger('app')
model_logger = setup_logger('model')
api_logger = setup_logger('api')
data_logger = setup_logger('data') 