import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, asdict
from logging.handlers import RotatingFileHandler

@dataclass
class LogConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_dir: str = "logs"
    app_log_file: str = "app.log"
    error_log_file: str = "error.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console: bool = True
    json_format: bool = False
    include_traceback: bool = True
    include_extra: bool = True

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, include_traceback: bool = True, include_extra: bool = True):
        """Initialize JSON formatter.
        
        Args:
            include_traceback: Whether to include traceback in JSON output
            include_extra: Whether to include extra fields in JSON output
        """
        super().__init__()
        self.include_traceback = include_traceback
        self.include_extra = include_extra
        
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if self.include_extra and hasattr(record, "extra"):
            log_data.update(record.extra)
            
        if self.include_traceback and record.exc_info:
            log_data["traceback"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

class Logger:
    """Application logger with file and console handlers."""
    
    def __init__(self):
        self.logger = logging.getLogger('flowcast')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # File handler for all logs
        file_handler = RotatingFileHandler(
            'logs/flowcast.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        
        # File handler for errors
        error_handler = RotatingFileHandler(
            'logs/error.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters and add them to the handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def critical(self, message):
        self.logger.critical(message)

# Example usage
if __name__ == "__main__":
    # Create logger with default configuration
    logger = Logger()
    
    # Get logger instance
    app_logger = logger.logger
    
    # Log some messages
    app_logger.debug("Debug message")
    app_logger.info("Info message")
    app_logger.warning("Warning message")
    app_logger.error("Error message")
    
    # Log with extra fields
    app_logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
    
    # Log exception
    try:
        1/0
    except Exception as e:
        app_logger.exception("Division by zero")
        
    # Clean up old logs
    logger.cleanup_old_logs() 