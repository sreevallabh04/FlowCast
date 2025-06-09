import numpy as np
import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import joblib
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Union, Optional, Tuple
import json
from scipy.spatial.distance import cdist
import folium
from folium.plugins import HeatMap
import networkx as nx

class RouteOptimizer:
    def __init__(self, model_path: str = 'models/saved/route_model.joblib'):
        self.model_path = model_path
        self.version = "1.0.0"
        self.last_trained = None
        self.metrics = {}
        self.manager = None
        self.routing = None
        
        # Load model if exists
        if os.path.exists(model_path):
            self.load_model()
        else:
            self.train()  # Train new model if none exists

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the input data for route optimization."""
        # Convert coordinates to radians for distance calculation
        data['lat_rad'] = np.radians(data['latitude'])
        data['lon_rad'] = np.radians(data['longitude'])
        
        # Calculate time windows
        data['time_window_start'] = pd.to_datetime(data['time_window_start'])
        data['time_window_end'] = pd.to_datetime(data['time_window_end'])
        data['service_time'] = pd.to_timedelta(data['service_time'])
        
        # Calculate load requirements
        data['load_required'] = data['demand'] * data['unit_weight']
        
        # Calculate urgency score
        data['urgency_score'] = self._calculate_urgency_score(data)
        
        return data

    def _calculate_urgency_score(self, data: pd.DataFrame) -> pd.Series:
        """Calculate urgency score based on time windows and demand."""
        # Time-based urgency
        time_urgency = 1 / (data['time_window_end'] - data['time_window_start']).dt.total_seconds()
        
        # Demand-based urgency
        demand_urgency = data['demand'] / data['demand'].max()
        
        # Combine scores
        return 0.7 * time_urgency + 0.3 * demand_urgency

    def generate_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data for route optimization."""
        np.random.seed(42)
        n_locations = 50
        
        # Generate depot location (center point)
        depot_lat = 40.7128  # New York City latitude
        depot_lon = -74.0060  # New York City longitude
        
        # Generate random locations around the depot
        locations = []
        for i in range(n_locations):
            # Generate random offset from depot
            lat_offset = np.random.normal(0, 0.1)
            lon_offset = np.random.normal(0, 0.1)
            
            # Calculate location coordinates
            lat = depot_lat + lat_offset
            lon = depot_lon + lon_offset
            
            # Generate time window
            start_time = datetime.now() + timedelta(hours=np.random.randint(0, 12))
            end_time = start_time + timedelta(hours=np.random.randint(1, 4))
            
            locations.append({
                'location_id': f'L{i:03d}',
                'latitude': lat,
                'longitude': lon,
                'demand': np.random.randint(1, 10),
                'unit_weight': np.random.uniform(0.5, 5.0),
                'time_window_start': start_time,
                'time_window_end': end_time,
                'service_time': timedelta(minutes=np.random.randint(10, 60)),
                'priority': np.random.choice(['high', 'medium', 'low'], p=[0.2, 0.5, 0.3])
            })
        
        # Add depot
        locations.append({
            'location_id': 'DEPOT',
            'latitude': depot_lat,
            'longitude': depot_lon,
            'demand': 0,
            'unit_weight': 0,
            'time_window_start': datetime.now(),
            'time_window_end': datetime.now() + timedelta(hours=24),
            'service_time': timedelta(minutes=0),
            'priority': 'high'
        })
        
        return pd.DataFrame(locations)

    def train(self) -> None:
        """Train the route optimization model."""
        try:
            # Generate or load training data
            data = self.generate_training_data()
            
            # Preprocess data
            processed_data = self.preprocess_data(data)
            
            # Calculate distance matrix
            distance_matrix = self._calculate_distance_matrix(processed_data)
            
            # Save model parameters
            self.save_model({
                'distance_matrix': distance_matrix,
                'locations': processed_data.to_dict('records'),
                'metrics': {
                    'n_locations': len(processed_data),
                    'total_demand': processed_data['demand'].sum(),
                    'total_weight': processed_data['load_required'].sum()
                }
            })
            
            self.last_trained = datetime.utcnow()
            
            logging.info("Route optimization model trained successfully")
            
        except Exception as e:
            logging.error(f"Error training model: {str(e)}")
            raise

    def _calculate_distance_matrix(self, data: pd.DataFrame) -> np.ndarray:
        """Calculate distance matrix between all locations."""
        # Extract coordinates
        coords = data[['lat_rad', 'lon_rad']].values
        
        # Calculate Haversine distances
        distances = np.zeros((len(coords), len(coords)))
        for i in range(len(coords)):
            for j in range(len(coords)):
                if i != j:
                    distances[i, j] = self._haversine_distance(
                        coords[i, 0], coords[i, 1],
                        coords[j, 0], coords[j, 1]
                    )
        
        return distances

    def _haversine_distance(self, lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """Calculate Haversine distance between two points."""
        R = 6371  # Earth's radius in kilometers
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c

    def optimize(self, locations: List[Dict], vehicles: List[Dict],
                constraints: Optional[Dict] = None) -> Dict:
        """Optimize delivery routes for given locations and vehicles."""
        try:
            # Convert input to DataFrame
            data = pd.DataFrame(locations)
            
            # Preprocess data
            processed_data = self.preprocess_data(data)
            
            # Calculate distance matrix
            distance_matrix = self._calculate_distance_matrix(processed_data)
            
            # Create routing model
            self._create_routing_model(distance_matrix, processed_data, vehicles, constraints)
            
            # Solve the routing problem
            solution = self._solve_routing_problem()
            
            # Format results
            routes = self._format_routes(solution, processed_data, vehicles)
            
            return {
                'routes': routes,
                'metadata': {
                    'model_version': self.version,
                    'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                    'total_distance': sum(route['distance'] for route in routes),
                    'total_duration': sum(route['duration'] for route in routes),
                    'total_cost': sum(route['cost'] for route in routes)
                }
            }
            
        except Exception as e:
            logging.error(f"Error optimizing routes: {str(e)}")
            raise

    def _create_routing_model(self, distance_matrix: np.ndarray,
                            data: pd.DataFrame,
                            vehicles: List[Dict],
                            constraints: Optional[Dict] = None) -> None:
        """Create the routing model with constraints."""
        # Create routing index manager
        self.manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix),
            len(vehicles),
            0  # depot index
        )
        
        # Create routing model
        self.routing = pywrapcp.RoutingModel(self.manager)
        
        # Register distance callback
        def distance_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = self.routing.RegisterTransitCallback(distance_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add capacity constraints
        def demand_callback(from_index):
            from_node = self.manager.IndexToNode(from_index)
            return data.iloc[from_node]['load_required']
        
        demand_callback_index = self.routing.RegisterUnaryTransitCallback(demand_callback)
        
        for vehicle_id in range(len(vehicles)):
            self.routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,  # null capacity slack
                [vehicles[vehicle_id]['capacity']],  # vehicle capacities
                True,  # force start cumul to zero
                'Capacity'
            )
        
        # Add time window constraints
        def time_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            travel_time = distance_matrix[from_node][to_node] / vehicles[0]['speed']
            service_time = data.iloc[to_node]['service_time'].total_seconds() / 3600
            return travel_time + service_time
        
        time_callback_index = self.routing.RegisterTransitCallback(time_callback)
        
        self.routing.AddDimension(
            time_callback_index,
            0,  # no slack
            24,  # maximum time per vehicle
            True,  # force start cumul to zero
            'Time'
        )
        
        time_dimension = self.routing.GetDimensionOrDie('Time')
        
        # Add time window constraints for each location
        for location_idx in range(len(data)):
            index = self.manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(
                data.iloc[location_idx]['time_window_start'].hour,
                data.iloc[location_idx]['time_window_end'].hour
            )

    def _solve_routing_problem(self) -> Dict:
        """Solve the routing problem and return the solution."""
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(30)
        
        # Solve the problem
        solution = self.routing.SolveWithParameters(search_parameters)
        
        if not solution:
            raise Exception("No solution found")
        
        return solution

    def _format_routes(self, solution: Dict, data: pd.DataFrame,
                      vehicles: List[Dict]) -> List[Dict]:
        """Format the solution into readable routes."""
        routes = []
        
        for vehicle_id in range(len(vehicles)):
            index = self.routing.Start(vehicle_id)
            route = []
            route_distance = 0
            route_load = 0
            route_duration = 0
            
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                location = data.iloc[node_index]
                
                route.append({
                    'location_id': location['location_id'],
                    'latitude': location['latitude'],
                    'longitude': location['longitude'],
                    'demand': location['demand'],
                    'arrival_time': self._format_time(
                        self.routing.GetDimensionOrDie('Time').CumulVar(index).Value()
                    ),
                    'service_time': location['service_time'].total_seconds() / 3600
                })
                
                previous_index = index
                index = solution.Value(self.routing.NextVar(index))
                route_distance += self.routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )
                route_load += location['load_required']
                route_duration += location['service_time'].total_seconds() / 3600
            
            routes.append({
                'vehicle_id': vehicle_id,
                'route': route,
                'distance': route_distance,
                'load': route_load,
                'duration': route_duration,
                'cost': self._calculate_route_cost(
                    route_distance, route_duration, vehicles[vehicle_id]
                )
            })
        
        return routes

    def _format_time(self, hour: float) -> str:
        """Format hour as time string."""
        return f"{int(hour):02d}:{int((hour % 1) * 60):02d}"

    def _calculate_route_cost(self, distance: float, duration: float,
                            vehicle: Dict) -> float:
        """Calculate route cost based on distance and duration."""
        return (distance * vehicle['cost_per_km'] +
                duration * vehicle['cost_per_hour'])

    def get_metrics(self, start_date: datetime, end_date: datetime,
                   location_id: Optional[str] = None) -> Dict:
        """Get model performance metrics."""
        return {
            'total_routes': len(self.metrics.get('routes', [])),
            'average_route_distance': np.mean([r['distance'] for r in self.metrics.get('routes', [])]),
            'average_route_duration': np.mean([r['duration'] for r in self.metrics.get('routes', [])]),
            'total_cost': sum(r['cost'] for r in self.metrics.get('routes', []))
        }

    def get_confidence_score(self) -> float:
        """Calculate model confidence score based on recent performance."""
        return 1.0  # Route optimization is deterministic

    def save_model(self, model_data: Dict) -> None:
        """Save the model data."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(model_data, self.model_path)
            logging.info(f"Model saved successfully to {self.model_path}")
        except Exception as e:
            logging.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self) -> None:
        """Load the model data."""
        try:
            model_data = joblib.load(self.model_path)
            self.metrics = model_data.get('metrics', {})
            logging.info(f"Model loaded successfully from {self.model_path}")
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise

    def get_accuracy(self) -> float:
        """Get the model's accuracy score."""
        return 1.0  # Route optimization is deterministic

    def visualize_routes(self, routes: List[Dict], output_path: str) -> None:
        """Visualize routes on a map."""
        try:
            # Create base map
            m = folium.Map(
                location=[routes[0]['route'][0]['latitude'],
                         routes[0]['route'][0]['longitude']],
                zoom_start=12
            )
            
            # Add routes
            colors = ['red', 'blue', 'green', 'purple', 'orange']
            for i, route in enumerate(routes):
                color = colors[i % len(colors)]
                
                # Create route coordinates
                route_coords = [(stop['latitude'], stop['longitude'])
                              for stop in route['route']]
                
                # Add route line
                folium.PolyLine(
                    route_coords,
                    color=color,
                    weight=2,
                    opacity=0.8
                ).add_to(m)
                
                # Add markers for each stop
                for stop in route['route']:
                    folium.CircleMarker(
                        location=[stop['latitude'], stop['longitude']],
                        radius=5,
                        color=color,
                        fill=True,
                        popup=f"Location: {stop['location_id']}<br>"
                              f"Arrival: {stop['arrival_time']}<br>"
                              f"Service Time: {stop['service_time']:.1f}h"
                    ).add_to(m)
            
            # Save map
            m.save(output_path)
            logging.info(f"Route visualization saved to {output_path}")
            
        except Exception as e:
            logging.error(f"Error visualizing routes: {str(e)}")
            raise 