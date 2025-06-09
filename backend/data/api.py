import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
import uvicorn
import jwt
from passlib.context import CryptContext
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
import time

@dataclass
class APIConfig:
    """Configuration for the API system."""
    host: str
    port: int
    debug: bool
    secret_key: str
    token_expire_minutes: int
    cors_origins: List[str]
    rate_limit: int
    cache_ttl: int
    enable_docs: bool
    enable_auth: bool

# Pydantic models for request/response validation
class ProductBase(BaseModel):
    name: str
    category: str
    price: float
    weight: float
    dimensions: str
    supplier_id: int
    created_at: datetime = Field(default_factory=datetime.now)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    supplier_id: Optional[int] = None

class Product(ProductBase):
    product_id: int

    class Config:
        orm_mode = True

class LocationBase(BaseModel):
    name: str
    address: str
    city: str
    state: str
    country: str
    postal_code: str
    latitude: float
    longitude: float
    created_at: datetime = Field(default_factory=datetime.now)

class LocationCreate(LocationBase):
    pass

class LocationUpdate(LocationBase):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Location(LocationBase):
    location_id: int

    class Config:
        orm_mode = True

class SupplierBase(BaseModel):
    name: str
    contact_person: str
    email: str
    phone: str
    address: str
    created_at: datetime = Field(default_factory=datetime.now)

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(SupplierBase):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class Supplier(SupplierBase):
    supplier_id: int

    class Config:
        orm_mode = True

class VehicleBase(BaseModel):
    type: str
    capacity: float
    fuel_efficiency: float
    maintenance_schedule: str
    created_at: datetime = Field(default_factory=datetime.now)

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(VehicleBase):
    type: Optional[str] = None
    capacity: Optional[float] = None
    fuel_efficiency: Optional[float] = None
    maintenance_schedule: Optional[str] = None

class Vehicle(VehicleBase):
    vehicle_id: int

    class Config:
        orm_mode = True

class EventBase(BaseModel):
    type: str
    name: str
    start_date: datetime
    end_date: datetime
    location_id: int
    impact_factor: float
    created_at: datetime = Field(default_factory=datetime.now)

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    type: Optional[str] = None
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location_id: Optional[int] = None
    impact_factor: Optional[float] = None

class Event(EventBase):
    event_id: int

    class Config:
        orm_mode = True

class WeatherDataBase(BaseModel):
    date: datetime
    location_id: int
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    condition: str
    created_at: datetime = Field(default_factory=datetime.now)

class WeatherDataCreate(WeatherDataBase):
    pass

class WeatherDataUpdate(WeatherDataBase):
    date: Optional[datetime] = None
    location_id: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    condition: Optional[str] = None

class WeatherData(WeatherDataBase):
    weather_id: int

    class Config:
        orm_mode = True

class SalesDataBase(BaseModel):
    date: datetime
    product_id: int
    location_id: int
    quantity: int
    revenue: float
    created_at: datetime = Field(default_factory=datetime.now)

class SalesDataCreate(SalesDataBase):
    pass

class SalesDataUpdate(SalesDataBase):
    date: Optional[datetime] = None
    product_id: Optional[int] = None
    location_id: Optional[int] = None
    quantity: Optional[int] = None
    revenue: Optional[float] = None

class SalesData(SalesDataBase):
    sale_id: int

    class Config:
        orm_mode = True

class InventoryDataBase(BaseModel):
    date: datetime
    product_id: int
    location_id: int
    inventory_level: int
    reorder_point: int
    created_at: datetime = Field(default_factory=datetime.now)

class InventoryDataCreate(InventoryDataBase):
    pass

class InventoryDataUpdate(InventoryDataBase):
    date: Optional[datetime] = None
    product_id: Optional[int] = None
    location_id: Optional[int] = None
    inventory_level: Optional[int] = None
    reorder_point: Optional[int] = None

class InventoryData(InventoryDataBase):
    inventory_id: int

    class Config:
        orm_mode = True

class DeliveryDataBase(BaseModel):
    delivery_date: datetime
    product_id: int
    origin_id: int
    destination_id: int
    vehicle_id: int
    quantity: int
    distance: float
    duration: float
    created_at: datetime = Field(default_factory=datetime.now)

class DeliveryDataCreate(DeliveryDataBase):
    pass

class DeliveryDataUpdate(DeliveryDataBase):
    delivery_date: Optional[datetime] = None
    product_id: Optional[int] = None
    origin_id: Optional[int] = None
    destination_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    quantity: Optional[int] = None
    distance: Optional[float] = None
    duration: Optional[float] = None

class DeliveryData(DeliveryDataBase):
    delivery_id: int

    class Config:
        orm_mode = True

class DataAPI:
    def __init__(self, config_path: str = 'config/api_config.yaml'):
        """Initialize the API system with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="FlowCast API",
            description="API for supply chain data management",
            version="1.0.0"
        )
        
        # Set up CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Set up database connection
        self.engine = create_engine(self.config.database_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.Base = declarative_base()
        
        # Set up authentication
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Define routes
        self._define_routes()

    def _load_config(self) -> APIConfig:
        """Load API configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return APIConfig(**config_dict)
        except Exception as e:
            self.logger.error(f"Error loading API configuration: {str(e)}")
            raise

    def _define_routes(self) -> None:
        """Define API routes."""
        # Authentication routes
        @self.app.post("/token")
        async def login(form_data: OAuth2PasswordRequestForm = Depends()):
            return await self._authenticate_user(form_data)

        # Product routes
        @self.app.get("/products", response_model=List[Product])
        async def get_products(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_products(db, skip, limit)

        @self.app.post("/products", response_model=Product)
        async def create_product(
            product: ProductCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_product(db, product)

        @self.app.get("/products/{product_id}", response_model=Product)
        async def get_product(
            product_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_product(db, product_id)

        @self.app.put("/products/{product_id}", response_model=Product)
        async def update_product(
            product_id: int = Path(..., ge=1),
            product: ProductUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_product(db, product_id, product)

        @self.app.delete("/products/{product_id}")
        async def delete_product(
            product_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_product(db, product_id)

        # Location routes
        @self.app.get("/locations", response_model=List[Location])
        async def get_locations(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_locations(db, skip, limit)

        @self.app.post("/locations", response_model=Location)
        async def create_location(
            location: LocationCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_location(db, location)

        @self.app.get("/locations/{location_id}", response_model=Location)
        async def get_location(
            location_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_location(db, location_id)

        @self.app.put("/locations/{location_id}", response_model=Location)
        async def update_location(
            location_id: int = Path(..., ge=1),
            location: LocationUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_location(db, location_id, location)

        @self.app.delete("/locations/{location_id}")
        async def delete_location(
            location_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_location(db, location_id)

        # Supplier routes
        @self.app.get("/suppliers", response_model=List[Supplier])
        async def get_suppliers(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_suppliers(db, skip, limit)

        @self.app.post("/suppliers", response_model=Supplier)
        async def create_supplier(
            supplier: SupplierCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_supplier(db, supplier)

        @self.app.get("/suppliers/{supplier_id}", response_model=Supplier)
        async def get_supplier(
            supplier_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_supplier(db, supplier_id)

        @self.app.put("/suppliers/{supplier_id}", response_model=Supplier)
        async def update_supplier(
            supplier_id: int = Path(..., ge=1),
            supplier: SupplierUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_supplier(db, supplier_id, supplier)

        @self.app.delete("/suppliers/{supplier_id}")
        async def delete_supplier(
            supplier_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_supplier(db, supplier_id)

        # Vehicle routes
        @self.app.get("/vehicles", response_model=List[Vehicle])
        async def get_vehicles(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_vehicles(db, skip, limit)

        @self.app.post("/vehicles", response_model=Vehicle)
        async def create_vehicle(
            vehicle: VehicleCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_vehicle(db, vehicle)

        @self.app.get("/vehicles/{vehicle_id}", response_model=Vehicle)
        async def get_vehicle(
            vehicle_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_vehicle(db, vehicle_id)

        @self.app.put("/vehicles/{vehicle_id}", response_model=Vehicle)
        async def update_vehicle(
            vehicle_id: int = Path(..., ge=1),
            vehicle: VehicleUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_vehicle(db, vehicle_id, vehicle)

        @self.app.delete("/vehicles/{vehicle_id}")
        async def delete_vehicle(
            vehicle_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_vehicle(db, vehicle_id)

        # Event routes
        @self.app.get("/events", response_model=List[Event])
        async def get_events(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_events(db, skip, limit)

        @self.app.post("/events", response_model=Event)
        async def create_event(
            event: EventCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_event(db, event)

        @self.app.get("/events/{event_id}", response_model=Event)
        async def get_event(
            event_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_event(db, event_id)

        @self.app.put("/events/{event_id}", response_model=Event)
        async def update_event(
            event_id: int = Path(..., ge=1),
            event: EventUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_event(db, event_id, event)

        @self.app.delete("/events/{event_id}")
        async def delete_event(
            event_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_event(db, event_id)

        # Weather data routes
        @self.app.get("/weather", response_model=List[WeatherData])
        async def get_weather_data(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_weather_data(db, skip, limit)

        @self.app.post("/weather", response_model=WeatherData)
        async def create_weather_data(
            weather_data: WeatherDataCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_weather_data(db, weather_data)

        @self.app.get("/weather/{weather_id}", response_model=WeatherData)
        async def get_weather_data_by_id(
            weather_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_weather_data_by_id(db, weather_id)

        @self.app.put("/weather/{weather_id}", response_model=WeatherData)
        async def update_weather_data(
            weather_id: int = Path(..., ge=1),
            weather_data: WeatherDataUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_weather_data(db, weather_id, weather_data)

        @self.app.delete("/weather/{weather_id}")
        async def delete_weather_data(
            weather_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_weather_data(db, weather_id)

        # Sales data routes
        @self.app.get("/sales", response_model=List[SalesData])
        async def get_sales_data(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_sales_data(db, skip, limit)

        @self.app.post("/sales", response_model=SalesData)
        async def create_sales_data(
            sales_data: SalesDataCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_sales_data(db, sales_data)

        @self.app.get("/sales/{sale_id}", response_model=SalesData)
        async def get_sales_data_by_id(
            sale_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_sales_data_by_id(db, sale_id)

        @self.app.put("/sales/{sale_id}", response_model=SalesData)
        async def update_sales_data(
            sale_id: int = Path(..., ge=1),
            sales_data: SalesDataUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_sales_data(db, sale_id, sales_data)

        @self.app.delete("/sales/{sale_id}")
        async def delete_sales_data(
            sale_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_sales_data(db, sale_id)

        # Inventory data routes
        @self.app.get("/inventory", response_model=List[InventoryData])
        async def get_inventory_data(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_inventory_data(db, skip, limit)

        @self.app.post("/inventory", response_model=InventoryData)
        async def create_inventory_data(
            inventory_data: InventoryDataCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_inventory_data(db, inventory_data)

        @self.app.get("/inventory/{inventory_id}", response_model=InventoryData)
        async def get_inventory_data_by_id(
            inventory_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_inventory_data_by_id(db, inventory_id)

        @self.app.put("/inventory/{inventory_id}", response_model=InventoryData)
        async def update_inventory_data(
            inventory_id: int = Path(..., ge=1),
            inventory_data: InventoryDataUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_inventory_data(db, inventory_id, inventory_data)

        @self.app.delete("/inventory/{inventory_id}")
        async def delete_inventory_data(
            inventory_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_inventory_data(db, inventory_id)

        # Delivery data routes
        @self.app.get("/deliveries", response_model=List[DeliveryData])
        async def get_delivery_data(
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_delivery_data(db, skip, limit)

        @self.app.post("/deliveries", response_model=DeliveryData)
        async def create_delivery_data(
            delivery_data: DeliveryDataCreate,
            db: Session = Depends(self._get_db)
        ):
            return await self._create_delivery_data(db, delivery_data)

        @self.app.get("/deliveries/{delivery_id}", response_model=DeliveryData)
        async def get_delivery_data_by_id(
            delivery_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._get_delivery_data_by_id(db, delivery_id)

        @self.app.put("/deliveries/{delivery_id}", response_model=DeliveryData)
        async def update_delivery_data(
            delivery_id: int = Path(..., ge=1),
            delivery_data: DeliveryDataUpdate = Body(...),
            db: Session = Depends(self._get_db)
        ):
            return await self._update_delivery_data(db, delivery_id, delivery_data)

        @self.app.delete("/deliveries/{delivery_id}")
        async def delete_delivery_data(
            delivery_id: int = Path(..., ge=1),
            db: Session = Depends(self._get_db)
        ):
            return await self._delete_delivery_data(db, delivery_id)

    def _get_db(self) -> Session:
        """Get database session."""
        db = self.Session()
        try:
            yield db
        finally:
            db.close()

    async def _authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> Dict:
        """Authenticate user and return JWT token."""
        try:
            # Verify user credentials
            user = await self._verify_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Incorrect username or password"
                )
            
            # Generate JWT token
            access_token = self._create_access_token(
                data={"sub": user.username}
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            self.logger.error(f"Error authenticating user: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    def _create_access_token(self, data: Dict) -> str:
        """Create JWT access token."""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(minutes=self.config.token_expire_minutes)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(
                to_encode,
                self.config.secret_key,
                algorithm="HS256"
            )
            return encoded_jwt
            
        except Exception as e:
            self.logger.error(f"Error creating access token: {str(e)}")
            raise

    def run(self) -> None:
        """Run the API server."""
        try:
            uvicorn.run(
                self.app,
                host=self.config.host,
                port=self.config.port,
                debug=self.config.debug
            )
        except Exception as e:
            self.logger.error(f"Error running API server: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run API
    api = DataAPI()
    api.run() 