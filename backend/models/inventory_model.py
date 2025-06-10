import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from scipy import stats
from utils.config import Config
from .demand_model import DemandPredictor

logger = logging.getLogger(__name__)

class InventoryModel:
    def __init__(self, service_level: float = 0.95):
        """
        Initialize the inventory optimization model.
        
        Args:
            service_level: Target service level (probability of not stocking out)
        """
        self.service_level = service_level
        self.logger = logging.getLogger(__name__)
        self.version = "1.0.0"
        
        # Z-score for service level
        self.z_score = stats.norm.ppf(service_level)

    def calculate_safety_stock(self, 
                             lead_time_days: float,
                             demand_mean: float,
                             demand_std: float,
                             lead_time_std: float = 0) -> float:
        """
        Calculate safety stock using the formula:
        SS = Z * sqrt(LT * σd² + d² * σLT²)
        
        Where:
        - Z is the z-score for desired service level
        - LT is the lead time in days
        - σd is the standard deviation of daily demand
        - d is the mean daily demand
        - σLT is the standard deviation of lead time
        """
        try:
            # Calculate safety stock
            safety_stock = self.z_score * np.sqrt(
                lead_time_days * (demand_std ** 2) + 
                (demand_mean ** 2) * (lead_time_std ** 2)
            )
            
            return max(0, safety_stock)
            
        except Exception as e:
            self.logger.error(f"Error calculating safety stock: {str(e)}")
            raise

    def calculate_reorder_point(self,
                              safety_stock: float,
                              lead_time_days: float,
                              demand_mean: float) -> float:
        """
        Calculate reorder point using the formula:
        ROP = (d * LT) + SS
        
        Where:
        - d is the mean daily demand
        - LT is the lead time in days
        - SS is the safety stock
        """
        try:
            reorder_point = (demand_mean * lead_time_days) + safety_stock
            return max(0, reorder_point)
            
        except Exception as e:
            self.logger.error(f"Error calculating reorder point: {str(e)}")
            raise

    def calculate_economic_order_quantity(self,
                                        annual_demand: float,
                                        order_cost: float,
                                        holding_cost_per_unit: float) -> float:
        """
        Calculate Economic Order Quantity (EOQ) using the formula:
        EOQ = sqrt((2 * D * S) / H)
        
        Where:
        - D is the annual demand
        - S is the order cost
        - H is the holding cost per unit
        """
        try:
            eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)
            return max(0, eoq)
            
        except Exception as e:
            self.logger.error(f"Error calculating EOQ: {str(e)}")
            raise

    def optimize_inventory(self, 
                          historical_data: pd.DataFrame,
                          current_inventory: Dict[str, float],
                          lead_times: Dict[str, float],
                          costs: Dict[str, Dict[str, float]]) -> Dict:
        """
        Optimize inventory levels for multiple products.
        
        Args:
            historical_data: DataFrame with columns [product_id, date, demand]
            current_inventory: Dict of current inventory levels by product_id
            lead_times: Dict of lead times in days by product_id
            costs: Dict of costs by product_id with keys [order_cost, holding_cost]
        """
        try:
            results = {}
            
            for product_id in current_inventory.keys():
                # Get product-specific data
                product_data = historical_data[historical_data['product_id'] == product_id]
                
                if len(product_data) == 0:
                    self.logger.warning(f"No historical data for product {product_id}")
                    continue
                
                # Calculate demand statistics
                daily_demand = product_data.groupby('date')['demand'].sum()
                demand_mean = daily_demand.mean()
                demand_std = daily_demand.std()
                
                # Get product-specific parameters
                lead_time = lead_times.get(product_id, 0)
                order_cost = costs.get(product_id, {}).get('order_cost', 0)
                holding_cost = costs.get(product_id, {}).get('holding_cost', 0)
                
                # Calculate optimal levels
                safety_stock = self.calculate_safety_stock(
                    lead_time_days=lead_time,
                    demand_mean=demand_mean,
                    demand_std=demand_std
                )
                
                reorder_point = self.calculate_reorder_point(
                    safety_stock=safety_stock,
                    lead_time_days=lead_time,
                    demand_mean=demand_mean
                )
                
                eoq = self.calculate_economic_order_quantity(
                    annual_demand=demand_mean * 365,
                    order_cost=order_cost,
                    holding_cost_per_unit=holding_cost
                )
                
                # Calculate current inventory position
                current_level = current_inventory.get(product_id, 0)
                inventory_position = current_level
                
                # Generate recommendations
                recommendations = []
                
                if inventory_position <= reorder_point:
                    order_quantity = max(eoq, reorder_point - inventory_position)
                    recommendations.append({
                        'action': 'order',
                        'quantity': order_quantity,
                        'urgency': 'high' if inventory_position < safety_stock else 'medium'
                    })
                
                if inventory_position > (reorder_point + eoq):
                    excess = inventory_position - (reorder_point + eoq)
                    recommendations.append({
                        'action': 'reduce',
                        'quantity': excess,
                        'urgency': 'low'
                    })
                
                # Store results
                results[product_id] = {
                    'current_level': current_level,
                    'safety_stock': safety_stock,
                    'reorder_point': reorder_point,
                    'economic_order_quantity': eoq,
                    'recommendations': recommendations,
                    'metrics': {
                        'service_level': self.service_level,
                        'lead_time': lead_time,
                        'demand_mean': demand_mean,
                        'demand_std': demand_std
                    }
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error optimizing inventory: {str(e)}")
            raise

    def calculate_inventory_metrics(self,
                                  historical_data: pd.DataFrame,
                                  current_inventory: Dict[str, float]) -> Dict:
        """
        Calculate key inventory performance metrics.
        """
        try:
            metrics = {
                'total_products': len(current_inventory),
                'total_inventory_value': sum(current_inventory.values()),
                'product_metrics': {}
            }
            
            for product_id in current_inventory.keys():
                product_data = historical_data[historical_data['product_id'] == product_id]
                
                if len(product_data) == 0:
                    continue
                
                # Calculate product-specific metrics
                daily_demand = product_data.groupby('date')['demand'].sum()
                
                metrics['product_metrics'][product_id] = {
                    'current_stock': current_inventory[product_id],
                    'average_daily_demand': daily_demand.mean(),
                    'demand_volatility': daily_demand.std(),
                    'stockout_probability': self._calculate_stockout_probability(
                        current_inventory[product_id],
                        daily_demand.mean(),
                        daily_demand.std()
                    ),
                    'inventory_turnover': self._calculate_inventory_turnover(
                        daily_demand.mean(),
                        current_inventory[product_id]
                    )
                }
            
            # Calculate aggregate metrics
            metrics['average_stockout_probability'] = np.mean([
                m['stockout_probability'] for m in metrics['product_metrics'].values()
            ])
            
            metrics['average_inventory_turnover'] = np.mean([
                m['inventory_turnover'] for m in metrics['product_metrics'].values()
            ])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating inventory metrics: {str(e)}")
            raise

    def _calculate_stockout_probability(self,
                                      current_stock: float,
                                      demand_mean: float,
                                      demand_std: float) -> float:
        """Calculate probability of stockout based on current stock level."""
        try:
            if demand_std == 0:
                return 0 if current_stock > demand_mean else 1
            
            z = (current_stock - demand_mean) / demand_std
            return 1 - stats.norm.cdf(z)
            
        except Exception as e:
            self.logger.error(f"Error calculating stockout probability: {str(e)}")
            raise

    def _calculate_inventory_turnover(self,
                                    daily_demand: float,
                                    current_stock: float) -> float:
        """Calculate inventory turnover rate."""
        try:
            if current_stock == 0:
                return 0
            
            annual_demand = daily_demand * 365
            return annual_demand / current_stock
            
        except Exception as e:
            self.logger.error(f"Error calculating inventory turnover: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize model
    model = InventoryModel(service_level=0.95)
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    products = ['PROD001', 'PROD002']
    
    historical_data = pd.DataFrame([
        {
            'product_id': product,
            'date': date,
            'demand': np.random.normal(100, 20)  # Random demand with mean 100, std 20
        }
        for product in products
        for date in dates
    ])
    
    current_inventory = {
        'PROD001': 500,
        'PROD002': 300
    }
    
    lead_times = {
        'PROD001': 7,
        'PROD002': 5
    }
    
    costs = {
        'PROD001': {
            'order_cost': 100,
            'holding_cost': 10
        },
        'PROD002': {
            'order_cost': 80,
            'holding_cost': 8
        }
    }
    
    # Get optimization results
    optimization_results = model.optimize_inventory(
        historical_data=historical_data,
        current_inventory=current_inventory,
        lead_times=lead_times,
        costs=costs
    )
    
    # Get inventory metrics
    metrics = model.calculate_inventory_metrics(
        historical_data=historical_data,
        current_inventory=current_inventory
    )
    
    print("Optimization Results:", optimization_results)
    print("\nInventory Metrics:", metrics) 