import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, asdict

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
    
    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize logger.
        
        Args:
            config: Logging configuration
        """
        self.config = config or LogConfig()
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Create log directory if it doesn't exist
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.level)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Add file handlers
        self._add_file_handlers(root_logger)
        
        # Add console handler if enabled
        if self.config.console:
            self._add_console_handler(root_logger)
            
    def _add_file_handlers(self, logger: logging.Logger) -> None:
        """Add file handlers to logger.
        
        Args:
            logger: Logger to add handlers to
        """
        # Application log handler
        app_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.config.log_dir, self.config.app_log_file),
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count
        )
        app_handler.setLevel(self.config.level)
        
        # Error log handler
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.config.log_dir, self.config.error_log_file),
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        
        # Set formatters
        if self.config.json_format:
            formatter = JSONFormatter(
                include_traceback=self.config.include_traceback,
                include_extra=self.config.include_extra
            )
        else:
            formatter = logging.Formatter(
                self.config.format,
                datefmt=self.config.date_format
            )
            
        app_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        logger.addHandler(app_handler)
        logger.addHandler(error_handler)
        
    def _add_console_handler(self, logger: logging.Logger) -> None:
        """Add console handler to logger.
        
        Args:
            logger: Logger to add handler to
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.config.level)
        
        if self.config.json_format:
            formatter = JSONFormatter(
                include_traceback=self.config.include_traceback,
                include_extra=self.config.include_extra
            )
        else:
            formatter = logging.Formatter(
                self.config.format,
                datefmt=self.config.date_format
            )
            
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger instance.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
        
    def set_level(self, level: Union[str, int]) -> None:
        """Set logging level.
        
        Args:
            level: Logging level (string or int)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())
            
        logging.getLogger().setLevel(level)
        
    def update_config(self, config: LogConfig) -> None:
        """Update logging configuration.
        
        Args:
            config: New logging configuration
        """
        self.config = config
        self._setup_logging()
        
    def get_config(self) -> Dict[str, Any]:
        """Get current logging configuration.
        
        Returns:
            Configuration as dictionary
        """
        return asdict(self.config)
        
    def cleanup_old_logs(self) -> None:
        """Clean up old log files."""
        log_dir = Path(self.config.log_dir)
        if not log_dir.exists():
            return
            
        # Get all log files
        log_files = list(log_dir.glob("*.log*"))
        
        # Sort by modification time
        log_files.sort(key=lambda x: x.stat().st_mtime)
        
        # Remove excess backup files
        while len(log_files) > self.config.backup_count:
            try:
                log_files[0].unlink()
                log_files.pop(0)
            except Exception as e:
                logging.error(f"Error cleaning up log file {log_files[0]}: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Create logger with default configuration
    logger = Logger()
    
    # Get logger instance
    app_logger = logger.get_logger("app")
    
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