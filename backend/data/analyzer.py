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
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from models import Transaction, Product, Store, Weather, Route

warnings.filterwarnings('ignore')

@dataclass
class AnalysisResult:
    """Class for storing analysis results."""
    title: str
    description: str
    metrics: Dict
    visualizations: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class DataAnalyzer:
    def __init__(self, data_dir: str = 'data/processed', output_dir: str = 'data/analysis'):
        """Initialize the data analyzer with input and output directories."""
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/plots', exist_ok=True)
        
        # Initialize data storage
        self.sales_data = None
        self.inventory_data = None
        self.delivery_data = None
        
        # Initialize analysis results
        self.analysis_results = []
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set up plotting style
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
        self.scaler = StandardScaler()

    def load_data(self) -> None:
        """Load processed data from CSV files."""
        try:
            # Load time-series data
            self.sales_data = pd.read_csv(f'{self.data_dir}/sales_processed.csv')
            self.inventory_data = pd.read_csv(f'{self.data_dir}/inventory_processed.csv')
            self.delivery_data = pd.read_csv(f'{self.data_dir}/deliveries_processed.csv')
            
            # Convert date columns to datetime
            for df in [self.sales_data, self.inventory_data, self.delivery_data]:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            
            self.logger.info("All data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def analyze_all(self) -> List[AnalysisResult]:
        """Run all analyses."""
        try:
            # Clear previous analysis results
            self.analysis_results = []
            
            # Perform sales analysis
            self._analyze_sales()
            
            # Perform inventory analysis
            self._analyze_inventory()
            
            # Perform delivery analysis
            self._analyze_deliveries()
            
            # Perform cross-functional analysis
            self._analyze_cross_functional()
            
            # Save analysis results
            self._save_analysis_results()
            
            return self.analysis_results
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            raise

    def _analyze_sales(self) -> None:
        """Analyze sales data."""
        # Time series analysis
        daily_sales = self.sales_data.groupby('date')['quantity'].sum().reset_index()
        monthly_sales = self.sales_data.groupby(self.sales_data['date'].dt.to_period('M'))['quantity'].sum()
        
        # Calculate key metrics
        total_sales = self.sales_data['quantity'].sum()
        avg_daily_sales = daily_sales['quantity'].mean()
        sales_std = daily_sales['quantity'].std()
        sales_trend = np.polyfit(range(len(daily_sales)), daily_sales['quantity'], 1)[0]
        
        # Product performance analysis
        product_performance = self.sales_data.groupby('product_id').agg({
            'quantity': ['sum', 'mean', 'std'],
            'revenue': 'sum'
        }).round(2)
        
        # Location performance analysis
        location_performance = self.sales_data.groupby('location_id').agg({
            'quantity': ['sum', 'mean', 'std'],
            'revenue': 'sum'
        }).round(2)
        
        # Create visualizations
        self._plot_sales_trend(daily_sales)
        self._plot_product_performance(product_performance)
        self._plot_location_performance(location_performance)
        
        # Generate recommendations
        recommendations = []
        if sales_trend < 0:
            recommendations.append("Sales trend is declining. Consider promotional activities.")
        if sales_std > avg_daily_sales:
            recommendations.append("High sales volatility. Consider inventory buffer.")
        
        # Store results
        result = AnalysisResult(
            title="Sales Analysis",
            description="Analysis of sales patterns and performance metrics",
            metrics={
                "total_sales": total_sales,
                "avg_daily_sales": avg_daily_sales,
                "sales_std": sales_std,
                "sales_trend": sales_trend,
                "top_products": product_performance.nlargest(5, ('quantity', 'sum')).index.tolist(),
                "top_locations": location_performance.nlargest(5, ('quantity', 'sum')).index.tolist()
            },
            visualizations=[
                f'{self.output_dir}/plots/sales_trend.png',
                f'{self.output_dir}/plots/product_performance.png',
                f'{self.output_dir}/plots/location_performance.png'
            ],
            recommendations=recommendations
        )
        self.analysis_results.append(result)

    def _analyze_inventory(self) -> None:
        """Analyze inventory data."""
        # Calculate key metrics
        avg_inventory = self.inventory_data['inventory_level'].mean()
        inventory_std = self.inventory_data['inventory_level'].std()
        stockout_rate = (self.inventory_data['inventory_level'] == 0).mean()
        excess_inventory = (self.inventory_data['inventory_level'] > 
                          self.inventory_data['reorder_point'] * 2).mean()
        
        # Product inventory analysis
        product_inventory = self.inventory_data.groupby('product_id').agg({
            'inventory_level': ['mean', 'std'],
            'stockout_risk': 'mean'
        }).round(2)
        
        # Location inventory analysis
        location_inventory = self.inventory_data.groupby('location_id').agg({
            'inventory_level': ['mean', 'std'],
            'stockout_risk': 'mean'
        }).round(2)
        
        # Create visualizations
        self._plot_inventory_distribution()
        self._plot_stockout_risk()
        self._plot_inventory_by_location()
        
        # Generate recommendations
        recommendations = []
        if stockout_rate > 0.1:
            recommendations.append("High stockout rate. Consider increasing safety stock.")
        if excess_inventory > 0.2:
            recommendations.append("High excess inventory. Consider reducing reorder points.")
        
        # Store results
        result = AnalysisResult(
            title="Inventory Analysis",
            description="Analysis of inventory levels and stockout risks",
            metrics={
                "avg_inventory": avg_inventory,
                "inventory_std": inventory_std,
                "stockout_rate": stockout_rate,
                "excess_inventory": excess_inventory,
                "high_risk_products": product_inventory[product_inventory[('stockout_risk', 'mean')] > 0.1].index.tolist(),
                "high_risk_locations": location_inventory[location_inventory[('stockout_risk', 'mean')] > 0.1].index.tolist()
            },
            visualizations=[
                f'{self.output_dir}/plots/inventory_distribution.png',
                f'{self.output_dir}/plots/stockout_risk.png',
                f'{self.output_dir}/plots/inventory_by_location.png'
            ],
            recommendations=recommendations
        )
        self.analysis_results.append(result)

    def _analyze_deliveries(self) -> None:
        """Analyze delivery data."""
        # Calculate key metrics
        avg_delivery_time = self.delivery_data['duration'].mean()
        delivery_std = self.delivery_data['duration'].std()
        delay_rate = (self.delivery_data['status'] == 'Delayed').mean()
        avg_distance = self.delivery_data['distance'].mean()
        
        # Vehicle performance analysis
        vehicle_performance = self.delivery_data.groupby('vehicle_id').agg({
            'distance': ['sum', 'mean'],
            'duration': ['mean', 'std'],
            'status': lambda x: (x == 'Delayed').mean()
        }).round(2)
        
        # Route analysis
        route_performance = self.delivery_data.groupby(['pickup_location_id', 'delivery_location_id']).agg({
            'distance': ['mean', 'std'],
            'duration': ['mean', 'std'],
            'status': lambda x: (x == 'Delayed').mean()
        }).round(2)
        
        # Create visualizations
        self._plot_delivery_performance()
        self._plot_route_analysis()
        self._plot_vehicle_utilization()
        
        # Generate recommendations
        recommendations = []
        if delay_rate > 0.1:
            recommendations.append("High delivery delay rate. Consider route optimization.")
        if delivery_std > avg_delivery_time:
            recommendations.append("High delivery time variability. Consider buffer time.")
        
        # Store results
        result = AnalysisResult(
            title="Delivery Analysis",
            description="Analysis of delivery performance and route efficiency",
            metrics={
                "avg_delivery_time": avg_delivery_time,
                "delivery_std": delivery_std,
                "delay_rate": delay_rate,
                "avg_distance": avg_distance,
                "high_delay_routes": route_performance[route_performance[('status', '<lambda_0>')] > 0.1].index.tolist(),
                "efficient_vehicles": vehicle_performance.nsmallest(5, ('duration', 'mean')).index.tolist()
            },
            visualizations=[
                f'{self.output_dir}/plots/delivery_performance.png',
                f'{self.output_dir}/plots/route_analysis.png',
                f'{self.output_dir}/plots/vehicle_utilization.png'
            ],
            recommendations=recommendations
        )
        self.analysis_results.append(result)

    def _analyze_cross_functional(self) -> None:
        """Perform cross-functional analysis."""
        # Sales-Inventory correlation
        sales_inv_corr = self.sales_data.merge(
            self.inventory_data,
            on=['date', 'product_id', 'location_id'],
            how='inner'
        )[['quantity', 'inventory_level']].corr().iloc[0,1]
        
        # Inventory-Delivery correlation
        inv_del_corr = self.inventory_data.merge(
            self.delivery_data,
            left_on=['date', 'location_id'],
            right_on=['date', 'delivery_location_id'],
            how='inner'
        )[['inventory_level', 'duration']].corr().iloc[0,1]
        
        # Create visualizations
        self._plot_sales_inventory_correlation()
        self._plot_inventory_delivery_correlation()
        self._plot_supply_chain_network()
        
        # Generate recommendations
        recommendations = []
        if abs(sales_inv_corr) < 0.3:
            recommendations.append("Weak sales-inventory correlation. Consider demand forecasting improvement.")
        if abs(inv_del_corr) > 0.5:
            recommendations.append("Strong inventory-delivery correlation. Consider delivery schedule optimization.")
        
        # Store results
        result = AnalysisResult(
            title="Cross-Functional Analysis",
            description="Analysis of relationships between different supply chain functions",
            metrics={
                "sales_inventory_correlation": sales_inv_corr,
                "inventory_delivery_correlation": inv_del_corr,
                "supply_chain_efficiency": (1 - delay_rate) * (1 - stockout_rate)
            },
            visualizations=[
                f'{self.output_dir}/plots/sales_inventory_correlation.png',
                f'{self.output_dir}/plots/inventory_delivery_correlation.png',
                f'{self.output_dir}/plots/supply_chain_network.png'
            ],
            recommendations=recommendations
        )
        self.analysis_results.append(result)

    def _plot_sales_trend(self, daily_sales: pd.DataFrame) -> None:
        """Plot sales trend over time."""
        plt.figure(figsize=(12, 6))
        plt.plot(daily_sales['date'], daily_sales['quantity'])
        plt.title('Daily Sales Trend')
        plt.xlabel('Date')
        plt.ylabel('Sales Quantity')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/sales_trend.png')
        plt.close()

    def _plot_product_performance(self, product_performance: pd.DataFrame) -> None:
        """Plot product performance metrics."""
        plt.figure(figsize=(12, 6))
        product_performance[('quantity', 'sum')].nlargest(10).plot(kind='bar')
        plt.title('Top 10 Products by Sales')
        plt.xlabel('Product ID')
        plt.ylabel('Total Sales')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/product_performance.png')
        plt.close()

    def _plot_location_performance(self, location_performance: pd.DataFrame) -> None:
        """Plot location performance metrics."""
        plt.figure(figsize=(12, 6))
        location_performance[('quantity', 'sum')].nlargest(10).plot(kind='bar')
        plt.title('Top 10 Locations by Sales')
        plt.xlabel('Location ID')
        plt.ylabel('Total Sales')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/location_performance.png')
        plt.close()

    def _plot_inventory_distribution(self) -> None:
        """Plot inventory level distribution."""
        plt.figure(figsize=(12, 6))
        sns.histplot(data=self.inventory_data, x='inventory_level', bins=50)
        plt.title('Inventory Level Distribution')
        plt.xlabel('Inventory Level')
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/inventory_distribution.png')
        plt.close()

    def _plot_stockout_risk(self) -> None:
        """Plot stockout risk by product."""
        plt.figure(figsize=(12, 6))
        stockout_risk = self.inventory_data.groupby('product_id')['stockout_risk'].mean()
        stockout_risk.nlargest(10).plot(kind='bar')
        plt.title('Top 10 Products by Stockout Risk')
        plt.xlabel('Product ID')
        plt.ylabel('Stockout Risk')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/stockout_risk.png')
        plt.close()

    def _plot_inventory_by_location(self) -> None:
        """Plot inventory levels by location."""
        plt.figure(figsize=(12, 6))
        location_inv = self.inventory_data.groupby('location_id')['inventory_level'].mean()
        location_inv.nlargest(10).plot(kind='bar')
        plt.title('Top 10 Locations by Average Inventory')
        plt.xlabel('Location ID')
        plt.ylabel('Average Inventory')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/inventory_by_location.png')
        plt.close()

    def _plot_delivery_performance(self) -> None:
        """Plot delivery performance metrics."""
        plt.figure(figsize=(12, 6))
        self.delivery_data.groupby('status').size().plot(kind='pie', autopct='%1.1f%%')
        plt.title('Delivery Status Distribution')
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/delivery_performance.png')
        plt.close()

    def _plot_route_analysis(self) -> None:
        """Plot route analysis."""
        plt.figure(figsize=(12, 6))
        route_avg = self.delivery_data.groupby(['pickup_location_id', 'delivery_location_id'])['duration'].mean()
        route_avg.nlargest(10).plot(kind='bar')
        plt.title('Top 10 Longest Routes by Duration')
        plt.xlabel('Route (Pickup-Delivery)')
        plt.ylabel('Average Duration')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/route_analysis.png')
        plt.close()

    def _plot_vehicle_utilization(self) -> None:
        """Plot vehicle utilization."""
        plt.figure(figsize=(12, 6))
        vehicle_util = self.delivery_data.groupby('vehicle_id').size()
        vehicle_util.nlargest(10).plot(kind='bar')
        plt.title('Top 10 Vehicles by Number of Deliveries')
        plt.xlabel('Vehicle ID')
        plt.ylabel('Number of Deliveries')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/vehicle_utilization.png')
        plt.close()

    def _plot_sales_inventory_correlation(self) -> None:
        """Plot sales-inventory correlation."""
        plt.figure(figsize=(12, 6))
        sales_inv = self.sales_data.merge(
            self.inventory_data,
            on=['date', 'product_id', 'location_id'],
            how='inner'
        )
        sns.scatterplot(data=sales_inv, x='quantity', y='inventory_level')
        plt.title('Sales vs Inventory Level')
        plt.xlabel('Sales Quantity')
        plt.ylabel('Inventory Level')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/sales_inventory_correlation.png')
        plt.close()

    def _plot_inventory_delivery_correlation(self) -> None:
        """Plot inventory-delivery correlation."""
        plt.figure(figsize=(12, 6))
        inv_del = self.inventory_data.merge(
            self.delivery_data,
            left_on=['date', 'location_id'],
            right_on=['date', 'delivery_location_id'],
            how='inner'
        )
        sns.scatterplot(data=inv_del, x='inventory_level', y='duration')
        plt.title('Inventory Level vs Delivery Duration')
        plt.xlabel('Inventory Level')
        plt.ylabel('Delivery Duration')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/inventory_delivery_correlation.png')
        plt.close()

    def _plot_supply_chain_network(self) -> None:
        """Plot supply chain network."""
        # Create a network graph using plotly
        fig = go.Figure()
        
        # Add nodes for locations
        locations = self.delivery_data[['pickup_location_id', 'delivery_location_id']].melt()['value'].unique()
        for loc in locations:
            fig.add_trace(go.Scatter(
                x=[np.random.rand()],
                y=[np.random.rand()],
                mode='markers+text',
                name=loc,
                text=[loc],
                textposition="top center"
            ))
        
        # Add edges for deliveries
        for _, row in self.delivery_data.iterrows():
            fig.add_trace(go.Scatter(
                x=[np.random.rand(), np.random.rand()],
                y=[np.random.rand(), np.random.rand()],
                mode='lines',
                line=dict(width=1),
                showlegend=False
            ))
        
        fig.update_layout(
            title='Supply Chain Network',
            showlegend=True,
            hovermode='closest'
        )
        
        fig.write_html(f'{self.output_dir}/plots/supply_chain_network.html')

    def _save_analysis_results(self) -> None:
        """Save analysis results to a JSON file."""
        try:
            results = [
                {
                    "title": result.title,
                    "description": result.description,
                    "metrics": result.metrics,
                    "visualizations": result.visualizations,
                    "recommendations": result.recommendations
                }
                for result in self.analysis_results
            ]
            
            with open(f'{self.output_dir}/analysis_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info("Analysis results saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving analysis results: {str(e)}")
            raise

    def get_analysis_summary(self) -> Dict:
        """Get a summary of analysis results."""
        summary = {
            "total_analyses": len(self.analysis_results),
            "total_recommendations": sum(len(r.recommendations) for r in self.analysis_results if r.recommendations),
            "total_visualizations": sum(len(r.visualizations) for r in self.analysis_results if r.visualizations),
            "key_metrics": {
                result.title: result.metrics
                for result in self.analysis_results
            }
        }
        
        return summary

    def analyze_sales_trends(self, date_range='30d', category='all', store='all'):
        """Analyze sales trends over time."""
        transactions = Transaction.get_sales_analytics(date_range, category, store)
        
        if not transactions:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.timestamp.date(),
            'sales': t.price * t.quantity
        } for t in transactions])
        
        # Group by date and calculate daily sales
        daily_sales = df.groupby('date')['sales'].sum().reset_index()
        
        # Calculate moving averages
        daily_sales['ma7'] = daily_sales['sales'].rolling(window=7).mean()
        daily_sales['ma30'] = daily_sales['sales'].rolling(window=30).mean()
        
        return daily_sales.to_dict('records')
    
    def analyze_inventory_trends(self, category='all', store='all'):
        """Analyze inventory trends."""
        products = Product.get_inventory_analytics(category, store)
        
        if not products:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'product': p.name,
            'quantity': p.quantity,
            'value': p.value
        } for p in products])
        
        # Calculate inventory metrics
        total_value = df['value'].sum()
        avg_quantity = df['quantity'].mean()
        low_stock = df[df['quantity'] <= df['reorder_point']].shape[0]
        
        return {
            'total_value': total_value,
            'avg_quantity': avg_quantity,
            'low_stock_count': low_stock,
            'products': df.to_dict('records')
        }
    
    def analyze_delivery_performance(self, date_range='30d'):
        """Analyze delivery performance metrics."""
        routes = Route.get_delivery_analytics(date_range)
        
        if not routes:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'status': r.status,
            'count': r.count
        } for r in routes])
        
        # Calculate delivery metrics
        total_deliveries = df['count'].sum()
        success_rate = df[df['status'] == 'completed']['count'].sum() / total_deliveries * 100
        
        return {
            'total_deliveries': total_deliveries,
            'success_rate': success_rate,
            'status_breakdown': df.to_dict('records')
        }
    
    def analyze_weather_impact(self, date_range='30d'):
        """Analyze the impact of weather on sales and deliveries."""
        # Get weather data
        weather_data = Weather.query.filter(
            Weather.timestamp >= datetime.utcnow() - timedelta(days=int(date_range[:-1]))
        ).all()
        
        if not weather_data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': w.timestamp.date(),
            'temperature': w.temperature,
            'condition': w.condition
        } for w in weather_data])
        
        # Get sales data for the same period
        sales_data = Transaction.get_sales_analytics(date_range)
        
        if not sales_data:
            return None
        
        # Convert sales to DataFrame
        sales_df = pd.DataFrame([{
            'date': t.timestamp.date(),
            'sales': t.price * t.quantity
        } for t in sales_data])
        
        # Merge weather and sales data
        merged_df = pd.merge(df, sales_df, on='date', how='left')
        
        # Calculate correlation between weather and sales
        correlation = merged_df['temperature'].corr(merged_df['sales'])
        
        return {
            'correlation': correlation,
            'weather_impact': merged_df.to_dict('records')
        }
    
    def generate_forecast(self, product_id, period=30, confidence=95):
        """Generate sales forecast for a product."""
        # Get historical sales data
        sales_data = Transaction.query.filter_by(product_id=product_id).all()
        
        if not sales_data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.timestamp.date(),
            'sales': t.price * t.quantity
        } for t in sales_data])
        
        # Prepare features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        
        # Split features and target
        X = df[['day_of_week', 'month', 'year']]
        y = df['sales']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        
        # Generate future dates
        future_dates = pd.date_range(
            start=datetime.utcnow(),
            periods=period,
            freq='D'
        )
        
        # Prepare future features
        future_df = pd.DataFrame({
            'date': future_dates,
            'day_of_week': future_dates.dayofweek,
            'month': future_dates.month,
            'year': future_dates.year
        })
        
        # Scale future features
        future_X_scaled = self.scaler.transform(future_df[['day_of_week', 'month', 'year']])
        
        # Make predictions
        predictions = model.predict(future_X_scaled)
        
        # Calculate confidence intervals
        std_dev = np.std(predictions)
        z_score = 1.96  # 95% confidence interval
        upper_bound = predictions + (z_score * std_dev)
        lower_bound = predictions - (z_score * std_dev)
        
        return {
            'forecasts': [
                {
                    'date': date.isoformat(),
                    'forecast': float(pred),
                    'confidence_upper': float(upper),
                    'confidence_lower': float(lower)
                }
                for date, pred, upper, lower in zip(
                    future_dates,
                    predictions,
                    upper_bound,
                    lower_bound
                )
            ]
        }
    
    def analyze_seasonal_patterns(self, date_range='365d'):
        """Analyze seasonal patterns in sales and inventory."""
        # Get sales data
        sales_data = Transaction.get_sales_analytics(date_range)
        
        if not sales_data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.timestamp.date(),
            'sales': t.price * t.quantity,
            'month': t.timestamp.month,
            'day_of_week': t.timestamp.weekday()
        } for t in sales_data])
        
        # Calculate monthly averages
        monthly_avg = df.groupby('month')['sales'].mean()
        
        # Calculate day of week averages
        daily_avg = df.groupby('day_of_week')['sales'].mean()
        
        return {
            'monthly_patterns': monthly_avg.to_dict(),
            'daily_patterns': daily_avg.to_dict()
        }
    
    def analyze_product_correlations(self, date_range='30d'):
        """Analyze correlations between product sales."""
        # Get sales data
        sales_data = Transaction.get_sales_analytics(date_range)
        
        if not sales_data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.timestamp.date(),
            'product_id': t.product_id,
            'sales': t.price * t.quantity
        } for t in sales_data])
        
        # Pivot data to get daily sales by product
        pivot_df = df.pivot_table(
            index='date',
            columns='product_id',
            values='sales',
            fill_value=0
        )
        
        # Calculate correlation matrix
        correlation_matrix = pivot_df.corr()
        
        return correlation_matrix.to_dict()

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create data analyzer
    analyzer = DataAnalyzer()
    
    # Load and analyze data
    analyzer.load_data()
    results = analyzer.analyze_all()
    
    # Print analysis summary
    summary = analyzer.get_analysis_summary()
    print("\nAnalysis Summary:")
    print(f"Total analyses: {summary['total_analyses']}")
    print(f"Total recommendations: {summary['total_recommendations']}")
    print(f"Total visualizations: {summary['total_visualizations']}")
    print("\nKey Metrics:")
    for title, metrics in summary['key_metrics'].items():
        print(f"\n{title}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}") 