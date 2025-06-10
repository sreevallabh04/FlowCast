from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os
from datetime import datetime, timedelta
import json
from functools import wraps
import jwt
from werkzeug.exceptions import HTTPException
import numpy as np
import pandas as pd
from models.database import get_db_connection, User, Product, Store, Inventory, Transaction, Route, Webhook
from models.demand_model import DemandModel
from models.inventory_model import InventoryModel
from models.routing_model import RoutingModel
from models.expiry_model import ExpiryModel
from middleware.auth import login_required, admin_required, generate_token, rate_limit
import requests
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from flask_redis import FlaskRedis
from dotenv import load_dotenv
from models import db
from schemas import (
    UserSchema, ProductSchema, StoreSchema, TransactionSchema,
    WeatherSchema, RouteSchema, ForecastSchema, LogSchema
)
from utils.logger import Logger
from utils.helpers import SecurityHelper
from data.analyzer import DataAnalyzer
from data.visualization import DataVisualization
from data.transformation import DataTransformation
from data.migration import DataMigration
from data.backup import DataBackup
from data.exporter import DataExporter

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.getenv('ALLOWED_ORIGINS', '*').split(',')}})

# Load configuration
config = Config()
app.config.from_object(config)

# Setup logging
logger = setup_logger('app')

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize cache
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Initialize models
demand_model = DemandModel()
inventory_model = InventoryModel()
routing_model = RoutingModel()
expiry_model = ExpiryModel()

# Initialize extensions
jwt = JWTManager(app)
mail = Mail(app)
redis_client = FlaskRedis(app)

# Initialize database
db.init_app(app)

# Initialize utilities
logger = Logger()
security = SecurityHelper()
analyzer = DataAnalyzer()
visualizer = DataVisualization()
transformer = DataTransformation()
migrator = DataMigration()
backup = DataBackup()
exporter = DataExporter()

# Initialize schemas
user_schema = UserSchema()
product_schema = ProductSchema()
store_schema = StoreSchema()
transaction_schema = TransactionSchema()
weather_schema = WeatherSchema()
route_schema = RouteSchema()
forecast_schema = ForecastSchema()
log_schema = LogSchema()

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

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Authentication routes
@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    try:
        data = request.get_json()
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        user = User(
            email=data['email'],
            name=data['name'],
            password=security.hash_password(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        
        token = security.generate_token()
        return jsonify({'token': token}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not security.verify_password(data['password'], user.password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = security.generate_token()
        return jsonify({'token': token}), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

# Dashboard routes
@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Get KPIs
        kpis = {
            'sales': Transaction.get_total_sales(),
            'salesTrend': Transaction.get_sales_trend(),
            'inventory': Product.get_total_inventory_value(),
            'inventoryTrend': Product.get_inventory_trend(),
            'deliveries': Route.get_active_deliveries(),
            'deliveriesTrend': Route.get_deliveries_trend()
        }
        
        # Get recent data
        sales = Transaction.get_recent_sales()
        inventory = Product.get_inventory_status()
        deliveries = Route.get_delivery_status()
        alerts = Log.get_recent_alerts()
        
        return jsonify({
            'kpis': kpis,
            'sales': sales,
            'inventory': inventory,
            'deliveries': deliveries,
            'alerts': alerts
        })
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

# Demand Forecast routes
@app.route('/api/forecast', methods=['GET'])
@jwt_required()
def get_forecast():
    try:
        product_id = request.args.get('product')
        confidence = float(request.args.get('confidence', 95))
        period = int(request.args.get('period', 30))
        
        # Get forecast data
        forecast = Forecast.generate_forecast(product_id, period, confidence)
        
        return jsonify(forecast)
    except Exception as e:
        logger.error(f"Forecast error: {str(e)}")
        return jsonify({'error': 'Failed to generate forecast'}), 500

# Inventory Management routes
@app.route('/api/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    try:
        inventory = Product.get_all_inventory()
        alerts = Product.get_inventory_alerts()
        
        return jsonify({
            'inventory': inventory,
            'alerts': alerts
        })
    except Exception as e:
        logger.error(f"Inventory error: {str(e)}")
        return jsonify({'error': 'Failed to fetch inventory data'}), 500

@app.route('/api/inventory/<int:id>', methods=['PUT'])
@jwt_required()
def update_inventory(id):
    try:
        data = request.get_json()
        product = Product.query.get(id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        for key, value in data.items():
            setattr(product, key, value)
        
        db.session.commit()
        return jsonify(product_schema.dump(product))
    except Exception as e:
        logger.error(f"Inventory update error: {str(e)}")
        return jsonify({'error': 'Failed to update inventory'}), 500

# Route Optimization routes
@app.route('/api/routes', methods=['GET'])
@jwt_required()
def get_routes():
    try:
        max_distance = float(request.args.get('maxDistance', 100))
        max_time = int(request.args.get('maxTime', 120))
        vehicle_capacity = float(request.args.get('vehicleCapacity', 1000))
        
        routes = Route.optimize_routes(max_distance, max_time, vehicle_capacity)
        deliveries = Route.get_active_deliveries()
        
        return jsonify({
            'routes': routes,
            'deliveries': deliveries
        })
    except Exception as e:
        logger.error(f"Route optimization error: {str(e)}")
        return jsonify({'error': 'Failed to optimize routes'}), 500

@app.route('/api/routes/<int:id>/directions', methods=['GET'])
@jwt_required()
def get_route_directions(id):
    try:
        route = Route.query.get(id)
        if not route:
            return jsonify({'error': 'Route not found'}), 404
        
        directions = route.get_directions()
        return jsonify(directions)
    except Exception as e:
        logger.error(f"Route directions error: {str(e)}")
        return jsonify({'error': 'Failed to fetch route directions'}), 500

# Analytics routes
@app.route('/api/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    try:
        date_range = request.args.get('dateRange', '30d')
        category = request.args.get('category', 'all')
        store = request.args.get('store', 'all')
        
        # Get analytics data
        sales = Transaction.get_sales_analytics(date_range, category, store)
        inventory = Product.get_inventory_analytics(category, store)
        deliveries = Route.get_delivery_analytics(date_range)
        metrics = {
            'totalSales': Transaction.get_total_sales(date_range, category, store),
            'averageOrderValue': Transaction.get_average_order_value(date_range, category, store),
            'deliverySuccessRate': Route.get_delivery_success_rate(date_range),
            'inventoryTurnover': Product.get_inventory_turnover(category, store)
        }
        
        return jsonify({
            'sales': sales,
            'inventory': inventory,
            'deliveries': deliveries,
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({'error': 'Failed to fetch analytics data'}), 500

# Export routes
@app.route('/api/analytics/export', methods=['GET'])
@jwt_required()
def export_analytics():
    try:
        format = request.args.get('format', 'csv')
        date_range = request.args.get('dateRange', '30d')
        category = request.args.get('category', 'all')
        store = request.args.get('store', 'all')
        
        data = {
            'sales': Transaction.get_sales_analytics(date_range, category, store),
            'inventory': Product.get_inventory_analytics(category, store),
            'deliveries': Route.get_delivery_analytics(date_range)
        }
        
        return exporter.export_data(data, format)
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': 'Failed to export data'}), 500

# Webhook routes
@app.route('/api/webhooks', methods=['POST'])
def handle_webhook():
    try:
        data = request.get_json()
        webhook_type = data.get('type')
        
        if webhook_type == 'weather':
            Weather.update_weather_data(data)
        elif webhook_type == 'delivery':
            Route.update_delivery_status(data)
        elif webhook_type == 'inventory':
            Product.update_inventory_levels(data)
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Failed to process webhook'}), 500

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV', 'production') == 'development'
    ) 