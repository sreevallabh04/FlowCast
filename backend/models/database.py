from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='user')  # 'admin' or 'user'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    stores = relationship("Store", back_populates="manager")
    api_keys = relationship("APIKey", back_populates="user")

class APIKey(Base):
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    key = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    unit_price = Column(Float)
    storage_temp = Column(Float)  # in Celsius
    storage_humidity = Column(Float)  # percentage
    shelf_life = Column(Integer)  # in days
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="product")
    transactions = relationship("Transaction", back_populates="product")

class Store(Base):
    __tablename__ = 'stores'
    
    id = Column(Integer, primary_key=True)
    store_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    manager_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    manager = relationship("User", back_populates="stores")
    inventory = relationship("Inventory", back_populates="store")
    transactions = relationship("Transaction", back_populates="store")

class Inventory(Base):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    store_id = Column(Integer, ForeignKey('stores.id'))
    current_stock = Column(Integer, default=0)
    safety_stock = Column(Integer)
    reorder_point = Column(Integer)
    last_restock = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory")
    store = relationship("Store", back_populates="inventory")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    store_id = Column(Integer, ForeignKey('stores.id'))
    quantity = Column(Integer)
    transaction_type = Column(String)  # 'sale', 'restock', 'waste'
    timestamp = Column(DateTime, default=datetime.utcnow)
    weather_conditions = Column(JSON)  # Store weather data
    economic_indicators = Column(JSON)  # Store economic data
    
    # Relationships
    product = relationship("Product", back_populates="transactions")
    store = relationship("Store", back_populates="transactions")

class Route(Base):
    __tablename__ = 'routes'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String)
    store_ids = Column(JSON)  # List of store IDs in route
    distance = Column(Float)  # in kilometers
    duration = Column(Integer)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String)  # 'planned', 'in_progress', 'completed'
    
    # Additional fields
    weather_conditions = Column(JSON)
    traffic_conditions = Column(JSON)
    route_polyline = Column(String)  # Google Maps polyline

class Webhook(Base):
    __tablename__ = 'webhooks'
    
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    events = Column(JSON)  # List of event types to trigger
    secret = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)

# Database connection
def get_db_connection():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///flowcast.db')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize database
def init_db():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///flowcast.db')
    engine = create_engine(database_url)
    Base.metadata.create_all(engine) 