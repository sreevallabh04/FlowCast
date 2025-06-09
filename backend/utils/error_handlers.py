import functools
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv

def handle_error(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.error(f"API Error: {e.message}", exc_info=True)
            response = jsonify(e.to_dict())
            response.status_code = e.status_code
            return response
        except HTTPException as e:
            logger.error(f"HTTP Error: {str(e)}", exc_info=True)
            response = jsonify({
                'message': e.description,
                'status': 'error'
            })
            response.status_code = e.code
            return response
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}", exc_info=True)
            response = jsonify({
                'message': 'An unexpected error occurred',
                'status': 'error'
            })
            response.status_code = 500
            return response
    return wrapped

def validate_request_data(required_fields):
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            data = request.get_json()
            if not data:
                raise APIError('No data provided', 400)
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise APIError(f'Missing required fields: {", ".join(missing_fields)}', 400)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def rate_limit(limit, period):
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Implement rate limiting logic here
            # This is a placeholder for actual rate limiting implementation
            return f(*args, **kwargs)
        return wrapped
    return decorator 