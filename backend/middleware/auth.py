from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
import os
from models.database import get_db_connection, User, APIKey

def generate_token(user_id, role):
    """Generate a JWT token for the user."""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET', 'your-secret-key'), algorithm='HS256')

def verify_token(token):
    """Verify a JWT token and return the payload."""
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET', 'your-secret-key'), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_api_key(api_key):
    """Verify an API key and return the associated user."""
    db = get_db_connection()
    try:
        key = db.query(APIKey).filter_by(key=api_key, is_active=True).first()
        if key:
            key.last_used = datetime.utcnow()
            db.commit()
            return key.user
    finally:
        db.close()
    return None

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            auth_type, auth_value = auth_header.split(' ', 1)
        except ValueError:
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        if auth_type.lower() == 'bearer':
            payload = verify_token(auth_value)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            request.user_id = payload['user_id']
            request.user_role = payload['role']
        elif auth_type.lower() == 'apikey':
            user = verify_api_key(auth_value)
            if not user:
                return jsonify({'error': 'Invalid API key'}), 401
            request.user_id = user.id
            request.user_role = user.role
        else:
            return jsonify({'error': 'Unsupported authorization type'}), 401
        
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            auth_type, auth_value = auth_header.split(' ', 1)
        except ValueError:
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        if auth_type.lower() == 'bearer':
            payload = verify_token(auth_value)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            if payload['role'] != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            request.user_id = payload['user_id']
            request.user_role = payload['role']
        elif auth_type.lower() == 'apikey':
            user = verify_api_key(auth_value)
            if not user:
                return jsonify({'error': 'Invalid API key'}), 401
            if user.role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            request.user_id = user.id
            request.user_role = user.role
        else:
            return jsonify({'error': 'Unsupported authorization type'}), 401
        
        return f(*args, **kwargs)
    return decorated

def rate_limit(f):
    """Decorator to implement rate limiting."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'user_id'):
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get rate limit from user role
        db = get_db_connection()
        try:
            user = db.query(User).get(request.user_id)
            if user.role == 'admin':
                limit = 1000  # requests per minute
            else:
                limit = 100  # requests per minute
            
            # TODO: Implement actual rate limiting logic using Redis
            # For now, just pass through
            return f(*args, **kwargs)
        finally:
            db.close()
    return decorated 