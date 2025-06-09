from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from datetime import datetime, timedelta
import json
from functools import wraps
import jwt
from werkzeug.exceptions import HTTPException
import numpy as np
import pandas as pd
from models.demand_model import DemandModel
from models.inventory_manager import InventoryManager
from models.route_optimizer import RouteOptimizer
from models.expiry_optimizer import ExpiryOptimizer
from utils.logger import setup_logger
from utils.config import Config
from utils.db import get_db_connection
from utils.cache import cache

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
config = Config()
app.config.from_object(config)

# Setup logging
logger = setup_logger('app')

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize models
demand_model = DemandModel()
inventory_manager = InventoryManager()
route_optimizer = RouteOptimizer()
expiry_optimizer = ExpiryOptimizer()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Error handlers
@app.errorhandler(HTTPException)
def handle_exception(e):
    logger.error(f"HTTP error: {str(e)}")
    return jsonify({
        "error": e.name,
        "message": e.description,
        "status_code": e.code
    }), e.code

@app.errorhandler(Exception)
def handle_generic_exception(e):
    logger.error(f"Unexpected error: {str(e)}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

# Demand prediction endpoint
@app.route('/predict-demand', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
@cache.cached(timeout=300)  # Cache for 5 minutes
def predict_demand(current_user):
    try:
        data = request.get_json()
        required_fields = ['product_id', 'location_id', 'start_date', 'end_date']
        
        # Validate input
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

        # Get predictions
        predictions = demand_model.predict(
            product_id=data['product_id'],
            location_id=data['location_id'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date'])
        )

        logger.info(f"Demand prediction generated for product {data['product_id']} at location {data['location_id']}")
        
        return jsonify({
            "predictions": predictions,
            "metadata": {
                "model_version": demand_model.version,
                "confidence_score": demand_model.get_confidence_score(),
                "generated_at": datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error in predict_demand: {str(e)}")
        return jsonify({
            "error": "Failed to generate demand predictions",
            "message": str(e)
        }), 500

# Inventory optimization endpoint
@app.route('/optimize-inventory', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
@cache.cached(timeout=300)
def optimize_inventory(current_user):
    try:
        data = request.get_json()
        required_fields = ['location_id', 'optimization_type']
        
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

        # Get optimization recommendations
        recommendations = inventory_manager.optimize(
            location_id=data['location_id'],
            optimization_type=data['optimization_type'],
            constraints=data.get('constraints', {})
        )

        logger.info(f"Inventory optimization completed for location {data['location_id']}")
        
        return jsonify({
            "recommendations": recommendations,
            "metadata": {
                "optimization_type": data['optimization_type'],
                "generated_at": datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error in optimize_inventory: {str(e)}")
        return jsonify({
            "error": "Failed to optimize inventory",
            "message": str(e)
        }), 500

# Route optimization endpoint
@app.route('/optimize-routes', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
@cache.cached(timeout=300)
def optimize_routes(current_user):
    try:
        data = request.get_json()
        required_fields = ['locations', 'vehicles', 'constraints']
        
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

        # Get optimized routes
        routes = route_optimizer.optimize(
            locations=data['locations'],
            vehicles=data['vehicles'],
            constraints=data['constraints']
        )

        logger.info(f"Route optimization completed for {len(data['locations'])} locations")
        
        return jsonify({
            "routes": routes,
            "metadata": {
                "total_distance": sum(route['distance'] for route in routes),
                "total_duration": sum(route['duration'] for route in routes),
                "generated_at": datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error in optimize_routes: {str(e)}")
        return jsonify({
            "error": "Failed to optimize routes",
            "message": str(e)
        }), 500

# Analytics endpoint
@app.route('/analytics', methods=['GET'])
@token_required
@limiter.limit("30 per minute")
@cache.cached(timeout=300)
def get_analytics(current_user):
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        location_id = request.args.get('location_id')
        product_id = request.args.get('product_id')

        # Validate dates
        try:
            start_date = datetime.fromisoformat(start_date) if start_date else datetime.utcnow() - timedelta(days=30)
            end_date = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        except ValueError:
            return jsonify({
                "error": "Invalid date format",
                "message": "Dates should be in ISO format (YYYY-MM-DD)"
            }), 400

        # Get analytics data
        analytics_data = {
            "demand_metrics": demand_model.get_metrics(
                start_date=start_date,
                end_date=end_date,
                location_id=location_id,
                product_id=product_id
            ),
            "inventory_metrics": inventory_manager.get_metrics(
                start_date=start_date,
                end_date=end_date,
                location_id=location_id,
                product_id=product_id
            ),
            "route_metrics": route_optimizer.get_metrics(
                start_date=start_date,
                end_date=end_date,
                location_id=location_id
            ),
            "expiry_metrics": expiry_optimizer.get_metrics(
                start_date=start_date,
                end_date=end_date,
                location_id=location_id,
                product_id=product_id
            )
        }

        logger.info(f"Analytics data generated for period {start_date} to {end_date}")
        
        return jsonify({
            "data": analytics_data,
            "metadata": {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error in get_analytics: {str(e)}")
        return jsonify({
            "error": "Failed to generate analytics",
            "message": str(e)
        }), 500

# Metrics endpoint for Prometheus
@app.route('/metrics')
def metrics():
    try:
        metrics_data = {
            "http_requests_total": {
                "type": "counter",
                "help": "Total number of HTTP requests",
                "value": app.config.get('request_count', 0)
            },
            "http_request_duration_seconds": {
                "type": "histogram",
                "help": "HTTP request duration in seconds",
                "value": app.config.get('request_duration', 0)
            },
            "model_accuracy": {
                "type": "gauge",
                "help": "Model accuracy score",
                "value": demand_model.get_accuracy()
            }
        }
        return jsonify(metrics_data)
    except Exception as e:
        logger.error(f"Error in metrics endpoint: {str(e)}")
        return jsonify({"error": "Failed to generate metrics"}), 500

if __name__ == '__main__':
    # Initialize database
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                response_time REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    # Start the application
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV', 'production') == 'development'
    ) 