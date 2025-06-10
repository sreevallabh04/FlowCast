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
import jwt
import bcrypt
from datetime import timedelta
import os
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity

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
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET')
        self.algorithm = 'HS256'
        self.token_expiry = timedelta(days=1)
    
    def hash_password(self, password):
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password, hashed):
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def generate_token(self, user_id):
        """Generate a JWT token for a user."""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + self.token_expiry
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token):
        """Verify a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def token_required(self, f):
        """Decorator to require a valid JWT token."""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            try:
                token = token.split(' ')[1]  # Remove 'Bearer ' prefix
                user_id = self.verify_token(token)
                
                if not user_id:
                    return jsonify({'error': 'Invalid token'}), 401
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 401
        
        return decorated
    
    def admin_required(self, f):
        """Decorator to require admin privileges."""
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = get_jwt_identity()
            
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user is admin
            # This is a placeholder - implement your admin check logic here
            is_admin = True  # Replace with actual admin check
            
            if not is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403
            
            return f(*args, **kwargs)
        
        return decorated

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