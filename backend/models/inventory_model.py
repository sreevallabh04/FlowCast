import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from utils.config import Config
from .demand_model import DemandPredictor

logger = logging.getLogger(__name__)

class InventoryOptimizer:
    def __init__(self):
        self.demand_predictor = DemandPredictor()
    
    def _calculate_safety_stock(self, demand_mean, demand_std, lead_time, service_level=0.95):
        """Calculate safety stock using the service level approach."""
        z_score = 1.96  # 95% service level
        safety_stock = z_score * demand_std * np.sqrt(lead_time)
        return safety_stock
    
    def _calculate_reorder_point(self, demand_mean, lead_time, safety_stock):
        """Calculate reorder point based on lead time demand and safety stock."""
        lead_time_demand = demand_mean * lead_time
        reorder_point = lead_time_demand + safety_stock
        return reorder_point
    
    def _calculate_economic_order_quantity(self, annual_demand, ordering_cost, holding_cost):
        """Calculate Economic Order Quantity (EOQ)."""
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        return eoq
    
    def optimize(self, product_ids, store_ids, constraints=None):
        """Optimize inventory levels for given products and stores."""
        try:
            if constraints is None:
                constraints = {}
            
            # Get demand predictions
            demand_predictions = self.demand_predictor.predict(
                product_ids=product_ids,
                store_ids=store_ids,
                forecast_horizon=30  # 30 days for better statistics
            )
            
            # Convert predictions to DataFrame for easier analysis
            df = pd.DataFrame(demand_predictions)
            
            optimization_results = []
            
            for product_id in product_ids:
                for store_id in store_ids:
                    # Filter predictions for this product-store combination
                    product_store_data = df[
                        (df['product_id'] == product_id) & 
                        (df['store_id'] == store_id)
                    ]
                    
                    # Calculate demand statistics
                    demand_mean = product_store_data['predicted_demand'].mean()
                    demand_std = product_store_data['predicted_demand'].std()
                    
                    # Get constraints for this product
                    product_constraints = constraints.get(product_id, {})
                    lead_time = product_constraints.get('lead_time', 7)  # days
                    service_level = product_constraints.get('service_level', 0.95)
                    ordering_cost = product_constraints.get('ordering_cost', 100)
                    holding_cost = product_constraints.get('holding_cost', 0.2)  # 20% of unit cost
                    
                    # Calculate optimal inventory parameters
                    safety_stock = self._calculate_safety_stock(
                        demand_mean, demand_std, lead_time, service_level
                    )
                    
                    reorder_point = self._calculate_reorder_point(
                        demand_mean, lead_time, safety_stock
                    )
                    
                    annual_demand = demand_mean * 365
                    eoq = self._calculate_economic_order_quantity(
                        annual_demand, ordering_cost, holding_cost
                    )
                    
                    # Calculate current inventory position
                    current_stock = product_constraints.get('current_stock', 0)
                    in_transit = product_constraints.get('in_transit', 0)
                    inventory_position = current_stock + in_transit
                    
                    # Determine if reorder is needed
                    needs_reorder = inventory_position <= reorder_point
                    order_quantity = eoq if needs_reorder else 0
                    
                    optimization_results.append({
                        'product_id': product_id,
                        'store_id': store_id,
                        'safety_stock': float(safety_stock),
                        'reorder_point': float(reorder_point),
                        'economic_order_quantity': float(eoq),
                        'current_stock': float(current_stock),
                        'in_transit': float(in_transit),
                        'inventory_position': float(inventory_position),
                        'needs_reorder': needs_reorder,
                        'order_quantity': float(order_quantity),
                        'service_level': service_level,
                        'lead_time': lead_time
                    })
            
            return optimization_results
        except Exception as e:
            logger.error(f"Error optimizing inventory: {str(e)}")
            raise
    
    def get_metrics(self, start_date, end_date):
        """Get inventory optimization metrics for a given date range."""
        try:
            # This would typically fetch actual vs optimized values from a database
            # For now, return placeholder metrics
            return {
                'service_level': 0.95,
                'inventory_turns': 12.5,
                'stockout_rate': 0.02,
                'carrying_cost': 0.15,
                'order_frequency': 7.5  # orders per month
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            raise 