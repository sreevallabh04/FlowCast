import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import googlemaps
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import polyline
import os

class RoutingModel:
    def __init__(self, google_maps_api_key: Optional[str] = None):
        """
        Initialize the routing optimization model.
        
        Args:
            google_maps_api_key: Optional Google Maps API key for real routing
        """
        self.logger = logging.getLogger(__name__)
        self.version = "1.0.0"
        
        # Initialize Google Maps client if API key is provided
        self.gmaps = None
        if google_maps_api_key:
            try:
                self.gmaps = googlemaps.Client(key=google_maps_api_key)
            except Exception as e:
                self.logger.error(f"Error initializing Google Maps client: {str(e)}")
                self.gmaps = None

    def create_distance_matrix(self,
                             locations: List[Dict[str, float]],
                             mode: str = 'driving') -> Tuple[np.ndarray, Dict]:
        """
        Create distance matrix using Google Maps API or fallback to Euclidean distance.
        
        Args:
            locations: List of locations with lat/lng coordinates
            mode: Travel mode (driving, walking, bicycling, transit)
        """
        try:
            n = len(locations)
            distance_matrix = np.zeros((n, n))
            duration_matrix = np.zeros((n, n))
            
            if self.gmaps:
                # Use Google Maps API
                origins = [f"{loc['lat']},{loc['lng']}" for loc in locations]
                destinations = origins
                
                # Get distance matrix from Google Maps
                result = self.gmaps.distance_matrix(
                    origins=origins,
                    destinations=destinations,
                    mode=mode,
                    departure_time=datetime.now()
                )
                
                # Parse results
                for i in range(n):
                    for j in range(n):
                        if i != j:
                            element = result['rows'][i]['elements'][j]
                            if element['status'] == 'OK':
                                distance_matrix[i, j] = element['distance']['value']  # meters
                                duration_matrix[i, j] = element['duration']['value']  # seconds
                            else:
                                # Fallback to Euclidean distance
                                distance_matrix[i, j] = self._calculate_euclidean_distance(
                                    locations[i], locations[j]
                                )
                                duration_matrix[i, j] = distance_matrix[i, j] / 13.89  # Assuming 50 km/h
                        else:
                            distance_matrix[i, j] = 0
                            duration_matrix[i, j] = 0
            else:
                # Use Euclidean distance as fallback
                for i in range(n):
                    for j in range(n):
                        if i != j:
                            distance_matrix[i, j] = self._calculate_euclidean_distance(
                                locations[i], locations[j]
                            )
                            duration_matrix[i, j] = distance_matrix[i, j] / 13.89  # Assuming 50 km/h
                        else:
                            distance_matrix[i, j] = 0
                            duration_matrix[i, j] = 0
            
            return distance_matrix, duration_matrix
            
        except Exception as e:
            self.logger.error(f"Error creating distance matrix: {str(e)}")
            raise

    def _calculate_euclidean_distance(self, loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
        """Calculate Euclidean distance between two points."""
        try:
            return np.sqrt(
                (loc1['lat'] - loc2['lat'])**2 + 
                (loc1['lng'] - loc2['lng'])**2
            ) * 111000  # Convert to meters (roughly)
        except Exception as e:
            self.logger.error(f"Error calculating Euclidean distance: {str(e)}")
            raise

    def optimize_route(self,
                      locations: List[Dict[str, float]],
                      demands: List[float],
                      vehicle_capacity: float,
                      num_vehicles: int = 1,
                      mode: str = 'driving') -> Dict:
        """
        Optimize delivery routes using Google OR-Tools.
        
        Args:
            locations: List of locations with lat/lng coordinates
            demands: List of demands for each location
            vehicle_capacity: Maximum capacity of each vehicle
            num_vehicles: Number of vehicles available
            mode: Travel mode for distance calculation
        """
        try:
            # Create distance matrix
            distance_matrix, duration_matrix = self.create_distance_matrix(locations, mode)
            
            # Create routing index manager
            manager = pywrapcp.RoutingIndexManager(
                len(locations), num_vehicles, 0  # 0 is the depot
            )
            
            # Create routing model
            routing = pywrapcp.RoutingModel(manager)
            
            # Register distance callback
            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return distance_matrix[from_node][to_node]
            
            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # Add capacity constraint
            def demand_callback(from_index):
                from_node = manager.IndexToNode(from_index)
                return demands[from_node]
            
            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,  # null capacity slack
                [vehicle_capacity] * num_vehicles,  # vehicle capacities
                True,  # force start cumul to zero
                'Capacity'
            )
            
            # Add time window constraints
            time_dimension = routing.GetDimensionOrDie('Capacity')
            time_dimension.SetGlobalSpanCostCoefficient(100)
            
            # Set first solution heuristic
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.FromSeconds(30)
            
            # Solve the problem
            solution = routing.SolveWithParameters(search_parameters)
            
            if not solution:
                raise Exception("No solution found")
            
            # Process solution
            routes = []
            total_distance = 0
            total_duration = 0
            
            for vehicle_id in range(num_vehicles):
                index = routing.Start(vehicle_id)
                route = []
                route_distance = 0
                route_duration = 0
                
                while not routing.IsEnd(index):
                    node_index = manager.IndexToNode(index)
                    route.append({
                        'location': locations[node_index],
                        'demand': demands[node_index]
                    })
                    
                    previous_index = index
                    index = solution.Value(routing.NextVar(index))
                    route_distance += routing.GetArcCostForVehicle(
                        previous_index, index, vehicle_id
                    )
                    route_duration += duration_matrix[
                        manager.IndexToNode(previous_index)
                    ][manager.IndexToNode(index)]
                
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route,
                    'distance': route_distance,
                    'duration': route_duration
                })
                
                total_distance += route_distance
                total_duration += route_duration
            
            # Get route polylines if Google Maps is available
            route_polylines = []
            if self.gmaps:
                for route in routes:
                    waypoints = [
                        f"{stop['location']['lat']},{stop['location']['lng']}"
                        for stop in route['route']
                    ]
                    
                    try:
                        directions = self.gmaps.directions(
                            waypoints[0],
                            waypoints[-1],
                            waypoints=waypoints[1:-1],
                            mode=mode,
                            departure_time=datetime.now()
                        )
                        
                        if directions:
                            route_polylines.append(directions[0]['overview_polyline']['points'])
                        else:
                            route_polylines.append(None)
                    except Exception as e:
                        self.logger.warning(f"Error getting route polyline: {str(e)}")
                        route_polylines.append(None)
            
            return {
                'routes': routes,
                'total_distance': total_distance,
                'total_duration': total_duration,
                'route_polylines': route_polylines if self.gmaps else None,
                'metrics': {
                    'num_vehicles': num_vehicles,
                    'vehicle_capacity': vehicle_capacity,
                    'total_demand': sum(demands),
                    'average_route_distance': total_distance / num_vehicles,
                    'average_route_duration': total_duration / num_vehicles
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing route: {str(e)}")
            raise

    def get_route_metrics(self, route_data: Dict) -> Dict:
        """Calculate key metrics for the optimized routes."""
        try:
            routes = route_data['routes']
            
            metrics = {
                'total_distance': route_data['total_distance'],
                'total_duration': route_data['total_duration'],
                'num_routes': len(routes),
                'route_metrics': []
            }
            
            for route in routes:
                route_metrics = {
                    'vehicle_id': route['vehicle_id'],
                    'distance': route['distance'],
                    'duration': route['duration'],
                    'num_stops': len(route['route']),
                    'total_demand': sum(stop['demand'] for stop in route['route']),
                    'average_stop_distance': route['distance'] / len(route['route']) if route['route'] else 0
                }
                metrics['route_metrics'].append(route_metrics)
            
            # Calculate aggregate metrics
            metrics['average_route_distance'] = np.mean([r['distance'] for r in routes])
            metrics['average_route_duration'] = np.mean([r['duration'] for r in routes])
            metrics['average_stops_per_route'] = np.mean([r['num_stops'] for r in routes])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating route metrics: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize model
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    model = RoutingModel(google_maps_api_key=google_maps_api_key)
    
    # Create sample data
    locations = [
        {'lat': 40.7128, 'lng': -74.0060},  # New York
        {'lat': 40.7589, 'lng': -73.9851},  # Times Square
        {'lat': 40.7829, 'lng': -73.9654},  # Central Park
        {'lat': 40.7527, 'lng': -73.9772},  # Empire State
        {'lat': 40.7484, 'lng': -73.9857}   # Madison Square
    ]
    
    demands = [0, 100, 150, 200, 120]  # First location is depot
    
    # Optimize routes
    route_data = model.optimize_route(
        locations=locations,
        demands=demands,
        vehicle_capacity=500,
        num_vehicles=2
    )
    
    # Get route metrics
    metrics = model.get_route_metrics(route_data)
    
    print("Route Data:", route_data)
    print("\nRoute Metrics:", metrics) 