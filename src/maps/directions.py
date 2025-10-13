import googlemaps
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config.settings import Config

class DirectionsAPI:
    """Google Directions API integration for route calculation with traffic"""
    
    def __init__(self):
        """Initialize the Directions API client"""
        self.client = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
    
    def get_routes(self, start_address: str, end_address: str, 
                   departure_time: Optional[datetime] = None) -> Optional[Dict]:
        """
        Get multiple route options with traffic data
        
        Args:
            start_address: Starting address
            end_address: Destination address
            departure_time: When to depart (default: now)
            
        Returns:
            Dictionary containing route information and recommendations
        """
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            # Get multiple route alternatives
            directions_result = self.client.directions(
                origin=start_address,
                destination=end_address,
                mode="driving",
                alternatives=True,
                traffic_model=Config.TRAFFIC_MODEL,
                departure_time=departure_time,
                units="metric"
            )
            
            if not directions_result:
                st.error("No routes found between the specified locations")
                return None
            
            # Process and rank routes
            processed_routes = self._process_routes(directions_result)
            
            return {
                'routes': processed_routes,
                'best_route': self._get_best_route(processed_routes),
                'summary': self._generate_route_summary(processed_routes),
                'departure_time': departure_time
            }
            
        except Exception as e:
            st.error(f"Directions API error: {str(e)}")
            return None
    
    def _process_routes(self, directions_result: List[Dict]) -> List[Dict]:
        """
        Process raw directions data into structured route information
        
        Args:
            directions_result: Raw Google Directions API response
            
        Returns:
            List of processed route dictionaries
        """
        processed_routes = []
        
        for i, route in enumerate(directions_result):
            leg = route['legs'][0]  # Assuming single leg journey
            
            # Extract route information
            route_info = {
                'route_index': i,
                'summary': route.get('summary', f'Route {i+1}'),
                'distance': {
                    'text': leg['distance']['text'],
                    'value': leg['distance']['value']  # in meters
                },
                'duration': {
                    'text': leg['duration']['text'],
                    'value': leg['duration']['value']  # in seconds
                },
                'duration_in_traffic': {
                    'text': leg.get('duration_in_traffic', {}).get('text', 'N/A'),
                    'value': leg.get('duration_in_traffic', {}).get('value', leg['duration']['value'])
                },
                'start_address': leg['start_address'],
                'end_address': leg['end_address'],
                'start_location': leg['start_location'],
                'end_location': leg['end_location'],
                'steps': self._extract_steps(leg['steps']),
                'polyline': route['overview_polyline']['points'],
                'warnings': route.get('warnings', []),
                'traffic_delay': self._calculate_traffic_delay(leg)
            }
            
            # Calculate efficiency score
            route_info['efficiency_score'] = self._calculate_efficiency_score(route_info)
            
            processed_routes.append(route_info)
        
        # Sort routes by efficiency score (higher is better)
        processed_routes.sort(key=lambda x: x['efficiency_score'], reverse=True)
        
        return processed_routes
    
    def _extract_steps(self, steps: List[Dict]) -> List[Dict]:
        """Extract key information from route steps"""
        extracted_steps = []
        
        for step in steps:
            step_info = {
                'instruction': step['html_instructions'],
                'distance': step['distance']['text'],
                'duration': step['duration']['text'],
                'start_location': step['start_location'],
                'end_location': step['end_location']
            }
            extracted_steps.append(step_info)
        
        return extracted_steps
    
    def _calculate_traffic_delay(self, leg: Dict) -> Dict:
        """Calculate traffic delay information"""
        normal_duration = leg['duration']['value']
        traffic_duration = leg.get('duration_in_traffic', {}).get('value', normal_duration)
        
        delay_seconds = traffic_duration - normal_duration
        delay_minutes = delay_seconds / 60
        
        return {
            'delay_seconds': delay_seconds,
            'delay_minutes': round(delay_minutes, 1),
            'delay_percentage': round((delay_seconds / normal_duration) * 100, 1) if normal_duration > 0 else 0
        }
    
    def _calculate_efficiency_score(self, route_info: Dict) -> float:
        """
        Calculate efficiency score for route ranking
        
        Factors considered:
        - Travel time with traffic (40% weight)
        - Distance (30% weight)
        - Traffic delay (30% weight)
        
        Returns:
            Efficiency score (0-100, higher is better)
        """
        try:
            # Normalize values (assuming max reasonable values for NYC)
            max_time = 7200  # 2 hours in seconds
            max_distance = 50000  # 50km in meters
            max_delay = 1800  # 30 minutes in seconds
            
            time_score = max(0, 100 - (route_info['duration_in_traffic']['value'] / max_time * 100))
            distance_score = max(0, 100 - (route_info['distance']['value'] / max_distance * 100))
            delay_score = max(0, 100 - (route_info['traffic_delay']['delay_seconds'] / max_delay * 100))
            
            # Weighted average
            efficiency_score = (time_score * 0.4) + (distance_score * 0.3) + (delay_score * 0.3)
            
            return round(efficiency_score, 2)
            
        except Exception:
            return 50.0  # Default score if calculation fails
    
    def _get_best_route(self, routes: List[Dict]) -> Dict:
        """Get the best route based on efficiency score"""
        if not routes:
            return {}
        
        return routes[0]  # Already sorted by efficiency score
    
    def _generate_route_summary(self, routes: List[Dict]) -> Dict:
        """Generate summary statistics for all routes"""
        if not routes:
            return {}
        
        total_routes = len(routes)
        avg_time = sum(route['duration_in_traffic']['value'] for route in routes) / total_routes
        avg_distance = sum(route['distance']['value'] for route in routes) / total_routes
        avg_delay = sum(route['traffic_delay']['delay_seconds'] for route in routes) / total_routes
        
        return {
            'total_routes': total_routes,
            'average_time_minutes': round(avg_time / 60, 1),
            'average_distance_km': round(avg_distance / 1000, 1),
            'average_delay_minutes': round(avg_delay / 60, 1),
            'time_range': {
                'min_minutes': round(min(route['duration_in_traffic']['value'] for route in routes) / 60, 1),
                'max_minutes': round(max(route['duration_in_traffic']['value'] for route in routes) / 60, 1)
            }
        }
    
    def get_route_polyline_coordinates(self, polyline_string: str) -> List[Tuple[float, float]]:
        """
        Decode polyline string to coordinates for map display
        
        Args:
            polyline_string: Encoded polyline from Google Directions
            
        Returns:
            List of (lat, lng) coordinate tuples
        """
        try:
            return googlemaps.convert.decode_polyline(polyline_string)
        except Exception as e:
            st.error(f"Polyline decoding error: {str(e)}")
            return []