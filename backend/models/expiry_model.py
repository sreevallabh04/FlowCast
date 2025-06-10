import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from utils.config import Config
from .demand_model import DemandPredictor
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProductShelfLife:
    product_id: str
    shelf_life_days: int
    decay_rate: float  # Daily decay rate
    min_quality_threshold: float  # Below this threshold, product is considered expired
    donation_threshold: float  # Below this threshold, consider for donation

class ExpiryModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.product_shelf_lives = {}
        self.donation_partners = []
        self.version = "1.0.0"
        self.demand_predictor = DemandPredictor()

    def add_product_shelf_life(self, product_id: str, shelf_life_days: int, 
                             decay_rate: float, min_quality_threshold: float = 0.7,
                             donation_threshold: float = 0.5):
        """Add or update product shelf life information."""
        self.product_shelf_lives[product_id] = ProductShelfLife(
            product_id=product_id,
            shelf_life_days=shelf_life_days,
            decay_rate=decay_rate,
            min_quality_threshold=min_quality_threshold,
            donation_threshold=donation_threshold
        )

    def add_donation_partner(self, partner_id: str, name: str, 
                           accepted_product_types: List[str],
                           pickup_lead_time_hours: int):
        """Add a donation partner."""
        self.donation_partners.append({
            'partner_id': partner_id,
            'name': name,
            'accepted_product_types': accepted_product_types,
            'pickup_lead_time_hours': pickup_lead_time_hours
        })

    def calculate_quality_score(self, product_id: str, days_since_production: int,
                              storage_conditions: Dict) -> float:
        """Calculate product quality score based on age and storage conditions."""
        if product_id not in self.product_shelf_lives:
            raise ValueError(f"No shelf life data for product {product_id}")

        product = self.product_shelf_lives[product_id]
        
        # Base decay
        base_quality = np.exp(-product.decay_rate * days_since_production)
        
        # Temperature impact
        temp_factor = 1.0
        if 'temperature' in storage_conditions:
            optimal_temp = storage_conditions.get('optimal_temperature', 4)  # Default 4°C
            current_temp = storage_conditions['temperature']
            temp_factor = np.exp(-0.1 * abs(current_temp - optimal_temp))
        
        # Humidity impact
        humidity_factor = 1.0
        if 'humidity' in storage_conditions:
            optimal_humidity = storage_conditions.get('optimal_humidity', 60)  # Default 60%
            current_humidity = storage_conditions['humidity']
            humidity_factor = np.exp(-0.05 * abs(current_humidity - optimal_humidity))
        
        # Calculate final quality score
        quality_score = base_quality * temp_factor * humidity_factor
        
        return max(0.0, min(1.0, quality_score))

    def predict_expiry(self, inventory_data: pd.DataFrame) -> pd.DataFrame:
        """Predict expiry dates and quality scores for inventory items."""
        try:
            results = []
            
            for _, row in inventory_data.iterrows():
                product_id = row['product_id']
                production_date = pd.to_datetime(row['production_date'])
                current_date = pd.to_datetime(row['current_date'])
                storage_conditions = {
                    'temperature': row.get('temperature', 4),
                    'humidity': row.get('humidity', 60)
                }
                
                days_since_production = (current_date - production_date).days
                
                # Calculate current quality
                current_quality = self.calculate_quality_score(
                    product_id, days_since_production, storage_conditions
                )
                
                # Predict days until expiry
                days_until_expiry = 0
                while current_quality > self.product_shelf_lives[product_id].min_quality_threshold:
                    days_until_expiry += 1
                    future_quality = self.calculate_quality_score(
                        product_id, days_since_production + days_until_expiry, storage_conditions
                    )
                    if future_quality <= self.product_shelf_lives[product_id].min_quality_threshold:
                        break
                
                # Check if donation is possible
                donation_recommendation = None
                if current_quality <= self.product_shelf_lives[product_id].donation_threshold:
                    for partner in self.donation_partners:
                        if product_id in partner['accepted_product_types']:
                            donation_recommendation = {
                                'partner_id': partner['partner_id'],
                                'partner_name': partner['name'],
                                'pickup_lead_time_hours': partner['pickup_lead_time_hours']
                            }
                            break
                
                results.append({
                    'product_id': product_id,
                    'current_quality': current_quality,
                    'days_until_expiry': days_until_expiry,
                    'expiry_date': (current_date + timedelta(days=days_until_expiry)).isoformat(),
                    'donation_recommendation': donation_recommendation
                })
            
            return pd.DataFrame(results)
            
        except Exception as e:
            self.logger.error(f"Error predicting expiry: {str(e)}")
            raise

    def optimize_waste_reduction(self, inventory_data: pd.DataFrame) -> Dict:
        """Generate waste reduction recommendations."""
        try:
            expiry_predictions = self.predict_expiry(inventory_data)
            
            recommendations = {
                'immediate_actions': [],
                'short_term_actions': [],
                'long_term_actions': []
            }
            
            # Immediate actions (expiring within 24 hours)
            immediate_expiry = expiry_predictions[
                expiry_predictions['days_until_expiry'] <= 1
            ]
            
            for _, row in immediate_expiry.iterrows():
                if row['donation_recommendation']:
                    recommendations['immediate_actions'].append({
                        'action': 'donate',
                        'product_id': row['product_id'],
                        'partner': row['donation_recommendation'],
                        'urgency': 'high'
                    })
                else:
                    recommendations['immediate_actions'].append({
                        'action': 'discount',
                        'product_id': row['product_id'],
                        'discount_percentage': 50,
                        'urgency': 'high'
                    })
            
            # Short-term actions (expiring within 7 days)
            short_term_expiry = expiry_predictions[
                (expiry_predictions['days_until_expiry'] > 1) &
                (expiry_predictions['days_until_expiry'] <= 7)
            ]
            
            for _, row in short_term_expiry.iterrows():
                recommendations['short_term_actions'].append({
                    'action': 'promote',
                    'product_id': row['product_id'],
                    'promotion_type': 'bundle' if row['current_quality'] > 0.8 else 'discount',
                    'discount_percentage': 30 if row['current_quality'] <= 0.8 else 0,
                    'urgency': 'medium'
                })
            
            # Long-term actions (expiring within 30 days)
            long_term_expiry = expiry_predictions[
                (expiry_predictions['days_until_expiry'] > 7) &
                (expiry_predictions['days_until_expiry'] <= 30)
            ]
            
            for _, row in long_term_expiry.iterrows():
                recommendations['long_term_actions'].append({
                    'action': 'adjust_order',
                    'product_id': row['product_id'],
                    'adjustment_type': 'reduce',
                    'percentage': 20,
                    'urgency': 'low'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error optimizing waste reduction: {str(e)}")
            raise

    def get_waste_metrics(self, inventory_data: pd.DataFrame) -> Dict:
        """Calculate waste-related metrics."""
        try:
            expiry_predictions = self.predict_expiry(inventory_data)
            
            total_units = len(inventory_data)
            expiring_units = len(expiry_predictions[
                expiry_predictions['days_until_expiry'] <= 7
            ])
            donatable_units = len(expiry_predictions[
                expiry_predictions['donation_recommendation'].notna()
            ])
            
            return {
                'total_units': total_units,
                'expiring_units': expiring_units,
                'expiry_rate': expiring_units / total_units if total_units > 0 else 0,
                'donatable_units': donatable_units,
                'donation_rate': donatable_units / total_units if total_units > 0 else 0,
                'average_quality': expiry_predictions['current_quality'].mean(),
                'average_days_until_expiry': expiry_predictions['days_until_expiry'].mean()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating waste metrics: {str(e)}")
            raise

    def _calculate_freshness_decay(self, product, days_remaining, storage_conditions):
        """Calculate freshness decay based on product type and storage conditions."""
        try:
            # Base decay rates by product category
            base_decay_rates = {
                'dairy': 0.15,  # 15% decay per day
                'produce': 0.25,
                'meat': 0.20,
                'bakery': 0.30,
                'frozen': 0.05,
                'canned': 0.02
            }
            
            # Storage condition multipliers
            condition_multipliers = {
                'optimal': 0.8,
                'normal': 1.0,
                'suboptimal': 1.2
            }
            
            # Get base decay rate for product category
            base_rate = base_decay_rates.get(product['category'], 0.1)
            
            # Apply storage condition multiplier
            condition = storage_conditions.get('temperature', 'normal')
            multiplier = condition_multipliers.get(condition, 1.0)
            
            # Calculate decay
            decay_rate = base_rate * multiplier
            
            # Calculate freshness score (0 to 1)
            freshness = max(0, 1 - (decay_rate * (product['shelf_life'] - days_remaining)))
            
            return freshness
        except Exception as e:
            logger.error(f"Error calculating freshness decay: {str(e)}")
            raise
    
    def _calculate_donation_value(self, product, freshness, quantity):
        """Calculate donation value based on product value and freshness."""
        try:
            # Base donation value (percentage of original value)
            base_value = product['unit_price'] * quantity
            
            # Freshness multiplier (higher freshness = higher value)
            freshness_multiplier = 0.5 + (freshness * 0.5)  # 0.5 to 1.0
            
            # Category-specific multipliers
            category_multipliers = {
                'dairy': 0.7,
                'produce': 0.8,
                'meat': 0.6,
                'bakery': 0.9,
                'frozen': 0.7,
                'canned': 0.5
            }
            
            category_multiplier = category_multipliers.get(product['category'], 0.6)
            
            # Calculate final donation value
            donation_value = base_value * freshness_multiplier * category_multiplier
            
            return donation_value
        except Exception as e:
            logger.error(f"Error calculating donation value: {str(e)}")
            raise
    
    def _get_donation_partners(self, location, product_type):
        """Get available donation partners for a location and product type."""
        try:
            # This would typically query a database of donation partners
            # For now, return placeholder data
            return [
                {
                    'id': 'food_bank_1',
                    'name': 'Local Food Bank',
                    'distance': 5.2,  # km
                    'capacity': 1000,  # kg
                    'accepted_types': ['dairy', 'produce', 'bakery']
                },
                {
                    'id': 'shelter_1',
                    'name': 'Homeless Shelter',
                    'distance': 3.8,
                    'capacity': 500,
                    'accepted_types': ['dairy', 'produce', 'meat', 'bakery']
                }
            ]
        except Exception as e:
            logger.error(f"Error getting donation partners: {str(e)}")
            raise
    
    def predict(self, products, locations, current_date=None):
        """Predict expiry and recommend actions for products."""
        try:
            if current_date is None:
                current_date = datetime.now()
            
            predictions = []
            
            for product in products:
                for location in locations:
                    # Calculate days remaining until expiry
                    days_remaining = (product['expiry_date'] - current_date).days
                    
                    if days_remaining <= 0:
                        # Product has already expired
                        action = 'dispose'
                        action_reason = 'Product has expired'
                        donation_value = 0
                        donation_partners = []
                    else:
                        # Calculate freshness
                        freshness = self._calculate_freshness_decay(
                            product,
                            days_remaining,
                            location.get('storage_conditions', {})
                        )
                        
                        # Get demand predictions
                        demand_predictions = self.demand_predictor.predict(
                            product_ids=[product['id']],
                            store_ids=[location['id']],
                            forecast_horizon=days_remaining
                        )
                        
                        # Calculate expected demand
                        expected_demand = sum(
                            pred['predicted_demand'] 
                            for pred in demand_predictions
                        )
                        
                        # Determine action based on freshness and demand
                        if freshness < 0.3:
                            # Product is too close to expiry
                            action = 'markdown'
                            action_reason = 'Low freshness score'
                            donation_value = self._calculate_donation_value(
                                product, freshness, product['quantity']
                            )
                            donation_partners = self._get_donation_partners(
                                location, product['category']
                            )
                        elif expected_demand < product['quantity']:
                            # Excess inventory
                            action = 'markdown'
                            action_reason = 'Expected demand below current inventory'
                            donation_value = self._calculate_donation_value(
                                product, freshness, 
                                product['quantity'] - expected_demand
                            )
                            donation_partners = self._get_donation_partners(
                                location, product['category']
                            )
                        else:
                            # Normal operation
                            action = 'maintain'
                            action_reason = 'Normal inventory levels'
                            donation_value = 0
                            donation_partners = []
                    
                    predictions.append({
                        'product_id': product['id'],
                        'location_id': location['id'],
                        'days_remaining': days_remaining,
                        'freshness_score': float(freshness) if 'freshness' in locals() else 0,
                        'expected_demand': float(expected_demand) if 'expected_demand' in locals() else 0,
                        'action': action,
                        'action_reason': action_reason,
                        'donation_value': float(donation_value),
                        'donation_partners': donation_partners
                    })
            
            return predictions
        except Exception as e:
            logger.error(f"Error predicting expiry: {str(e)}")
            raise
    
    def get_metrics(self, start_date, end_date):
        """Get expiry prediction metrics for a given date range."""
        try:
            # This would typically fetch actual vs predicted values from a database
            # For now, return placeholder metrics
            return {
                'waste_reduction': 0.85,  # 85% reduction in waste
                'donation_value': 25000,  # $25,000 in donations
                'markdown_revenue': 15000,  # $15,000 from markdowns
                'freshness_score': 0.92,  # Average freshness score
                'donation_partners': 5  # Number of active donation partners
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize model
    model = ExpiryModel()
    
    # Add product shelf lives
    model.add_product_shelf_life(
        product_id="PROD001",
        shelf_life_days=14,
        decay_rate=0.1,
        min_quality_threshold=0.7,
        donation_threshold=0.5
    )
    
    # Add donation partner
    model.add_donation_partner(
        partner_id="PART001",
        name="Local Food Bank",
        accepted_product_types=["PROD001", "PROD002"],
        pickup_lead_time_hours=24
    )
    
    # Create sample inventory data
    inventory_data = pd.DataFrame([
        {
            'product_id': 'PROD001',
            'production_date': '2024-01-01',
            'current_date': '2024-01-10',
            'temperature': 4,
            'humidity': 60
        }
    ])
    
    # Get predictions and recommendations
    expiry_predictions = model.predict_expiry(inventory_data)
    waste_recommendations = model.optimize_waste_reduction(inventory_data)
    waste_metrics = model.get_waste_metrics(inventory_data)
    
    print("Expiry Predictions:", expiry_predictions)
    print("\nWaste Reduction Recommendations:", waste_recommendations)
    print("\nWaste Metrics:", waste_metrics) 