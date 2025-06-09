import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import networkx as nx
import folium
from folium.plugins import HeatMap
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import altair as alt
import bokeh
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
import time

@dataclass
class VisualizationConfig:
    """Configuration for the visualization system."""
    output_dir: str
    template_dir: str
    dashboard_dir: str
    theme: str
    default_colors: List[str]
    chart_types: List[str]
    interactive: bool
    auto_refresh: bool
    cache_results: bool

class DataVisualization:
    def __init__(self, config_path: str = 'config/viz_config.yaml'):
        """Initialize the visualization system with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize visualization state
        self.is_generating = False
        self.viz_status = {}
        
        # Set up database connection
        self.engine = create_engine(self.config.database_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Create necessary directories
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.template_dir, exist_ok=True)
        os.makedirs(self.config.dashboard_dir, exist_ok=True)
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )

    def _load_config(self) -> VisualizationConfig:
        """Load visualization configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return VisualizationConfig(**config_dict)
        except Exception as e:
            self.logger.error(f"Error loading visualization configuration: {str(e)}")
            raise

    def generate_visualizations(self, viz_type: str = 'all') -> Dict:
        """Generate visualizations."""
        try:
            self.is_generating = True
            self.logger.info(f"Generating {viz_type} visualizations")
            
            start_time = time.time()
            results = {
                'generated': [],
                'errors': []
            }
            
            if viz_type in ['all', 'sales']:
                self._generate_sales_visualizations(results)
            
            if viz_type in ['all', 'inventory']:
                self._generate_inventory_visualizations(results)
            
            if viz_type in ['all', 'delivery']:
                self._generate_delivery_visualizations(results)
            
            if viz_type in ['all', 'dashboard']:
                self._generate_dashboard(results)
            
            # Save visualization status
            self._save_visualization_status(results)
            
            duration = time.time() - start_time
            self.logger.info(f"Visualization generation completed in {duration:.2f} seconds")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {str(e)}")
            raise
        finally:
            self.is_generating = False

    def _generate_sales_visualizations(self, results: Dict) -> None:
        """Generate sales visualizations."""
        try:
            # Load sales data
            sales_data = self._load_sales_data()
            
            # Generate time series plot
            self._generate_sales_time_series(sales_data)
            
            # Generate product performance plot
            self._generate_product_performance(sales_data)
            
            # Generate location performance plot
            self._generate_location_performance(sales_data)
            
            # Generate correlation heatmap
            self._generate_sales_correlation(sales_data)
            
            results['generated'].append('sales_visualizations')
            
        except Exception as e:
            self.logger.error(f"Error generating sales visualizations: {str(e)}")
            results['errors'].append({
                'type': 'sales',
                'error': str(e)
            })

    def _generate_inventory_visualizations(self, results: Dict) -> None:
        """Generate inventory visualizations."""
        try:
            # Load inventory data
            inventory_data = self._load_inventory_data()
            
            # Generate inventory level plot
            self._generate_inventory_levels(inventory_data)
            
            # Generate stockout risk plot
            self._generate_stockout_risk(inventory_data)
            
            # Generate reorder point analysis
            self._generate_reorder_analysis(inventory_data)
            
            # Generate inventory distribution
            self._generate_inventory_distribution(inventory_data)
            
            results['generated'].append('inventory_visualizations')
            
        except Exception as e:
            self.logger.error(f"Error generating inventory visualizations: {str(e)}")
            results['errors'].append({
                'type': 'inventory',
                'error': str(e)
            })

    def _generate_delivery_visualizations(self, results: Dict) -> None:
        """Generate delivery visualizations."""
        try:
            # Load delivery data
            delivery_data = self._load_delivery_data()
            
            # Generate delivery performance plot
            self._generate_delivery_performance(delivery_data)
            
            # Generate route efficiency map
            self._generate_route_efficiency(delivery_data)
            
            # Generate vehicle utilization plot
            self._generate_vehicle_utilization(delivery_data)
            
            # Generate delivery time analysis
            self._generate_delivery_time_analysis(delivery_data)
            
            results['generated'].append('delivery_visualizations')
            
        except Exception as e:
            self.logger.error(f"Error generating delivery visualizations: {str(e)}")
            results['errors'].append({
                'type': 'delivery',
                'error': str(e)
            })

    def _generate_dashboard(self, results: Dict) -> None:
        """Generate interactive dashboard."""
        try:
            # Define dashboard layout
            self.app.layout = dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H1("FlowCast Supply Chain Dashboard"),
                        html.P("Interactive dashboard for supply chain analytics")
                    ])
                ]),
                
                dbc.Row([
                    dbc.Col([
                        dcc.Tabs([
                            dcc.Tab(label='Sales', children=[
                                self._create_sales_tab()
                            ]),
                            dcc.Tab(label='Inventory', children=[
                                self._create_inventory_tab()
                            ]),
                            dcc.Tab(label='Delivery', children=[
                                self._create_delivery_tab()
                            ])
                        ])
                    ])
                ])
            ])
            
            # Define callbacks
            self._define_dashboard_callbacks()
            
            # Run dashboard
            self.app.run_server(debug=True)
            
            results['generated'].append('dashboard')
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard: {str(e)}")
            results['errors'].append({
                'type': 'dashboard',
                'error': str(e)
            })

    def _generate_sales_time_series(self, data: pd.DataFrame) -> None:
        """Generate sales time series plot."""
        try:
            # Create time series plot
            fig = go.Figure()
            
            # Add sales line
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['quantity'],
                mode='lines',
                name='Sales'
            ))
            
            # Add trend line
            z = np.polyfit(range(len(data)), data['quantity'], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=p(range(len(data))),
                mode='lines',
                name='Trend',
                line=dict(dash='dash')
            ))
            
            # Update layout
            fig.update_layout(
                title='Sales Time Series',
                xaxis_title='Date',
                yaxis_title='Quantity',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'sales_time_series')
            
        except Exception as e:
            self.logger.error(f"Error generating sales time series: {str(e)}")
            raise

    def _generate_product_performance(self, data: pd.DataFrame) -> None:
        """Generate product performance plot."""
        try:
            # Aggregate data by product
            product_data = data.groupby('product_id').agg({
                'quantity': 'sum',
                'revenue': 'sum'
            }).reset_index()
            
            # Create bar plot
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=product_data['product_id'],
                y=product_data['quantity'],
                name='Quantity'
            ))
            
            fig.add_trace(go.Bar(
                x=product_data['product_id'],
                y=product_data['revenue'],
                name='Revenue'
            ))
            
            # Update layout
            fig.update_layout(
                title='Product Performance',
                xaxis_title='Product ID',
                yaxis_title='Value',
                template=self.config.theme,
                barmode='group'
            )
            
            # Save plot
            self._save_plot(fig, 'product_performance')
            
        except Exception as e:
            self.logger.error(f"Error generating product performance plot: {str(e)}")
            raise

    def _generate_location_performance(self, data: pd.DataFrame) -> None:
        """Generate location performance plot."""
        try:
            # Aggregate data by location
            location_data = data.groupby('location_id').agg({
                'quantity': 'sum',
                'revenue': 'sum'
            }).reset_index()
            
            # Create scatter plot
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=location_data['quantity'],
                y=location_data['revenue'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=location_data['revenue'],
                    colorscale='Viridis',
                    showscale=True
                ),
                text=location_data['location_id']
            ))
            
            # Update layout
            fig.update_layout(
                title='Location Performance',
                xaxis_title='Quantity',
                yaxis_title='Revenue',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'location_performance')
            
        except Exception as e:
            self.logger.error(f"Error generating location performance plot: {str(e)}")
            raise

    def _generate_sales_correlation(self, data: pd.DataFrame) -> None:
        """Generate sales correlation heatmap."""
        try:
            # Calculate correlation matrix
            corr_matrix = data[['quantity', 'revenue', 'price']].corr()
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmin=-1,
                zmax=1
            ))
            
            # Update layout
            fig.update_layout(
                title='Sales Correlation Heatmap',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'sales_correlation')
            
        except Exception as e:
            self.logger.error(f"Error generating sales correlation heatmap: {str(e)}")
            raise

    def _generate_inventory_levels(self, data: pd.DataFrame) -> None:
        """Generate inventory levels plot."""
        try:
            # Create time series plot
            fig = go.Figure()
            
            # Add inventory level line
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['inventory_level'],
                mode='lines',
                name='Inventory Level'
            ))
            
            # Add reorder point line
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['reorder_point'],
                mode='lines',
                name='Reorder Point',
                line=dict(dash='dash')
            ))
            
            # Update layout
            fig.update_layout(
                title='Inventory Levels Over Time',
                xaxis_title='Date',
                yaxis_title='Level',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'inventory_levels')
            
        except Exception as e:
            self.logger.error(f"Error generating inventory levels plot: {str(e)}")
            raise

    def _generate_stockout_risk(self, data: pd.DataFrame) -> None:
        """Generate stockout risk plot."""
        try:
            # Calculate stockout risk
            data['stockout_risk'] = data['inventory_level'] / data['reorder_point']
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=data.pivot_table(
                    values='stockout_risk',
                    index='product_id',
                    columns='location_id'
                ),
                colorscale='RdYlGn_r',
                zmin=0,
                zmax=2
            ))
            
            # Update layout
            fig.update_layout(
                title='Stockout Risk by Product and Location',
                xaxis_title='Location ID',
                yaxis_title='Product ID',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'stockout_risk')
            
        except Exception as e:
            self.logger.error(f"Error generating stockout risk plot: {str(e)}")
            raise

    def _generate_reorder_analysis(self, data: pd.DataFrame) -> None:
        """Generate reorder point analysis plot."""
        try:
            # Create scatter plot
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=data['inventory_level'],
                y=data['reorder_point'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=data['days_to_stockout'],
                    colorscale='RdYlGn_r',
                    showscale=True
                ),
                text=data['product_id']
            ))
            
            # Add diagonal line
            fig.add_trace(go.Scatter(
                x=[0, data['inventory_level'].max()],
                y=[0, data['reorder_point'].max()],
                mode='lines',
                name='Reorder Point',
                line=dict(dash='dash')
            ))
            
            # Update layout
            fig.update_layout(
                title='Reorder Point Analysis',
                xaxis_title='Current Inventory Level',
                yaxis_title='Reorder Point',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'reorder_analysis')
            
        except Exception as e:
            self.logger.error(f"Error generating reorder analysis plot: {str(e)}")
            raise

    def _generate_inventory_distribution(self, data: pd.DataFrame) -> None:
        """Generate inventory distribution plot."""
        try:
            # Create histogram
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=data['inventory_level'],
                nbinsx=50,
                name='Inventory Level'
            ))
            
            # Update layout
            fig.update_layout(
                title='Inventory Level Distribution',
                xaxis_title='Inventory Level',
                yaxis_title='Frequency',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'inventory_distribution')
            
        except Exception as e:
            self.logger.error(f"Error generating inventory distribution plot: {str(e)}")
            raise

    def _generate_delivery_performance(self, data: pd.DataFrame) -> None:
        """Generate delivery performance plot."""
        try:
            # Create time series plot
            fig = go.Figure()
            
            # Add delivery time line
            fig.add_trace(go.Scatter(
                x=data['delivery_date'],
                y=data['delivery_time'],
                mode='lines',
                name='Delivery Time'
            ))
            
            # Add target time line
            fig.add_trace(go.Scatter(
                x=data['delivery_date'],
                y=data['target_time'],
                mode='lines',
                name='Target Time',
                line=dict(dash='dash')
            ))
            
            # Update layout
            fig.update_layout(
                title='Delivery Performance Over Time',
                xaxis_title='Date',
                yaxis_title='Time (hours)',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'delivery_performance')
            
        except Exception as e:
            self.logger.error(f"Error generating delivery performance plot: {str(e)}")
            raise

    def _generate_route_efficiency(self, data: pd.DataFrame) -> None:
        """Generate route efficiency map."""
        try:
            # Create map
            m = folium.Map(location=[0, 0], zoom_start=2)
            
            # Add delivery routes
            for _, row in data.iterrows():
                folium.PolyLine(
                    locations=[
                        [row['origin_lat'], row['origin_lon']],
                        [row['destination_lat'], row['destination_lon']]
                    ],
                    color='blue',
                    weight=2,
                    opacity=0.8
                ).add_to(m)
            
            # Add delivery points
            for _, row in data.iterrows():
                folium.CircleMarker(
                    location=[row['destination_lat'], row['destination_lon']],
                    radius=5,
                    color='red',
                    fill=True
                ).add_to(m)
            
            # Save map
            map_path = os.path.join(self.config.output_dir, 'route_efficiency.html')
            m.save(map_path)
            
        except Exception as e:
            self.logger.error(f"Error generating route efficiency map: {str(e)}")
            raise

    def _generate_vehicle_utilization(self, data: pd.DataFrame) -> None:
        """Generate vehicle utilization plot."""
        try:
            # Calculate utilization
            vehicle_data = data.groupby('vehicle_id').agg({
                'distance': 'sum',
                'duration': 'sum',
                'capacity': 'first'
            }).reset_index()
            
            vehicle_data['utilization'] = vehicle_data['distance'] / vehicle_data['capacity']
            
            # Create bar plot
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=vehicle_data['vehicle_id'],
                y=vehicle_data['utilization'],
                name='Utilization'
            ))
            
            # Update layout
            fig.update_layout(
                title='Vehicle Utilization',
                xaxis_title='Vehicle ID',
                yaxis_title='Utilization',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'vehicle_utilization')
            
        except Exception as e:
            self.logger.error(f"Error generating vehicle utilization plot: {str(e)}")
            raise

    def _generate_delivery_time_analysis(self, data: pd.DataFrame) -> None:
        """Generate delivery time analysis plot."""
        try:
            # Create box plot
            fig = go.Figure()
            
            fig.add_trace(go.Box(
                y=data['delivery_time'],
                name='Delivery Time'
            ))
            
            # Update layout
            fig.update_layout(
                title='Delivery Time Distribution',
                yaxis_title='Time (hours)',
                template=self.config.theme
            )
            
            # Save plot
            self._save_plot(fig, 'delivery_time_analysis')
            
        except Exception as e:
            self.logger.error(f"Error generating delivery time analysis plot: {str(e)}")
            raise

    def _save_plot(self, fig: go.Figure, name: str) -> None:
        """Save plot to file."""
        try:
            # Save as HTML
            html_path = os.path.join(self.config.output_dir, f'{name}.html')
            fig.write_html(html_path)
            
            # Save as PNG
            png_path = os.path.join(self.config.output_dir, f'{name}.png')
            fig.write_image(png_path)
            
        except Exception as e:
            self.logger.error(f"Error saving plot {name}: {str(e)}")
            raise

    def _save_visualization_status(self, results: Dict) -> None:
        """Save visualization generation status."""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'generated': results['generated'],
                'errors': results['errors']
            }
            
            status_path = os.path.join(self.config.output_dir, 'visualization_status.json')
            with open(status_path, 'w') as f:
                json.dump(status, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving visualization status: {str(e)}")
            raise

    def get_visualization_status(self) -> Dict:
        """Get current visualization status."""
        return {
            'is_generating': self.is_generating,
            'last_generated': self.viz_status.get('timestamp'),
            'generated_viz': self.viz_status.get('generated', []),
            'errors': self.viz_status.get('errors', [])
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and generate visualizations
    visualization = DataVisualization()
    results = visualization.generate_visualizations() 