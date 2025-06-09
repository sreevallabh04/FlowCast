import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from utils.config import Config
from .demand_model import DemandPredictor

logger = logging.getLogger(__name__)

class ExpiryPredictor:
    def __init__(self):
        self.demand_predictor = DemandPredictor()
    
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