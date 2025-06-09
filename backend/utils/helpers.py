import re
import json
import hashlib
import uuid
import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import logging
import pytz
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from dateutil import parser
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import base64
import secrets
import string

class ValidationError(Exception):
    """Custom validation error."""
    pass

class DataFormatter:
    """Data formatting and validation utilities."""
    
    @staticmethod
    def format_currency(amount: float, currency: str = 'USD') -> str:
        """Format amount as currency string.
        
        Args:
            amount: Amount to format
            currency: Currency code
            
        Returns:
            Formatted currency string
        """
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥'
        }
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"
        
    @staticmethod
    def format_phone_number(phone: str, region: str = 'US') -> str:
        """Format phone number to international format.
        
        Args:
            phone: Phone number to format
            region: Region code
            
        Returns:
            Formatted phone number
        """
        try:
            number = phonenumbers.parse(phone, region)
            return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception as e:
            logging.error(f"Error formatting phone number: {str(e)}")
            return phone
            
    @staticmethod
    def format_date(date: Union[str, datetime.datetime], format: str = '%Y-%m-%d') -> str:
        """Format date string.
        
        Args:
            date: Date to format
            format: Output format string
            
        Returns:
            Formatted date string
        """
        if isinstance(date, str):
            date = parser.parse(date)
        return date.strftime(format)
        
    @staticmethod
    def format_datetime(dt: Union[str, datetime.datetime], format: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format datetime string.
        
        Args:
            dt: Datetime to format
            format: Output format string
            
        Returns:
            Formatted datetime string
        """
        if isinstance(dt, str):
            dt = parser.parse(dt)
        return dt.strftime(format)

class DataValidator:
    """Data validation utilities."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
            
    @staticmethod
    def validate_phone(phone: str, region: str = 'US') -> bool:
        """Validate phone number.
        
        Args:
            phone: Phone number to validate
            region: Region code
            
        Returns:
            True if valid, False otherwise
        """
        try:
            number = phonenumbers.parse(phone, region)
            return phonenumbers.is_valid_number(number)
        except Exception:
            return False
            
    @staticmethod
    def validate_date(date: str, format: str = '%Y-%m-%d') -> bool:
        """Validate date string.
        
        Args:
            date: Date string to validate
            format: Expected format
            
        Returns:
            True if valid, False otherwise
        """
        try:
            datetime.datetime.strptime(date, format)
            return True
        except ValueError:
            return False
            
    @staticmethod
    def validate_json(data: str) -> bool:
        """Validate JSON string.
        
        Args:
            data: JSON string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            json.loads(data)
            return True
        except json.JSONDecodeError:
            return False

class SecurityHelper:
    """Security-related utilities."""
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """Generate secure random password.
        
        Args:
            length: Password length
            
        Returns:
            Generated password
        """
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
        
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}${hash_obj.hexdigest()}"
        
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Password to verify
            hashed: Hashed password
            
        Returns:
            True if password matches hash
        """
        salt, hash_value = hashed.split('$')
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == hash_value
        
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure random token.
        
        Args:
            length: Token length
            
        Returns:
            Generated token
        """
        return secrets.token_urlsafe(length)

class FileHelper:
    """File handling utilities."""
    
    @staticmethod
    def read_yaml(file_path: str) -> Dict:
        """Read YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Dictionary containing YAML data
        """
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
            
    @staticmethod
    def write_yaml(data: Dict, file_path: str) -> None:
        """Write data to YAML file.
        
        Args:
            data: Data to write
            file_path: Path to YAML file
        """
        with open(file_path, 'w') as f:
            yaml.dump(data, f)
            
    @staticmethod
    def read_json(file_path: str) -> Dict:
        """Read JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary containing JSON data
        """
        with open(file_path, 'r') as f:
            return json.load(f)
            
    @staticmethod
    def write_json(data: Dict, file_path: str) -> None:
        """Write data to JSON file.
        
        Args:
            data: Data to write
            file_path: Path to JSON file
        """
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

class TimeHelper:
    """Time-related utilities."""
    
    @staticmethod
    def get_current_time(timezone: str = 'UTC') -> datetime.datetime:
        """Get current time in specified timezone.
        
        Args:
            timezone: Timezone name
            
        Returns:
            Current datetime
        """
        return datetime.datetime.now(pytz.timezone(timezone))
        
    @staticmethod
    def convert_timezone(dt: datetime.datetime, from_tz: str, to_tz: str) -> datetime.datetime:
        """Convert datetime between timezones.
        
        Args:
            dt: Datetime to convert
            from_tz: Source timezone
            to_tz: Target timezone
            
        Returns:
            Converted datetime
        """
        from_zone = pytz.timezone(from_tz)
        to_zone = pytz.timezone(to_tz)
        return dt.astimezone(from_zone).astimezone(to_zone)
        
    @staticmethod
    def format_timedelta(td: datetime.timedelta) -> str:
        """Format timedelta as human-readable string.
        
        Args:
            td: Timedelta to format
            
        Returns:
            Formatted string
        """
        total_seconds = int(td.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
            
        return " ".join(parts)

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator for functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator

def memoize(func: Callable) -> Callable:
    """Memoization decorator for functions.
    
    Args:
        func: Function to memoize
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper

# Example usage
if __name__ == "__main__":
    # Test data formatting
    formatter = DataFormatter()
    print(formatter.format_currency(1234.56))
    print(formatter.format_phone_number("1234567890"))
    print(formatter.format_date("2024-01-01"))
    
    # Test validation
    validator = DataValidator()
    print(validator.validate_email("test@example.com"))
    print(validator.validate_phone("1234567890"))
    print(validator.validate_date("2024-01-01"))
    
    # Test security
    security = SecurityHelper()
    password = security.generate_password()
    hashed = security.hash_password(password)
    print(security.verify_password(password, hashed))
    
    # Test time utilities
    time_helper = TimeHelper()
    print(time_helper.get_current_time())
    print(time_helper.format_timedelta(datetime.timedelta(days=1, hours=2, minutes=3))) 