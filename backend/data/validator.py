import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import os
from scipy import stats
import warnings
from dataclasses import dataclass
from enum import Enum

warnings.filterwarnings('ignore')

class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class ValidationResult:
    """Class for storing validation results."""
    level: ValidationLevel
    message: str
    details: Optional[Dict] = None

class DataValidator:
    def __init__(self, data_dir: str = 'data/generated', output_dir: str = 'data/validation'):
        """Initialize the data validator with input and output directories."""
        self.data_dir = data_dir
        self.output_dir = output_dir
        
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
        
        # Initialize validation results
        self.validation_results = []
        
        # Set up logging
        self.logger = logging.getLogger(__name__)

    def load_data(self) -> None:
        """Load all data from CSV files."""
        try:
            # Load static data
            self.products = pd.read_csv(f'{self.data_dir}/products.csv')
            self.locations = pd.read_csv(f'{self.data_dir}/locations.csv')
            self.suppliers = pd.read_csv(f'{self.data_dir}/suppliers.csv')
            self.vehicles = pd.read_csv(f'{self.data_dir}/vehicles.csv')
            self.events = pd.read_csv(f'{self.data_dir}/events.csv')
            
            # Load time-series data
            self.weather_data = pd.read_csv(f'{self.data_dir}/weather.csv')
            self.sales_data = pd.read_csv(f'{self.data_dir}/sales.csv')
            self.inventory_data = pd.read_csv(f'{self.data_dir}/inventory.csv')
            self.delivery_data = pd.read_csv(f'{self.data_dir}/deliveries.csv')
            
            # Convert date columns to datetime
            for df in [self.events, self.weather_data, self.sales_data, 
                      self.inventory_data, self.delivery_data]:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                if 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at'])
            
            self.logger.info("All data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def validate_all(self) -> List[ValidationResult]:
        """Run all validation checks."""
        try:
            # Clear previous validation results
            self.validation_results = []
            
            # Validate static data
            self._validate_products()
            self._validate_locations()
            self._validate_suppliers()
            self._validate_vehicles()
            self._validate_events()
            
            # Validate time-series data
            self._validate_weather()
            self._validate_sales()
            self._validate_inventory()
            self._validate_deliveries()
            
            # Validate data relationships
            self._validate_relationships()
            
            # Save validation results
            self._save_validation_results()
            
            return self.validation_results
            
        except Exception as e:
            self.logger.error(f"Error during validation: {str(e)}")
            raise

    def _add_validation_result(self, level: ValidationLevel, message: str, details: Optional[Dict] = None) -> None:
        """Add a validation result to the list."""
        result = ValidationResult(level=level, message=message, details=details)
        self.validation_results.append(result)
        
        # Log the validation result
        if level == ValidationLevel.INFO:
            self.logger.info(message)
        elif level == ValidationLevel.WARNING:
            self.logger.warning(message)
        elif level == ValidationLevel.ERROR:
            self.logger.error(message)
        elif level == ValidationLevel.CRITICAL:
            self.logger.critical(message)

    def _validate_products(self) -> None:
        """Validate products data."""
        # Check for missing values
        missing_values = self.products.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Products data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for duplicate product IDs
        duplicates = self.products['product_id'].duplicated()
        if duplicates.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Products data contains duplicate product IDs",
                {"duplicate_ids": self.products[duplicates]['product_id'].tolist()}
            )
        
        # Check for invalid numeric values
        numeric_cols = ['unit_price', 'unit_weight', 'shelf_life_days', 
                       'reorder_point', 'safety_stock', 'lead_time_days']
        for col in numeric_cols:
            if (self.products[col] <= 0).any():
                self._add_validation_result(
                    ValidationLevel.ERROR,
                    f"Products data contains non-positive {col}",
                    {"invalid_values": self.products[self.products[col] <= 0][['product_id', col]].to_dict()}
                )

    def _validate_locations(self) -> None:
        """Validate locations data."""
        # Check for missing values
        missing_values = self.locations.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Locations data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for duplicate location IDs
        duplicates = self.locations['location_id'].duplicated()
        if duplicates.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Locations data contains duplicate location IDs",
                {"duplicate_ids": self.locations[duplicates]['location_id'].tolist()}
            )
        
        # Check for invalid coordinates
        invalid_coords = (
            (self.locations['latitude'] < -90) | 
            (self.locations['latitude'] > 90) |
            (self.locations['longitude'] < -180) | 
            (self.locations['longitude'] > 180)
        )
        if invalid_coords.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Locations data contains invalid coordinates",
                {"invalid_coords": self.locations[invalid_coords][['location_id', 'latitude', 'longitude']].to_dict()}
            )

    def _validate_suppliers(self) -> None:
        """Validate suppliers data."""
        # Check for missing values
        missing_values = self.suppliers.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Suppliers data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for duplicate supplier IDs
        duplicates = self.suppliers['supplier_id'].duplicated()
        if duplicates.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Suppliers data contains duplicate supplier IDs",
                {"duplicate_ids": self.suppliers[duplicates]['supplier_id'].tolist()}
            )
        
        # Check for invalid numeric values
        numeric_cols = ['lead_time_days', 'minimum_order_quantity', 'payment_terms_days']
        for col in numeric_cols:
            if (self.suppliers[col] <= 0).any():
                self._add_validation_result(
                    ValidationLevel.ERROR,
                    f"Suppliers data contains non-positive {col}",
                    {"invalid_values": self.suppliers[self.suppliers[col] <= 0][['supplier_id', col]].to_dict()}
                )

    def _validate_vehicles(self) -> None:
        """Validate vehicles data."""
        # Check for missing values
        missing_values = self.vehicles.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Vehicles data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for duplicate vehicle IDs
        duplicates = self.vehicles['vehicle_id'].duplicated()
        if duplicates.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Vehicles data contains duplicate vehicle IDs",
                {"duplicate_ids": self.vehicles[duplicates]['vehicle_id'].tolist()}
            )
        
        # Check for invalid numeric values
        numeric_cols = ['capacity', 'fuel_efficiency', 'maintenance_cost_per_km']
        for col in numeric_cols:
            if (self.vehicles[col] <= 0).any():
                self._add_validation_result(
                    ValidationLevel.ERROR,
                    f"Vehicles data contains non-positive {col}",
                    {"invalid_values": self.vehicles[self.vehicles[col] <= 0][['vehicle_id', col]].to_dict()}
                )

    def _validate_events(self) -> None:
        """Validate events data."""
        # Check for missing values
        missing_values = self.events.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Events data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for duplicate event IDs
        duplicates = self.events['event_id'].duplicated()
        if duplicates.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Events data contains duplicate event IDs",
                {"duplicate_ids": self.events[duplicates]['event_id'].tolist()}
            )
        
        # Check for invalid dates
        invalid_dates = self.events['end_date'] < self.events['start_date']
        if invalid_dates.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Events data contains invalid date ranges",
                {"invalid_dates": self.events[invalid_dates][['event_id', 'start_date', 'end_date']].to_dict()}
            )

    def _validate_weather(self) -> None:
        """Validate weather data."""
        # Check for missing values
        missing_values = self.weather_data.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Weather data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for invalid temperature values
        invalid_temp = (self.weather_data['temperature'] < -50) | (self.weather_data['temperature'] > 50)
        if invalid_temp.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Weather data contains invalid temperature values",
                {"invalid_values": self.weather_data[invalid_temp][['date', 'location_id', 'temperature']].to_dict()}
            )
        
        # Check for invalid humidity values
        invalid_humidity = (self.weather_data['humidity'] < 0) | (self.weather_data['humidity'] > 100)
        if invalid_humidity.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Weather data contains invalid humidity values",
                {"invalid_values": self.weather_data[invalid_humidity][['date', 'location_id', 'humidity']].to_dict()}
            )

    def _validate_sales(self) -> None:
        """Validate sales data."""
        # Check for missing values
        missing_values = self.sales_data.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Sales data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for negative quantities
        negative_quantities = self.sales_data['quantity'] < 0
        if negative_quantities.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Sales data contains negative quantities",
                {"invalid_values": self.sales_data[negative_quantities][['date', 'product_id', 'location_id', 'quantity']].to_dict()}
            )
        
        # Check for negative revenue
        negative_revenue = self.sales_data['revenue'] < 0
        if negative_revenue.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Sales data contains negative revenue",
                {"invalid_values": self.sales_data[negative_revenue][['date', 'product_id', 'location_id', 'revenue']].to_dict()}
            )

    def _validate_inventory(self) -> None:
        """Validate inventory data."""
        # Check for missing values
        missing_values = self.inventory_data.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Inventory data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for negative inventory levels
        negative_inventory = self.inventory_data['inventory_level'] < 0
        if negative_inventory.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Inventory data contains negative inventory levels",
                {"invalid_values": self.inventory_data[negative_inventory][['date', 'product_id', 'location_id', 'inventory_level']].to_dict()}
            )
        
        # Check for invalid reorder points
        invalid_reorder = self.inventory_data['reorder_point'] <= 0
        if invalid_reorder.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Inventory data contains invalid reorder points",
                {"invalid_values": self.inventory_data[invalid_reorder][['date', 'product_id', 'location_id', 'reorder_point']].to_dict()}
            )

    def _validate_deliveries(self) -> None:
        """Validate delivery data."""
        # Check for missing values
        missing_values = self.delivery_data.isnull().sum()
        if missing_values.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Delivery data contains missing values",
                {"missing_values": missing_values[missing_values > 0].to_dict()}
            )
        
        # Check for duplicate delivery IDs
        duplicates = self.delivery_data['delivery_id'].duplicated()
        if duplicates.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Delivery data contains duplicate delivery IDs",
                {"duplicate_ids": self.delivery_data[duplicates]['delivery_id'].tolist()}
            )
        
        # Check for invalid distances
        invalid_distance = self.delivery_data['distance'] <= 0
        if invalid_distance.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Delivery data contains invalid distances",
                {"invalid_values": self.delivery_data[invalid_distance][['delivery_id', 'distance']].to_dict()}
            )
        
        # Check for invalid durations
        invalid_duration = self.delivery_data['duration'] <= 0
        if invalid_duration.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Delivery data contains invalid durations",
                {"invalid_values": self.delivery_data[invalid_duration][['delivery_id', 'duration']].to_dict()}
            )

    def _validate_relationships(self) -> None:
        """Validate relationships between different data tables."""
        # Check product-supplier relationships
        invalid_products = ~self.products['supplier_id'].isin(self.suppliers['supplier_id'])
        if invalid_products.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Products data contains invalid supplier references",
                {"invalid_products": self.products[invalid_products][['product_id', 'supplier_id']].to_dict()}
            )
        
        # Check location references in events
        invalid_events = ~self.events['location_id'].isin(self.locations['location_id'])
        if invalid_events.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Events data contains invalid location references",
                {"invalid_events": self.events[invalid_events][['event_id', 'location_id']].to_dict()}
            )
        
        # Check location references in sales
        invalid_sales = ~self.sales_data['location_id'].isin(self.locations['location_id'])
        if invalid_sales.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Sales data contains invalid location references",
                {"invalid_sales": self.sales_data[invalid_sales][['date', 'product_id', 'location_id']].to_dict()}
            )
        
        # Check product references in sales
        invalid_sales = ~self.sales_data['product_id'].isin(self.products['product_id'])
        if invalid_sales.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Sales data contains invalid product references",
                {"invalid_sales": self.sales_data[invalid_sales][['date', 'product_id', 'location_id']].to_dict()}
            )
        
        # Check vehicle references in deliveries
        invalid_deliveries = ~self.delivery_data['vehicle_id'].isin(self.vehicles['vehicle_id'])
        if invalid_deliveries.any():
            self._add_validation_result(
                ValidationLevel.ERROR,
                "Delivery data contains invalid vehicle references",
                {"invalid_deliveries": self.delivery_data[invalid_deliveries][['delivery_id', 'vehicle_id']].to_dict()}
            )

    def _save_validation_results(self) -> None:
        """Save validation results to a JSON file."""
        try:
            results = [
                {
                    "level": result.level.value,
                    "message": result.message,
                    "details": result.details
                }
                for result in self.validation_results
            ]
            
            with open(f'{self.output_dir}/validation_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info("Validation results saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving validation results: {str(e)}")
            raise

    def get_validation_summary(self) -> Dict:
        """Get a summary of validation results."""
        summary = {
            "total_checks": len(self.validation_results),
            "info": len([r for r in self.validation_results if r.level == ValidationLevel.INFO]),
            "warnings": len([r for r in self.validation_results if r.level == ValidationLevel.WARNING]),
            "errors": len([r for r in self.validation_results if r.level == ValidationLevel.ERROR]),
            "critical": len([r for r in self.validation_results if r.level == ValidationLevel.CRITICAL])
        }
        
        return summary

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create data validator
    validator = DataValidator()
    
    # Load and validate data
    validator.load_data()
    results = validator.validate_all()
    
    # Print validation summary
    summary = validator.get_validation_summary()
    print("\nValidation Summary:")
    print(f"Total checks: {summary['total_checks']}")
    print(f"Info: {summary['info']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Errors: {summary['errors']}")
    print(f"Critical: {summary['critical']}") 