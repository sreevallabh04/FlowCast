from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, and_, or_

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    reorder_point = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @hybrid_property
    def value(self):
        return self.price * self.quantity
    
    @classmethod
    def get_all_inventory(cls):
        return cls.query.all()
    
    @classmethod
    def get_inventory_status(cls):
        return cls.query.filter(cls.quantity > 0).all()
    
    @classmethod
    def get_inventory_alerts(cls):
        alerts = []
        low_stock = cls.query.filter(cls.quantity <= cls.reorder_point).all()
        expiring = cls.query.filter(
            and_(
                cls.expiry_date.isnot(None),
                cls.expiry_date <= datetime.utcnow() + timedelta(days=30)
            )
        ).all()
        
        for product in low_stock:
            alerts.append({
                'type': 'low_stock',
                'message': f'Low stock alert: {product.name} (SKU: {product.sku})',
                'severity': 'warning'
            })
        
        for product in expiring:
            alerts.append({
                'type': 'expiring',
                'message': f'Expiring soon: {product.name} (SKU: {product.sku})',
                'severity': 'error'
            })
        
        return alerts
    
    @classmethod
    def get_total_inventory_value(cls):
        return db.session.query(func.sum(cls.price * cls.quantity)).scalar() or 0
    
    @classmethod
    def get_inventory_trend(cls):
        # Calculate inventory trend over the last 30 days
        current_value = cls.get_total_inventory_value()
        past_value = db.session.query(func.sum(cls.price * cls.quantity)).filter(
            cls.updated_at <= datetime.utcnow() - timedelta(days=30)
        ).scalar() or 0
        
        if past_value == 0:
            return 0
        
        return ((current_value - past_value) / past_value) * 100
    
    @classmethod
    def get_inventory_analytics(cls, category='all', store='all'):
        query = cls.query
        
        if category != 'all':
            query = query.filter(cls.category == category)
        
        if store != 'all':
            query = query.join(Store).filter(Store.id == store)
        
        return query.all()
    
    @classmethod
    def get_inventory_turnover(cls, category='all', store='all'):
        # Calculate inventory turnover ratio
        avg_inventory = cls.get_total_inventory_value() / 2
        if avg_inventory == 0:
            return 0
        
        sales = Transaction.get_total_sales(category=category, store=store)
        return sales / avg_inventory
    
    def __repr__(self):
        return f'<Product {self.sku}>'

class Store(db.Model):
    __tablename__ = 'stores'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    products = db.relationship('Product', secondary='store_products')
    
    def __repr__(self):
        return f'<Store {self.name}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    store = db.relationship('Store')
    
    @classmethod
    def get_total_sales(cls, date_range='30d', category='all', store='all'):
        query = cls.query
        
        if date_range:
            days = int(date_range[:-1])
            query = query.filter(cls.timestamp >= datetime.utcnow() - timedelta(days=days))
        
        if category != 'all':
            query = query.join(Product).filter(Product.category == category)
        
        if store != 'all':
            query = query.filter(cls.store_id == store)
        
        return db.session.query(func.sum(cls.price * cls.quantity)).filter(
            query.whereclause
        ).scalar() or 0
    
    @classmethod
    def get_sales_trend(cls):
        # Calculate sales trend over the last 30 days
        current_sales = cls.get_total_sales('30d')
        past_sales = cls.get_total_sales('60d') - current_sales
        
        if past_sales == 0:
            return 0
        
        return ((current_sales - past_sales) / past_sales) * 100
    
    @classmethod
    def get_recent_sales(cls):
        return cls.query.order_by(cls.timestamp.desc()).limit(30).all()
    
    @classmethod
    def get_sales_analytics(cls, date_range='30d', category='all', store='all'):
        query = cls.query
        
        if date_range:
            days = int(date_range[:-1])
            query = query.filter(cls.timestamp >= datetime.utcnow() - timedelta(days=days))
        
        if category != 'all':
            query = query.join(Product).filter(Product.category == category)
        
        if store != 'all':
            query = query.filter(cls.store_id == store)
        
        return query.order_by(cls.timestamp).all()
    
    @classmethod
    def get_average_order_value(cls, date_range='30d', category='all', store='all'):
        total_sales = cls.get_total_sales(date_range, category, store)
        total_orders = cls.query.filter(
            cls.timestamp >= datetime.utcnow() - timedelta(days=int(date_range[:-1]))
        ).count()
        
        if total_orders == 0:
            return 0
        
        return total_sales / total_orders
    
    def __repr__(self):
        return f'<Transaction {self.id}>'

class Weather(db.Model):
    __tablename__ = 'weather'
    
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    store = db.relationship('Store')
    
    @classmethod
    def update_weather_data(cls, data):
        store_id = data.get('store_id')
        weather = cls.query.filter_by(store_id=store_id).first()
        
        if weather:
            weather.temperature = data.get('temperature')
            weather.condition = data.get('condition')
            weather.timestamp = datetime.utcnow()
        else:
            weather = cls(
                store_id=store_id,
                temperature=data.get('temperature'),
                condition=data.get('condition')
            )
            db.session.add(weather)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<Weather {self.id}>'

class Route(db.Model):
    __tablename__ = 'routes'
    
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    distance = db.Column(db.Float)
    duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    store = db.relationship('Store')
    deliveries = db.relationship('Delivery', backref='route')
    
    @classmethod
    def get_active_deliveries(cls):
        return cls.query.filter(cls.status == 'active').count()
    
    @classmethod
    def get_deliveries_trend(cls):
        # Calculate delivery trend over the last 30 days
        current_deliveries = cls.query.filter(
            and_(
                cls.status == 'completed',
                cls.end_time >= datetime.utcnow() - timedelta(days=30)
            )
        ).count()
        
        past_deliveries = cls.query.filter(
            and_(
                cls.status == 'completed',
                cls.end_time >= datetime.utcnow() - timedelta(days=60),
                cls.end_time < datetime.utcnow() - timedelta(days=30)
            )
        ).count()
        
        if past_deliveries == 0:
            return 0
        
        return ((current_deliveries - past_deliveries) / past_deliveries) * 100
    
    @classmethod
    def get_delivery_status(cls):
        return db.session.query(
            cls.status,
            func.count(cls.id).label('count')
        ).group_by(cls.status).all()
    
    @classmethod
    def optimize_routes(cls, max_distance, max_time, vehicle_capacity):
        # Implement route optimization algorithm
        # This is a placeholder for the actual implementation
        return cls.query.filter(cls.status == 'pending').all()
    
    @classmethod
    def get_delivery_analytics(cls, date_range='30d'):
        query = cls.query
        
        if date_range:
            days = int(date_range[:-1])
            query = query.filter(cls.start_time >= datetime.utcnow() - timedelta(days=days))
        
        return db.session.query(
            cls.status,
            func.count(cls.id).label('count')
        ).group_by(cls.status).all()
    
    @classmethod
    def get_delivery_success_rate(cls, date_range='30d'):
        total_deliveries = cls.query.filter(
            cls.start_time >= datetime.utcnow() - timedelta(days=int(date_range[:-1]))
        ).count()
        
        successful_deliveries = cls.query.filter(
            and_(
                cls.status == 'completed',
                cls.start_time >= datetime.utcnow() - timedelta(days=int(date_range[:-1]))
            )
        ).count()
        
        if total_deliveries == 0:
            return 0
        
        return (successful_deliveries / total_deliveries) * 100
    
    def get_directions(self):
        # Implement Google Maps Directions API integration
        # This is a placeholder for the actual implementation
        return {
            'routes': [
                {
                    'legs': [
                        {
                            'distance': {'text': f'{self.distance} km'},
                            'duration': {'text': f'{self.duration} mins'}
                        }
                    ]
                }
            ]
        }
    
    def __repr__(self):
        return f'<Route {self.id}>'

class Delivery(db.Model):
    __tablename__ = 'deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Delivery {self.id}>'

class Forecast(db.Model):
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    forecast = db.Column(db.Float, nullable=False)
    confidence_upper = db.Column(db.Float)
    confidence_lower = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    
    @classmethod
    def generate_forecast(cls, product_id, period, confidence):
        # Implement forecasting algorithm
        # This is a placeholder for the actual implementation
        return {
            'forecasts': [
                {
                    'date': (datetime.utcnow() + timedelta(days=i)).isoformat(),
                    'forecast': 100,
                    'confidence_upper': 120,
                    'confidence_lower': 80
                }
                for i in range(period)
            ]
        }
    
    def __repr__(self):
        return f'<Forecast {self.id}>'

class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_recent_alerts(cls):
        return cls.query.filter(
            cls.level.in_(['warning', 'error'])
        ).order_by(cls.timestamp.desc()).limit(10).all()
    
    def __repr__(self):
        return f'<Log {self.id}>'

# Association table for store products
store_products = db.Table('store_products',
    db.Column('store_id', db.Integer, db.ForeignKey('stores.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
) 