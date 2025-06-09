import numpy as np
import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import googlemaps
import logging
from datetime import datetime, timedelta
from utils.config import Config

logger = logging.getLogger(__name__)

class RouteOptimizer:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
    
    def _get_distance_matrix(self, locations):
        """Get distance matrix from Google Maps API."""
        try:
            # Format locations for Google Maps API
            origins = [f"{loc['lat']},{loc['lng']}" for loc in locations]
            destinations = origins.copy()
            
            # Get distance matrix
            matrix = self.gmaps.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode="driving",
                departure_time=datetime.now()
            )
            
            # Extract distances and durations
            distances = []
            durations = []
            
            for row in matrix['rows']:
                distance_row = []
                duration_row = []
                for element in row['elements']:
                    if element['status'] == 'OK':
                        distance_row.append(element['distance']['value'])  # meters
                        duration_row.append(element['duration']['value'])  # seconds
                    else:
                        distance_row.append(float('inf'))
                        duration_row.append(float('inf'))
                distances.append(distance_row)
                durations.append(duration_row)
            
            return np.array(distances), np.array(durations)
        except Exception as e:
            logger.error(f"Error getting distance matrix: {str(e)}")
            raise
    
    def _create_distance_callback(self, manager, distances):
        """Create distance callback for OR-Tools."""
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distances[from_node][to_node]
        return distance_callback
    
    def _create_duration_callback(self, manager, durations):
        """Create duration callback for OR-Tools."""
        def duration_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return durations[from_node][to_node]
        return duration_callback
    
    def _create_time_window_callback(self, manager, time_windows):
        """Create time window callback for OR-Tools."""
        def time_window_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return time_windows[from_node][to_node]
        return time_window_callback
    
    def optimize(self, locations, time_windows=None, traffic_data=None):
        """Optimize delivery routes considering time windows and traffic."""
        try:
            # Get distance matrix
            distances, durations = self._get_distance_matrix(locations)
            
            # Create routing index manager
            manager = pywrapcp.RoutingIndexManager(
                len(locations),  # number of locations
                1,  # number of vehicles
                0   # depot index
            )
            
            # Create routing model
            routing = pywrapcp.RoutingModel(manager)
            
            # Register distance callback
            distance_callback = self._create_distance_callback(manager, distances)
            routing.RegisterTransitCallback(distance_callback)
            
            # Register duration callback
            duration_callback = self._create_duration_callback(manager, durations)
            routing.RegisterTransitCallback(duration_callback)
            
            # Set cost function
            routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)
            
            # Add time window constraints if provided
            if time_windows:
                time_window_callback = self._create_time_window_callback(manager, time_windows)
                routing.AddDimension(
                    time_window_callback,
                    0,  # no slack
                    Config.ROUTING_TIME_WINDOW,  # maximum time per vehicle
                    False,  # force start cumul to zero
                    'Time'
                )
                time_dimension = routing.GetDimensionOrDie('Time')
                
                # Add time window constraints for each location
                for location_idx, time_window in enumerate(time_windows):
                    index = manager.NodeToIndex(location_idx)
                    time_dimension.CumulVar(index).SetRange(
                        time_window[0],
                        time_window[1]
                    )
            
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
            solution = routing.SolveWithParameters(search_parameters)
            
            if not solution:
                raise Exception("No solution found")
            
            # Extract route
            index = routing.Start(0)
            route = []
            route_distances = []
            route_durations = []
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append(locations[node_index])
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                
                if not routing.IsEnd(index):
                    next_node_index = manager.IndexToNode(index)
                    route_distances.append(distances[node_index][next_node_index])
                    route_durations.append(durations[node_index][next_node_index])
            
            # Calculate route metrics
            total_distance = sum(route_distances)
            total_duration = sum(route_durations)
            
            return {
                'route': route,
                'total_distance': float(total_distance),
                'total_duration': float(total_duration),
                'distance_breakdown': [float(d) for d in route_distances],
                'duration_breakdown': [float(d) for d in route_durations]
            }
        except Exception as e:
            logger.error(f"Error optimizing routes: {str(e)}")
            raise
    
    def get_metrics(self, start_date, end_date):
        """Get routing optimization metrics for a given date range."""
        try:
            # This would typically fetch actual vs optimized values from a database
            # For now, return placeholder metrics
            return {
                'average_route_distance': 15000,  # meters
                'average_route_duration': 1800,  # seconds
                'time_window_violations': 0.05,
                'fuel_efficiency': 0.85,
                'driver_utilization': 0.92
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            raise 