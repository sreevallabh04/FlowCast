import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import json
import os
from typing import Dict, List, Union, Optional
import logging
from faker import Faker
import requests
from geopy.distance import geodesic
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataGenerator:
    def __init__(self, output_dir: str = 'data/generated'):
        self.faker = Faker()
        self.output_dir = output_dir
        self.timezone = pytz.timezone('UTC')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize data storage
        self.products = None
        self.locations = None
        self.suppliers = None
        self.vehicles = None
        self.events = None
        self.weather_data = None
        self.sales_data = None
        self.inventory_data = None
        self.delivery_data = None

    def generate_all_data(self, start_date: datetime, end_date: datetime) -> None:
        """Generate all types of data for the specified date range."""
        try:
            # Generate static data
            self.generate_products()
            self.generate_locations()
            self.generate_suppliers()
            self.generate_vehicles()
            self.generate_events(start_date, end_date)
            
            # Generate time-series data
            self.generate_weather_data(start_date, end_date)
            self.generate_sales_data(start_date, end_date)
            self.generate_inventory_data(start_date, end_date)
            self.generate_delivery_data(start_date, end_date)
            
            # Save all data
            self.save_all_data()
            
            logging.info("All data generated successfully")
            
        except Exception as e:
            logging.error(f"Error generating data: {str(e)}")
            raise

    def generate_products(self, n_products: int = 100) -> None:
        """Generate product data."""
        products = []
        categories = ['Electronics', 'Clothing', 'Food', 'Furniture', 'Books']
        suppliers = [f'S{i:03d}' for i in range(1, 11)]
        
        for i in range(n_products):
            category = random.choice(categories)
            product = {
                'product_id': f'P{i:03d}',
                'name': self.faker.word().capitalize(),
                'category': category,
                'supplier_id': random.choice(suppliers),
                'unit_price': round(random.uniform(10, 1000), 2),
                'unit_weight': round(random.uniform(0.1, 50), 2),
                'shelf_life_days': random.randint(1, 365),
                'reorder_point': random.randint(10, 100),
                'safety_stock': random.randint(5, 50),
                'lead_time_days': random.randint(1, 30),
                'created_at': self.faker.date_time_this_year()
            }
            products.append(product)
        
        self.products = pd.DataFrame(products)
        logging.info(f"Generated {len(products)} products")

    def generate_locations(self, n_locations: int = 50) -> None:
        """Generate location data."""
        locations = []
        location_types = ['Store', 'Warehouse', 'Distribution Center']
        
        # Generate a base location (e.g., New York City)
        base_lat, base_lon = 40.7128, -74.0060
        
        for i in range(n_locations):
            # Generate random offset from base location
            lat_offset = random.uniform(-0.5, 0.5)
            lon_offset = random.uniform(-0.5, 0.5)
            
            location = {
                'location_id': f'L{i:03d}',
                'name': f"{self.faker.company()} {random.choice(location_types)}",
                'type': random.choice(location_types),
                'latitude': base_lat + lat_offset,
                'longitude': base_lon + lon_offset,
                'address': self.faker.address(),
                'capacity': random.randint(1000, 10000),
                'operating_hours': {
                    'open': '08:00',
                    'close': '20:00'
                },
                'timezone': random.choice(pytz.common_timezones),
                'created_at': self.faker.date_time_this_year()
            }
            locations.append(location)
        
        self.locations = pd.DataFrame(locations)
        logging.info(f"Generated {len(locations)} locations")

    def generate_suppliers(self, n_suppliers: int = 10) -> None:
        """Generate supplier data."""
        suppliers = []
        
        for i in range(n_suppliers):
            supplier = {
                'supplier_id': f'S{i:03d}',
                'name': self.faker.company(),
                'contact_person': self.faker.name(),
                'email': self.faker.email(),
                'phone': self.faker.phone_number(),
                'address': self.faker.address(),
                'lead_time_days': random.randint(1, 30),
                'minimum_order_quantity': random.randint(10, 100),
                'payment_terms_days': random.randint(15, 60),
                'created_at': self.faker.date_time_this_year()
            }
            suppliers.append(supplier)
        
        self.suppliers = pd.DataFrame(suppliers)
        logging.info(f"Generated {len(suppliers)} suppliers")

    def generate_vehicles(self, n_vehicles: int = 20) -> None:
        """Generate vehicle data."""
        vehicles = []
        vehicle_types = ['Van', 'Truck', 'Refrigerated Truck']
        
        for i in range(n_vehicles):
            vehicle = {
                'vehicle_id': f'V{i:03d}',
                'type': random.choice(vehicle_types),
                'capacity': random.randint(1000, 5000),
                'fuel_efficiency': round(random.uniform(5, 15), 2),
                'maintenance_cost_per_km': round(random.uniform(0.1, 0.5), 2),
                'driver_id': f'D{i:03d}',
                'status': random.choice(['Available', 'In Use', 'Maintenance']),
                'created_at': self.faker.date_time_this_year()
            }
            vehicles.append(vehicle)
        
        self.vehicles = pd.DataFrame(vehicles)
        logging.info(f"Generated {len(vehicles)} vehicles")

    def generate_events(self, start_date: datetime, end_date: datetime) -> None:
        """Generate event data."""
        events = []
        event_types = ['Promotion', 'Holiday', 'Sport Event', 'Weather Event']
        
        current_date = start_date
        while current_date <= end_date:
            # Generate 0-2 events per day
            n_events = random.randint(0, 2)
            
            for _ in range(n_events):
                event_type = random.choice(event_types)
                event = {
                    'event_id': f'E{len(events):03d}',
                    'type': event_type,
                    'name': f"{event_type} {self.faker.word().capitalize()}",
                    'start_date': current_date,
                    'end_date': current_date + timedelta(days=random.randint(1, 7)),
                    'location_id': random.choice(self.locations['location_id'].tolist()),
                    'impact_factor': round(random.uniform(0.1, 2.0), 2),
                    'created_at': self.faker.date_time_this_year()
                }
                events.append(event)
            
            current_date += timedelta(days=1)
        
        self.events = pd.DataFrame(events)
        logging.info(f"Generated {len(events)} events")

    def generate_weather_data(self, start_date: datetime, end_date: datetime) -> None:
        """Generate weather data."""
        weather_data = []
        weather_conditions = ['Sunny', 'Rainy', 'Cloudy', 'Snowy', 'Windy']
        
        current_date = start_date
        while current_date <= end_date:
            for _, location in self.locations.iterrows():
                weather = {
                    'date': current_date,
                    'location_id': location['location_id'],
                    'temperature': round(random.uniform(-10, 35), 1),
                    'humidity': random.randint(0, 100),
                    'precipitation': round(random.uniform(0, 50), 1),
                    'wind_speed': round(random.uniform(0, 30), 1),
                    'condition': random.choice(weather_conditions),
                    'created_at': self.faker.date_time_this_year()
                }
                weather_data.append(weather)
            
            current_date += timedelta(days=1)
        
        self.weather_data = pd.DataFrame(weather_data)
        logging.info(f"Generated {len(weather_data)} weather records")

    def generate_sales_data(self, start_date: datetime, end_date: datetime) -> None:
        """Generate sales data."""
        sales_data = []
        
        current_date = start_date
        while current_date <= end_date:
            for _, product in self.products.iterrows():
                for _, location in self.locations.iterrows():
                    # Base sales with seasonality
                    base_sales = 100 + 50 * np.sin(2 * np.pi * current_date.dayofyear / 365)
                    
                    # Add product and location effects
                    product_effect = hash(product['product_id']) % 50
                    location_effect = hash(location['location_id']) % 30
                    
                    # Add weather effect
                    weather = self.weather_data[
                        (self.weather_data['date'] == current_date) &
                        (self.weather_data['location_id'] == location['location_id'])
                    ]
                    weather_effect = 0
                    if not weather.empty:
                        if weather.iloc[0]['condition'] == 'Rainy':
                            weather_effect = -20
                        elif weather.iloc[0]['condition'] == 'Sunny':
                            weather_effect = 20
                    
                    # Add event effect
                    events = self.events[
                        (self.events['start_date'] <= current_date) &
                        (self.events['end_date'] >= current_date) &
                        (self.events['location_id'] == location['location_id'])
                    ]
                    event_effect = events['impact_factor'].sum() * 10 if not events.empty else 0
                    
                    # Calculate final sales
                    sales = max(0, int(base_sales + product_effect + location_effect + 
                                     weather_effect + event_effect + random.normalvariate(0, 20)))
                    
                    sale = {
                        'date': current_date,
                        'product_id': product['product_id'],
                        'location_id': location['location_id'],
                        'quantity': sales,
                        'revenue': sales * product['unit_price'],
                        'created_at': self.faker.date_time_this_year()
                    }
                    sales_data.append(sale)
            
            current_date += timedelta(days=1)
        
        self.sales_data = pd.DataFrame(sales_data)
        logging.info(f"Generated {len(sales_data)} sales records")

    def generate_inventory_data(self, start_date: datetime, end_date: datetime) -> None:
        """Generate inventory data."""
        inventory_data = []
        
        current_date = start_date
        while current_date <= end_date:
            for _, product in self.products.iterrows():
                for _, location in self.locations.iterrows():
                    # Get sales for this product and location
                    sales = self.sales_data[
                        (self.sales_data['date'] == current_date) &
                        (self.sales_data['product_id'] == product['product_id']) &
                        (self.sales_data['location_id'] == location['location_id'])
                    ]
                    sales_quantity = sales['quantity'].sum() if not sales.empty else 0
                    
                    # Calculate inventory level
                    if current_date == start_date:
                        inventory_level = random.randint(
                            product['reorder_point'],
                            product['reorder_point'] * 2
                        )
                    else:
                        previous_inventory = inventory_data[-1]['inventory_level']
                        inventory_level = max(0, previous_inventory - sales_quantity)
                        
                        # Simulate reordering
                        if inventory_level <= product['reorder_point']:
                            inventory_level += random.randint(
                                product['minimum_order_quantity'],
                                product['minimum_order_quantity'] * 2
                            )
                    
                    inventory = {
                        'date': current_date,
                        'product_id': product['product_id'],
                        'location_id': location['location_id'],
                        'inventory_level': inventory_level,
                        'reorder_point': product['reorder_point'],
                        'safety_stock': product['safety_stock'],
                        'created_at': self.faker.date_time_this_year()
                    }
                    inventory_data.append(inventory)
            
            current_date += timedelta(days=1)
        
        self.inventory_data = pd.DataFrame(inventory_data)
        logging.info(f"Generated {len(inventory_data)} inventory records")

    def generate_delivery_data(self, start_date: datetime, end_date: datetime) -> None:
        """Generate delivery data."""
        delivery_data = []
        
        current_date = start_date
        while current_date <= end_date:
            for _, vehicle in self.vehicles.iterrows():
                # Generate 0-3 deliveries per vehicle per day
                n_deliveries = random.randint(0, 3)
                
                for _ in range(n_deliveries):
                    # Select random locations for pickup and delivery
                    pickup_location = random.choice(self.locations['location_id'].tolist())
                    delivery_location = random.choice(
                        [loc for loc in self.locations['location_id'].tolist() 
                         if loc != pickup_location]
                    )
                    
                    # Calculate distance
                    pickup_coords = self.locations[
                        self.locations['location_id'] == pickup_location
                    ][['latitude', 'longitude']].iloc[0]
                    delivery_coords = self.locations[
                        self.locations['location_id'] == delivery_location
                    ][['latitude', 'longitude']].iloc[0]
                    
                    distance = geodesic(
                        (pickup_coords['latitude'], pickup_coords['longitude']),
                        (delivery_coords['latitude'], delivery_coords['longitude'])
                    ).kilometers
                    
                    # Generate delivery details
                    delivery = {
                        'delivery_id': f'D{len(delivery_data):03d}',
                        'date': current_date,
                        'vehicle_id': vehicle['vehicle_id'],
                        'pickup_location_id': pickup_location,
                        'delivery_location_id': delivery_location,
                        'distance': round(distance, 2),
                        'duration': round(distance / 50, 2),  # Assuming 50 km/h average speed
                        'status': random.choice(['Completed', 'In Transit', 'Delayed']),
                        'created_at': self.faker.date_time_this_year()
                    }
                    delivery_data.append(delivery)
            
            current_date += timedelta(days=1)
        
        self.delivery_data = pd.DataFrame(delivery_data)
        logging.info(f"Generated {len(delivery_data)} delivery records")

    def save_all_data(self) -> None:
        """Save all generated data to CSV files."""
        try:
            # Save static data
            self.products.to_csv(f'{self.output_dir}/products.csv', index=False)
            self.locations.to_csv(f'{self.output_dir}/locations.csv', index=False)
            self.suppliers.to_csv(f'{self.output_dir}/suppliers.csv', index=False)
            self.vehicles.to_csv(f'{self.output_dir}/vehicles.csv', index=False)
            self.events.to_csv(f'{self.output_dir}/events.csv', index=False)
            
            # Save time-series data
            self.weather_data.to_csv(f'{self.output_dir}/weather.csv', index=False)
            self.sales_data.to_csv(f'{self.output_dir}/sales.csv', index=False)
            self.inventory_data.to_csv(f'{self.output_dir}/inventory.csv', index=False)
            self.delivery_data.to_csv(f'{self.output_dir}/deliveries.csv', index=False)
            
            logging.info("All data saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            raise

    def load_data(self) -> None:
        """Load all data from CSV files."""
        try:
            # Load static data
            self.products = pd.read_csv(f'{self.output_dir}/products.csv')
            self.locations = pd.read_csv(f'{self.output_dir}/locations.csv')
            self.suppliers = pd.read_csv(f'{self.output_dir}/suppliers.csv')
            self.vehicles = pd.read_csv(f'{self.output_dir}/vehicles.csv')
            self.events = pd.read_csv(f'{self.output_dir}/events.csv')
            
            # Load time-series data
            self.weather_data = pd.read_csv(f'{self.output_dir}/weather.csv')
            self.sales_data = pd.read_csv(f'{self.output_dir}/sales.csv')
            self.inventory_data = pd.read_csv(f'{self.output_dir}/inventory.csv')
            self.delivery_data = pd.read_csv(f'{self.output_dir}/deliveries.csv')
            
            logging.info("All data loaded successfully")
            
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create data generator
    generator = DataGenerator()
    
    # Generate data for the last year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    generator.generate_all_data(start_date, end_date) 