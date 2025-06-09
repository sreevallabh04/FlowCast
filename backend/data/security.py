import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import jwt
from passlib.context import CryptContext
import bcrypt
import secrets
import string
import re
from functools import wraps
import time
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

@dataclass
class SecurityConfig:
    """Configuration for the security system."""
    secret_key: str
    encryption_key: str
    token_expire_minutes: int
    password_min_length: int
    password_requirements: Dict[str, bool]
    max_login_attempts: int
    lockout_duration: int
    session_timeout: int
    audit_log_path: str
    backup_encryption: bool
    data_masking: bool
    ssl_required: bool

class DataSecurity:
    def __init__(self, config_path: str = 'config/security_config.yaml'):
        """Initialize the security system with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize security state
        self.is_encrypting = False
        self.security_status = {}
        
        # Set up database connection
        self.engine = create_engine(self.config.database_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self._initialize_encryption()
        
        # Initialize password hashing
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto"
        )

    def _load_config(self) -> SecurityConfig:
        """Load security configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return SecurityConfig(**config_dict)
        except Exception as e:
            self.logger.error(f"Error loading security configuration: {str(e)}")
            raise

    def _initialize_encryption(self) -> None:
        """Initialize encryption keys and ciphers."""
        try:
            # Generate encryption key
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.config.encryption_key.encode()))
            
            # Initialize Fernet cipher
            self.cipher = Fernet(key)
            
            # Generate RSA key pair
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            self.public_key = self.private_key.public_key()
            
        except Exception as e:
            self.logger.error(f"Error initializing encryption: {str(e)}")
            raise

    def encrypt_data(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data using Fernet symmetric encryption."""
        try:
            if isinstance(data, str):
                data = data.encode()
            return self.cipher.encrypt(data)
        except Exception as e:
            self.logger.error(f"Error encrypting data: {str(e)}")
            raise

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using Fernet symmetric encryption."""
        try:
            return self.cipher.decrypt(encrypted_data)
        except Exception as e:
            self.logger.error(f"Error decrypting data: {str(e)}")
            raise

    def encrypt_asymmetric(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data using RSA asymmetric encryption."""
        try:
            if isinstance(data, str):
                data = data.encode()
            return self.public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except Exception as e:
            self.logger.error(f"Error encrypting data asymmetrically: {str(e)}")
            raise

    def decrypt_asymmetric(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using RSA asymmetric encryption."""
        try:
            return self.private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except Exception as e:
            self.logger.error(f"Error decrypting data asymmetrically: {str(e)}")
            raise

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            self.logger.error(f"Error hashing password: {str(e)}")
            raise

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            return self.pwd_context.verify(password, hashed_password)
        except Exception as e:
            self.logger.error(f"Error verifying password: {str(e)}")
            raise

    def generate_token(self, data: Dict) -> str:
        """Generate JWT token."""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(minutes=self.config.token_expire_minutes)
            to_encode.update({"exp": expire})
            return jwt.encode(
                to_encode,
                self.config.secret_key,
                algorithm="HS256"
            )
        except Exception as e:
            self.logger.error(f"Error generating token: {str(e)}")
            raise

    def verify_token(self, token: str) -> Dict:
        """Verify JWT token."""
        try:
            return jwt.decode(
                token,
                self.config.secret_key,
                algorithms=["HS256"]
            )
        except Exception as e:
            self.logger.error(f"Error verifying token: {str(e)}")
            raise

    def generate_secure_password(self) -> str:
        """Generate secure password."""
        try:
            # Define character sets
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase
            digits = string.digits
            special = string.punctuation
            
            # Ensure at least one character from each set
            password = [
                secrets.choice(lowercase),
                secrets.choice(uppercase),
                secrets.choice(digits),
                secrets.choice(special)
            ]
            
            # Fill the rest with random characters
            all_chars = lowercase + uppercase + digits + special
            password.extend(secrets.choice(all_chars) for _ in range(self.config.password_min_length - 4))
            
            # Shuffle the password
            secrets.SystemRandom().shuffle(password)
            
            return ''.join(password)
            
        except Exception as e:
            self.logger.error(f"Error generating secure password: {str(e)}")
            raise

    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against requirements."""
        try:
            errors = []
            
            # Check length
            if len(password) < self.config.password_min_length:
                errors.append(f"Password must be at least {self.config.password_min_length} characters long")
            
            # Check requirements
            if self.config.password_requirements.get('uppercase') and not re.search(r'[A-Z]', password):
                errors.append("Password must contain at least one uppercase letter")
            
            if self.config.password_requirements.get('lowercase') and not re.search(r'[a-z]', password):
                errors.append("Password must contain at least one lowercase letter")
            
            if self.config.password_requirements.get('digit') and not re.search(r'\d', password):
                errors.append("Password must contain at least one digit")
            
            if self.config.password_requirements.get('special') and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append("Password must contain at least one special character")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating password: {str(e)}")
            raise

    def mask_sensitive_data(self, data: Dict) -> Dict:
        """Mask sensitive data."""
        try:
            masked_data = data.copy()
            
            # Define sensitive fields
            sensitive_fields = [
                'password',
                'credit_card',
                'ssn',
                'email',
                'phone'
            ]
            
            # Mask sensitive fields
            for field in sensitive_fields:
                if field in masked_data:
                    if isinstance(masked_data[field], str):
                        masked_data[field] = '*' * len(masked_data[field])
                    else:
                        masked_data[field] = '********'
            
            return masked_data
            
        except Exception as e:
            self.logger.error(f"Error masking sensitive data: {str(e)}")
            raise

    def audit_log(self, action: str, user: str, details: Dict) -> None:
        """Log security audit events."""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'user': user,
                'details': details
            }
            
            # Write to audit log file
            with open(self.config.audit_log_path, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
            
        except Exception as e:
            self.logger.error(f"Error writing to audit log: {str(e)}")
            raise

    def check_access_control(self, user: str, resource: str, action: str) -> bool:
        """Check user access control."""
        try:
            # Load access control rules
            with open('config/access_control.yaml', 'r') as f:
                rules = yaml.safe_load(f)
            
            # Check if user has permission
            if user in rules.get('users', {}):
                user_rules = rules['users'][user]
                if resource in user_rules.get('resources', {}):
                    resource_rules = user_rules['resources'][resource]
                    return action in resource_rules.get('actions', [])
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking access control: {str(e)}")
            raise

    def monitor_security_events(self) -> None:
        """Monitor security events."""
        try:
            # Load security event patterns
            with open('config/security_patterns.yaml', 'r') as f:
                patterns = yaml.safe_load(f)
            
            # Monitor audit log
            with open(self.config.audit_log_path, 'r') as f:
                for line in f:
                    event = json.loads(line)
                    
                    # Check for suspicious patterns
                    for pattern in patterns:
                        if self._match_pattern(event, pattern):
                            self._handle_security_event(event, pattern)
            
        except Exception as e:
            self.logger.error(f"Error monitoring security events: {str(e)}")
            raise

    def _match_pattern(self, event: Dict, pattern: Dict) -> bool:
        """Match event against security pattern."""
        try:
            # Check action
            if pattern.get('action') and event['action'] != pattern['action']:
                return False
            
            # Check user
            if pattern.get('user') and event['user'] != pattern['user']:
                return False
            
            # Check details
            if pattern.get('details'):
                for key, value in pattern['details'].items():
                    if key not in event['details'] or event['details'][key] != value:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error matching security pattern: {str(e)}")
            raise

    def _handle_security_event(self, event: Dict, pattern: Dict) -> None:
        """Handle security event."""
        try:
            # Log security event
            self.logger.warning(f"Security event detected: {event}")
            
            # Take action based on pattern
            if pattern.get('action') == 'alert':
                self._send_security_alert(event)
            elif pattern.get('action') == 'block':
                self._block_user(event['user'])
            elif pattern.get('action') == 'notify':
                self._notify_admin(event)
            
        except Exception as e:
            self.logger.error(f"Error handling security event: {str(e)}")
            raise

    def _send_security_alert(self, event: Dict) -> None:
        """Send security alert."""
        try:
            # Implement alert mechanism (email, SMS, etc.)
            self.logger.info(f"Security alert sent for event: {event}")
            
        except Exception as e:
            self.logger.error(f"Error sending security alert: {str(e)}")
            raise

    def _block_user(self, user: str) -> None:
        """Block user access."""
        try:
            # Update user status in database
            with self.Session() as session:
                user_record = session.query(User).filter_by(username=user).first()
                if user_record:
                    user_record.is_blocked = True
                    user_record.blocked_until = datetime.now() + timedelta(minutes=self.config.lockout_duration)
                    session.commit()
            
        except Exception as e:
            self.logger.error(f"Error blocking user: {str(e)}")
            raise

    def _notify_admin(self, event: Dict) -> None:
        """Notify administrator."""
        try:
            # Implement admin notification mechanism
            self.logger.info(f"Admin notified of event: {event}")
            
        except Exception as e:
            self.logger.error(f"Error notifying admin: {str(e)}")
            raise

    def get_security_status(self) -> Dict:
        """Get current security status."""
        return {
            'is_encrypting': self.is_encrypting,
            'last_audit': self.security_status.get('last_audit'),
            'security_events': self.security_status.get('events', []),
            'blocked_users': self.security_status.get('blocked_users', [])
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create security instance
    security = DataSecurity()
    
    # Example security operations
    password = security.generate_secure_password()
    is_valid, errors = security.validate_password(password)
    if is_valid:
        hashed_password = security.hash_password(password)
        print(f"Generated secure password: {password}")
        print(f"Hashed password: {hashed_password}")
    else:
        print(f"Password validation errors: {errors}") 